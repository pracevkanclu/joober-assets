#!/usr/bin/env python3
"""Složí Joober sales intro deck pro konkrétní firmu a vyrenderuje PDF.

Použití:
  python3 scripts/build_deck.py --company "T-Mobile Czech Republic a.s." \
      --candidates out/candidates-tmobile.png --exclude "O2" \
      --out out/Joober_x_TMobile.pdf

Závislosti: playwright (Chromium) a Pillow.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
DECK = SKILL / "deck"
CONFIG = SKILL / "config.json"
EXPECTED_SLIDES = 11

MONTHS = ["leden", "únor", "březen", "duben", "květen", "červen",
          "červenec", "srpen", "září", "říjen", "listopad", "prosinec"]

NB = "&nbsp;"


def die(msg):
    print("CHYBA: " + msg, file=sys.stderr)
    sys.exit(1)


def default_date():
    now = datetime.date.today()
    return "%s %d" % (MONTHS[now.month - 1], now.year)


def slugify(text):
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t or "deck"


# ---------- typografie (nezlomitelné mezery) ----------

_MONTH_RE = re.compile(r"\b(%s)( )(?=\d{4}\b)" % "|".join(MONTHS), re.I)


def _fix_text(t):
    # jednopísmenné předložky a spojky (v, s, z, k, o, u, a, i) na konci řádku
    t = re.sub(r"(?<![\w&;])([vszkouaiVSZKOUAI]) (?=\S)", lambda m: m.group(1) + NB, t)
    # tisíce: 1 000
    t = re.sub(r"(?<=\d) (?=\d{3}\b)", NB, t)
    # číslo + jednotka
    t = re.sub(r"(?<=\d) (?=%|Kč|měsíců|minut|hodin|PARTNERŮ|partnerů)", NB, t)
    t = re.sub(r"(?<=\+) (?=let)", NB, t)
    t = re.sub(r"(?<=\d\.) (?=letech)", NB, t)
    # měsíc + rok (libovolný český měsíc v 1. pádě), např. "listopad 2026"
    t = _MONTH_RE.sub(lambda m: m.group(1) + NB, t)
    # za znakem ×
    t = re.sub(r"(?<=×) ", NB, t)
    return t


def fix_typography(src):
    """Opraví mezery jen v textových uzlech, <style> a značky nechá být."""
    parts = re.split(r"(<style.*?</style>|<script.*?</script>|<!--.*?-->|<[^>]+>)", src, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        out.append(_fix_text(p) if i % 2 == 0 and p.strip() else p)
    return "".join(out)


# ---------- partneři ----------

def load_partners():
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        die("nelze načíst %s: %s" % (CONFIG, e))
    return cfg.get("partners", [])


def tile_html(p):
    name = html.escape(p["name"], quote=True)
    if p.get("logo"):
        logo = DECK / "assets" / p["logo"]
        if not logo.is_file():
            die("chybí logo %s pro partnera %s" % (logo, p["name"]))
        style = ' style="%s"' % html.escape(p["style"], quote=True) if p.get("style") else ""
        return '<div class="tile"><img src="assets/%s" alt="%s"%s></div>' % (
            html.escape(p["logo"], quote=True), name, style)
    text = html.escape(p.get("text") or p["name"])
    return '<div class="tile bdo">%s</div>' % text


def select_partners(exclude_arg):
    partners = load_partners()
    excl = [x.strip() for x in (exclude_arg or "").split(",") if x.strip()]
    known = {p["name"].lower(): p["name"] for p in partners}
    excluded = set()
    for x in excl:
        if x.lower() in known:
            excluded.add(x.lower())
        else:
            print("VAROVÁNÍ: neznámý partner v --exclude: %r (známí: %s)" % (x, ", ".join(known.values())),
                  file=sys.stderr)
    kept = [p for p in partners if p["name"].lower() not in excluded]
    if excluded:
        print("Vyřazená loga: " + ", ".join(known[x] for x in sorted(excluded)))
    return kept


# ---------- sestavení HTML ----------

def build_html(company, date, candidates_url, partners):
    tpl = (DECK / "template.html").read_text(encoding="utf-8")
    for key in ("{{COMPANY}}", "{{DATE}}", "{{CANDIDATES_PNG}}", "{{PARTNER_TILES}}", "{{TILE_COLS}}"):
        if key not in tpl:
            die("v template.html chybí placeholder %s" % key)
    tiles = "\n    ".join(tile_html(p) for p in partners)
    s = tpl.replace("{{PARTNER_TILES}}", tiles)
    s = s.replace("{{TILE_COLS}}", str(len(partners) + 1))
    s = s.replace("{{CANDIDATES_PNG}}", candidates_url)
    s = s.replace("{{DATE}}", html.escape(date))
    s = s.replace("{{COMPANY}}", html.escape(company))
    s = fix_typography(s)
    left = re.findall(r"\{\{[A-Z_]+\}\}", s)
    if left:
        die("v HTML zůstaly nevyplněné placeholdery: %s" % ", ".join(sorted(set(left))))
    return s


# ---------- render ----------

def render(html_path, png_dir):
    from playwright.sync_api import sync_playwright
    png_dir.mkdir(parents=True, exist_ok=True)
    for old in png_dir.glob("slide-*.png"):
        old.unlink()
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg.goto(html_path.as_uri(), wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_function(
            "Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r}))).then(()=>true)")
        bad = pg.evaluate("[...document.images].filter(i=>!i.naturalWidth).map(i=>i.getAttribute('src'))")
        if bad:
            b.close()
            die("nenačetly se obrázky: %s" % ", ".join(bad))
        if not pg.evaluate("document.fonts.check('700 20px \"Schibsted Grotesk\"')"):
            print("VAROVÁNÍ: font Schibsted Grotesk není načtený", file=sys.stderr)
        pg.wait_for_timeout(400)
        slides = pg.query_selector_all("section.slide")
        if len(slides) != EXPECTED_SLIDES:
            b.close()
            die("očekáváno %d slajdů, nalezeno %d" % (EXPECTED_SLIDES, len(slides)))
        for i, s in enumerate(slides, 1):
            out = png_dir / ("slide-%02d.png" % i)
            s.screenshot(path=str(out))
            paths.append(out)
        b.close()
    return paths


def build_pdf(pngs, pdf_path):
    from PIL import Image
    ims = []
    for p in pngs:
        im = Image.open(p).convert("RGB")
        if im.size != (3840, 2160):
            die("neočekávaná velikost %s: %s" % (p, im.size))
        ims.append(im)
    # 3840 px = 1440 pt  ->  192 dpi  (72 pt na palec)
    ims[0].save(str(pdf_path), "PDF", save_all=True, append_images=ims[1:],
                resolution=192.0, quality=92)


def count_pdf_pages(pdf_path):
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def main():
    ap = argparse.ArgumentParser(description="Joober sales intro deck -> PDF")
    ap.add_argument("--company", required=True, help="právní název firmy")
    ap.add_argument("--candidates", required=True, help="PNG slajdu 5, přesně 1920x1080")
    ap.add_argument("--exclude", default="", help="čárkou oddělený seznam partnerů k vyřazení")
    ap.add_argument("--date", default=None, help='např. "listopad 2026" (výchozí: aktuální měsíc a rok)')
    ap.add_argument("--out", required=True, help="cesta k výstupnímu PDF")
    a = ap.parse_args()

    company = a.company.strip()
    if not company:
        die("--company je prázdné")
    cand = Path(a.candidates).expanduser().resolve()
    if not cand.is_file():
        die("soubor se slajdem 5 neexistuje: %s" % cand)
    try:
        from PIL import Image
        with Image.open(cand) as im:
            size = im.size
    except Exception as e:
        die("nelze otevřít %s jako obrázek: %s" % (cand, e))
    if size != (1920, 1080):
        die("slajd 5 musí mít 1920x1080 px, %s má %dx%d" % (cand.name, size[0], size[1]))

    date = (a.date or default_date()).strip()
    out_pdf = Path(a.out).expanduser().resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    png_dir = out_pdf.parent / "png"

    partners = select_partners(a.exclude)
    page = build_html(company, date, cand.as_uri(), partners)

    html_path = DECK / ("_build_%s.html" % slugify(company))
    html_path.write_text(page, encoding="utf-8")
    try:
        pngs = render(html_path, png_dir)
    finally:
        try:
            html_path.unlink()
        except OSError:
            pass

    build_pdf(pngs, out_pdf)
    pages = count_pdf_pages(out_pdf)
    if pages != EXPECTED_SLIDES:
        die("PDF má %d stránek, očekáváno %d" % (pages, EXPECTED_SLIDES))
    print("PDF:  %s (%d stran, %.1f MB)" % (out_pdf, pages, out_pdf.stat().st_size / 1e6))
    print("PNG:  %s/slide-01.png ... slide-%02d.png" % (png_dir, len(pngs)))
    print("Datum na úvodním slajdu: %s" % date)


if __name__ == "__main__":
    main()
