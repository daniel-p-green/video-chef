#!/usr/bin/env python3
"""Local, token-authenticated broker for the bundled Premiere UXP connector.

The broker is deliberately narrow: the bundled connector is read-only and only
accepts an allowlisted protocol. It never evaluates arbitrary JavaScript.
"""

from __future__ import annotations

import argparse
import http.client
import json
import plistlib
import queue
import secrets
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "1.0"
CONNECTOR_VERSION = "1.0.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17841
READ_OPERATIONS = {"ping", "snapshot_active_sequence"}


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """HTTP server that avoids HTTPServer's unnecessary reverse-DNS lookup."""

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        self.server_name = DEFAULT_HOST
        self.server_port = self.server_address[1]


def default_config_path() -> Path:
    return Path.home() / ".codex" / "video-chef" / "premiere-bridge.json"


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version in {path}")
    if data.get("host") != DEFAULT_HOST:
        raise ValueError("bridge host must be 127.0.0.1")
    token = data.get("token")
    if not isinstance(token, str) or len(token) < 32:
        raise ValueError("bridge token is missing or too short")
    return data


def initialize_config(path: Path, port: int, force: bool = False) -> dict[str, Any]:
    if path.exists() and not force:
        raise FileExistsError(f"config already exists: {path}")
    if not 1024 <= port <= 65535:
        raise ValueError("port must be between 1024 and 65535")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "protocol_version": PROTOCOL_VERSION,
        "host": DEFAULT_HOST,
        "port": port,
        "token": secrets.token_urlsafe(32),
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return data


@dataclass
class Job:
    operation: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    result: dict[str, Any] | None = None
    event: threading.Event = field(default_factory=threading.Event)


class Broker:
    def __init__(self, token: str) -> None:
        self.token = token
        self.jobs: queue.Queue[Job] = queue.Queue()
        self.inflight: dict[str, Job] = {}
        self.lock = threading.Lock()
        self.connector: dict[str, Any] | None = None

    def enqueue(self, operation: str, payload: dict[str, Any]) -> Job:
        job = Job(operation=operation, payload=payload)
        with self.lock:
            self.inflight[job.id] = job
        self.jobs.put(job)
        return job

    def finish(self, job_id: str, result: dict[str, Any]) -> bool:
        with self.lock:
            job = self.inflight.get(job_id)
        if not job:
            return False
        job.result = result
        job.event.set()
        return True

    def next_job(self) -> Job | None:
        while True:
            try:
                job = self.jobs.get_nowait()
            except queue.Empty:
                return None
            with self.lock:
                if job.id in self.inflight:
                    return job

    def release(self, job_id: str) -> None:
        with self.lock:
            self.inflight.pop(job_id, None)


