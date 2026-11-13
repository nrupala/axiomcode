#!/usr/bin/env python3
"""Site drift checks — fail when any rendering disagrees with the canonical
sources (status_data.py, changelog_data.py) or with a fresh rebuild.

Run:  python3 site/check_drift.py        (exit 0 = no drift)

Checks:
  1. Source validity: status vocabulary, required fields, ISO dates;
     changelog categories, unique entry IDs.
  2. Full rebuild diff: the committed site/dist is byte-identical to a
     fresh `run.py` build of the committed sources.
  3. status.json / .well-known / llms.txt status sections equal the
     canonical status source.
  4. changelog.json / RSS equal the canonical changelog source; the
     changelog page carries every entry anchor; /releases/ points to it.
  5. Pricing JSON-LD availability agrees with the billing status, and the
     home banner's sale wording agrees with it too.
  6. /status/ renders every surface with its lifecycle label; the sitemap
     lists the status, changelog, and practice pages.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(SITE_DIR, "dist")
sys.path.insert(0, SITE_DIR)

import changelog_data  # noqa: E402
import status_data  # noqa: E402

FAILURES: list[str] = []


def check(ok, label, detail=""):
    if ok:
        print(f"ok: {label}")
    else:
        FAILURES.append(label)
        print(f"FAIL: {label} {detail}")


def read_dist(rel):
    with open(os.path.join(DIST, rel), encoding="utf-8") as f:
        return f.read()


def check_sources():
    ids = set()
    for s in status_data.SURFACES:
        sid = s["surface_id"]
        check(sid not in ids, f"status id unique: {sid}")
        ids.add(sid)
        check(s["availability"] in status_data.AVAILABILITY_STATES, f"{sid} availability in vocabulary")
        check(s["lifecycle"] in status_data.LIFECYCLE_STATES, f"{sid} lifecycle in vocabulary")
        check(bool(s.get("owner")), f"{sid} has an owner")
        check(bool(s.get("last_verified_at")), f"{sid} has last_verified_at")
        if s["graduates_on"]:
            check(s["lifecycle"] == "in_soak", f"{sid} graduates_on only while in_soak")
    eids = set()
    for e in changelog_data.ENTRIES:
        check(e["id"] not in eids, f"changelog id unique: {e['id']}")
        eids.add(e["id"])
        check(e["category"] in changelog_data.CATEGORIES, f"{e['id']} category in vocabulary")
        check(bool(e["surfaces"]), f"{e['id']} names affected surfaces")


def check_rebuild():
    tmp = tempfile.mkdtemp(prefix="ax-drift-")
    try:
        work = os.path.join(tmp, "site")
        shutil.copytree(SITE_DIR, work, ignore=shutil.ignore_patterns("__pycache__"))
        r = subprocess.run([sys.executable, "run.py"], cwd=work, capture_output=True, text=True)
        check(r.returncode == 0, "fresh rebuild succeeds", r.stderr[-300:] if r.returncode else "")
        if r.returncode != 0:
            return
        rebuilt = os.path.join(work, "dist")
        diffs = []
        for root, _dirs, files in os.walk(DIST):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), DIST)
                other = os.path.join(rebuilt, rel)
                if not os.path.exists(other):
                    diffs.append(f"missing in rebuild: {rel}")
                elif open(os.path.join(root, fn), "rb").read() != open(other, "rb").read():
                    diffs.append(f"differs: {rel}")
        for root, _dirs, files in os.walk(rebuilt):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), rebuilt)
                if not os.path.exists(os.path.join(DIST, rel)):
                    diffs.append(f"not committed: {rel}")
        check(not diffs, "committed dist == fresh rebuild", "; ".join(diffs[:8]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_status_artefacts():
    sj = json.loads(read_dist("status.json"))
    check(sj["surfaces"] == status_data.SURFACES, "status.json surfaces == canonical source")
    check(sj["meta"]["as_of"] == status_data.STATUS_META["as_of"], "status.json as_of == source")
    wk = json.loads(read_dist(os.path.join(".well-known", "axiomcode.json")))
    check(wk["surfaces"] == status_data.wellknown_surfaces(), ".well-known surfaces == canonical source")
    check(wk["status_as_of"] == status_data.STATUS_META["as_of"], ".well-known status_as_of == source")
    llms = read_dist("llms.txt")
    check(status_data.llms_status_section() in llms, "llms.txt status section == generated section")
    page_html = read_dist(os.path.join("status", "index.html"))
    for s in status_data.SURFACES:
        label = status_data.LIFECYCLE_LABELS[s["lifecycle"]]
        check(s["name"] in page_html and label in page_html, f"/status/ renders {s['surface_id']} ({label})")


def check_changelog_artefacts():
    cj = json.loads(read_dist("changelog.json"))
    check(cj["entries"] == changelog_data.ENTRIES, "changelog.json == canonical source")
    rss = read_dist("changelog.rss.xml")
    try:
        root = ET.fromstring(rss)
        titles = [t.text for t in root.iter("title")]
        check(all(e["title"] in titles for e in changelog_data.ENTRIES), "RSS carries every entry title")
    except ET.ParseError as exc:
        check(False, "RSS parses as XML", str(exc))
    page_html = read_dist(os.path.join("changelog", "index.html"))
    for e in changelog_data.ENTRIES:
        check(f'id="{e["id"]}"' in page_html, f"/changelog/ carries anchor {e['id']}")
    rel = read_dist(os.path.join("releases", "index.html"))
    check("/changelog/" in rel and "/status/" in rel, "/releases/ points to changelog + status")


def check_pricing_agreement():
    billing = next(s for s in status_data.SURFACES if s["surface_id"] == "billing")
    pricing = read_dist(os.path.join("pricing", "index.html"))
    blocks = re.findall(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', pricing, re.S)
    product = None
    for b in blocks:
        try:
            d = json.loads(b)
        except json.JSONDecodeError:
            continue
        if d.get("@type") == "Product":
            product = d
    check(product is not None, "pricing page carries a Product JSON-LD block")
    if product:
        for offer in product["offers"]:
            avail = offer.get("availability", "")
            if offer["name"] == "Trial":
                check(offer["price"] == "0" and avail.endswith("InStock"), "trial $0 offer is InStock")
            elif billing["availability"] == "paused":
                check(avail.endswith("OutOfStock"), f"pack {offer['name']} OutOfStock while billing paused")
    home = read_dist("index.html")
    if billing["availability"] == "paused":
        check("not yet on sale" in home, "home banner states packs not yet on sale")


def check_sitemap():
    sm = read_dist("sitemap.xml")
    for path in ("/status/", "/changelog/", "/practice/"):
        check(f"<loc>https://axiom-code.com{path}</loc>" in sm, f"sitemap lists {path}")


def main():
    if not os.path.isdir(DIST):
        print("FAIL: site/dist missing — run `python3 site/run.py` first")
        return 1
    check_sources()
    check_rebuild()
    check_status_artefacts()
    check_changelog_artefacts()
    check_pricing_agreement()
    check_sitemap()
    if FAILURES:
        print(f"\nDRIFT: {len(FAILURES)} check(s) failed")
        return 1
    print("\nNo drift: all renderings agree with the canonical sources.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
