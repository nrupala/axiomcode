<!--
Copyright (c) 2026 Nrupal Akolkar. All rights reserved.
Proprietary — see LICENSE. No license is granted.
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Public flip (2026-11-09, v0.2.0): the hosted verification service at api.axiom-code.com is declared live — the site's pre-launch posture is removed and its documentation reconciled to the API that actually ships. Durable FIFO verification queue (`services/api/jobqueue.py`, gate F-AX-5): when every proof slot is busy, `POST /verify` answers `202 {status: queued, job_id, position}` instead of running unbounded concurrent proofs; `GET /verify/jobs/{job_id}` returns the caller's position or finished result and answers 404 to any other key; queued code is cleared from the store when the job completes; interrupted jobs return to the queue on restart. Eligibility (trial/balance) is decided before admission, so a key that cannot pay never occupies a slot or a place in line. Release-gate package (gate F-AX-4): `gate.yaml` (route table, defined pathways, isolation register), `docs/THREAT-MODEL.md`, `docs/COVERAGE-LEDGER.json`, `scripts/check_gate_contract.py`, and `.github/workflows/gate.yml` keeping the declaration honest in CI. Billing remains paused by the owner's readiness-arming rule: the Stripe webhook endpoint and Payment Links stay deactivated, and credit packs are not on sale.
- Product finishing (2026-10-07): embeddable certificate badges — `core/badge.py` renders version-pinned, tamper-evident SVG badges live from registry data (`Certified vX.Y.Z`), plus Markdown/HTML embed snippets via `axiomcode badge <serial>`; QR code image rendering — `core/qr.py` (pure-Python `segno`) renders the certificate's QR payload as PNG/SVG via `axiomcode qr <serial>`; read-only registry HTTP surface — `services/registry_app.py`, a zero-dependency WSGI app exposing the transparency-log registry (active list, full log, per-serial machine-readable JSON, human cert pages, live badges, QR images), runnable via `axiomcode serve-registry`. Non-GET requests rejected with 405; no mutation over HTTP, ever.
- Portfolio certification rollout (2026-10-05): new `CONTRIBUTING.md` with the standing PR-flow discipline (draft PR → checks green → owner merges; no direct pushes to `main`; CHANGELOG entry under Unreleased + semver bump per PR; releases tagged `vX.Y.Z`); new `NOTICE.md` attribution file; version bumped 0.1.0 → 0.1.1 (patch, chore).

### Removed
- Dead `sys.path` entry in `services/api/verify_api.py` pointing at a developer-machine checkout (gate F-AX-6).

### Flags
- Publishes are CI-only (GitHub Pages from `docs/`, PyPI publish on release, GitHub release on `v*` tags) — the signed-deploy wrapper currently covers Cloudflare Workers only, so a signed path for these artifacts needs the owner's decision; license headers on existing source files are a follow-up (new files in this PR carry the proprietary header).

Note: this changelog starts with the current state — earlier history is not reconstructed here.
