#!/usr/bin/env python3
"""AxiomCode launch site generator. Builds static HTML into ./dist."""

import html
import json
import os
import shutil

SITE = "https://axiom-code.com"
NAME = "AxiomCode"
TAGLINE = "The certification authority for software correctness."
HERO_LINE = "Don\u2019t trust our AI \u2014 verify our proof."
API_BASE = "https://api.axiom-code.com"  # backend goes live in the next step
PADDLE_VENDOR = 0  # set when Nrupal creates the products
PADDLE_ENV = "production"
PRICE_IDS = {  # set when Nrupal creates the products
    "starter": "",
    "growth": "",
    "scale": "",
}

NAV = [
    ("How it works", "/how-it-works/"),
    ("Pricing", "/pricing/"),
    ("Docs", "/docs/"),
    ("API", "/docs/api/"),
    ("Paperwork", "/paperwork/"),
]

CSS = """
:root{--ink:#101828;--mut:#475467;--line:#e4e7ec;--paper:#fff;--wash:#f8fafc;
--gold:#b98a2f;--goldsoft:#faf3e3;--green:#12805c;--greensoft:#e9f7f0;
--red:#b42318;--redsoft:#fdeceb;--navy:#0c1f3f;--radius:10px;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:var(--sans);color:var(--ink);background:var(--paper);line-height:1.65;font-size:17px}
a{color:#175cd3;text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.prose{max-width:72ch}
/* header */
.sitehead{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:50}
.sitehead .wrap{display:flex;align-items:center;gap:28px;height:64px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:19px;color:var(--ink)}
.brand:hover{text-decoration:none}
.brand svg{width:30px;height:30px}
.nav{display:flex;gap:22px;margin-left:auto;font-size:15px}
.nav a{color:var(--mut)}.nav a:hover{color:var(--ink)}
.cta{display:inline-block;background:var(--navy);color:#fff!important;padding:9px 18px;border-radius:8px;font-weight:600;font-size:15px}
.cta:hover{background:#16294f;text-decoration:none}
/* hero */
.hero{background:linear-gradient(180deg,#0c1f3f 0%,#12294f 100%);color:#fff;padding:84px 0 72px}
.hero h1{font-size:46px;line-height:1.15;margin:0 0 18px;letter-spacing:-.5px;max-width:16em}
.hero p.lede{font-size:20px;color:#cbd5e1;max-width:34em;margin:0 0 28px}
.hero .row{display:flex;gap:14px;flex-wrap:wrap}
.btn{display:inline-block;padding:13px 26px;border-radius:9px;font-weight:700;font-size:16px;border:1px solid transparent}
.btn-gold{background:var(--gold);color:#1a1206!important}.btn-gold:hover{background:#c99a3f;text-decoration:none}
.btn-ghost{border-color:#3b4a63;color:#fff!important}.btn-ghost:hover{border-color:#5b6b85;text-decoration:none}
.trustline{margin-top:26px;font-size:14px;color:#93a1b8}
/* sections */
section.block{padding:64px 0}
section.block h2{font-size:30px;margin:0 0 12px;letter-spacing:-.3px}
.kicker{font-size:13px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--gold);margin-bottom:8px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:28px}
.card{border:1px solid var(--line);border-radius:var(--radius);padding:26px;background:#fff}
.card h3{margin:0 0 8px;font-size:19px}
.card p{margin:0;color:var(--mut);font-size:15.5px}
.card .num{display:inline-flex;width:34px;height:34px;border-radius:50%;background:var(--navy);color:#fff;
align-items:center;justify-content:center;font-weight:700;margin-bottom:12px}
/* seal / cert demo */
.sealbox{background:var(--wash);border:1px solid var(--line);border-radius:12px;padding:28px;margin-top:24px}
pre.code{background:#0c1f3f;color:#d7e3f4;padding:20px;border-radius:10px;overflow:auto;font-size:14px;line-height:1.55;font-family:var(--mono)}
code.inline{font-family:var(--mono);background:var(--wash);border:1px solid var(--line);border-radius:5px;padding:1px 7px;font-size:.88em}
/* verdict badges */
.badge{display:inline-block;padding:4px 14px;border-radius:999px;font-weight:700;font-size:14px}
.b-pass{background:var(--greensoft);color:var(--green);border:1px solid #bfe6d2}
.b-fail{background:var(--redsoft);color:var(--red);border:1px solid #f3c2bc}
.b-warn{background:var(--goldsoft);color:#8a6414;border:1px solid #ecd9a8}
/* pricing */
.ptable{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;margin-top:28px}
.plan{border:1px solid var(--line);border-radius:12px;padding:28px;background:#fff;position:relative}
.plan.hot{border:2px solid var(--gold);box-shadow:0 8px 30px rgba(185,138,47,.12)}
.plan h3{margin:0 0 4px}.plan .price{font-size:34px;font-weight:800;margin:8px 0}
.plan .per{color:var(--mut);font-size:14px}
.plan ul{padding-left:20px;color:var(--mut);font-size:15px;margin:16px 0}
.plan li{margin-bottom:8px}
/* forms */
textarea.codebox{width:100%;min-height:260px;font-family:var(--mono);font-size:14px;padding:16px;
border:1px solid var(--line);border-radius:10px;background:#fbfcfe;resize:vertical}
input[type=text],input[type=email]{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:8px;font-size:16px}
label.fl{display:block;font-weight:600;margin:18px 0 6px}
button.go{background:var(--navy);color:#fff;border:0;padding:13px 30px;border-radius:9px;font-size:16px;font-weight:700;cursor:pointer}
button.go:hover{background:#16294f}button.go:disabled{opacity:.55;cursor:wait}
.result{margin-top:24px;border:1px solid var(--line);border-radius:10px;padding:22px;display:none}
.result.show{display:block}
/* footer */
.sitefoot{background:#0c1f3f;color:#aeb9cc;padding:56px 0 32px;margin-top:40px;font-size:15px}
.sitefoot a{color:#d7e0ee}.sitefoot .cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px}
.sitefoot h4{color:#fff;margin:0 0 12px;font-size:15px}
.sitefoot ul{list-style:none;margin:0;padding:0}.sitefoot li{margin-bottom:8px}
.fine{margin-top:36px;padding-top:20px;border-top:1px solid #22345a;font-size:13px;color:#7d8ba3}
/* docs */
.docnav{background:var(--wash);border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin:24px 0}
table.spec{width:100%;border-collapse:collapse;font-size:15px;margin:20px 0}
table.spec th,table.spec td{border:1px solid var(--line);padding:10px 14px;text-align:left;vertical-align:top}
table.spec th{background:var(--wash)}
.note{border-left:4px solid var(--gold);background:var(--goldsoft);padding:14px 18px;border-radius:0 8px 8px 0;margin:20px 0;font-size:15.5px}
.note.blue{border-color:#175cd3;background:#eff4ff}
h1.pt{font-size:38px;letter-spacing:-.4px;margin:0 0 10px}
.sub{color:var(--mut);font-size:19px;margin:0 0 8px}
.faq details{border:1px solid var(--line);border-radius:8px;padding:14px 18px;margin-bottom:10px}
.faq summary{font-weight:700;cursor:pointer}
@media(max-width:760px){.hero h1{font-size:32px}.nav{display:none}}
"""

