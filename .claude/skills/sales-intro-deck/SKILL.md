---
name: sales-intro-deck
description: Sales intro prezentace Joober pro konkrétní firmu. Použij, když někdo řekne „udělej deck / prezku / sales intro pro <firma>“, „připrav prezentaci k <firma>“ nebo potřebuje slajd s top uchazeči z Joober adminu. Výstup je hotové PDF (11 slajdů, 16:9).
---

# Sales intro deck pro firmu

Uživatel řekne firmu, ke které jde. Výsledkem je hotové PDF `Joober_x_<Firma>.pdf` s 11 slajdy. Skoro celý deck je fixní. Pro každou firmu se mění jen:

1. **název firmy** na úvodním slajdu („Pro <právní název> · <měsíc rok>“),
2. **slajd 8 s top uchazeči a inzeráty** firmy (generuje se z Joober adminu),
3. **loga na slajdu 5 „S kým už jednáme“**: vyřadit konkurenty cílové firmy.

Všechno ostatní (texty, design, pořadí slajdů, nabídka) se NEMĚNÍ, pokud to uživatel výslovně nechce.

Jazyk: čeština. S uživatelem tykej. Na slajdech vůči klientovi vykání. Nikdy nepoužívej em dash (—) ani en dash jako interpunkci. Značka se píše „Joober“ (s velkým J), logo na slajdech je wordmark „joober“.

Úspora: datové lookupy v Joober adminu a stavbu/render deleguj na levnějšího subagenta (Sonnet nebo Haiku). Rozhodnutí (výběr uchazečů, formát slajdu, texty, konkurenti) dělej sám.

## Struktura skillu

```
sales-intro-deck/
  SKILL.md
  config.json                  partneři (loga) a jejich obory, kontakty
  deck/template.html           šablona 11 slajdů ({{COMPANY}}, {{DATE}}, {{CANDIDATES_PNG}}, {{PARTNER_TILES}})
  deck/assets/, deck/fonts/    loga, fotky, ikony, Schibsted Grotesk
  candidates-slide/            template.html + build.py pro slajd 8 (Figtree lokálně)
  scripts/build_deck.py        složí deck a vyrenderuje PDF
  reference/                   vzor hotového slajdu 8 (T-Mobile)
```

Předpoklady: Python 3, `pip install playwright pillow` a Chromium (`python3 -m playwright install chromium`, pokud v prostředí ještě není). Ověř na začátku jedním příkazem a případně doinstaluj.

## Postup

### Krok 0: Ujasni zadání
- Přesný právní název firmy (např. „T-Mobile Czech Republic a.s.“). Když ho uživatel nenapíše, najdi ho v adminu (`company.list`) a potvrď.
- Pokud už uživatel má hotový PNG slajd 8 (např. z jiného chatu), přeskoč kroky 1 až 7 a použij ho.

### Kroky 1 až 7: Slajd 8 „Top uchazeči“ z Joober adminu

Výstup: PNG 1920×1080 přes `candidates-slide/build.py data.json out.png`. Vzor: `reference/candidates-example-tmobile.png`.

**1. Najdi firmu (všechny její entity).**
- `company.list { q: <název>, hasPostings: true, page: 1, pageSize: 20 }`.
- Firma může mít víc entit (T-Mobile má 4: „T-Mobile Czech Republic a.s.“, „Partner T-Mobile Czech Republic a.s.“ s inzeráty obchodních partnerů, „T-Mobile Czech Republic a.s.; Slovak Telekom a.s.“, „T-Mobile … - Partner“). Vezmi všechny, které jasně patří ke značce, a u každého výsledku si pamatuj entitu. Partnerské inzeráty vždy nahlas, o jejich zařazení rozhoduje uživatel.
- Firma s opt-out: negeneruj, nahlas.

**2. Aktivní inzeráty.**
- `company.postings` se `status: "published"`, `includeDeleted: false`, `sort: "-createdAt"`, `pageSize: 100` (schéma vyžaduje i všechna `null` pole, ověř přes `admin_describe`).
- Aktivní = jen `published`, nesmazaný, neskrytý. `totalCount` je autorita.
- U vybraných inzerátů `posting.get { postingId }`: `current.title`, `current.rawLocation`, `salaryMin/Max`, `commitment.workload` (full_time = Plný úvazek, part_time = Zkrácený úvazek), `workMode` (on_site = Na pracovišti, hybrid = Hybridně, remote = Remote), `summary.requirements`.

