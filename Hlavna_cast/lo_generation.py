import time

from json_load import safe_load_json
from llm_client import generate_with_retry


def generate_learning_objects(segmenty, batch_size=20, model="gemini-2.5-flash-lite", client=None, verbose=True):
    vsetky_lo = []
    next_id = 1

    if verbose:
        print("Generujem vzdelávacie ciele.")

    start_total = time.perf_counter()
    batch_num = 1
    for start in range(0, len(segmenty), batch_size):
        batch = segmenty[start:start + batch_size]
        parts = []
        start_batch = time.perf_counter()
        for seg in batch:
            parts.append(f"{seg.get('text', '')}")
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

        response = generate_with_retry(prompt, client=client, model=model, verbose=verbose)
        response_text = response.text if response else ""

        try:
            parsed_seg = safe_load_json(response_text)
        except Exception as e:
            if verbose:
                print("Nepodarilo sa parsovať JSON odpoveď:", e)
            continue

        if not parsed_seg:
            continue

        if isinstance(parsed_seg, dict):
            parsed_seg = [parsed_seg]

        end_batch = time.perf_counter()
        if verbose:
            print(f"Čas generovania batchu {batch_num}: {end_batch - start_batch:.2f} s")

        batch_num += 1
        for obj in parsed_seg:
            obj["id"] = next_id
            next_id += 1

        missing = []
        for obj in parsed_seg:
            sources = obj.get("citovane_zdroje")
            if sources is None:
                missing.append(obj)
                continue
            if isinstance(sources, (list, tuple, set)):
                if not any(str(v).strip() for v in sources):
                    missing.append(obj)
            elif not str(sources).strip():
                missing.append(obj)

        if missing:
            parts_with_pages = []
            for seg in batch:
                page = seg.get("page")
                text = seg.get("text", "")
                parts_with_pages.append(f"[strana {page}]\n{text}")
            batch_text_with_pages = "\n\n".join(parts_with_pages)

            lo_summary = []
            for obj in missing:
                lo_summary.append(
                    f"id: {obj.get('id')}, "
                    f"vzdelavaci_objekt: {obj.get('vzdelávací_objekt', '')}, "
                    f"bloom_level: {obj.get('bloom_level', '')}, "
                    f"odporucane_zadania: {obj.get('odporúčané_zadania', '')}"
                )
            lo_summary_text = "\n".join(lo_summary)

            prompt_missing = f"""
                Si ucitel. Doplň pole citovane_zdroje pre nasledujuce LO, kde je prazdne. 
                Pouzi iba strany, ktore su viditelne v texte so znacenkou [strana X].
                Ak si nie si isty, vrat aspon najrelevantnejsiu jednu stranu. (štruktúra citovane_zdroje: 1, 2, 3 ...).

                Vstupne LO:
                {lo_summary_text}

                Text materialu:
                \"\"\"{batch_text_with_pages}\"\"\"

                Vrat LEN validny JSON ako pole objektov:
                [
                    {{"id": 1, "citovane_zdroje": [12, 13]}}
                ]
                """
            try:
                response_missing = generate_with_retry(prompt_missing, client=client, model=model, verbose=verbose)
                parsed_missing = safe_load_json(response_missing.text if response_missing else "")
                if isinstance(parsed_missing, dict):
                    parsed_missing = [parsed_missing]
            except Exception as e:
                parsed_missing = []
                if verbose:
                    print(f"Doplnenie citovanych zdrojov zlyhalo: {e}")

            src_map = {}
            if isinstance(parsed_missing, list):
                for row in parsed_missing:
                    if not isinstance(row, dict):
                        continue
                    row_id = row.get("id")
                    if row_id is None:
                        continue

                    raw_sources = row.get("citovane_zdroje")
                    if isinstance(raw_sources, (list, tuple, set)):
                        normalized = [str(v).strip() for v in raw_sources if str(v).strip()]
                    elif raw_sources is None:
                        normalized = []
                    else:
                        text = str(raw_sources).strip()
                        if not text:
                            normalized = []
                        elif "," in text:
                            normalized = [p.strip() for p in text.split(",") if p.strip()]
                        else:
                            normalized = [text]

                    if normalized:
                        src_map[row_id] = normalized

            for obj in parsed_seg:
                sources = obj.get("citovane_zdroje")
                has_sources = False
                if isinstance(sources, (list, tuple, set)):
                    has_sources = any(str(v).strip() for v in sources)
                elif sources is not None:
                    has_sources = bool(str(sources).strip())

                if not has_sources:
                    filled = src_map.get(obj.get("id"))
                    if filled:
                        obj["citovane_zdroje"] = filled

        for obj in parsed_seg:
            vsetky_lo.append(obj)

    end_total = time.perf_counter()
    if verbose:
        print(f"Generovanie LO dokončené. Celkový počet LO: {len(vsetky_lo)}")
        print(f"Celkový čas generovania: {end_total - start_total:.2f} s")

    return vsetky_lo
