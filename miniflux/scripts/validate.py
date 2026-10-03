#!/usr/bin/env python3
"""Offline HTTP-boundary regressions for configured Miniflux access."""

import base64
import io
import json
import os
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import miniflux


class APIHandler(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.calls.append((self.command, self.path, dict(self.headers), body))
        path = urlsplit(self.path).path
        status, media_type = 200, "application/json"
        data = {"ok": True}
        if path == "/base/v1/me":
            data = {"id": 7, "username": "reader", "is_admin": False, "password": "not-for-output"}
        elif path == "/base/v1/entries" and self.command == "PUT":
            status, data = 204, None
        elif path == "/base/v1/api-keys":
            data = [{"token": "private-response-token", "feed": {"password": "private-feed-password"}, "content": "private-response-token"}]
        elif path == "/base/v1/feeds/unauthorized":
            status, data = 401, {"error_message": "denied env-token and private-echo", "password": "private-echo"}
        elif path == "/base/v1/feeds/redirect":
            self.send_response(302)
            self.send_header("Location", "/base/v1/api-keys")
            self.end_headers()
            return
        elif path == "/base/v1/export":
            media_type, data = "application/xml", b"<opml/>"
        elif path == "/liveness":
            media_type, data = "text/plain", b"OK"
        elif self.command == "POST":
            status = 201
        self.send_response(status)
        self.send_header("Content-Type", media_type)
        self.end_headers()
        if data is not None:
            self.wfile.write(data if isinstance(data, bytes) else json.dumps(data).encode())

    do_POST = do_PUT = do_DELETE = do_GET


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), APIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/base"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        APIHandler.calls.clear()
        environment = patch.dict(os.environ, {"MINIFLUX_URL": self.url, "MINIFLUX_API_KEY": "env-token"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def run_cli(self, *args, http=True):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = miniflux.main((["--allow-http"] if http else []) + list(args))
        return status, out.getvalue(), err.getvalue()

    def test_configuration_rejects_before_network(self):
        for environment, http in [
            ({}, True),
            ({"MINIFLUX_URL": self.url}, True),
            ({"MINIFLUX_URL": self.url, "MINIFLUX_USERNAME": "reader"}, True),
            ({"MINIFLUX_URL": self.url, "MINIFLUX_API_KEY": "env-token", "MINIFLUX_PASSWORD": "other-secret"}, True),
            ({"MINIFLUX_URL": self.url, "MINIFLUX_API_KEY": "env-token"}, False),
            ({"MINIFLUX_URL": "https://reader:secret@example.com", "MINIFLUX_API_KEY": "env-token"}, True),
            ({"MINIFLUX_URL": self.url, "MINIFLUX_API_KEY": "env-token", "MINIFLUX_CONFIG": "/missing/miniflux.json"}, True),
        ]:
            with self.subTest(environment=list(environment), http=http), patch.dict(os.environ, environment, clear=True):
                code, out, err = self.run_cli("check", http=http)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertTrue(err)
        self.assertEqual(APIHandler.calls, [])

    def test_token_and_isolated_basic_config_authentication(self):
        code, out, err = self.run_cli("check")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["user"], {"id": 7, "username": "reader", "is_admin": False})
        self.assertEqual(APIHandler.calls[-1][2]["X-Auth-Token"], "env-token")
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"url": self.url, "username": "reader", "password": "basic-secret"}))
            code, out, err = self.run_cli("--config", str(config), "check")
        self.assertEqual((code, err), (0, ""))
        headers = APIHandler.calls[-1][2]
        self.assertEqual(headers["Authorization"], "Basic " + base64.b64encode(b"reader:basic-secret").decode())
        self.assertNotIn("X-Auth-Token", headers)  # File config must not merge environment auth.

    def test_repeated_queries_and_json_xml_bodies(self):
        code, _, err = self.run_cli("request", "GET", "/v1/entries", "--query", "status=read", "--query", "status=unread", "--query", "starred=false", "--query", "search=a & b")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(parse_qs(urlsplit(APIHandler.calls[-1][1]).query), {"status": ["read", "unread"], "starred": ["false"], "search": ["a & b"]})
        with tempfile.TemporaryDirectory() as directory:
            body = Path(directory) / "body"
            for option, payload, route, media_type in [
                ("--json", '{"url":"https://example.org"}', "/v1/discover", "application/json"),
                ("--body", "<opml/>", "/v1/import", "application/xml"),
            ]:
                body.write_text(payload)
                code, out, err = self.run_cli("request", "POST", route, "--allow-write", option, str(body))
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["status"], 201)
                headers, sent = APIHandler.calls[-1][2:]
                self.assertEqual(headers["Content-Type"], media_type)
                if option == "--json":
                    self.assertEqual(json.loads(sent), json.loads(payload))
                else:
                    self.assertEqual(sent, payload.encode())
            body.write_text('{"limit": NaN}')
            count = len(APIHandler.calls)
            self.assertEqual(self.run_cli("request", "POST", "/v1/discover", "--allow-write", "--json", str(body))[0], 1)
            self.assertEqual(len(APIHandler.calls), count)

    def test_mutation_gate_and_empty_success(self):
        for command in [
            ("request", "PUT", "/v1/entries"),
            ("request", "GET", "/v1/entries/1/fetch-content", "--query", "update_content=1"),
            ("request", "GET", "/v1/entries/1/%66etch-content", "--query", "update_content=true"),
            ("request", "GET", "https://other.example/v1/me"),
            ("request", "GET", "/v1/../article"),
        ]:
            self.assertEqual(self.run_cli(*command)[0], 1)
        self.assertEqual(APIHandler.calls, [])
        self.assertEqual(self.run_cli("request", "GET", "/v1/entries/1/fetch-content", "--query", "update_content=false")[0], 0)
        code, out, err = self.run_cli("request", "PUT", "/v1/entries", "--allow-write")
        self.assertEqual((code, json.loads(out), err), (0, {"status": 204}, ""))

    def test_redaction_errors_and_refused_redirect(self):
        code, out, err = self.run_cli("request", "GET", "/v1/api-keys")
        self.assertEqual((code, err), (0, ""))
        self.assertNotIn("private-response-token", out)
        self.assertNotIn("private-feed-password", out)
        code, _, err = self.run_cli("request", "GET", "/v1/feeds/unauthorized")
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", err)
        self.assertNotIn("env-token", err)
        self.assertNotIn("private-echo", err)
        count = len(APIHandler.calls)
        code, _, err = self.run_cli("request", "GET", "/v1/feeds/redirect")
        self.assertEqual(code, 1)
        self.assertIn("HTTP 302", err)
        self.assertEqual(len(APIHandler.calls), count + 1)

    def test_private_exact_output_and_no_overwrite_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "response"
            code, out, err = self.run_cli("request", "GET", "/v1/api-keys", "--output", str(output))
            self.assertEqual((code, err), (0, ""))
            self.assertIn("private-response-token", output.read_text())
            self.assertNotIn("private-response-token", out)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            count = len(APIHandler.calls)
            self.assertEqual(self.run_cli("request", "PUT", "/v1/entries", "--allow-write", "--output", str(output))[0], 1)
            self.assertEqual(len(APIHandler.calls), count)
            xml = Path(directory) / "opml"
            self.assertEqual(self.run_cli("request", "GET", "/v1/export", "--output", str(xml))[0], 0)
            self.assertEqual(xml.read_bytes(), b"<opml/>")

    def test_root_probe_and_non_miniflux_identity(self):
        self.assertEqual(self.run_cli("request", "GET", "/liveness")[0], 0)
        self.assertEqual(APIHandler.calls[-1][1], "/liveness")
        os.environ["MINIFLUX_URL"] = self.url.replace("/base", "/other")
        code, _, err = self.run_cli("check")
        self.assertEqual(code, 1)
        self.assertIn("Miniflux identity", err)


if __name__ == "__main__":
    unittest.main()
