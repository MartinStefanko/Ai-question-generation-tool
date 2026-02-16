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
            vsetky_lo.append(obj)

    end_total = time.perf_counter()
    if verbose:
        print(f"Generovanie LO dokončené. Celkový počet LO: {len(vsetky_lo)}")
        print(f"Celkový čas generovania: {end_total - start_total:.2f} s")

    return vsetky_lo
