"""
AxiomCode certificate badges
=============================
Embeddable, version-pinned, tamper-evident badges a builder puts on their
README or site.

Tamper-evidence model (read this before embedding):
- The badge image is RENDERED SERVER-SIDE from live registry data at
  request time (`/badge/<serial>.svg`). The embed snippet points at the
  issuer-hosted URL, so a badge can never be copy-pasted into a false
  claim: whatever page embeds it always shows the certificate's CURRENT
  registry status. A revoked certificate's badge turns red everywhere it
  is embedded, automatically.
- The badge message is version-pinned ("Certified v1.2.3") — it can never
  claim more than the certificate's own artifact version.
- The badge links to the public certificate page, where anyone (or any
  agent) can check the signature, validity window, and status.
"""

from __future__ import annotations

import html as _html

# Status -> (badge message suffix style, color)
_COLORS = {
    "certified": "#2cbe4e",  # bright green
    "verified": "#44cc11",  # green
    "revoked": "#e05d44",  # red
    "expired": "#fe7d37",  # orange
    "invalid": "#e05d44",  # red — signature does not verify
    "unverified": "#dfb317",  # yellow — published but never machine-checked
    "pending": "#dfb317",  # yellow — not yet valid
    "unknown": "#9f9f9f",  # grey — serial not in registry
}

_TIER_LABELS = {"certified": "Certified", "verified": "Verified"}


def badge_data(serial: str, registry, base_url: str, now: float | None = None) -> dict:
    """Resolve the live badge state for a certificate serial.

    Returns a dict with: serial, status, label, message, color, cert_url,
    badge_url. Status is one of: certified | verified | revoked | expired |
    invalid | unverified | pending | unknown.
    """
    base = base_url.rstrip("/")
    cert_url = f"{base}/cert/{serial}"
    badge_url = f"{base}/badge/{serial}.svg"
    unknown = {
        "serial": serial,
        "status": "unknown",
        "label": "axiomcode",
        "message": "Unknown",
        "color": _COLORS["unknown"],
        "cert_url": cert_url,
        "badge_url": badge_url,
    }
    try:
        cert = registry.get(serial)
    except Exception:
        return unknown
    if cert is None:
        return unknown
    if not cert.signature or not cert.verify():
        return {**unknown, "status": "invalid", "message": "Invalid signature", "color": _COLORS["invalid"]}
    if registry.is_revoked(serial):
        return {**unknown, "status": "revoked", "message": "Revoked", "color": _COLORS["revoked"]}
    if (cert.verification_status or "") != "verified":
        return {**unknown, "status": "unverified", "message": "Unverified", "color": _COLORS["unverified"]}
    validity = cert.validity_status(now)
    if validity == "expired":
        return {**unknown, "status": "expired", "message": "Expired", "color": _COLORS["expired"]}
    if validity == "not-yet-valid":
        return {**unknown, "status": "pending", "message": "Pending", "color": _COLORS["pending"]}
    tier_label = _TIER_LABELS.get((cert.tier or "").lower(), "Certified")
    version = (cert.artifact_version or "").strip()
    message = f"{tier_label} v{version}" if version else tier_label
    status = (cert.tier or "").lower() if (cert.tier or "").lower() in ("certified", "verified") else "certified"
    return {
        "serial": serial,
        "status": status,
        "label": "axiomcode",
        "message": message,
        "color": _COLORS.get(status, _COLORS["certified"]),
        "cert_url": cert_url,
        "badge_url": badge_url,
    }


def _text_width(text: str) -> float:
    # Approximate Verdana 11px advance width; good enough for badges.
    return sum(7.2 if c.isupper() or c in "mwMW@%" else 5.6 for c in text) + 2


def render_badge_svg(data: dict) -> str:
    """Render a shields.io-style flat badge SVG from badge_data()."""
    label = data.get("label", "axiomcode")
    message = data.get("message", "")
    color = data.get("color", _COLORS["unknown"])
    lw = _text_width(label) + 12
    mw = _text_width(message) + 12
    total = lw + mw
    lx = lw / 2
    mx = lw + mw / 2
    label_e = _html.escape(label)
    message_e = _html.escape(message)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total:.0f}" height="20" role="img" '
        f'aria-label="{label_e}: {message_e}">'
        f"<title>{label_e}: {message_e}</title>"
        '<linearGradient id="s" x2="0" y2="100%">'
        '<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        '<stop offset="1" stop-opacity=".1"/></linearGradient>'
        f'<clipPath id="r"><rect width="{total:.0f}" height="20" rx="3" fill="#fff"/></clipPath>'
        '<g clip-path="url(#r)">'
        f'<rect width="{lw:.0f}" height="20" fill="#555"/>'
        f'<rect x="{lw:.0f}" width="{mw:.0f}" height="20" fill="{color}"/>'
        f'<rect width="{total:.0f}" height="20" fill="url(#s)"/></g>'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        'text-rendering="geometricPrecision" font-size="11">'
        f'<text x="{lx:.0f}" y="15" fill="#010101" fill-opacity=".3">{label_e}</text>'
        f'<text x="{lx:.0f}" y="14">{label_e}</text>'
        f'<text x="{mx:.0f}" y="15" fill="#010101" fill-opacity=".3">{message_e}</text>'
        f'<text x="{mx:.0f}" y="14">{message_e}</text>'
        "</g></svg>"
    )


def badge_snippet(serial: str, base_url: str) -> dict:
    """Embed snippets for a certificate badge.

    Returns {"markdown": ..., "html": ...}. Both point the <img> at the
    issuer-hosted badge URL (rendered live from the registry) and link to
    the public certificate page — so the badge stays honest wherever it
    is embedded.
    """
    base = base_url.rstrip("/")
    img = f"{base}/badge/{serial}.svg"
    link = f"{base}/cert/{serial}"
    return {
        "markdown": f"[![AxiomCode certificate]({img})]({link})",
        "html": (
            f'<a href="{_html.escape(link)}">'
            f'<img src="{_html.escape(img)}" alt="AxiomCode certificate {_html.escape(serial)}" />'
            "</a>"
        ),
    }
