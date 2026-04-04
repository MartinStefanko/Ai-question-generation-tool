import streamlit as st
import tempfile
import os
import time
from text_extraction import pdf_to_text
from lo_pipeline import generate_lo_pipeline
from item_pipeline import generate_all_items
from outputs import ( save_extracted_material_txt,
    save_learning_objects_json_txt,
    save_learning_objects_pdf,
    save_questions_json_txt,
    save_questions_pdf,
    save_lo_graph_png,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "vystup")

LO_GENERATION_MODEL = "gemini-2.5-flash"
LO_PREREQ_MODEL = "gemini-2.5-flash" 
ITEM_GENERATION_MODEL = "gemini-2.5-flash"
ITEM_EVALUATION_MODEL = "gemini-2.5-flash-lite"
ITEM_EVALUATION_BATCH_SIZE = 20

def to_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def render_list(label, value):
    values = to_list(value)
    if values:
        st.markdown(f"**{label}:**")
        for item in values:
            st.markdown(f"- {item}")
    else:
        st.markdown(f"**{label}:** -")


def _read_download_bytes(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def render_download_button(label, path, mime, key):
    data = _read_download_bytes(path)
    if data is None:
        return
    st.download_button(
        label=label,
        data=data,
        file_name=os.path.basename(path),
        mime=mime,
        key=key,
    )

st.set_page_config(layout="centered")

st.title("Nástroj na automatické generovanie otázok a úloh")

tab_domov, tab_dokument, tab_lo, tab_otazky, tab_viz = st.tabs(
    ["Domov", "Načítanie dokumentu", "Vzdelávacie objekty","Otázky a úlohy","Vizualizácia"]
)

with tab_domov:
    st.write(
        "Tento nástroj slúži na spracovanie učebného PDF dokumentu a automatické vytvorenie vzdelávacích objektov, "
        "otázok a úloh viazaných na konkrétne časti zdrojového materiálu. Výstupom sú štruktúrované vzdelávacie objekty "
        "s citovanými zdrojmi, prerekvizitami, otázkami alebo úlohami, odpoveďami, nápovedami a vizualizáciou ich vzťahov."
    )

    st.subheader("Postup spracovania dokumentu")
    st.markdown(
        """
        1. **Načítanie dokumentu** – používateľ nahrá PDF dokument, ktorý slúži ako vstupný učebný materiál.  
        2. **Extrakcia textu** – z dokumentu sa získa text po jednotlivých stranách a uloží sa ako základ pre ďalšie spracovanie.  
        3. **Generovanie vzdelávacích objektov** – z extrahovaného textu sa vytvoria vzdelávacie objekty s názvom, Bloomovou úrovňou, odporúčanými aktivitami, odporúčanými zadaniami a citovanými zdrojmi.  
        4. **Zlúčenie a doplnenie LO** – podobné vzdelávacie objekty sa zoskupia, zoradia a doplnia sa medzi nimi prerekvizity.  
        5. **Validácia a evaluácia LO** – kontroluje sa formálna správnosť výstupu, pokrytie tém, relevantnosť voči dokumentu a vernosť voči zdrojovému textu.  
        6. **Generovanie otázok a úloh** – pre každý prijatý vzdelávací objekt sa vytvárajú teoretické otázky alebo praktické úlohy spolu s odpoveďou, nápovedou a citovanými zdrojmi.  
        7. **Evaluácia otázok a úloh** – položky sa filtrujú podľa kvality, zodpovedateľnosti, vernosti voči zdrojovému textu a pri Python úlohách aj podľa spustiteľnosti a korektnosti testov.  
        8. **Vizualizácia výsledkov** – vzdelávacie objekty a ich väzby sú zobrazené v grafe.
        """
    )

    st.write(
        "Generovanie nástroja je postavené na veľkom jazykovom modeli, pričom každý vzdelávací objekt aj každá vygenerovaná položka sú "
        "naviazané na citované strany dokumentu. Nástroj priebežne kontroluje a filtruje vygenerovaný obsah, "
        "aby výsledok čo najlepšie zodpovedal reálnemu obsahu nahraného materiálu. Výstupom je prehľad učebného obsahu, ktorý môže slúžiť ako podpora pri učení alebo príprave na skúšku."
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
if "lo_pdf_path" not in st.session_state:
    st.session_state.lo_pdf_path = None
if "questions_json_path" not in st.session_state:
    st.session_state.questions_json_path = None
if "questions_txt_path" not in st.session_state:
    st.session_state.questions_txt_path = None
if "questions_pdf_path" not in st.session_state:
    st.session_state.questions_pdf_path = None
if "lo_timing_report" not in st.session_state:
    st.session_state.lo_timing_report = None
if "item_timing_report" not in st.session_state:
    st.session_state.item_timing_report = None

with tab_dokument:
    st.write("Nahrajte PDF dokument, ktorý bude slúžiť ako vstupný učebný materiál.")
    uploaded_file = st.file_uploader("Miesto pre nahratie PDF", type=["pdf"])

    if uploaded_file is not None:
        st.success(f"Nahraný súbor: {uploaded_file.name}")

        if st.button("Spustiť extrakciu textu", use_container_width=False):
            st.session_state.los = None
            st.session_state["items"] = None
            st.session_state.lo_graph_path = None
            st.session_state.lo_json_path = None
            st.session_state.lo_txt_path = None
            st.session_state.lo_pdf_path = None
            st.session_state.questions_json_path = None
            st.session_state.questions_txt_path = None
            st.session_state.questions_pdf_path = None
            st.session_state.lo_timing_report = None
            st.session_state.item_timing_report = None

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                f.write(uploaded_file.getbuffer())
                st.session_state.pdf_path = f.name

            t0 = time.perf_counter()
            with st.spinner("Spracovávam dokument..."):
                st.session_state.segments = pdf_to_text(st.session_state.pdf_path)
            extraction_time = time.perf_counter() - t0
            save_extracted_material_txt(st.session_state.segments, OUTPUT_DIR)

            st.success(f"Extrakcia dokončená. Čas extrakcie textu: {extraction_time:.2f} s")

            with st.spinner("Generujem vzdelávacie objekty..."):
                los, lo_timing_report = generate_lo_pipeline(
                    st.session_state.segments,
                    batch_size=10,
                    generation_model=LO_GENERATION_MODEL,
                    prerequisites_model=LO_PREREQ_MODEL,
                    output_dir=OUTPUT_DIR,
                    verbose=True,
                    return_metrics=True,
                )
                st.session_state.los = los
                st.session_state.lo_timing_report = lo_timing_report

            lo_json_path, lo_txt_path = save_learning_objects_json_txt(
                st.session_state.los,
                OUTPUT_DIR,
                all_los=lo_timing_report.get("all_los"),
            )
            lo_pdf_path = save_learning_objects_pdf(
                st.session_state.los,
                OUTPUT_DIR,
            )
            st.session_state.lo_json_path = lo_json_path
            st.session_state.lo_txt_path = lo_txt_path
            st.session_state.lo_pdf_path = lo_pdf_path

            if st.session_state.los:
                st.success(
                    f"Vzdelávacie objekty vygenerované: {len(st.session_state.los)}. "
                    f"Čas generovania: {lo_timing_report.get('generation_seconds', 0.0):.2f} s. "
                    f"Čas evaluácie: {lo_timing_report.get('evaluation_seconds', 0.0):.2f} s"
                )
            else:
                st.warning("Žiadny vzdelávací objekt neprešiel filtrom.")

            if st.session_state.los:
                with st.spinner("Generujem otázky a úlohy..."):
                    items, item_timing_report = generate_all_items(
                        st.session_state.los,
                        st.session_state.segments,
                        batch_size=10,
                        evaluation_batch_size=ITEM_EVALUATION_BATCH_SIZE,
                        generation_model=ITEM_GENERATION_MODEL,
                        evaluation_model=ITEM_EVALUATION_MODEL,
                        output_dir=OUTPUT_DIR,
                        verbose=True,
                        return_metrics=True,
                    )
                    st.session_state["items"] = items
                    st.session_state.item_timing_report = item_timing_report

                q_json_path, q_txt_path = save_questions_json_txt(
                    st.session_state["items"],
                    OUTPUT_DIR,
                    all_items=item_timing_report.get("all_items"),
                )
                q_pdf_path = save_questions_pdf(
                    st.session_state["items"],
                    OUTPUT_DIR,
                )
                st.session_state.questions_json_path = q_json_path
                st.session_state.questions_txt_path = q_txt_path
                st.session_state.questions_pdf_path = q_pdf_path

                if st.session_state["items"]:
                    st.success(
                        f"Otázky a úlohy vygenerované: {len(st.session_state['items'])}. "
                        f"Čas generovania: {item_timing_report.get('generation_seconds', 0.0):.2f} s. "
                        f"Čas evaluácie: {item_timing_report.get('evaluation_seconds', 0.0):.2f} s"
                    )
                else:
                    st.warning("Žiadna otázka ani úloha neprešla filtrom.")

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
        st.subheader("Vzdelávacie objekty")
        st.metric("Počet LO", len(st.session_state.los))
        render_download_button(
            "Stiahnuť LO v PDF",
            st.session_state.get("lo_pdf_path"),
            "application/pdf",
            "download_lo_pdf",
        )
        if st.session_state.get("lo_pdf_path") is None:
            st.caption("PDF export bude dostupný po nainštalovaní knižnice `reportlab`.")
        for obj in st.session_state.los:
            lo_id = obj.get("id", "-")
            lo_name = obj.get("vzdelávací_objekt", "Bez názvu")
            bloom = obj.get("bloom_level", "-")

            with st.expander(f"LO {lo_id}: {lo_name}", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**ID:** {lo_id}")
                c2.markdown(f"**Bloom:** {bloom}")
                c3.markdown(f"**Prerekvizity:** {', '.join(to_list(obj.get('prerekvizity'))) or '-'}")

                render_list("Odporúčané aktivity", obj.get("odporúčané_aktivity"))
                render_list("Odporúčané zadania", obj.get("odporúčané_zadania"))
                st.markdown(f"**Citované zdroje:** {', '.join(to_list(obj.get('citovane_zdroje'))) or '-'}")


with tab_otazky:
    if not st.session_state.get("segments"):
        st.warning("Najprv nahrajte PDF a spustite extrakciu textu v karte „Načítanie dokumentu“ a počkajte na vygenerovanie vzdelávacích objektov.")
    elif not st.session_state.get("items"):
        st.info("Otázky a úlohy zatiaľ nie sú vygenerované.")
    else:
        st.subheader("Otázky a úlohy")
        st.metric("Počet položiek", len(st.session_state["items"]))
        render_download_button(
            "Stiahnuť otázky v PDF",
            st.session_state.get("questions_pdf_path"),
            "application/pdf",
            "download_questions_pdf",
        )
        if st.session_state.get("questions_pdf_path") is None:
            st.caption("PDF export bude dostupný po nainštalovaní knižnice `reportlab`.")
        for it in st.session_state["items"]:
            item_id = it.get("id", "-")
            lo_id = it.get("lo_id", "-")
            typ = it.get("typ", "-")
            otazka = it.get("otazka", "-")
            title = f"{otazka}"

            with st.expander(title, expanded=False):
                #st.markdown(f"**Otázka / úloha:**\n\n{it.get('otazka', '-')}")
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Typ:** {typ}")
                c2.markdown(f"**Položka ID:** {item_id}")
                c3.markdown(f"**LO ID:** {lo_id}")
                hodnotenie = it.get("hodnotenie", {})
                if isinstance(hodnotenie, dict):
                    skore = hodnotenie.get("skore")
                    zdovodnenie = hodnotenie.get("zdovodnenie", "")
                else:
                    skore = it.get("hodnotenie_skore")
                    zdovodnenie = it.get("hodnotenie_zdovodnenie", "")
                st.markdown(f"**Hodnotenie:** {skore if skore is not None else '-'}")
                
                with st.expander("Zobraziť odpoveď", expanded=False):
                    render_list("Odpoveď", it.get("odpoved"))
                with st.expander("Zobraziť nápovedu", expanded=False):
                    render_list("Nápoveda", it.get("napoveda"))
                render_list("Zdôvodnenie hodnotenia", zdovodnenie)
                st.markdown(f"**Citované zdroje:** {', '.join(to_list(it.get('citovane_zdroje'))) or '-'}")

with tab_viz:
  
    if not st.session_state.get("lo_graph_path"):
        st.info("Vizualizácia zatiaľ nie je pripravená.")
    else:
        st.image(st.session_state.lo_graph_path, caption="Vzdelávacie objekty a prerekvizity")
    
    
