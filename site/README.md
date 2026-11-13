# axiom-code.com launch site

Static site for the AxiomCode launch. Vanilla HTML/CSS/JS, no frameworks —
dependency-light and fast.

## Layout

- `build.py`, `pages_*.py` — tiny static site generator (page content + shared chrome)
- `status_data.py` — the canonical status source. `/status/`, `status.json`, the
  `.well-known` and `llms.txt` status sections, and the practice page's limitations
  are generated from it; never type a status fact into a page directly.
- `changelog_data.py` — the canonical changelog source (append-only, no silent
  edits), rendered to `/changelog/`, `changelog.json`, and `changelog.rss.xml`.
- `check_drift.py` — fails when any rendering disagrees with the canonical sources
  or with a fresh rebuild; runs in CI (`.github/workflows/site-drift.yml`) and can
  be run locally before pushing site changes.
- `run.py` — builds into `dist/` (pages + `llms.txt`, `robots.txt`, `sitemap.xml`,
  `.well-known/axiomcode.json`, `docs/api/openapi.json`, `status.json`,
  `changelog.json`, `changelog.rss.xml`)
- `dist/` — the built site; this is what gets deployed
- `gen_docx.py` — generates `.docx` copies of the paperwork into `paperwork-docx/`
- `paperwork-docx/` — downloadable Word versions of ToS, Privacy, CP/CPS, Refunds, SLA, Security

## Build

```bash
python run.py          # -> dist/
python gen_docx.py     # -> paperwork-docx/
```

## Deploy

`dist/` is a static directory — deploy to Cloudflare Pages (or any static host)
with the domain `axiom-code.com`. Before deploy, set in `build.py`:

- `API_BASE` — the production verification API base URL
- `PADDLE_VENDOR` and `PRICE_IDS` — once the Paddle credit-pack products exist

The `/verify` and `/check` pages call the API at `API_BASE`; they degrade
gracefully (honest "backend not connected" message) until the backend is live.
