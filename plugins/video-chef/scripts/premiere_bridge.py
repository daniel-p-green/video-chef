#!/usr/bin/env python3
"""Local, token-authenticated broker for the bundled Premiere UXP connector.

The broker is deliberately narrow: the bundled connector is read-only and only
accepts an allowlisted protocol. It never evaluates arbitrary JavaScript.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import plistlib
import queue
import secrets
import shutil
import socketserver
import ssl
import subprocess
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
CONNECTOR_VERSION = "1.2.2"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 17841
CONNECTOR_STALE_AFTER = 5.0
READ_OPERATIONS = {"ping", "snapshot_active_sequence"}
TLS_CERT_NAME = "premiere-bridge-cert.pem"
TLS_KEY_NAME = "premiere-bridge-key.pem"


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """HTTP server that avoids HTTPServer's unnecessary reverse-DNS lookup."""

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        self.server_name = DEFAULT_HOST
        self.server_port = self.server_address[1]


def default_config_path() -> Path:
    return Path.home() / ".codex" / "video-chef" / "premiere-bridge.json"


def default_tls_paths(config_path: Path) -> tuple[Path, Path]:
    return config_path.parent / TLS_CERT_NAME, config_path.parent / TLS_KEY_NAME


def mkcert_ca_path() -> Path | None:
    executable = shutil.which("mkcert")
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, "-CAROOT"], check=False, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    root = Path(completed.stdout.strip()) / "rootCA.pem"
    return root if root.is_file() else None


def setup_tls(cert_path: Path, key_path: Path, force: bool = False) -> Path:
    executable = shutil.which("mkcert")
    if not executable:
        raise ValueError("mkcert is required; install it first and review its local-CA security model")
    if (cert_path.exists() or key_path.exists()) and not force:
        raise FileExistsError(f"TLS material already exists: {cert_path} or {key_path}")
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = secrets.token_hex(8)
    staged_cert = cert_path.with_name(f".{cert_path.name}.{suffix}.tmp")
    staged_key = key_path.with_name(f".{key_path.name}.{suffix}.tmp")
    try:
        completed = subprocess.run([
            executable,
            "-cert-file", str(staged_cert),
            "-key-file", str(staged_key),
            DEFAULT_HOST, "localhost", "::1",
        ], check=False, capture_output=True, text=True, timeout=30)
        if completed.returncode != 0:
            raise ValueError(completed.stderr.strip() or "mkcert failed")
        staged_cert.chmod(0o644)
        staged_key.chmod(0o600)
        os.replace(staged_key, key_path)
        os.replace(staged_cert, cert_path)
    finally:
        staged_cert.unlink(missing_ok=True)
        staged_key.unlink(missing_ok=True)
    ca_path = mkcert_ca_path()
    if not ca_path:
        raise ValueError("mkcert created the leaf certificate but its rootCA.pem was not found")
    return ca_path


