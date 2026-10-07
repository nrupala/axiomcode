# axiom-code.com launch site

Static site for the AxiomCode launch. Vanilla HTML/CSS/JS, no frameworks —
dependency-light and fast.

## Layout

- `build.py`, `pages_*.py` — tiny static site generator (page content + shared chrome)
- `run.py` — builds into `dist/` (16 pages + `llms.txt`, `robots.txt`, `sitemap.xml`,
  `.well-known/axiomcode.json`, `docs/api/openapi.json`)
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
