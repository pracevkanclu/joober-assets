# Joober sales intro deck

Claude Code skill, který z jedné šablony vyrobí sales intro prezentaci Joober pro konkrétní firmu. Výsledek je hotové PDF (11 slajdů, 16:9). Skoro celý deck je fixní. Pro každou firmu se mění jen tři věci:

1. název firmy a datum na úvodním slajdu,
2. slajd 5 s top uchazeči a inzeráty dané firmy (generuje se z Joober adminu),
3. loga na slajdu „S kým už jednáme“ (vyřadí se konkurenti cílové firmy).

## Jak to používají kolegové

1. Otevři tuhle složku (repo) v Claude Code.
2. Napiš třeba: `udělej sales intro deck pro T-Mobile`.
3. Claude se zeptá na přesný právní název firmy, stáhne data z Joober adminu, vyrobí slajd 5, vyřadí konkurenční loga a postaví PDF. Na konci ti ukáže shrnutí: zvolený formát slajdu, vyřazené účty, členy týmu nebo zaměstnance firmy v top uchazečích (to rozhoduješ ty) a vyřazená loga.
4. Hotové PDF najdeš ve složce `.claude/skills/sales-intro-deck/out/`. Než ho někomu pošleš, projdi si slajdy a ujisti se, že je všechno v pořádku.

Celý postup je popsaný ve skillu: `.claude/skills/sales-intro-deck/SKILL.md`.

## Co potřebuješ

- **Joober Admin MCP konektor** napojený v Claude Code (bez něj nejde vyrobit slajd 5 s uchazeči). Když už slajd 5 jako PNG 1920x1080 máš, konektor nepotřebuješ.
- **Python 3** a balíčky `playwright` a `pillow`:
  ```
  pip install playwright pillow
  python3 -m playwright install chromium
  ```
- **Chromium** pro Playwright (instaluje ho druhý příkaz výše). Žádný Node.js ani další nástroje nejsou potřeba.

## Struktura repa

```
.claude/skills/sales-intro-deck/
  SKILL.md                 postup pro Claude (zadání, data z adminu, build, kontrola)
  config.json              partneři pro slajd „S kým už jednáme“ (loga a obory)
  deck/
    template.html          šablona všech 11 slajdů s placeholdery
    assets/                loga, fotky, ikony
    fonts/                 Schibsted Grotesk (lokálně)
  candidates-slide/
    template.html          šablona slajdu 5 (top uchazeči)
    build.py               JSON s daty -> PNG 1920x1080
    fonts/                 Figtree (lokálně, funguje bez sítě)
  scripts/build_deck.py    složí deck a vyrenderuje PNG slajdů a PDF
  reference/               vzor hotového slajdu 5 (T-Mobile)
README.md
```

Výstupy (`out/`) se do gitu neukládají.

## Ruční spuštění bez Claude

Slajd 5 z JSONu:

```
cd .claude/skills/sales-intro-deck
python3 candidates-slide/build.py data.json out/candidates-firma.png
```

Celý deck:

```
python3 scripts/build_deck.py \
  --company "T-Mobile Czech Republic a.s." \
  --candidates out/candidates-firma.png \
  --exclude "O2" \
  --out out/Joober_x_TMobile.pdf
```

Parametry: `--company` (povinný, právní název), `--candidates` (povinný, PNG přesně 1920x1080), `--exclude` (partneři k vyřazení oddělení čárkou, na velikosti písmen nezáleží), `--date` (výchozí je aktuální měsíc a rok, např. „listopad 2026“), `--out` (cesta k PDF). PNG všech slajdů se uloží do `png/` vedle PDF.

## Jak přidat logo partnera

1. Dej soubor s logem do `.claude/skills/sales-intro-deck/deck/assets/` (PNG s průhledným pozadím, tmavé logo, např. `logo-nazev.png`).
2. Přidej partnera do `config.json`:
   ```json
   {"name": "Název", "logo": "logo-nazev.png", "sector": "obor firmy"}
   ```
   Podle potřeby přidej `"style": "max-height:60px"` nebo `"max-width:76%"`, když je logo moc velké nebo malé. Partner bez loga se vykreslí jako textová dlaždice: místo `logo` dej `"text": "NÁZEV"`.
3. Pole `sector` používá Claude při rozhodování, koho vyřadit jako konkurenci. Vyplň ho pořádně.
4. Počet sloupců na slajdu se přizpůsobí automaticky (počet partnerů + dlaždice „+ další každý den“).

## Jak změnit fixní texty

Všechny texty a design decku jsou v `.claude/skills/sales-intro-deck/deck/template.html`. Uprav je přímo tam. Placeholdery `{{COMPANY}}`, `{{DATE}}`, `{{CANDIDATES_PNG}}`, `{{PARTNER_TILES}}` a `{{TILE_COLS}}` nech být, doplňuje je skript. Nezlomitelné mezery (za jednopísmennými předložkami, v „80 %“, „listopad 2026“ a podobně) skript doplní sám, v šabloně je psát nemusíš. Po změně spusť build a projdi PNG v `out/png/`.

## Proč je PDF rastrové

PDF je záměrně složené z obrázků (každý slajd jako JPEG ve 2x rozlišení, stránka 1440x810 pt), ne z vektorů. Vektorové PDF z Chromia ukazuje na iPhonu tmavé čtverce kolem stínů a průhledných prvků. Rastrové PDF vypadá všude stejně. Cenou je větší soubor (kolem 5 MB) a nevybíratelný text.