def make_handler(broker: Broker, request_timeout: float):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VideoChefPremiereBridge/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("bridge: " + (fmt % args) + "\n")

        def _send(self, status: int, body: dict[str, Any] | None = None) -> None:
            encoded = b"" if body is None else json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            if encoded:
                self.wfile.write(encoded)

        def _authorized(self) -> bool:
            return self.headers.get("Authorization") == f"Bearer {broker.token}"

        def _json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("invalid request body size")
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict):
                raise ValueError("JSON body must be an object")
            return value

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send(HTTPStatus.NO_CONTENT)

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            if self.path == "/v1/status":
                self._send(HTTPStatus.OK, {
                    "protocol_version": PROTOCOL_VERSION,
                    "connector": broker.connector,
                    "read_operations": sorted(READ_OPERATIONS),
                    "mutation_enabled": False,
                })
                return
            if self.path == "/v1/connector/next":
                job = broker.next_job()
                if job is None:
                    self._send(HTTPStatus.NO_CONTENT)
                    return
                self._send(HTTPStatus.OK, {
                    "id": job.id,
                    "operation": job.operation,
                    "payload": job.payload,
                    "protocol_version": PROTOCOL_VERSION,
                })
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            try:
                body = self._json()
            except (ValueError, json.JSONDecodeError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            if self.path == "/v1/connector/register":
                if body.get("protocol_version") != PROTOCOL_VERSION:
                    self._send(HTTPStatus.CONFLICT, {"error": "protocol version mismatch"})
                    return
                capabilities = body.get("capabilities")
                if not isinstance(capabilities, list) or not set(capabilities).issubset(READ_OPERATIONS):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid capabilities"})
                    return
                broker.connector = {
                    "connector_version": str(body.get("connector_version", "unknown")),
                    "premiere_version": str(body.get("premiere_version", "unknown")),
                    "capabilities": capabilities,
                    "registered_at": time.time(),
                }
                self._send(HTTPStatus.OK, {"ok": True, "mutation_enabled": False})
                return

            if self.path == "/v1/connector/result":
                job_id = body.get("id")
                result = body.get("result")
                if not isinstance(job_id, str) or not isinstance(result, dict):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "id and result are required"})
                    return
                if not broker.finish(job_id, result):
                    self._send(HTTPStatus.NOT_FOUND, {"error": "unknown job"})
                    return
                self._send(HTTPStatus.OK, {"ok": True})
                return

            if self.path == "/v1/request":
                operation = body.get("operation")
                payload = body.get("payload", {})
                if operation not in READ_OPERATIONS:
                    self._send(HTTPStatus.FORBIDDEN, {
                        "error": "operation is not in the read-only allowlist",
                        "mutation_enabled": False,
                    })
                    return
                if not isinstance(payload, dict):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "payload must be an object"})
                    return
                if not broker.connector:
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Premiere connector is not registered"})
                    return
                if operation not in broker.connector.get("capabilities", []):
                    self._send(HTTPStatus.NOT_IMPLEMENTED, {"error": "connector lacks requested capability"})
                    return
                job = broker.enqueue(operation, payload)
                if not job.event.wait(request_timeout):
                    broker.release(job.id)
                    self._send(HTTPStatus.GATEWAY_TIMEOUT, {"error": "connector response timed out"})
                    return
                result = job.result or {"ok": False, "error": "connector returned no result"}
                broker.release(job.id)
                self._send(HTTPStatus.OK, {"id": job.id, "result": result})
                return

            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    return Handler


