import streamlit as st
import tempfile
import os
import time
from text_extraction import pdf_to_text
from lo_pipeline import generate_lo_pipeline
from item_pipeline import generate_all_items
from outputs import save_learning_objects_json_txt, save_questions_json_txt, save_lo_graph_png

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "vystup")

st.set_page_config(layout="centered")

st.title("Nástroj na automatické generovanie otázok a úloh")

tab_domov, tab_dokument, tab_lo, tab_otazky, tab_viz = st.tabs(
    ["Domov", "Načítanie dokumentu", "Vzdelávacie objekty","Otázky a úlohy","Vizualizácia"]
)

with tab_domov:
    st.write(
        "Tento nástroj slúži na automatické generovanie otázok, úloh, odpovedí a nápovedí z učebných materiálov vo formáte PDF. "
        "Cieľom je uľahčiť študentom prácu s rozsiahlymi učebnými materiálmi a poskytnúť prehľadnú sadu " 
        "učebných položiek (otázka, úloha, odpoveď, nápoveda)."
    )

    st.subheader("Postup spracovania dokumentu")
    st.markdown(
        """
        1. **Načítanie dokumentu** – používateľ nahrá PDF dokument, ktorý slúži ako vstupný učebný materiál.  
        2. **Extrakcia a segmentácia textu** – z dokumentu sa extrahuje text a rozdelí sa na menšie časti pre ďalšie spracovanie.  
        3. **Tvorba vzdelávacích objektov** – nástroj identifikuje základné vzdelávacie objekty (témy a pojmy) spolu s ich metadátami.  
        4. **Zhlukovanie vzdelávacích objektov** – podobné alebo duplicitné vzdelávacie objekty sú automaticky zoskupované na základe sémantickej podobnosti.  
        5. **Generovanie otázok a úloh** – pre každý vzdelávací objekt sa vytvárajú teoretické otázky alebo praktické úlohy spolu s odpoveďami a nápovedami.  
        6. **Vizualizácia výsledkov** – vzdelávacie objekty a ich vzťahy sú prehľadne zobrazené pomocou grafických vizualizácií.
        """
    )

    st.write(
        "Generovanie je postavené na veľkom jazykovom modeli (LLM), pričom jednotlivé otázky a odpovede sú viazané na konkrétne časti "
        "zdrojového dokumentu (inšpirované RAG princípom). Zhlukovanie vzdelávacích objektov umožňuje odstrániť duplicity a lepšie " 
        "zachytiť štruktúru učiva. Výsledkom je prehľad učebného obsahu, ktorý môže slúžiť ako podpora pri učení alebo príprave na skúšku."
    )



if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "segments" not in st.session_state:
    st.session_state.segments = None
if "los" not in st.session_state:
    st.session_state.los = None
if "items" not in st.session_state:
    st.session_state["items"] = None
if "lo_graph_path" not in st.session_state:
    st.session_state.lo_graph_path = None
if "lo_json_path" not in st.session_state:
    st.session_state.lo_json_path = None
if "lo_txt_path" not in st.session_state:
    st.session_state.lo_txt_path = None
if "questions_json_path" not in st.session_state:
    st.session_state.questions_json_path = None
if "questions_txt_path" not in st.session_state:
    st.session_state.questions_txt_path = None

