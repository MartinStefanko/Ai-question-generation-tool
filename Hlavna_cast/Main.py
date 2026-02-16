import os
from google import genai
from dotenv import load_dotenv
import json
import re
import time

from lo_clustering import cluster_by_core
from visualization import visualize_to_png
from text_extraction import pdf_to_text

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

base_dir = os.path.dirname(os.path.abspath(__file__))

materials_dir = os.path.join(base_dir, "ucebny_material")   
output_dir = os.path.join(base_dir, "vystup")               
os.makedirs(output_dir, exist_ok=True)                      

pdf_name = "aza.pdf"                                    
pdf_path = os.path.join(materials_dir, pdf_name)           

if not os.path.exists(pdf_path):                            
    raise FileNotFoundError(f"PDF súbor sa nenašiel: {pdf_path}")  

print(f"Konvertujem PDF na text: {pdf_name}")       


segmenty = pdf_to_text(pdf_path)

material_path = os.path.join(output_dir, "material.txt")   
with open(material_path, "w", encoding="utf-8") as f:
    for seg in segmenty:
        f.write(seg["text"])
        f.write("\n\n")

print("Konvertovanie PDF na text dokončené.")

def safe_load_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'(\[.*\]|\{.*\})', text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    raise

vsetky_lo = []
next_id = 1  

BATCH_SIZE = 20


def generate_with_retry(prompt, retries=5, delay=3.0):
    for attempt in range(1, retries + 1):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
        except Exception as e:
            if attempt == retries:
                raise
            print(f"LLM zlyhalo (pokus {attempt}/{retries}), čakám {delay}s a opakujem. Chyba: {e}")
            time.sleep(delay)

print("Generujem vzdelávacie ciele.")

start_total = time.perf_counter()
numb = 1
for start in range(0, len(segmenty), BATCH_SIZE):
    batch = segmenty[start:start + BATCH_SIZE]
    parts = []
    start_batch = time.perf_counter()
    for seg in batch:
        parts.append(f"{seg['text']}")
    combined_text = "\n\n".join(parts)
    
    prompt = f"""
Si učiteľ. Na základe nasledujúceho materiálu extrahuj merateľné vzdelávacie ciele.

Output only valid JSON: an array of objects with the following fields:
id (jedinečný identifikátor 1, 2, 3...),
vzdelávací_objekt (hlavný bod/cieľ, najviac dve slová),
bloom_level (jedno z: Zapamätať si, Pochopiť, Aplikovať, Analyzovať, Hodnotiť, Vytvoriť),
odporúčané_aktivity (krátky zoznam),
odporúčané_zadania - v jednej úlohe maximálne jedno aktívne sloveso a slovesá nech sú v imperatíve (krátky popis),
citovane_zdroje - každý vzdelávací objekt MUSÍ mať citované strany. Toto pole nesmie byť prázdne. (štruktúra citovane_zdroje: 1, 2, 3 ...).

V prípade, že identifikuješ časť materiálu ktorá má štruktúru začiatku dokumentu (napríklad obsah dokumentu, úvod atď.) 
tak túto časť ignoruj a nevytváraj pre ňu žiadne vzdelávacie objekty.

Vyučovací materiál:
\"\"\"{combined_text}\"\"\" 
""" 
    
    response = generate_with_retry(prompt)
    response_text = response.text

    try:
        parsed_seg = safe_load_json(response_text)
    except Exception as e:
        print("Nepodarilo sa parsovať JSON odpoveď:", e)
        continue

    if not parsed_seg:
        continue

    if isinstance(parsed_seg, dict):
        parsed_seg = [parsed_seg]
    end_batch = time.perf_counter()

    print(f"Čas generovania batchu {numb}: {end_batch - start_batch:.2f} s")
    numb += 1
    for obj in parsed_seg:
        obj["id"] = next_id
        next_id += 1
        vsetky_lo.append(obj)


vsetky_lo = cluster_by_core(vsetky_lo) 
for i, obj in enumerate(vsetky_lo, start=1):
    obj["id"] = i 


def infer_prerequisites(lo_list):
    if not lo_list:
        return lo_list

    summary_lines = []
    for obj in lo_list:
        acts = obj.get("odporúčané_aktivity", [])
        if not isinstance(acts, (list, tuple)):
            acts = [acts]
        zadania = obj.get("odporúčané_zadania", [])
        if not isinstance(zadania, (list, tuple)):
            zadania = [zadania]
        summary_lines.append(
            f"id: {obj.get('id')}, vzdelávací_objekt: {obj.get('vzdelávací_objekt')}, "
            f"bloom_level: {obj.get('bloom_level')}, odporúčané_aktivity: {acts}, odporúčané_zadania: {zadania}"
        )
    summary_text = "\n".join(summary_lines)

    prompt = f"""
Si učiteľ. Pre nasledujúci zoznam vzdelávacích cieľov navrhni doplň všetky prerekvizity medzi nimi.
Vráť JSON: pole objektov {{"id": číslo, "prerekvizity": [zoznam id, ktoré musia byť predtým]}}.
Nedávaj cykly.

Zoznam cieľov:
{summary_text}
"""
    try:
        response = generate_with_retry(prompt)
        parsed = safe_load_json(response.text)
        if isinstance(parsed, dict):
            parsed = [parsed]
    except Exception as e:
        print(f"Prerekvizity zlyhali: {e}")
        return lo_list

    mapping = {item.get("id"): item.get("prerekvizity", []) for item in parsed if isinstance(item, dict)}

    for obj in lo_list:
        pid = obj.get("id")
        if pid in mapping:
            obj["prerekvizity"] = mapping[pid]
        else:
            obj.setdefault("prerekvizity", [])
    print("Prerekvizity boli doplnené.")
    return lo_list