def client_ssl_context(ca_cert: Path | None) -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=str(ca_cert) if ca_cert and ca_cert.is_file() else None)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def make_https_connection(
    config: dict[str, Any], timeout: float, ca_cert: Path | None
) -> http.client.HTTPSConnection:
    return http.client.HTTPSConnection(
        config["host"], int(config["port"]), timeout=timeout, context=client_ssl_context(ca_cert)
    )


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

    def register(self, details: dict[str, Any]) -> None:
        now = time.time()
        with self.lock:
            self.connector = {
                **details,
                "registered_at": now,
                "last_seen_at": now,
            }

    def touch_connector(self, instance_id: str | None = None) -> bool:
        with self.lock:
            if not self.connector:
                return False
            registered_id = self.connector.get("instance_id")
            if instance_id and registered_id != instance_id:
                return False
            self.connector["last_seen_at"] = time.time()
            return True

    def unregister(self, instance_id: str | None) -> bool:
        with self.lock:
            if not self.connector:
                return False
            registered_id = self.connector.get("instance_id")
            if instance_id and registered_id and instance_id != registered_id:
                return False
            self.connector = None
            return True

    def connector_status(self) -> dict[str, Any] | None:
        with self.lock:
            connector = dict(self.connector) if self.connector else None
        if not connector:
            return None
        age = max(0.0, time.time() - float(connector.get("last_seen_at", 0.0)))
        connector["last_seen_seconds_ago"] = round(age, 3)
        connector["connected"] = age <= CONNECTOR_STALE_AFTER
        return connector

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
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Video-Chef-Connector-ID")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Private-Network", "true")
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
                connector = broker.connector_status()
                self._send(HTTPStatus.OK, {
                    "protocol_version": PROTOCOL_VERSION,
                    "connector": connector,
                    "connected": bool(connector and connector["connected"]),
                    "read_operations": sorted(READ_OPERATIONS),
                    "mutation_enabled": False,
                })
                return
            if self.path == "/v1/connector/next":
                instance_id = self.headers.get("X-Video-Chef-Connector-ID")
                if not instance_id or not broker.touch_connector(instance_id):
                    self._send(HTTPStatus.CONFLICT, {"error": "connector instance is not current"})
                    return
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
                instance_id = body.get("instance_id")
                if not isinstance(instance_id, str) or not 8 <= len(instance_id) <= 128:
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "valid connector instance_id is required"})
                    return
                broker.register({
                    "instance_id": instance_id,
                    "connector_version": str(body.get("connector_version", "unknown")),
                    "premiere_version": str(body.get("premiere_version", "unknown")),
                    "capabilities": capabilities,
                })
                self._send(HTTPStatus.OK, {"ok": True, "mutation_enabled": False})
                return

            if self.path == "/v1/connector/unregister":
                instance_id = body.get("instance_id")
                if not isinstance(instance_id, str):
                    self._send(HTTPStatus.BAD_REQUEST, {"error": "connector instance_id is required"})
                    return
                removed = broker.unregister(instance_id)
                self._send(HTTPStatus.OK, {"ok": True, "removed": removed})
                return

            if self.path == "/v1/connector/result":
                instance_id = self.headers.get("X-Video-Chef-Connector-ID")
                if not instance_id or not broker.touch_connector(instance_id):
                    self._send(HTTPStatus.CONFLICT, {"error": "connector instance is not current"})
                    return
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
                connector = broker.connector_status()
                if not connector:
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Premiere connector is not registered"})
                    return
                if not connector["connected"]:
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Premiere connector heartbeat is stale"})
                    return
                if operation not in connector.get("capabilities", []):
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


def request_bridge(
    config: dict[str, Any], operation: str, payload: dict[str, Any], timeout: float,
    ca_cert: Path | None,
) -> dict[str, Any]:
    body = json.dumps({"operation": operation, "payload": payload}).encode("utf-8")
    connection = make_https_connection(config, timeout, ca_cert)
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


def bridge_status(config: dict[str, Any], timeout: float, ca_cert: Path | None) -> dict[str, Any]:
    connection = make_https_connection(config, timeout, ca_cert)
    try:
        connection.request("GET", "/v1/status", headers={"Authorization": f"Bearer {config['token']}"})
        response = connection.getresponse()
        raw = response.read()
        value = json.loads(raw) if raw else {}
        if not 200 <= response.status < 300:
            raise ValueError(f"bridge returned {response.status}: {value.get('error', 'status failed')}")
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


def doctor(
    config_path: Path, cert_path: Path | None = None, key_path: Path | None = None
) -> tuple[dict[str, Any], bool]:
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
    if sys.platform == "darwin":
        developer_settings = Path("/Library/Application Support/Adobe/UXP/Developer/settings.json")
    elif sys.platform == "win32":
        common_files = os.environ.get("CommonProgramFiles")
        developer_settings = Path(common_files) / "Adobe" / "UXP" / "Developer" / "settings.json" if common_files else None
    else:
        developer_settings = None
    if developer_settings:
        try:
            developer_mode = json.loads(developer_settings.read_text(encoding="utf-8")).get("developer") is True
        except (OSError, json.JSONDecodeError):
            developer_mode = False
        check("Adobe UXP developer mode", developer_mode, str(developer_settings))
    manifest_path = connector / "manifest.json"
    check("Bundled UXP manifest", manifest_path.is_file(), str(manifest_path))
    check("Bundled UXP runtime", (connector / "index.html").is_file() and (connector / "main.js").is_file(), str(connector))
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            domains = manifest.get("requiredPermissions", {}).get("network", {}).get("domains", [])
            safe = domains == ["https://localhost"]
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
    default_cert, default_key = default_tls_paths(config_path)
    cert_path = cert_path or default_cert
    key_path = key_path or default_key
    check("Bridge TLS certificate", cert_path.is_file(), str(cert_path))
    check("Bridge TLS private key", key_path.is_file(), str(key_path))
    if key_path.is_file():
        key_mode = key_path.stat().st_mode & 0o777
        check("Bridge TLS private-key permissions", key_mode & 0o077 == 0, oct(key_mode))
    if cert_path.is_file() and key_path.is_file():
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
            check("Bridge TLS key pair", True, str(cert_path))
        except (OSError, ssl.SSLError) as exc:
            check("Bridge TLS key pair", False, str(exc))
        if sys.platform == "darwin":
            try:
                trusted = subprocess.run(
                    ["security", "verify-cert", "-c", str(cert_path), "-p", "ssl", "-s", DEFAULT_HOST],
                    check=False, capture_output=True, text=True, timeout=15,
                )
                detail = trusted.stderr.strip() or trusted.stdout.strip() or "macOS trust evaluation passed"
                check("Bridge TLS trusted by macOS", trusted.returncode == 0, detail)
            except (OSError, subprocess.SubprocessError) as exc:
                check("Bridge TLS trusted by macOS", False, str(exc))
    ca_path = mkcert_ca_path()
    check("mkcert local CA", ca_path is not None, str(ca_path or "not found"), required=False)
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


