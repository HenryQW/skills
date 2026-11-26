"""Bind a foreground preview command to this machine's active Tailscale address."""

import ipaddress
import json
import os
import subprocess
import sys


def main(args):
    if not args or "{host}" not in args[1:]:
        raise SystemExit("Pass the server command with {host} as its bind address.")
    status = json.loads(subprocess.check_output(["tailscale", "status", "--json"]))
    if status.get("BackendState") != "Running":
        raise SystemExit("Start Tailscale before sharing a preview.")
    addresses = (ipaddress.ip_address(ip) for ip in status["Self"]["TailscaleIPs"])
    host = next((str(ip) for ip in addresses if ip.version == 4), None)
    if host is None:
        raise SystemExit("Tailscale has no IPv4 address for this machine.")
    print(f"Preview host: {host}. Use the port reported by the server.", flush=True)
    os.execvp(args[0], [host if arg == "{host}" else arg for arg in args])


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        raise SystemExit(f"Cannot start preview: {error}") from None
