#!/usr/bin/env python3
"""Usage: python3 build.py data.json out.png

Vyrenderuje slajd 5 (Top uchazeči) jako PNG 1920x1080.
Font Figtree se načítá lokálně z fonts/*.woff2 (bez sítě).
Vedle PNG se uloží i vygenerované HTML (pro kontrolu: grep na '@' a na jména).
"""
import sys, json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python3 build.py data.json out.png")
    data_path, png_path = sys.argv[1], os.path.abspath(sys.argv[2])
    here = os.path.dirname(os.path.abspath(__file__))
    data = json.load(open(data_path, encoding="utf-8"))
    tpl = open(os.path.join(here, "template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    if "/*DATA*/" not in tpl:
        sys.exit("placeholder /*DATA*/ missing in template")
    html = tpl.replace("/*DATA*/null", payload, 1) if "/*DATA*/null" in tpl else tpl.replace("/*DATA*/", payload, 1)
    # HTML leží vedle PNG, fonty se dohledají přes <base> na složku skriptu
    base = Path(here).as_uri() + "/"
    html = html.replace("<head>", '<head><base href="%s">' % base, 1)
    os.makedirs(os.path.dirname(png_path), exist_ok=True)
    html_path = os.path.splitext(png_path)[0] + ".html"
    open(html_path, "w", encoding="utf-8").write(html)

    # kontrola soukromí: v HTML nesmí být zavináč (e-mail), @font-face a @media se ignorují
    probe = re.sub(r"@(font-face|media|keyframes|import|supports)", "", html)
    if "@" in probe:
        print("VAROVÁNÍ: vygenerované HTML obsahuje '@' (e-mail?). Zkontroluj %s a odstraň osobní údaje." % html_path,
              file=sys.stderr)

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.goto(Path(html_path).as_uri(), wait_until="load")
        pg.evaluate("document.fonts.ready")
        try:
            pg.wait_for_function("document.fonts.status==='loaded'", timeout=8000)
        except Exception:
            print("VAROVÁNÍ: fonty se nenačetly včas", file=sys.stderr)
        ok = pg.evaluate("document.fonts.check('700 20px Figtree')")
        if not ok:
            print("VAROVÁNÍ: Figtree není k dispozici, slajd by vypadal jinak", file=sys.stderr)
        pg.wait_for_timeout(300)
        pg.screenshot(path=png_path, clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
        b.close()
    print(png_path, html_path)


main()
