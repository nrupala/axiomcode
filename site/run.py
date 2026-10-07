#!/usr/bin/env python3
"""Runner: import all page modules, render, write extras."""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# import order is page registration order (drives sitemap.xml) - not alphabetical
import pages_main  # noqa: F401, I001 (registration side effects)
import pages_docs  # noqa: F401, I001 (registration side effects)
import pages_paperwork  # noqa: F401, I001 (registration side effects)
import pages_blog
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

# stub OpenAPI for agents (full spec ships with the API)
openapi = {
    "openapi": "3.0.3",
    "info": {
        "title": "AxiomCode API",
        "version": "1.0.0",
        "description": ("Verification and certification API. Full reference at https://axiom-code.com/docs/api/"),
    },
    "servers": [{"url": API_BASE}],
    "paths": {
        "/v1/trial/verify": {"post": {"summary": "Trial verification (email, 10 lifetime, no certificate)"}},
        "/v1/verify": {"post": {"summary": "Paid verification with certificate (API key)"}},
        "/v1/check": {"get": {"summary": "Certificate status by serial (no auth)"}},
        "/v1/revoked": {"get": {"summary": "Public revocation list (no auth)"}},
        "/v1/account": {"get": {"summary": "Balance and usage (API key)"}},
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
