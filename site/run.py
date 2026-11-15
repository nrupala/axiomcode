#!/usr/bin/env python3
"""Runner: import all page modules, render, write extras."""

import html as _html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# import order is page registration order (drives sitemap.xml) - not alphabetical
import changelog_data  # noqa: I001 (block order is registration order, not alphabetical)
import pages_main  # noqa: F401, I001 (registration side effects)
import pages_shell  # noqa: F401, I001 (registration side effects)
import pages_docs_pack  # noqa: F401, I001 (registration side effects)
import pages_docs  # noqa: F401, I001 (registration side effects)
import pages_company  # noqa: F401, I001 (registration side effects)
import pages_paperwork  # noqa: F401, I001 (registration side effects)
import pages_status  # noqa: F401, I001 (registration side effects)
import pages_blog
import status_data
from build import API_BASE, PAGES, SITE, render_all

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
render_all(OUT)

# machine-readable extras
wk = os.path.join(OUT, ".well-known")
os.makedirs(wk, exist_ok=True)
with open(os.path.join(wk, "axiomcode.json"), "w") as f:
    json.dump(pages_blog.WELLKNOWN, f, indent=2)
with open(os.path.join(OUT, "llms.txt"), "w") as f:
    f.write(pages_blog.LLMS_TXT)

# canonical status + changelog artefacts (generated from status_data.py /
# changelog_data.py — the same sources the /status/ and /changelog/ pages use)
with open(os.path.join(OUT, "status.json"), "w") as f:
    json.dump(status_data.status_json(), f, indent=2)
with open(os.path.join(OUT, "changelog.json"), "w") as f:
    json.dump(changelog_data.changelog_json(), f, indent=2)
with open(os.path.join(OUT, "changelog.rss.xml"), "w") as f:
    f.write(changelog_data.changelog_rss())

# OpenAPI summary for agents — mirrors the live API's route table.
# The API's own live spec is served at https://api.axiom-code.com/openapi.json.
openapi = {
    "openapi": "3.0.3",
    "info": {
        "title": "AxiomCode API",
        "version": "0.2.0",
        "description": (
            "SUMMARY of the live contract, kept for offline reading — the canonical "
            "OpenAPI 3.1 document is served by the API itself at "
            "https://api.axiom-code.com/openapi.json and overrides this summary "
            "wherever they differ. Verification and certification API — live since "
            "2026-11-09. The first 10 verification cases per API key are a free trial "
            "(no certificates). When every proof slot is busy, POST /verify answers "
            "202 with a queue position. Full reference at https://axiom-code.com/docs/api/"
        ),
    },
    "servers": [{"url": API_BASE}],
    "paths": {
        "/verify": {
            "post": {"summary": "Verify a Lean artifact (API key). 200 verdict, 202 queued, 402 trial exhausted."}
        },
        "/verify/jobs/{job_id}": {"get": {"summary": "Queued job position or result (submitting key only)"}},
        "/check": {"post": {"summary": "Validate a certificate JSON (API key)"}},
        "/shell/turn": {
            "post": {"summary": "Interactive shell turn: optional verify/check action plus conversation (API key)"}
        },
        "/shell/jobs/{job_id}": {"get": {"summary": "Shell polling read for a queued job (submitting key only)"}},
        "/revoked": {"get": {"summary": "Public revocation list (no auth)"}},
        "/.well-known/axiomcode-keys.json": {"get": {"summary": "CA public keys for offline validation (no auth)"}},
        "/health": {"get": {"summary": "Service health (no auth)"}},
        "/billing/checkout": {
            "post": {"summary": "Credit-pack checkout session (API key; 501 while billing is paused)"}
        },
        "/billing/webhook": {"post": {"summary": "Stripe webhook (signature-verified)"}},
    },
}
api_dir = os.path.join(OUT, "docs", "api")
with open(os.path.join(api_dir, "openapi.json"), "w") as f:
    json.dump(openapi, f, indent=2)

