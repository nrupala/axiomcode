"""
AxiomCode public registry — read-only HTTP surface
===================================================
Minimal WSGI application exposing the public certificate registry.
Pure standard library: no dependencies, runs anywhere (wsgiref for local
dev, any WSGI server or serverless adapter in production).

READ-ONLY by construction: there are no mutation endpoints at all.
Publication and revocation happen through the CLI (`axiomcode registry
publish|revoke`), never over HTTP. Non-GET requests get 405.

Endpoints (all GET):
  /                        human storefront (active certificates)
  /health                  {"ok": true}
  /api/registry            JSON list, active only (default storefront view)
  /api/registry?status=all JSON list, full transparency log incl. revoked/expired
  /api/export              machine-readable registry export (agents verify
                           signatures without parsing images)
  /api/cert/<serial>       machine-readable single certificate + live status
  /cert/<serial>           human certificate page (live status, QR, badge snippet)
  /badge/<serial>.svg      badge SVG rendered LIVE from registry data —
                           tamper-evident, always current
  /qr/<serial>.png         QR code PNG encoding the certificate page URL

Configuration via environment:
  AXC_REGISTRY_DIR  path to the registry directory (default: ./registry)
  AXC_BASE_URL      public base URL used in QR payloads and badge snippets
                    (default: http://localhost:8000)
"""

from __future__ import annotations

import html as _html
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from core.badge import badge_data, badge_snippet, render_badge_svg
from core.qr import render_qr_png, verification_url
from core.registry import CertificateRegistry

_SERIAL_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _json_response(start_response, obj, status="200 OK"):
    body = json.dumps(obj, indent=2, sort_keys=True).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


def _html_response(start_response, doc: str, status="200 OK"):
    body = doc.encode("utf-8")
    start_response(status, [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]


def _svg_response(start_response, svg: str, status="200 OK"):
    body = svg.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "image/svg+xml"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-cache"),
        ],
    )
    return [body]


def _png_response(start_response, png: bytes, status="200 OK"):
    start_response(
        status,
        [("Content-Type", "image/png"), ("Content-Length", str(len(png))), ("Cache-Control", "no-cache")],
    )
    return [png]


def _not_found(start_response, what="not found"):
    return _json_response(start_response, {"error": what}, status="404 Not Found")


def _bad_request(start_response, what):
    return _json_response(start_response, {"error": what}, status="400 Bad Request")


def _cert_entry(cert, status: str) -> dict:
    """Machine-readable certificate entry (agent-verifiable identity)."""
    return {
        "serial": cert.serial,
        "status": status,
        "product_name": cert.product_name or cert.algorithm_name,
        "artifact_version": cert.artifact_version,
        "tier": cert.tier,
        "owner": cert.owner,
        "repo_or_website": cert.repo_or_website,
        "verification_status": cert.verification_status,
        "issued_at": cert.issued_at,
        "expires_at": cert.expires_at,
        "artifact_hash": cert.proof_hash,
        "spec_hash": cert.spec_hash,
        "signature": cert.signature,
        "verify_key": cert.verify_key,
        "key_id": cert.key_id,
        "verify_url": cert.qr_payload,
        "issuer": {
            "name": cert.issuer_name,
            "website": cert.issuer_website,
            "contact": cert.issuer_contact,
        },
    }