**3. Shody (match.list).**
- `match.list { search: <přesný název entity>, page: N, pageSize: 100, sort: "-totalScore" }`, stránkuj dokud `hasMore`. Nevynechej poslední stránku, bývají na ní KO řádky se skóre 0.
- Výstup přeteče limit nástroje a uloží se do souboru. Agreguj pythonem nad soubory, nečti to do kontextu.
- `search` je podřetězcové hledání. Vždy filtruj: `companyName` je jedna z entit firmy, `postingStatus === "published"`, žádné `postingDeletedAt` / `postingHiddenAt`.
- Algoritmus je **v4** (v5 vrací prázdno, v3 `stored: null`).

**4. Statistiky nahoře (pevná definice).** Z řádků po filtru z kroku 3, bez vyloučení (interní účty i KO zůstávají):

| Dlaždice | Výpočet |
|---|---|
| uchazečů ohodnoceno | počet řádků (uchazeč × aktivní inzerát), KO započítané |
| se shodou nad 60 % | počet řádků s `totalScore > 0,60` |
| průměrná shoda | průměr `totalScore` přes všechny řádky, KO = 0, zaokrouhlit na celé % |

U formátu pro jeden inzerát totéž jen pro řádky toho inzerátu. Nikdy nepoužívej surový `totalCount` z match.list. (Příklad T-Mobile 3. 11. 2026: 341 surových řádků, správně 85 / 4 / 27 %.)

**5. Výběr uchazečů.** Pool je přísnější než statistiky:
1. Jen `koStatus === "SUCCESS"`.
2. Dedup na člověka podle normalizovaného e-mailu (zahoď `+suffix`), více profilů jedné osoby slouč, ber nejvyšší skóre.
3. Vždy vyřaď benchmark profily `@nexojob-bench.test`, testovací účty a Honzovy vlastní profily.
4. Nahlas a zeptej se (nevyřazuj automaticky): členy týmu Joober (např. Luboš) a současné zaměstnance cílové firmy. Když člen týmu zůstane, roli napiš obecně, aby nebyl poznat.
5. Zaměstnavatele a roli ber z `user.get { userId: <profileId> }`: jen `rawRoleTitle` aktuální zkušenosti (`isCurrent: true`), zaměstnavatele, předchozí roli a délku praxe. Zbytek odpovědi zahoď (obsahuje tokeny, telefon, datum narození).

Formát slajdu:
- **A) Jeden inzerát, top 5:** když existuje inzerát s aspoň 5 platnými uchazeči a přesvědčivým skóre (ideálně všech 5 nad 60 %). Ber inzerát s nejvyšším průměrem top 5.
- **B) Napříč inzeráty, top N:** když žádný inzerát nemá silnou pětku. Ke každému inzerátu nejlepší platný uchazeč, každý člověk max jednou, seřadit podle skóre, na slajd jen uchazeči nad 60 % (typicky 3 až 5). Při 4 řádcích `cardH: 158`, `rowStep: 170`; při 5 výchozí, ale pak u každého uchazeče jen 1 plus a 1 mínus (řádek s inzerátem + 2 plusy se do výchozí karty nevejdou).
- Když nad 60 % nevychází nikdo nebo jen 1 až 2 lidé, slajd ani deck nedělej a ukaž uživateli, jak data vypadají. Slabý slajd klientovi uškodí.

**6. Data k uchazečům.**
- `match.diagnostics { algorithmVersion: "v4", profileId, postingId }` → `storedExplain.pillar1/2/3.score` (dovednosti / kariérní dráha / osobnostní fit, váhy 40/40/20) a `finalScore`. Ověř `skóre ≈ 0,4·dovednosti + 0,4·kariéra + 0,2·fit`, nesoulad nahlas.
- Zdůvodnění z `storedExplain.reasonings` (případně `reasoning.list`): nadpis + 2 plusy + 1 mínus. Když chybí, slož ho z pilířů, skillů a historie a řekni, u kterých řádků je složené.
- Délky: role max ~28 znaků, podtitulek ~45, nadpis zdůvodnění ~60, plus/mínus ~65. Zkracuj sám, ať nic neořízne trojtečka.
- Mínus neutrálně („zatím není doložené“, „v profilu chybí“), nikdy shazovat.