vsetky_lo = infer_prerequisites(vsetky_lo)

print(f"Generovanie LO dokončené. Celkový počet LO: {len(vsetky_lo)}")
end_total = time.perf_counter()
print(f"Celkový čas generovania: {end_total - start_total:.2f} s")

parsed = vsetky_lo if vsetky_lo else None

if parsed is not None:
    out_path = os.path.join(output_dir, "learning_objects.json")  
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    lines = []
    for obj in parsed:
        lines.append(f"id: {obj.get('id')}")
        lines.append(f"vzdelávací_objekt: {obj.get('vzdelávací_objekt')}")
        lines.append(f"bloom_level: {obj.get('bloom_level')}")
        acts = obj.get("odporúčané_aktivity")
        if isinstance(acts, list):
            acts_str = ", ".join(str(a) for a in acts)
        else:
            acts_str = "" if acts is None else str(acts)
        lines.append(f"odporúčané_aktivity: {acts_str}")
        zad = obj.get("odporúčané_zadania")
        lines.append(f"odporúčané_zadania: {'' if zad is None else str(zad)}")
        prereq = obj.get("prerekvizity")
        if isinstance(prereq, list):
            prereq_str = ", ".join(str(p) for p in prereq)
        else:
            prereq_str = "" if prereq is None else str(prereq)
        lines.append(f"prerekvizity: {prereq_str}")

        cit = obj.get("citovane_zdroje", [])
        if isinstance(cit, list):
            cit_clean = [str(c).strip() for c in cit if str(c).strip()]
            cit_str = ", ".join(cit_clean)
        else:
            cit_str = str(cit).strip()
        lines.append(f"citovane_zdroje: {cit_str}")

        lines.append("-" * 30)

    txt_path = os.path.join(output_dir, "learning_objects.txt")
    with open(txt_path, "w", encoding="utf-8") as tf:
        tf.write("\n".join(lines))

    print(f"Textový výstup uložený do {txt_path}")

if parsed:
    png_path = os.path.join(output_dir, "learning_objects_graph.png") 
    visualize_to_png(parsed, png_path, layer_gap=10.0, node_gap=6.0)
    print(f"PNG graf uložený do: {png_path}")



def build_page_map(segmenty):
    page_map = {}
    for seg in segmenty:
        page = seg.get("page")
        text = seg.get("text", "")
        if page is not None:
            page_map[page] = text
    return page_map


def parse_pages(citovane_zdroje):
    pages = set()

    if isinstance(citovane_zdroje, list):
        for it in citovane_zdroje:
            if isinstance(it, int):
                pages.add(it)
            elif isinstance(it, str):
                for token in re.split(r"[,\s/]+", it):
                    token = token.strip()
                    if token.isdigit():
                        pages.add(int(token))
    elif isinstance(citovane_zdroje, (int, float)):
        pages.add(int(citovane_zdroje))
    elif isinstance(citovane_zdroje, str):
        for token in re.split(r"[,\s/]+", citovane_zdroje):
            token = token.strip()
            if token.isdigit():
                pages.add(int(token))

    return sorted(pages)


def build_context_for_lo(lo, page_map, max_chars=8000):
    cit = lo.get("citovane_zdroje", [])
    pages = parse_pages(cit)
    if not pages:
        return ""

    texts = []
    total_len = 0
    for p in pages:
        txt = page_map.get(p, "")
        if not txt:
            continue
        if total_len + len(txt) > max_chars:
            remaining = max_chars - total_len
            if remaining > 200:
                texts.append(txt[:remaining])
                total_len += remaining
            break
        else:
            texts.append(txt)
            total_len += len(txt)

    return "\n\n".join(texts)