def create_app(registry_dir: str | Path | None = None, base_url: str | None = None):
    registry_dir = Path(registry_dir or os.environ.get("AXC_REGISTRY_DIR", "registry"))
    base_url = (base_url or os.environ.get("AXC_BASE_URL", "http://localhost:8000")).rstrip("/")
    reg = CertificateRegistry(registry_dir)

    def app(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        if method not in ("GET", "HEAD"):
            # Read-only surface: no mutation over HTTP, ever.
            start_response("405 Method Not Allowed", [("Content-Type", "text/plain")])
            return [b"Method not allowed: this registry is read-only"]
        path = environ.get("PATH_INFO", "/") or "/"
        query = parse_qs(environ.get("QUERY_STRING", ""))
        head_only = method == "HEAD"

        def respond(chunks):
            if head_only:
                # Discard bodies for HEAD but keep headers/status.
                out = []
                for c in chunks:
                    out.append(b"" if isinstance(c, (bytes, bytearray)) else "")
                return out
            return chunks

        # ── /health ──────────────────────────────────────────────────
        if path == "/health":
            return respond(_json_response(start_response, {"ok": True}))

        # ── /api/registry ────────────────────────────────────────────
        if path == "/api/registry":
            status_filter = query.get("status", ["active"])[0]
            if status_filter not in ("active", "all"):
                return respond(_bad_request(start_response, "status must be 'active' or 'all'"))
            return respond(
                _json_response(
                    start_response,
                    {
                        "registry": "AxiomCode Certificate Registry",
                        "status_filter": status_filter,
                        "exported_at": time.time(),
                        "certificates": reg.list_certificates(status_filter=status_filter),
                    },
                )
            )

        # ── /api/export ──────────────────────────────────────────────
        if path == "/api/export":
            body = reg.export_json().encode("utf-8")
            start_response(
                "200 OK",
                [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))],
            )
            return respond([body])

        # ── /api/cert/<serial> ───────────────────────────────────────
        m = re.fullmatch(r"/api/cert/([^/]+)", path)
        if m:
            serial = m.group(1)
            if not _SERIAL_RE.match(serial):
                return respond(_bad_request(start_response, "invalid serial"))
            cert = reg.get(serial)
            if cert is None:
                return respond(_not_found(start_response, f"unknown serial {serial}"))
            return respond(_json_response(start_response, _cert_entry(cert, reg.status(serial))))

        # ── /badge/<serial>.svg ──────────────────────────────────────
        m = re.fullmatch(r"/badge/([^/]+)\.svg", path)
        if m:
            serial = m.group(1)
            if not _SERIAL_RE.match(serial):
                return respond(_bad_request(start_response, "invalid serial"))
            data = badge_data(serial, reg, base_url)
            return respond(_svg_response(start_response, render_badge_svg(data)))

        # ── /qr/<serial>.png ─────────────────────────────────────────
        m = re.fullmatch(r"/qr/([^/]+)\.png", path)
        if m:
            serial = m.group(1)
            if not _SERIAL_RE.match(serial):
                return respond(_bad_request(start_response, "invalid serial"))
            cert = reg.get(serial)
            if cert is None:
                return respond(_not_found(start_response, f"unknown serial {serial}"))
            payload = (cert.qr_payload or "").strip() or verification_url(serial, base_url)
            try:
                png = render_qr_png(payload)
            except RuntimeError as e:
                return respond(_json_response(start_response, {"error": str(e)}, status="503 Service Unavailable"))
            return respond(_png_response(start_response, png))

        # ── /cert/<serial> (human page) ──────────────────────────────
        m = re.fullmatch(r"/cert/([^/]+)", path)
        if m:
            serial = m.group(1)
            if not _SERIAL_RE.match(serial):
                return respond(_bad_request(start_response, "invalid serial"))
            cert = reg.get(serial)
            if cert is None:
                return respond(
                    _html_response(
                        start_response, _page("Unknown certificate", "<p>Unknown serial.</p>"), "404 Not Found"
                    )
                )
            status = reg.status(serial)
            sig_ok = bool(cert.signature) and cert.verify()
            rows = [
                ("Serial", cert.serial),
                ("Status", status.upper()),
                ("Signature", "VALID" if sig_ok else "INVALID"),
                ("Product", cert.product_name or cert.algorithm_name),
                ("Artifact version", cert.artifact_version),
                ("Tier", cert.tier),
                ("Owner", cert.owner),
                ("Repo / website", cert.repo_or_website),
                ("Verification status", cert.verification_status),
                ("Issued", _fmt_ts(cert.issued_at)),
                ("Expires", _fmt_ts(cert.expires_at)),
                ("Issuer", f"{cert.issuer_name} — {cert.issuer_website}"),
            ]
            body_rows = "".join(f"<tr><th>{_html.escape(k)}</th><td>{_html.escape(str(v))}</td></tr>" for k, v in rows)
            snip = badge_snippet(serial, base_url)
            doc = (
                f"<h1>Certificate {_html.escape(serial)}</h1>"
                f'<p><img src="/qr/{_html.escape(serial)}.png" alt="QR code" width="180" height="180"></p>'
                f"<table>{body_rows}</table>"
                "<h2>Embed this badge</h2>"
                f"<pre>{_html.escape(snip['markdown'])}</pre>"
                f"<pre>{_html.escape(snip['html'])}</pre>"
            )
            return respond(_html_response(start_response, _page(f"Certificate {serial}", doc)))

        # ── / (storefront) ───────────────────────────────────────────
        if path == "/":
            entries = reg.list_certificates(status_filter="active")
            items = "".join(
                f'<li><a href="/cert/{_html.escape(e["serial"])}">{_html.escape(e["serial"])}</a> — '
                f"{_html.escape(e['product_name'] or '')} v{_html.escape(e['artifact_version'] or '?')} "
                f"({_html.escape(e['tier'] or '')})</li>"
                for e in entries
            )
            doc = (
                "<h1>AxiomCode Public Certificate Registry</h1>"
                f"<p>{len(entries)} active certificate(s). "
                '<a href="/api/registry?status=all">Full transparency log</a> · '
                '<a href="/api/export">Machine-readable export</a></p>'
                f"<ul>{items or '<li>No active certificates.</li>'}</ul>"
            )
            return respond(_html_response(start_response, _page("AxiomCode Certificate Registry", doc)))

        return respond(_not_found(start_response))

    return app


def _fmt_ts(ts: float) -> str:
    if not ts:
        return "—"
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts))


def _page(title: str, body: str) -> str:
    t = _html.escape(title)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{t}</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:720px;margin:2em auto;padding:0 1em}"
        "table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:.4em .8em;text-align:left}"
        "pre{background:#f4f4f4;padding:.8em;overflow:auto}</style>"
        f"</head><body>{body}</body></html>"
    )


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Serve the AxiomCode public certificate registry (read-only)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--registry-dir", default=os.environ.get("AXC_REGISTRY_DIR", "registry"))
    p.add_argument("--base-url", default=os.environ.get("AXC_BASE_URL", "http://localhost:8000"))
    args = p.parse_args()
    app = create_app(args.registry_dir, args.base_url)
    with make_server(args.host, args.port, app) as httpd:
        print(f"[+] AxiomCode registry serving {args.registry_dir} at http://{args.host}:{args.port} (read-only)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