**7. JSON a render.** Struktura JSONu (formát B, u formátu A viz komentáře):

```jsonc
{
 "company": "T-Mobile Czech Republic a.s.",
 "eyebrow": "VAŠE AKTIVNÍ INZERÁTY · TOP 4 UCHAZEČI",   // A: "VÁŠ AKTIVNÍ INZERÁT · TOP 5 UCHAZEČŮ"
 "title": "Nejlepší uchazeči pro vaše otevřené pozice", // A: název inzerátu
 "location": "Praha · Jihlava · České Budějovice",
 "chips": ["CRM a zákaznická analytika", "Obchod v partnerské síti", "Shoda nad 60 %"], // A: mzda, úvazek, work mode
 "requirements": "Ke každému uchazeči uvádíme inzerát, na který se hodí nejvíc · hodnoceno napříč všemi vašimi aktivními inzeráty", // A: "Požadavky: …"
 "stats": [{"value":"85","label":"uchazečů\nohodnoceno"},{"value":"4","label":"se shodou\nnad 60 %"},{"value":"27 %","label":"průměrná\nshoda"}],
 "whyHeader": "INZERÁT · ZDŮVODNĚNÍ",  // A: vynech
 "cardH": 158, "rowStep": 170,          // A s 5 řádky: vynech
 "candidates": [
  {"rank":1,"role":"Obchodní konzultantka","subtitle":"projekty a B2B obchod, 26 let praxe",
   "score":78,"pillars":{"skills":100,"career":54,"fit":82},
   "posting":"Obchodní specialista pro optický internet · Jihlava", // jen B
   "headline":"Obchodní zkušenosti a vyjednávání sedí na terénní prodej",
   "pros":["Obchodní jednání a příprava nabídek","Aktivně vyhledává zákazníky, bydlí na Vysočině"],
   "con":"Komunikativnost zatím není doložená výsledky"}
 ],
 "footer": "Reálná data z joober.ai, algoritmus v4 · skóre = 40 % dovednosti + 40 % kariérní dráha + 20 % osobnostní fit · jména skrytá",
 "cta": "⚡ Převezměte profil a oslovte je"
}
```

Render: `python3 candidates-slide/build.py data.json out/candidates-<firma>.png`.

Kontrola slajdu 8: do JSONu nikdy nedávej jméno, e-mail ani id uchazeče (šablona má jen rozmazaný placeholder). Po buildu grepni vygenerované HTML na `@` a na jména z běhu, musí být prázdné. Otevři PNG (Read) a zkontroluj, že nic není oříznuté ani nepřetéká a čísla odpovídají kroku 4.

### Krok 7b: Simulace (jen na výslovný pokyn uživatele)
Když firma nemá aktivní inzeráty nebo jsou shody slabé a uživatel výslovně chce simulaci: vezmi nedávné (i stažené) inzeráty a skutečné profily a skóre uprav podle zadání. Pilíře dopočítej tak, aby sedělo 0,4·dovednosti + 0,4·kariéra + 0,2·fit. Texty slajdu nech standardní (simulaci vysvětluje prezentující ve voiceoveru), eyebrow ale piš „VAŠE NEDÁVNÉ INZERÁTY“ (ne „aktivní“) a patička NESMÍ tvrdit reálná data: použij „Algoritmus v4 · skóre = 40 % dovednosti + 40 % kariérní dráha + 20 % osobnostní fit · jména skrytá“. V shrnutí uživateli vždy připomeň, že slajd je simulace.

### Krok 8: Konkurenti na slajdu 5 „S kým už jednáme“