# copy paperwork docx into dist
_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paperwork-docx")
for _f in os.listdir(_src):
    if _f.endswith(".docx"):
        shutil.copy(os.path.join(_src, _f), os.path.join(OUT, "paperwork", _f))


# Markdown mirrors for every docs page (blueprint C6/D3.4 standard element):
# generated from the registered page body, so a mirror can never drift from
# the HTML it mirrors. Front matter comes from the DOCMETA registry.
def _strip_tags(fragment):
    return _html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def _html_to_md(body_html):
    s = body_html
    s = re.sub(r'<div class="docmeta">.*?</div>', "", s, count=1, flags=re.S)
    pres = []

    def _keep_pre(m):
        pres.append("```\n" + _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() + "\n```")
        return f"\n\x00PRE{len(pres) - 1}\x00\n"

    s = re.sub(r"<pre[^>]*>(.*?)</pre>", _keep_pre, s, flags=re.S)
    s = re.sub(r"<h1[^>]*>(.*?)</h1>", lambda m: "\n# " + _strip_tags(m.group(1)) + "\n", s, flags=re.S)
    s = re.sub(r"<h2[^>]*>(.*?)</h2>", lambda m: "\n## " + _strip_tags(m.group(1)) + "\n", s, flags=re.S)
    s = re.sub(r"<h3[^>]*>(.*?)</h3>", lambda m: "\n### " + _strip_tags(m.group(1)) + "\n", s, flags=re.S)

    def _table(m):
        rows = []
        for tr in re.findall(r"<tr>(.*?)</tr>", m.group(1), flags=re.S):
            cells = [_strip_tags(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S)]
            if cells:
                rows.append("| " + " | ".join(cells) + " |")
        if len(rows) > 1:
            rows.insert(1, "|" + " --- |" * rows[0].count("|") + "")
        return "\n" + "\n".join(rows) + "\n"

    s = re.sub(r"<table[^>]*>(.*?)</table>", _table, s, flags=re.S)
    s = re.sub(
        r'<a href="([^"]+)">(.*?)</a>',
        lambda m: "[" + _strip_tags(m.group(2)) + "](" + m.group(1) + ")",
        s,
        flags=re.S,
    )
    s = re.sub(r"<code[^>]*>(.*?)</code>", lambda m: "`" + _strip_tags(m.group(1)) + "`", s, flags=re.S)
    s = re.sub(r"<strong>(.*?)</strong>", lambda m: "**" + _strip_tags(m.group(1)) + "**", s, flags=re.S)
    s = re.sub(r"<em>(.*?)</em>", lambda m: "*" + _strip_tags(m.group(1)) + "*", s, flags=re.S)
    s = re.sub(r"<li>(.*?)</li>", lambda m: "\n- " + _strip_tags(m.group(1)), s, flags=re.S)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = _html.unescape(s)
    for i, pre in enumerate(pres):
        s = s.replace(f"\x00PRE{i}\x00", pre)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


_mirrors = 0
for _path, _title, _desc, _body, _jsonld in PAGES:
    if not _path.startswith("/docs/"):
        continue
    _meta = pages_docs_pack.DOCMETA.get(_path)
    if _meta is None or '<div class="docbody">' not in _body:
        continue
    _inner = _body.split('<div class="docbody">', 1)[1]
    _inner = re.sub(r"(</div>\s*){3}</section>\s*$", "", _inner)
    _front = (
        f"> Canonical: {SITE}{_path} · Type: {_meta['type']} · Audience: {_meta['audience']} · "
        f"Role packs: {_meta['packs']} · Version: {pages_docs_pack.DOCS_VERSION} · "
        f"Last verified: {pages_docs_pack.LAST_VERIFIED} · Source: {_meta['source']}\n\n"
    )
    _md = _front + _html_to_md(_inner)
    with open(os.path.join(OUT, _path.lstrip("/"), "index.md"), "w") as f:
        f.write(_md)
    _mirrors += 1
print(f"markdown mirrors written: {_mirrors}")
print("extras written")
