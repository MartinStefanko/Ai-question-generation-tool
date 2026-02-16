import time

from context_builder import build_page_map, build_context_for_lo
from json_load import safe_load_json
from llm_client import generate_with_retry


def generate_items_for_batch(los_batch, page_map, model="gemini-2.5-flash-lite", client=None, verbose=True):
    lo_blocks = []
    for lo in los_batch:
        lo_id = lo.get("id")
        context = build_context_for_lo(lo, page_map)
        if not context.strip():
            if verbose:
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
Si skusený učiteľ.
Na zaklade viacerých vzdelávacích cieľov (LO) a ich textového kontextu z učebného materiálu
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
- "napoveda": krátka pomocná stopa pre študenta, NESMIE obsahovať finálnu odpoveď ani kľúčový výsledok. Napoveda má len nasmerovať, čo si má študent v texte pozrieť alebo aký postup zvoliť.
- "citovane_zdroje": zoznam čísel strán ako textových reťazcov, napr. ["12","13"].

Výstup:
LEN JSON pole bez akéhokoľvek ďalšieho textu.
"""

    try:
        response = generate_with_retry(prompt, client=client, model=model, verbose=verbose)
        parsed = safe_load_json(response.text if response else "")
    except Exception as e:
        ids = [b["id"] for b in lo_blocks]
        if verbose:
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


def generate_all_items(los, segmenty, batch_size=10, model="gemini-2.5-flash-lite", client=None, verbose=True, max_batch_attempts=3):
    page_map = build_page_map(segmenty)
    all_items = []
    next_item_id = 1
    total_los = len(los)

    if verbose:
        print(f"Začínam generovanie položiek pre {total_los} LO v batchoch po {batch_size}.")
    start_full = time.perf_counter()
    batch_num = 1
    for start in range(0, total_los, batch_size):
        batch = los[start:start + batch_size]
        lo_ids = [lo.get("id") for lo in batch]
        if verbose:
            print(f"\nBatch {batch_num}: LO id {lo_ids}")
        start_batch = time.perf_counter()

        raw_items = []
        for attempt in range(1, max_batch_attempts + 1):
            raw_items = generate_items_for_batch(batch, page_map, model=model, client=client, verbose=verbose)
            if raw_items:
                break
            if verbose and max_batch_attempts > 1:
                print(f"Batch {batch_num}: prazdny vystup, opakujem ({attempt}/{max_batch_attempts})")

        if not raw_items:
            if verbose:
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

            if verbose:
                print(f"Batch {batch_num}: vytvorených položiek: {len(raw_items)}")

        end_batch = time.perf_counter()
        if verbose:
            print(f"Batch {batch_num} hotový za {end_batch - start_batch:.2f} s")
        batch_num += 1
    end_full = time.perf_counter()
    if verbose:
        print(f"\nGenerovanie položiek pre všetky LO dokončené. Celkový počet položiek: {len(all_items)}")
        print(f"Celkový čas generovania položiek: {end_full - start_full:.2f} s")
    return all_items
