#!/usr/bin/env python3
"""Gate contract check (F-AX-4): gate.yaml must describe the service
that actually ships. Fails when:

- gate.yaml does not parse, or a required top-level key is missing;
- a declared route does not exist in services/api/verify_api.py
  (path + method), or the API serves a route the declaration hides;
- a declared route is not backed by an app mount where the API
  mounts it (app.mount("/mcp", ...) serves a whole subtree with the
  sub-app's own method handling), or the API mounts a path the
  declaration hides;
- a declared pathway covers a path with no declared route, or a
  declared route is covered by no pathway;
- a declared doc (threat model, coverage ledger, changelog) is
  missing, or the coverage ledger is not a JSON list of units each
  carrying coverage_id + status.

Run: python3 scripts/check_gate_contract.py [repo-root]
Exit 0 = contract holds. Wired into .github/workflows/gate.yml.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
API = ROOT / "services" / "api" / "verify_api.py"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def main() -> int:
    try:
        import yaml
    except ImportError:
        print("check_gate_contract: PyYAML is required (pip install pyyaml)", file=sys.stderr)
        return 2

    gate_path = ROOT / "gate.yaml"
    if not gate_path.exists():
        print("check_gate_contract: gate.yaml missing", file=sys.stderr)
        return 1
    gate = yaml.safe_load(gate_path.read_text())
    if not isinstance(gate, dict):
        print("check_gate_contract: gate.yaml is not a mapping", file=sys.stderr)
        return 1

    for key in ("product", "version", "base_url", "types", "test_command", "docs", "routes", "pathways"):
        if key not in gate:
            fail(f"gate.yaml missing required key: {key}")

    # --- routes vs the shipped API -------------------------------------
    src = API.read_text()
    served: dict[str, set[str]] = {}
    for method, path in re.findall(r"@app\.(get|post|put|delete|patch)\(\"([^\"]+)\"\)", src):
        served.setdefault(path, set()).add(method.upper())
    # An app.mount("/mcp", ...) serves its whole subtree with the
    # mounted app's own method handling; the declaration names the
    # mount path as a route, and the checker holds it to the mount.
    mounts = set(re.findall(r"\.mount\(\s*[\"']([^\"']+)[\"']", src))

    declared: dict[str, set[str]] = {}
    for route in gate.get("routes") or []:
        declared.setdefault(route["path"], set()).update(m.upper() for m in route["methods"])
        if route["path"] in served:
            for m in route["methods"]:
                if m.upper() not in served[route["path"]]:
                    fail(f"declared method not served: {m} {route['path']}")
        elif route["path"] in mounts:
            pass  # served by the mount; methods are the mounted app's own
        else:
            fail(f"declared route not served by the API: {route['path']}")
    for path in served:
        if path not in declared:
            fail(f"API serves a route gate.yaml does not declare: {path}")
    for path in mounts:
        if path not in declared:
            fail(f"API mounts a path gate.yaml does not declare: {path}")

    # --- pathways cover declared routes --------------------------------
    covered: set[str] = set()
    for pw in gate.get("pathways") or []:
        covers = pw.get("covers")
        paths = covers if isinstance(covers, list) else [covers]
        for p in paths:
            covered.add(p)
            if p not in declared:
                fail(f"pathway {pw.get('id')} covers undeclared route: {p}")
    for path in declared:
        if path not in covered:
            fail(f"declared route covered by no pathway: {path}")

    # --- declared docs exist -------------------------------------------
    docs = gate.get("docs") or {}
    for name, rel in docs.items():
        if not (ROOT / rel).exists():
            fail(f"declared doc missing: {name} -> {rel}")
    ledger_rel = docs.get("coverage_ledger")
    if ledger_rel and (ROOT / ledger_rel).exists():
        try:
            units = json.loads((ROOT / ledger_rel).read_text())
            if not isinstance(units, list) or not units:
                fail("coverage ledger is not a non-empty JSON list")
            else:
                for i, u in enumerate(units):
                    if not isinstance(u, dict) or not u.get("coverage_id") or not u.get("status"):
                        fail(f"coverage ledger unit {i} lacks coverage_id/status")
        except json.JSONDecodeError as e:
            fail(f"coverage ledger is not valid JSON: {e}")

    if failures:
        for f in failures:
            print(f"GATE CONTRACT FAIL: {f}")
        return 1
    print(f"gate contract OK: {len(declared)} routes, {len(gate.get('pathways') or [])} pathways, docs present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