with tab_dokument:
    st.write("Nahrajte PDF dokument, ktorý bude slúžiť ako vstupný učebný materiál.")
    uploaded_file = st.file_uploader("Miesto pre nahratie PDF", type=["pdf"])

    if uploaded_file is not None:
        st.success(f"Nahraný súbor: {uploaded_file.name}")

        if st.button("Spustiť extrakciu textu", use_container_width=False):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                f.write(uploaded_file.getbuffer())
                st.session_state.pdf_path = f.name

            t0 = time.perf_counter()
            with st.spinner("Spracovávam dokument..."):
                st.session_state.segments = pdf_to_text(st.session_state.pdf_path)
            extraction_time = time.perf_counter() - t0

            st.success(f"Extrakcia dokončená. Čas extrakcie textu: {extraction_time:.2f} s")

            t1 = time.perf_counter()
            with st.spinner("Generujem vzdelávacie objekty..."):
                st.session_state.los = generate_lo_pipeline(
                    st.session_state.segments,
                    batch_size=20,
                    verbose=False
                )
            lo_time = time.perf_counter() - t1

            if st.session_state.los:
                st.success(
                    f"Vzdelávacie objekty vygenerované: {len(st.session_state.los)}. "
                    f"Čas generovania: {lo_time:.2f} s"
                )
                lo_json_path, lo_txt_path = save_learning_objects_json_txt(st.session_state.los, OUTPUT_DIR)
                st.session_state.lo_json_path = lo_json_path
                st.session_state.lo_txt_path = lo_txt_path
            else:
                st.warning("Nepodarilo sa vygenerovať žiadne vzdelávacie objekty.")

            if st.session_state.los:
                t2 = time.perf_counter()
                with st.spinner("Generujem otázky a úlohy..."):
                    st.session_state["items"] = generate_all_items(
                        st.session_state.los,
                        st.session_state.segments,
                        batch_size=10,
                        verbose=False
                    )
                items_time = time.perf_counter() - t2

                if st.session_state["items"]:
                    st.success(
                        f"Otázky a úlohy vygenerované: {len(st.session_state['items'])}. "
                        f"Čas generovania: {items_time:.2f} s"
                    )
                    q_json_path, q_txt_path = save_questions_json_txt(st.session_state["items"], OUTPUT_DIR)
                    st.session_state.questions_json_path = q_json_path
                    st.session_state.questions_txt_path = q_txt_path
                else:
                    st.warning("Nepodarilo sa vygenerovať žiadne otázky ani úlohy.")

                with st.spinner("Vykresľujem vizualizáciu LO..."):
                    st.session_state.lo_graph_path = save_lo_graph_png(
                        st.session_state.los,
                        OUTPUT_DIR,
                        layer_gap=10.0,
                        node_gap=6.0
                    )

                st.success(f"Vizualizácia vzdelávacích objektov vykreslená.")

            


with tab_lo:
    if not st.session_state.get("segments"):
        st.warning("Najprv nahrajte PDF a spustite extrakciu textu v karte „Načítanie dokumentu“.")
    elif not st.session_state.get("los"):
        st.info("Vzdelávacie objekty zatiaľ nie sú vygenerované.")
    else:
        st.write(f"Počet LO: {len(st.session_state.los)}")
        for obj in st.session_state.los:
            st.markdown("---")
            st.write(f"ID: {obj.get('id')}")
            st.write(f"Vzdelávací objekt: {obj.get('vzdelávací_objekt')}")
            st.write(f"Bloom level: {obj.get('bloom_level')}")
            acts = obj.get("odporúčané_aktivity")
            st.write(f"Odporúčané aktivity: {acts}")
            zad = obj.get("odporúčané_zadania")
            st.write(f"Odporúčané zadania: {zad}")
            pre = obj.get("prerekvizity")
            st.write(f"Prerekvizity: {pre}")
            cit = obj.get("citovane_zdroje")
            st.write(f"Citované zdroje: {cit}")


with tab_otazky:
    if not st.session_state.get("segments"):
        st.warning("Najprv nahrajte PDF a spustite extrakciu textu v karte „Načítanie dokumentu“ a počkajte na vygenerovanie vzdelávacích objektov.")
    elif not st.session_state.get("items"):
        st.info("Otázky a úlohy zatiaľ nie sú vygenerované.")
    else:
        st.write(f"Počet položiek: {len(st.session_state['items'])}")
        for it in st.session_state["items"]:
            st.markdown("---")
            st.write(f"ID: {it.get('id')}")
            st.write(f"LO ID: {it.get('lo_id')}")
            st.write(f"Typ: {it.get('typ')}")
            st.write(f"Otázka/úloha: {it.get('otazka')}")
            st.write(f"Odpoveď: {it.get('odpoved')}")
            st.write(f"Nápoveda: {it.get('napoveda')}")
            st.write(f"Citované zdroje: {it.get('citovane_zdroje')}")

with tab_viz:
  
    if not st.session_state.get("lo_graph_path"):
        st.info("Vizualizácia zatiaľ nie je pripravená.")
    else:
        st.image(st.session_state.lo_graph_path, caption="Vzdelávacie objekty a prerekvizity")
    
    
