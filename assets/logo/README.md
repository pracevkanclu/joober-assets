# joober — logo

Vektorové SVG jsou zdroj pravdy. PNG jsou z nich vygenerované, needituj je ručně —
při změně přegeneruj z SVG.

## Soubory

| Soubor | K čemu |
|---|---|
| `joober-logo.svg` | Hlavní logo (blesk + nápis na fialové plošce). Výchozí volba. |
| `joober-logo.png` | Rastr 696 × 264 px pro nástroje, které SVG neberou. |
| `joober-logo@2x.png` / `@1x.png` | 232 × 88 a 116 × 44 px — e-mailový podpis. Zobrazuj vždy na 116 × 44. |
| `joober-mark.svg` / `.png` | Jen ikona ve fialovém čtverci. Avatary, dlaždice, malé plochy. |
| `joober-mark-bolt.svg` | Samotný blesk bez podkladu. Jen na fialové pozadí. |
| `joober-wordmark.svg` | Jen nápis, tmavý. Pouze na světlé pozadí. |
| `joober-wordmark-white.svg` | Jen nápis, bílý. Pouze na tmavé pozadí. |
| `favicon-32.png`, `favicon-192.png`, `apple-touch-icon.png` | Ikony pro web. |

## Barvy

| | HEX |
|---|---|
| Fialová | `#7314D0` |
| Fialový přechod | `#8A2BE8` → `#6A0FC2` |
| Oranžová | `#EFA968` |
| Přechod blesku | `#FDE6C9` → `#F3B073` → `#ED9A55` |
| Tmavá | `#0F0F15` |

## Na co si dát pozor

- `joober-wordmark.svg` je tmavý na průhledném pozadí — na tmavém podkladu zmizí.
  Na tmavé pozadí patří `joober-wordmark-white.svg`, nebo rovnou `joober-logo.svg`,
  které má vlastní podklad a funguje všude.
- PNG mají nastaveno 72 DPI. Outlook si obrázky přepočítává podle DPI, při jiné
  hodnotě zobrazí logo špatně velké.
- Logo nepřebarvuj, nerotuj a needituj mu proporce. Pro jinou velikost použij SVG.

## Přegenerování PNG ze SVG

```bash
# potřebuje: pip install cairosvg pillow
python3 - <<'PY'
import cairosvg, io
from PIL import Image
def png(svg, w, h, out):
    b = cairosvg.svg2png(url=svg, output_width=w, output_height=h)
    Image.open(io.BytesIO(b)).convert("RGBA").save(out, "PNG", dpi=(72, 72), optimize=True)

png("joober-logo.svg", 696, 264, "joober-logo.png")
png("joober-logo.svg", 232,  88, "joober-logo@2x.png")
png("joober-logo.svg", 116,  44, "joober-logo@1x.png")
png("joober-mark.svg", 512, 512, "joober-mark.png")
png("joober-mark.svg",  32,  32, "favicon-32.png")
png("joober-mark.svg", 192, 192, "favicon-192.png")
png("joober-mark.svg", 180, 180, "apple-touch-icon.png")
PY
```
