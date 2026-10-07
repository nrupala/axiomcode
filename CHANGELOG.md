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
- Product finishing (2026-10-07): embeddable certificate badges — `core/badge.py` renders version-pinned, tamper-evident SVG badges live from registry data (`Certified vX.Y.Z`), plus Markdown/HTML embed snippets via `axiomcode badge <serial>`; QR code image rendering — `core/qr.py` (pure-Python `segno`) renders the certificate's QR payload as PNG/SVG via `axiomcode qr <serial>`; read-only registry HTTP surface — `services/registry_app.py`, a zero-dependency WSGI app exposing the transparency-log registry (active list, full log, per-serial machine-readable JSON, human cert pages, live badges, QR images), runnable via `axiomcode serve-registry`. Non-GET requests rejected with 405; no mutation over HTTP, ever.
- Portfolio certification rollout (2026-10-05): new `CONTRIBUTING.md` with the standing PR-flow discipline (draft PR → checks green → owner merges; no direct pushes to `main`; CHANGELOG entry under Unreleased + semver bump per PR; releases tagged `vX.Y.Z`); new `NOTICE.md` attribution file; version bumped 0.1.0 → 0.1.1 (patch, chore).
- Flags: publishes are CI-only (GitHub Pages from `docs/`, PyPI publish on release, GitHub release on `v*` tags) — the signed-deploy wrapper currently covers Cloudflare Workers only, so a signed path for these artifacts needs the owner's decision; license headers on existing source files are a follow-up (new files in this PR carry the proprietary header).

Note: this changelog starts with the current state — earlier history is not reconstructed here.
