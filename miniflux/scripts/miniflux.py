#!/usr/bin/env python3
"""Configured, bounded native Miniflux API access using the Python standard library."""

import argparse
import base64
import json
import os
import sys
from contextlib import nullcontext
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class AccessError(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


SECRET_FIELDS = {
    "api_key", "token", "password", "cookie", "authorization", "x-auth-token",
    "proxy_url", "apprise_service_urls", "webhook_url",
}
ROOT_PROBES = {"/liveness", "/healthz", "/readiness", "/readyz"}


def secrets_in(value):
    if isinstance(value, dict):
        return [v for k, v in value.items() if k.lower() in SECRET_FIELDS and isinstance(v, str) and v] + [s for v in value.values() for s in secrets_in(v)]
    if isinstance(value, list):
        return [s for v in value for s in secrets_in(v)]
    return []


def scrub(value, secrets):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in SECRET_FIELDS else scrub(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in sorted(set(secrets), key=len, reverse=True):
            value = value.replace(secret, "[REDACTED]")
    return value


def configuration(args):
    config_path = args.config if args.config is not None else os.environ.get("MINIFLUX_CONFIG")
    if config_path is not None:
        try:
            config = json.loads(Path(config_path).read_text())
        except (OSError, ValueError) as error:
            raise AccessError("Cannot read Miniflux JSON config; check its path, permissions, and syntax") from error
    else:
        config = {key: os.environ[env] for key, env in {
            "url": "MINIFLUX_URL", "api_key": "MINIFLUX_API_KEY",
            "username": "MINIFLUX_USERNAME", "password": "MINIFLUX_PASSWORD",
        }.items() if env in os.environ}
    allowed = {"url", "api_key", "username", "password"}
    if not isinstance(config, dict) or config.keys() - allowed:
        raise AccessError("Config must be an object with only url, api_key, username, password")
    if any(not isinstance(v, str) or not v.strip() or any(ord(c) < 32 or ord(c) == 127 for c in v) for v in config.values()):
        raise AccessError("Configured values must be non-empty strings without control characters")
    if "url" not in config:
        raise AccessError("Missing Miniflux URL: set MINIFLUX_URL or configure url")
    token = "api_key" in config
    basic = "username" in config or "password" in config
    if token == basic or basic and not {"username", "password"} <= config.keys():
        raise AccessError("Require exactly one auth method: MINIFLUX_API_KEY or both MINIFLUX_USERNAME and MINIFLUX_PASSWORD (equivalent config fields)")
    url = config["url"].rstrip("/")
    try:
        parsed = urlsplit(url)
        parsed.port
    except ValueError as error:
        raise AccessError("Invalid Miniflux instance URL") from error
    if (not parsed.hostname or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or any(c.isspace() for c in url) or parsed.path.endswith("/v1")):
        raise AccessError("URL must be an instance base URL without credentials, query, fragment, or /v1 suffix")
    if parsed.scheme not in {"https", "http"} or parsed.scheme == "http" and not args.allow_http:
        raise AccessError("HTTPS is required; --allow-http explicitly permits trusted plaintext HTTP")
    if token:
        headers = {"X-Auth-Token": config["api_key"]}
    else:
        if ":" in config["username"]:
            raise AccessError("Basic-auth username cannot contain a colon")
        credential = base64.b64encode(f'{config["username"]}:{config["password"]}'.encode()).decode()
        headers = {"Authorization": "Basic " + credential}
    return url, f"{parsed.scheme}://{parsed.netloc}", headers, secrets_in(config) + list(headers.values())


def read_body(args):
    filename = args.json if args.json is not None else args.body
    if filename is None:
        return None, None, []
    raw = sys.stdin.buffer.read() if filename == "-" else Path(filename).read_bytes()
    if args.json is not None:
        try:
            value = json.loads(raw)
        except ValueError as error:
            raise AccessError("Request file/stdin is not valid JSON") from error
        return raw, "application/json", secrets_in(value)
    return raw, "application/xml", []


def execute(args):
    base, origin, headers, secrets = configuration(args)
    if args.timeout <= 0:
        raise AccessError("Timeout must be a positive number of seconds")
    method, path = args.method, args.path
    if (not (path.startswith("/v1/") or path in ROOT_PROBES | {"/healthcheck", "/version"})
            or any(c.isspace() for c in path) or any(c in path for c in "?#\\")
            or any(segment in {".", ".."} for segment in unquote(path).split("/"))):
        raise AccessError("Path must be a native /v1/... route or documented probe/version path, without query, fragment, or traversal")
    pairs = []
    for item in args.query:
        key, separator, value = item.partition("=")
        if not separator or not key:
            raise AccessError("Each --query must be KEY=VALUE")
        pairs.append((key, value))
    writing = method != "GET" or unquote(path).endswith("/fetch-content") and any(k == "update_content" and v != "false" for k, v in pairs)
    if writing and not args.allow_write:
        raise AccessError("Mutation refused: require authorized --allow-write (including fetch-content updates)")
    body, content_type, body_secrets = read_body(args)
    if method == "GET" and body is not None:
        raise AccessError("GET requests cannot have a body")
    secrets += body_secrets
    if content_type:
        headers["Content-Type"] = content_type
    url = (origin if path in ROOT_PROBES else base) + path
    if pairs:
        url += "?" + urlencode(pairs)
    # Reserve before sending: a bad/existing output path must not cause a mutation.
    destination = os.fdopen(os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") if args.output else nullcontext(None)
    with destination as file:
        try:
            with build_opener(NoRedirects()).open(Request(url, data=body, headers=headers, method=method), timeout=args.timeout) as response:
                status, media_type, raw = response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            detail = ""
            try:
                data = json.loads(error.read())
                if isinstance(data, dict) and isinstance(data.get("error_message"), str):
                    detail = ": " + json.dumps(scrub(data["error_message"], secrets)[:500])
            except ValueError:
                pass
            raise AccessError(f"{method} {scrub(path, secrets)}: HTTP {error.code}{detail}") from error
        except (URLError, TimeoutError, HTTPException) as error:
            raise AccessError(f"{method} {scrub(path, secrets)}: network/TLS failure; verify instance reachability and certificate trust") from error
        if args.command == "check":
            try:
                data = json.loads(raw)
            except ValueError as error:
                raise AccessError("Authentication check did not return a JSON Miniflux identity") from error
            if not isinstance(data, dict) or not {"id", "username"} <= data.keys():
                raise AccessError("Authentication check did not return a valid Miniflux identity")
            return {"status": status, "user": scrub({k: data[k] for k in ("id", "username", "is_admin") if k in data}, secrets)}
        if file is not None:
            file.write(raw)
            return {"status": status, "saved": True, "bytes": len(raw)}
        if not raw:
            return {"status": status}
        try:
            data = json.loads(raw)
        except ValueError:
            return {"status": status, "content_type": media_type, "bytes": len(raw), "note": "Use --output FILE to save non-JSON response bytes"}
        return {"status": status, "data": scrub(data, secrets + secrets_in(data))}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--config", help="JSON configuration file; otherwise MINIFLUX_CONFIG or environment credentials")
    cli.add_argument("--allow-http", action="store_true", help="explicitly permit trusted plaintext HTTP")
    cli.add_argument("--timeout", type=int, default=30, help="request timeout in seconds (default: 30)")
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="authenticate via GET /v1/me; emit minimal identity").set_defaults(
        method="GET", path="/v1/me", query=[], json=None, body=None, allow_write=False, output=None)
    request = commands.add_parser("request", help="send one configured native API request; never retry automatically")
    request.add_argument("method", choices=("GET", "POST", "PUT", "DELETE"))
    request.add_argument("path", help="native API path; base path is preserved")
    request.add_argument("--query", action="append", default=[], metavar="KEY=VALUE", help="repeat for multiple query fields or values")
    bodies = request.add_mutually_exclusive_group()
    bodies.add_argument("--json", metavar="FILE", help="JSON body file, or - for stdin")
    bodies.add_argument("--body", metavar="FILE", help="OPML XML body file, or - for stdin")
    request.add_argument("--allow-write", action="store_true", help="send an explicitly authorized mutation")
    request.add_argument("--output", metavar="FILE", help="save exact response bytes to a NEW private file instead of redacted terminal JSON")
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = execute(args)
    except AccessError as error:
        print(f"miniflux: {error}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as error:
        print(f"miniflux: local I/O or transport failure ({type(error).__name__}); check input/output paths and connection; existing output files are never overwritten", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
