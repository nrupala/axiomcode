"""AxiomCode billing — full-cost pricing.

Price covers EVERYTHING, not just compute. The product pays for itself:
whole infra, operations, founder time, agent runtime, insurance —
plus industry-standard profit margin on top.

    price_per_compute_s = sum(cost components) / (1 - margin)

1 credit = $0.01. Tune via AXIOMCODE_PRICING_JSON or the defaults below.
Currently: 2.25x multiple over fully-loaded cost (~55.6% gross margin).

Production (W2): meter records go through the durable store
(store.record_meter — sqlite + hash-chained audit trail), not the
prototype's meter.jsonl. meter()/usage_for() accept a Store; a plain
file path still works via the legacy JSONL path for old fixtures.
"""

import json
import os
import time
from pathlib import Path

CREDIT_USD = 0.01

DEFAULT_PRICING = {
    # Fully-loaded cost per compute-second, in credits:
    "compute": 0.05,  # raw CPU for Lean builds
    "infra": 0.08,  # servers, bandwidth, storage, cert infra
    "operations": 0.10,  # support, billing, abuse handling, every effort
    "founder_time": 0.05,  # his time — product, sales, support, amortized
    "agent_cost": 0.05,  # the AI runtime behind the service
    "insurance": 0.07,  # liability coverage for certified verdicts
    # Industry multiple on fully-loaded cost — the business gets paid,
    # not just the servers. 2.25x ~= 55.6% gross margin (Google-class).
    "multiple": 2.25,
}


def load_pricing() -> dict:
    raw = os.environ.get("AXIOMCODE_PRICING_JSON")
    if raw:
        p = json.loads(raw)
        merged = dict(DEFAULT_PRICING)
        merged.update(p)
        return merged
    return dict(DEFAULT_PRICING)


def price_per_compute_s(pricing: dict | None = None) -> float:
    p = pricing or load_pricing()
    loaded = sum(v for k, v in p.items() if k != "multiple")
    return float(loaded * p["multiple"])


def charge_for(compute_s: float, pricing: dict | None = None) -> dict:
    p = pricing or load_pricing()
    rate = price_per_compute_s(p)
    credits = round(compute_s * rate, 4)
    return {
        "compute_s": round(compute_s, 2),
        "rate_credits_per_s": round(rate, 4),
        "credits": credits,
        "usd": round(credits * CREDIT_USD, 4),
        "multiple": p["multiple"],
    }


def load_keys(keys_file: str) -> dict:
    keys = {}
    p = Path(keys_file)
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and ":" in line and not line.startswith("#"):
                kid, key = line.split(":", 1)
                keys[key.strip()] = kid.strip()
    return keys


def _is_store(target) -> bool:
    return hasattr(target, "record_meter") and hasattr(target, "usage_for")


def meter(target, key_id: str, code_sha: str, verified: bool, compute_s: float, pricing: dict | None = None) -> dict:
    """Record one metered call. `target` is the durable Store
    (production) or a legacy JSONL path. Returns the entry."""
    bill = charge_for(compute_s, pricing)
    entry = {
        "ts": int(time.time()),
        "key_id": key_id,
        "code_sha256": code_sha,
        "verified": verified,
        **bill,
    }
    if _is_store(target):
        entry_out: dict = target.record_meter(entry)
        return entry_out
    with open(target, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def usage_for(target, key_id: str) -> dict:
    """Total metered spend for a key — from the Store (production)
    or a legacy JSONL path."""
    if _is_store(target):
        usage: dict = target.usage_for(key_id)
        return usage
    total_c, total_usd, calls = 0.0, 0.0, 0
    p = Path(target)
    if p.exists():
        for line in p.read_text().splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("key_id") == key_id:
                total_c += e.get("credits", 0)
                total_usd += e.get("usd", 0)
                calls += 1
    return {"key_id": key_id, "calls": calls, "credits_used": round(total_c, 4), "usd_used": round(total_usd, 4)}