SEAL_SVG = """<svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M16 2l10 4v8c0 6.6-4.2 11.4-10 14C10.2 25.4 6 20.6 6 14V6l10-4z" fill="#b98a2f"/><path d="M11.5 16.2l3.2 3.2 6-6.4" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def head(title, desc, path, extra_jsonld=None):
    canon = SITE + path
    jl = ""
    if extra_jsonld:
        jl = '<script type="application/ld+json">\n' + json.dumps(extra_jsonld, indent=2) + "\n</script>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} | AxiomCode</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:site_name" content="AxiomCode">
<meta property="og:title" content="{html.escape(title)} | AxiomCode">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)} | AxiomCode">
<meta name="twitter:description" content="{html.escape(desc)}">
<style>{CSS}</style>
{jl}
</head>
<body>
"""


def header(active=""):
    links = []
    for label, href in NAV:
        links.append(f'<a href="{href}">{label}</a>')
    return f"""<div class="sitehead"><div class="wrap">
<a class="brand" href="/">{SEAL_SVG}<span>AxiomCode</span></a>
<nav class="nav">{"".join(links)}</nav>
<a class="cta" href="/verify/">Try free</a>
</div></div>
"""


FOOTER = """<footer class="sitefoot"><div class="wrap">
<div class="cols">
<div><h4>Product</h4><ul>
<li><a href="/how-it-works/">How it works</a></li>
<li><a href="/pricing/">Pricing</a></li>
<li><a href="/verify/">Try free</a></li>
<li><a href="/check/">Check a certificate</a></li>
</ul></div>
<div><h4>Developers &amp; agents</h4><ul>
<li><a href="/docs/">Documentation</a></li>
<li><a href="/docs/api/">REST &amp; MCP API</a></li>
<li><a href="/llms.txt">llms.txt</a></li>
<li><a href="/.well-known/axiomcode.json">Machine-readable service info</a></li>
</ul></div>
<div><h4>Trust &amp; paperwork</h4><ul>
<li><a href="/paperwork/terms/">Terms of Service</a></li>
<li><a href="/paperwork/privacy/">Privacy Policy</a></li>
<li><a href="/paperwork/certificate-policy/">Certificate Policy &amp; CPS</a></li>
<li><a href="/paperwork/refunds/">Refund Policy</a></li>
<li><a href="/paperwork/sla/">Service Levels</a></li>
</ul></div>
<div><h4>Company</h4><ul>
<li><a href="/blog/">Blog</a></li>
<li><a href="/paperwork/security/">Security &amp; disclosure</a></li>
<li><a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a></li>
</ul></div>
</div>
<div class="fine">Owned by Nrupal Akolkar &middot; Built with Muse by Meta &middot; &copy; 2026 AxiomCode. Verification is evidence, not opinion.</div>
</div></footer>
</body>
</html>"""

PAGES: list = []  # (path, title, desc, body_html, jsonld)


def page(path, title, desc, body, jsonld=None):
    PAGES.append((path, title, desc, body, jsonld))


def render_all(outdir):
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    for path, title, desc, body, jsonld in PAGES:
        full = os.path.join(outdir, path.lstrip("/"))
        os.makedirs(full, exist_ok=True)
        with open(os.path.join(full, "index.html"), "w") as f:
            f.write(head(title, desc, path, jsonld) + header() + body + FOOTER)
    # root-level files
    with open(os.path.join(outdir, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: " + SITE + "/sitemap.xml\n")
    urls = [p for p, _, _, _, _ in PAGES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{SITE}{u}</loc><changefreq>weekly</changefreq></url>")
    sm.append("</urlset>")
    with open(os.path.join(outdir, "sitemap.xml"), "w") as f:
        f.write("\n".join(sm))
    print(f"rendered {len(PAGES)} pages -> {outdir}")