def generate_items_for_batch(los_batch, page_map):

    lo_blocks = []
    for lo in los_batch:
        lo_id = lo.get("id")
        context = build_context_for_lo(lo, page_map)
        if not context.strip():
            print(f"  LO {lo_id}: bez kontextu, preskakujem v tomto batche.")
            continue
        lo_blocks.append({
            "id": lo_id,
            "name": lo.get("vzdelávací_objekt", ""),
            "bloom": lo.get("bloom_level", ""),
            "context": context,
        })

    if not lo_blocks:
        return []

    parts = []
    for i, block in enumerate(lo_blocks, start=1):
        parts.append(
            f"LO {i}:\n"
            f"- lo_id: {block['id']}\n"
            f"- nazov: {block['name']}\n"
            f"- bloom_level: {block['bloom']}\n"
            f"- text:\n\"\"\"{block['context']}\"\"\""
        )
    los_text = "\n\n".join(parts)

    prompt = f"""
Si skúsený učiteľ.
Na základe viacerých vzdelávacích cieľov (LO) a ich textového kontextu z učebného materiálu
vygeneruj vzdelávacie položky (otázky/úlohy) pre každý LO.

POŽIADAVKY:
- Pre každé LO generuj len položky, ktoré vychádzajú z jeho textu a sú tematicky zamerané na daný cieľ.
- NEvymýšľaj informácie, ktoré nie sú v texte.
- Pre každú položku vždy uveď, ku ktorému LO patrí, pomocou poľa "lo_id".
- Ak kontext neumožňuje žiadnu rozumnú položku, pre dané LO nevytváraj nič.

Zoznam LO:
{los_text}

Formát výstupu:
Vráť LEN validný JSON – pole objektov.
Každý objekt musí mať:
- "lo_id": id vzdelávacieho objektu, ku ktorému položka patrí,
- "typ": "teoreticka_otazka" alebo "prakticka_uloha",
- "otazka": zadanie otázky alebo úlohy,
- "odpoved": správna odpoveď alebo referenčné riešenie, v prípade že je to praktická úloha na programovanie uveď aj kód,
- "napoveda": krátka nápoveda pre študenta z učebného materiálu,
- "citovane_zdroje": zoznam čísel strán ako textových reťazcov, napr. ["12","13"].

Výstup:
LEN JSON pole bez akéhokoľvek ďalšieho textu.
"""

    try:
        response = generate_with_retry(prompt)
        parsed = safe_load_json(response.text)
    except Exception as e:
        ids = [b["id"] for b in lo_blocks]
        print(f"Generovanie položiek pre batch LO {ids} zlyhalo: {e}")
        return []

    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []

    items = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if "lo_id" not in item:
            continue
        items.append(item)
    return items


def generate_all_items(los, segmenty, batch_size=10):
    page_map = build_page_map(segmenty)
    all_items = []
    next_item_id = 1
    total_los = len(los)

    print(f"Začínam generovanie položiek pre {total_los} LO v batchoch po {batch_size}.")
    start_full = time.perf_counter()
    batch_num = 1
    for start in range(0, total_los, batch_size):
        batch = los[start:start + batch_size]
        lo_ids = [lo.get("id") for lo in batch]
        print(f"\nBatch {batch_num}: LO id {lo_ids}")
        start_batch = time.perf_counter()

        raw_items = generate_items_for_batch(batch, page_map)

        if not raw_items:
            print(f"Batch {batch_num}: LLM nevrátil žiadne položky.")
        else:
            for raw in raw_items:
                lo_id = raw.get("lo_id")
                record = {
                    "id": next_item_id,
                    "lo_id": lo_id,
                    "typ": raw.get("typ", ""),
                    "otazka": raw.get("otazka", ""),
                    "odpoved": raw.get("odpoved", ""),
                    "napoveda": raw.get("napoveda", ""),
                    "citovane_zdroje": raw.get("citovane_zdroje", [])
                }
                all_items.append(record)
                next_item_id += 1

            print(f"Batch {batch_num}: vytvorených položiek: {len(raw_items)}")

        end_batch = time.perf_counter()
        print(f"Batch {batch_num} hotový za {end_batch - start_batch:.2f} s")
        batch_num += 1
    end_full = time.perf_counter()
    print(f"\nGenerovanie položiek pre všetky LO dokončené. Celkový počet položiek: {len(all_items)}")
    print(f"Celkový čas generovania položiek: {end_full - start_full:.2f} s")
    return all_items


print("Generujem otázky/úlohy z LO...")
items = generate_all_items(vsetky_lo, segmenty, batch_size=10)


if items:
    items_json_path = os.path.join(output_dir, "questions.json")
    with open(items_json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Položky uložené do {items_json_path}")

    items_txt_lines = []
    for it in items:
        items_txt_lines.append(f"id: {it.get('id')}")
        items_txt_lines.append(f"lo_id: {it.get('lo_id')}")
        items_txt_lines.append(f"typ: {it.get('typ')}")
        items_txt_lines.append(f"otazka: {it.get('otazka')}")
        items_txt_lines.append(f"odpoved: {it.get('odpoved')}")
        items_txt_lines.append(f"napoveda: {it.get('napoveda')}")
        cit = it.get("citovane_zdroje", [])
        if isinstance(cit, list):
            cit_str = ", ".join(str(c).strip() for c in cit if str(c).strip())
        else:
            cit_str = str(cit).strip()
        items_txt_lines.append(f"citovane_zdroje: {cit_str}")
        items_txt_lines.append("-" * 30)

    items_txt_path = os.path.join(output_dir, "questions.txt")
    with open(items_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(items_txt_lines))
    print(f"Textový prehľad položiek uložený do {items_txt_path}")