`config.json` obsahuje partnery (loga) s obory. Vyřaď každé logo, které je přímou konkurencí cílové firmy (stejný trh nebo produkt). Příklady: pro T-Mobile vyřadit O2; pro personální agenturu vyřadit jiné personální agentury a job portály. Vždy vyřaď i logo samotné cílové firmy (např. ABRA v decku pro ABRA). Když si nejsi jistý, zeptej se. Vyřazení vždy uveď v závěrečném shrnutí.

Když uživatel řekne, že s novou firmou jednáte, přidej ji do `config.json` (logo do `deck/assets/`) a commitni.

### Krok 9: Postav deck

```
python3 scripts/build_deck.py \
  --company "T-Mobile Czech Republic a.s." \
  --candidates out/candidates-tmobile.png \
  --exclude "O2" \
  --out out/Joober_x_TMobile.pdf
```

Datum se doplní automaticky (český měsíc a rok, např. „listopad 2026“), jde přepsat `--date`. Skript:
- doplní firmu, datum, slajd 8 a loga do šablony a opraví českou typografii (nezlomitelné mezery),
- vyrenderuje každý slajd jako PNG ve 2× rozlišení (`out/png/`),
- složí PDF z obrázků (JPEG, 1440×810 pt). PDF je záměrně rastrové: vektorové PDF z Chromia ukazuje na iPhonu tmavé čtverce kolem stínů a průhledných prvků.

### Krok 10: Kontrola a předání
- Otevři (Read) všechny PNG z `out/png/` a zkontroluj: název firmy na slajdu 1, slajd 8 je ten správný, žádné konkurenční logo, nic nepřetéká.
- Pošli PDF uživateli (SendUserFile) s krátkým shrnutím.

## Co vždy nahlásit uživateli
- Zvolený formát slajdu 8 (A, nebo B) a proč.
- Koho jsi vyřadil (interní a testovací účty) a kolik řádků to bylo.
- Členy týmu nebo zaměstnance cílové firmy v top N, jako věc k rozhodnutí. Netvrď, že je deck hotový k odeslání, dokud to uživatel nerozhodne.
- Řádky z partnerských entit.
- U kterých uchazečů je zdůvodnění z Jooberu a u kterých složené.
- Vyřazená konkurenční loga.
- Cokoli podezřelého v datech (chybějící mzda, duplicitní profily, divné skóre).

## Struktura decku (fixní, pro orientaci)
1. Úvod: eyebrow „AI kariérní marketplace · revoluce v hledání práce“, headline „Pracovní portály pořád vypadají jako v 90. letech. Rozhodli jsme se to změnit.“, subheadline „Uchazeče oskórujeme, seřadíme a vysvětlíme, proč sedí. Vy si jen vyberete.“ + „Pro <firma> · <datum>“
2. Kdo jsme a proč jsme do toho šli (zakladatelé, tým, CzechInvest)
3. Spuštěno pro uchazeče. Teď stavíme pro firmy.
4. Uchazeče Joober baví, tráví u nás čas a vrací se (60 000+ návštěvníků).
5. S kým už jednáme (loga bez konkurentů a bez cílové firmy)
6. Jak to vypadá v praxi (live demo ATS)
7. Technologie, kterou nikdo jiný na trhu nemá (vlastní data, vlastní modely, AI Act ready; galaxie 70 000 dovedností)
8. **Top uchazeči pro firmu (proměnný)**
9. Nabídka pro prvních 100 firem: 1/10 ceny (999 Kč za inzerát) na 6 měsíců; inzerát běží 45 dní a když k němu nenajdeme žádného uchazeče nad 60 %, prodloužíme ho zdarma
10. Předěl: Co připravujeme dál
11. AI headhunting (live demo, kontakty)

Pokud je cílovou firmou provozovatel pracovního portálu (např. Alma Career / jobs.cz), změň headline slajdu 1 na „Pracovní portály se od 90. let skoro nezměnily. My to měníme.“ nebo se zeptej uživatele.

Voiceover poznámky pro prezentujícího: na slajdu 3 mluvit o automatizaci jako o výkonu recruiterů, ne o náhradě; na slajdu 9 se před částí 2 zeptat na nabídku přímo; na slajdu 11 jen ústně zmínit, že hledáme investora.
