# Nástroj na automatické generovanie otázok a úloh

Tento projekt predstavuje nástroj pre automatické generovanie vzdelávacích objektov, otázok, úloh, odpovedí a nápovedí z PDF dokumentov pomocou veľkého jazykového modelu.

Aplikácia je vytvorená v jazyku Python a používa webové rozhranie Streamlit. Na generovanie a hodnotenie výstupov využíva veľký jazykový model Gemini cez API kľúč.

## Hlavné funkcie

- nahratie PDF dokumentu cez webové rozhranie,
- extrakcia textu z PDF dokumentu,
- OCR spracovanie textu z obrázkov v dokumente,
- generovanie vzdelávacích objektov,
- zhlukovanie podobných vzdelávacích objektov,
- dopĺňanie prerekvizít medzi vzdelávacími objektmi,
- validácia a filtrácia vygenerovaných výstupov,
- generovanie otázok a praktických úloh,
- generovanie odpovedí a nápovedí,
- export výsledkov do JSON, TXT a PDF súborov,
- vizualizácia vzťahov medzi vzdelávacími objektmi.

## Požiadavky

Pred spustením projektu je potrebné mať nainštalované:

- odporúčaná verzia: Python 3.12,
- nástroj `pip`,
- API kľúč pre Gemini,
- vo Windowse: Microsoft Visual C++ v14 Redistributable, odporúčané nainštalovať verziu x64 aj x86.

Projekt bol vyvíjaný a testovaný na Python 3.12.6. Použitie Pythonu 3.10 alebo novšieho by malo byť možné, ale odporúča sa Python 3.12.

Projekt bol pripravovaný ako lokálna Streamlit aplikácia.

Skontrolujte si, či máte nainštalované Microsoft Visual C++ v14 Redistributable x64 a x86.

Inštalačný súbor je možné stiahnuť z oficiálnej stránky Microsoftu:

```text
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170
```

Vo Windowse je možné Microsoft Visual C++ v14 Redistributable nainštalovať aj cez `winget` a to nasledovne:

```bash
winget install --id Microsoft.VCRedist.2015+.x64 -e
winget install --id Microsoft.VCRedist.2015+.x86 -e
```

## Inštalácia

Najskôr si stiahnite alebo naklonujte projekt a otvorte jeho koreňový priečinok v termináli.

Vytvorte virtuálne prostredie:

```bash
python -m venv venv
```

Aktivujte virtuálne prostredie.

Vo Windows:

```bash
venv\Scripts\activate
```

V Linuxe alebo macOS:

```bash
source venv/bin/activate
```

Nainštalujte potrebné knižnice:

```bash
pip install -r requirements.txt
```

## Nastavenie API kľúča

Projekt používa model Gemini, preto je potrebné nastaviť API kľúč.

V koreňovom priečinku projektu vytvorte súbor s názvom:

```text
.env
```

Do súboru `.env` vložte riadok:

```env
GEMINI_API_KEY=vas_api_kluc
```

Hodnotu `vas_api_kluc` nahraďte vlastným API kľúčom pre Gemini.

Príklad:

```env
GEMINI_API_KEY=AIza...
```

Súbor `.env` nesmie byť zverejnený v repozitári, pretože obsahuje súkromný API kľúč.

## Spustenie aplikácie

Po nainštalovaní závislostí a nastavení API kľúča spustite aplikáciu príkazom:

```bash
streamlit run Hlavna_cast/app.py
```

Po spustení sa v termináli zobrazí lokálna adresa aplikácie, napríklad:

```text
http://localhost:8501
```

Túto adresu otvorte vo webovom prehliadači.

## Použitie aplikácie

1. Otvorte aplikáciu v prehliadači.
2. Prejdite na časť určenú na nahratie dokumentu.
3. Nahrajte PDF dokument.
4. Spustite extrakciu a spracovanie dokumentu.
5. Aplikácia automaticky vygeneruje vzdelávacie objekty.
6. Následne sa vygenerujú otázky, úlohy, odpovede a nápovedy.
7. Výsledky je možné zobraziť v aplikácii a stiahnuť vo výstupných formátoch.

## Výstupy

Výstupy sa ukladajú do priečinka:

```text
Hlavna_cast/vystup
```

Medzi hlavné výstupy patria:

- extrahovaný text z dokumentu,
- vzdelávacie objekty,
- otázky a úlohy,
- odpovede a nápovedy,
- PDF a TXT exporty,
- vizualizácia vzťahov medzi vzdelávacími objektmi.


## Riešenie častých problémov

Ak aplikácia vypíše chybu, že chýba `GEMINI_API_KEY`, skontrolujte, či existuje súbor `.env` v koreňovom priečinku projektu a či obsahuje správny riadok:

```env
GEMINI_API_KEY=vas_api_kluc
```

Ak sa aplikácia nespustí kvôli chýbajúcim knižniciam, znova spustite:

```bash
pip install -r requirements.txt
```

Ak sa zobrazí chyba typu `DLL load failed`, vo Windows pravdepodobne chýba Microsoft Visual C++ v14 Redistributable. Nainštalujte obe verzie:

- Microsoft Visual C++ v14 Redistributable x64,
- Microsoft Visual C++ v14 Redistributable x86.

Oficiálna stránka Microsoftu na stiahnutie:

```text
https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170
```

Príkazy pre inštaláciu Microsoft Visual C++ v14 Redistributable cez `winget`:

```bash
winget install --id Microsoft.VCRedist.2015+.x64 -e
winget install --id Microsoft.VCRedist.2015+.x86 -e
```

Po inštalácii odporúčame zavrieť terminál, otvoriť ho znova, aktivovať virtuálne prostredie a aplikáciu spustiť opäť.

Ak sa príkaz `streamlit` nerozpozná, skontrolujte, či je aktivované virtuálne prostredie.

Ak spracovanie trvá dlhšie, je to očakávané pri väčších PDF dokumentoch, dokumentoch s obrázkami alebo pri väčšom počte generovaných otázok a úloh.

## Poznámky

Projekt vyžaduje internetové pripojenie, pretože generovanie výstupov prebieha cez Gemini API.

Kvalita výstupov závisí od kvality vstupného PDF dokumentu, extrahovaného textu a odpovedí jazykového modelu.

API kľúč uchovávajte iba lokálne v súbore `.env` a nezdieľajte ho verejne.
