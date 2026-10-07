"""
AxiomCode QR code rendering
============================
Renders the certificate's QR payload (the public certificate verification
URL) as real QR code images (PNG/SVG) embedded in certificate artifacts.

Uses `segno` — pure Python, zero dependencies — so the QR path stays
dependency-light and portable.
"""

from __future__ import annotations

try:
    import segno
except ImportError:  # pragma: no cover - exercised when segno missing
    segno = None  # type: ignore[assignment]


def _require_segno() -> None:
    if segno is None:
        raise RuntimeError(
            "QR rendering requires the 'segno' package (pip install segno). It is listed in requirements.txt."
        )


def verification_url(serial: str, base_url: str) -> str:
    """Canonical public verification URL for a certificate serial.

    This is what the QR code encodes: the public certificate page showing
    live status (active / expired / revoked).
    """
    if not serial or not str(serial).strip():
        raise ValueError("Cannot build a verification URL without a serial number")
    if not base_url or not str(base_url).strip():
        raise ValueError("Cannot build a verification URL without a base URL")
    return f"{base_url.rstrip('/')}/cert/{serial}"


def render_qr_png(payload: str, scale: int = 8, border: int = 2) -> bytes:
    """Render a QR code PNG for the given payload. Returns PNG bytes."""
    _require_segno()
    if not payload or not str(payload).strip():
        raise ValueError("QR payload must be a non-empty string")
    qr = segno.make(str(payload), error="m")
    import io

    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale, border=border)
    return buf.getvalue()


def render_qr_svg(payload: str, scale: int = 8, border: int = 2) -> str:
    """Render a QR code SVG for the given payload. Returns SVG text."""
    _require_segno()
    if not payload or not str(payload).strip():
        raise ValueError("QR payload must be a non-empty string")
    qr = segno.make(str(payload), error="m")
    import io

    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, border=border)
    return buf.getvalue().decode("utf-8")


def qr_for_certificate(cert, base_url: str, scale: int = 8) -> bytes:
    """Render the QR PNG for a certificate.

    Uses the certificate's own `qr_payload` when set (it is covered by the
    Ed25519 signature); otherwise builds the canonical verification URL
    from the serial and base URL.
    """
    payload = (cert.qr_payload or "").strip() or verification_url(cert.serial, base_url)
    return render_qr_png(payload, scale=scale)
