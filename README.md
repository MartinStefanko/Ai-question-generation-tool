# Nástroj na automatické generovanie otázok a úloh

Tento projekt predstavuje nástroj pre automatické generovanie
vzdelávacích objektov, otázok, úloh, odpovedí a nápovedí z PDF dokumentov
pomocou veľkého jazykového modelu.

## Funkcionalita
- nahratie PDF dokumentu
- extrakcia a segmentácia textu
- generovanie vzdelávacích objektov (LO)
- zhlukovanie LO na základe sémantickej podobnosti
- generovanie otázok a úloh
- vizualizácia vzťahov medzi LO

## Spustenie projektu

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
streamlit run Hlavna_cast/app.py