def request_bridge(config: dict[str, Any], operation: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps({"operation": operation, "payload": payload}).encode("utf-8")
    connection = http.client.HTTPConnection(config["host"], int(config["port"]), timeout=timeout)
    try:
        connection.request("POST", "/v1/request", body=body, headers={
            "Authorization": f"Bearer {config['token']}",
            "Content-Type": "application/json",
        })
        response = connection.getresponse()
        raw = response.read()
        value = json.loads(raw) if raw else {}
        if not 200 <= response.status < 300:
            raise ValueError(f"bridge returned {response.status}: {value.get('error', 'request failed')}")
        return value
    finally:
        connection.close()


def app_version(app: Path) -> str | None:
    info = app / "Contents" / "Info.plist"
    if not info.is_file():
        return None
    with info.open("rb") as handle:
        return str(plistlib.load(handle).get("CFBundleShortVersionString", "unknown"))


def version_at_least(actual: str | None, required: tuple[int, ...]) -> bool:
    if not actual:
        return False
    try:
        parts = tuple(int(part) for part in actual.split(".")[:len(required)])
    except ValueError:
        return False
    return parts + (0,) * (len(required) - len(parts)) >= required


def doctor(config_path: Path) -> tuple[dict[str, Any], bool]:
    plugin_root = Path(__file__).resolve().parents[1]
    connector = plugin_root / "premiere-uxp" / "video-chef-bridge"
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str, required: bool = True) -> None:
        checks.append({"name": name, "ok": ok, "required": required, "detail": detail})

    applications = Path("/Applications")
    premiere_apps = sorted({
        *applications.glob("Adobe Premiere Pro 20*.app"),
        *applications.glob("Adobe Premiere Pro 20*/Adobe Premiere Pro 20*.app"),
    })
    current = premiere_apps[-1] if premiere_apps else None
    current_version = app_version(current) if current else None
    check("Premiere Pro 25.6+", version_at_least(current_version, (25, 6, 0)), f"{current}: {current_version or 'not found'}")
    udt = Path("/Applications/Adobe UXP Developer Tools/Adobe UXP Developer Tools.app")
    if not udt.exists():
        udt = Path("/Applications/Adobe UXP Developer Tools.app")
    udt_version = app_version(udt) if udt.exists() else None
    check("Adobe UXP Developer Tool 2.2+", version_at_least(udt_version, (2, 2, 0)), f"{udt}: {udt_version or 'not found'}")
    manifest_path = connector / "manifest.json"
    check("Bundled UXP manifest", manifest_path.is_file(), str(manifest_path))
    check("Bundled UXP runtime", (connector / "index.html").is_file() and (connector / "main.js").is_file(), str(connector))
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            domains = manifest.get("requiredPermissions", {}).get("network", {}).get("domains", [])
            safe = domains == [f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"]
            check("Localhost-only network permission", safe, json.dumps(domains))
        except (OSError, json.JSONDecodeError) as exc:
            check("UXP manifest parses", False, str(exc))
    capabilities_path = connector / "capabilities.json"
    try:
        capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
        safe_capabilities = capabilities.get("mutationEnabled") is False and set(capabilities.get("capabilities", [])) == READ_OPERATIONS
        check("Read-only connector declaration", safe_capabilities, str(capabilities_path))
    except (OSError, json.JSONDecodeError) as exc:
        check("Read-only connector declaration", False, str(exc))
    try:
        config = load_config(config_path)
        mode = config_path.stat().st_mode & 0o777
        check("Bridge config", True, str(config_path))
        check("Bridge config permissions", mode & 0o077 == 0, oct(mode))
        check("Connector port alignment", int(config.get("port", 0)) == DEFAULT_PORT, f"configured {config.get('port')}; connector requires {DEFAULT_PORT}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        check("Bridge config", False, f"{config_path}: {exc}", required=False)
    passed = all(item["ok"] for item in checks if item["required"])
    return {"passed": passed, "checks": checks, "mutation_enabled": False}, passed


def parse_payload(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=default_config_path())
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a private localhost bridge configuration")
    init.add_argument("--port", type=int, default=DEFAULT_PORT)
    init.add_argument("--force", action="store_true")

    doc = sub.add_parser("doctor", help="check local Premiere bridge prerequisites")
    doc.add_argument("--json", action="store_true")

    serve = sub.add_parser("serve", help="run the localhost-only broker")
    serve.add_argument("--request-timeout", type=float, default=30.0)

    req = sub.add_parser("request", help="send an allowlisted read request")
    req.add_argument("operation", choices=sorted(READ_OPERATIONS))
    req.add_argument("--payload", default="{}")
    req.add_argument("--timeout", type=float, default=35.0)

    args = parser.parse_args()
    try:
        if args.command == "init":
            data = initialize_config(args.config, args.port, args.force)
            print(json.dumps({"config": str(args.config), "host": data["host"], "port": data["port"]}, indent=2))
            print("Paste the token from the private config into the Video Chef Bridge panel; do not share it.", file=sys.stderr)
            return 0
        if args.command == "doctor":
            report, passed = doctor(args.config)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for item in report["checks"]:
                    marker = "PASS" if item["ok"] else ("WARN" if not item["required"] else "FAIL")
                    print(f"{marker:4} {item['name']}: {item['detail']}")
                print("PASS" if passed else "FAIL")
            return 0 if passed else 2
        config = load_config(args.config)
        if args.command == "serve":
            broker = Broker(config["token"])
            server = LocalThreadingHTTPServer((config["host"], int(config["port"])), make_handler(broker, args.request_timeout))
            print(f"Video Chef Premiere Bridge listening on http://{config['host']}:{config['port']}", flush=True)
            server.serve_forever()
            return 0
        if args.command == "request":
            print(json.dumps(request_bridge(config, args.operation, parse_payload(args.payload), args.timeout), indent=2))
            return 0
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError, http.client.HTTPException) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