def write_json_output(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        staged.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument("--cert", type=Path, help="TLS leaf certificate (defaults beside the private config)")
    parser.add_argument("--key", type=Path, help="TLS private key (defaults beside the private config)")
    parser.add_argument("--ca-cert", type=Path, help="CA certificate for broker client verification")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a private localhost bridge configuration")
    init.add_argument("--port", type=int, default=DEFAULT_PORT)
    init.add_argument("--force", action="store_true")

    tls = sub.add_parser("setup-tls", help="generate a per-machine HTTPS leaf certificate with mkcert")
    tls.add_argument("--force", action="store_true")

    doc = sub.add_parser("doctor", help="check local Premiere bridge prerequisites")
    doc.add_argument("--json", action="store_true")

    serve = sub.add_parser("serve", help="run the localhost-only broker")
    serve.add_argument("--request-timeout", type=float, default=30.0)

    status = sub.add_parser("status", help="report authenticated broker and connector liveness")
    status.add_argument("--timeout", type=float, default=3.0)

    req = sub.add_parser("request", help="send an allowlisted read request")
    req.add_argument("operation", choices=sorted(READ_OPERATIONS))
    req.add_argument("--payload", default="{}")
    req.add_argument("--timeout", type=float, default=35.0)
    req.add_argument("--output", type=Path, help="atomically write the broker envelope as JSON")

    args = parser.parse_args()
    default_cert, default_key = default_tls_paths(args.config)
    cert_path = args.cert or default_cert
    key_path = args.key or default_key
    ca_cert = args.ca_cert or mkcert_ca_path()
    try:
        if args.command == "init":
            data = initialize_config(args.config, args.port, args.force)
            print(json.dumps({"config": str(args.config), "host": data["host"], "port": data["port"]}, indent=2))
            print("Paste the token from the private config into the Video Chef Bridge panel; do not share it.", file=sys.stderr)
            return 0
        if args.command == "setup-tls":
            ca_path = setup_tls(cert_path, key_path, args.force)
            print(json.dumps({
                "certificate": str(cert_path),
                "private_key": str(key_path),
                "ca_certificate": str(ca_path),
            }, indent=2))
            print(
                "Run doctor next. If macOS trust fails, review mkcert's security model and explicitly run `mkcert -install`.",
                file=sys.stderr,
            )
            return 0
        if args.command == "doctor":
            report, passed = doctor(args.config, cert_path, key_path)
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
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
            tls_context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
            server.socket = tls_context.wrap_socket(server.socket, server_side=True)
            print(f"Video Chef Premiere Bridge listening on https://{config['host']}:{config['port']}", flush=True)
            server.serve_forever()
            return 0
        if args.command == "status":
            value = bridge_status(config, args.timeout, ca_cert)
            print(json.dumps(value, indent=2))
            return 0 if value.get("connected") is True else 2
        if args.command == "request":
            value = request_bridge(
                config, args.operation, parse_payload(args.payload), args.timeout, ca_cert
            )
            if args.output:
                write_json_output(args.output, value)
                print(str(args.output))
            else:
                print(json.dumps(value, indent=2))
            return 0
    except (
        OSError, ValueError, json.JSONDecodeError, urllib.error.URLError,
        http.client.HTTPException, subprocess.SubprocessError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
