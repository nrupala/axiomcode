#!/usr/bin/env python3
"""Runner: import all page modules, render, write extras."""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# import order is page registration order (drives sitemap.xml) - not alphabetical
import changelog_data  # noqa: I001 (block order is registration order, not alphabetical)
import pages_main  # noqa: F401, I001 (registration side effects)
import pages_shell  # noqa: F401, I001 (registration side effects)
import pages_docs  # noqa: F401, I001 (registration side effects)
import pages_paperwork  # noqa: F401, I001 (registration side effects)
import pages_status  # noqa: F401, I001 (registration side effects)
import pages_blog
import status_data
from build import API_BASE, render_all

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
            "Verification and certification API — live since 2026-11-09. "
            "The first 10 verification cases per API key are a free trial (no certificates). "
            "When every proof slot is busy, POST /verify answers 202 with a queue position. "
            "Full reference at https://axiom-code.com/docs/api/"
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
print("extras written")
