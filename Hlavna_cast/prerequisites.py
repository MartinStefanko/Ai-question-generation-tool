from json_load import safe_load_json
from llm_client import generate_with_retry


def infer_prerequisites(lo_list, model="gemini-2.5-flash-lite", client=None, verbose=True):
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
            f"bloom_level: {obj.get('bloom_level')}, odporucane_aktivity: {acts}, odporucane_zadania: {zadania}"
        )
    summary_text = "\n".join(summary_lines)

    prompt = f"""
Si ucitel. Pre nasledujuci zoznam vzdelavacich cielov navrhni dopln vsetky prerekvizity medzi nimi.
Vrat JSON: pole objektov {{"id": cislo, "prerekvizity": [zoznam id, ktore musia byt predtym]}}.
Nedavaj cykly.

Zoznam cielov:
{summary_text}
"""
    try:
        response = generate_with_retry(prompt, client=client, model=model, verbose=verbose)
        parsed = safe_load_json(response.text if response else "")
        if isinstance(parsed, dict):
            parsed = [parsed]
    except Exception as e:
        if verbose:
            print(f"Prerekvizity zlyhali: {e}")
        return lo_list

    mapping = {item.get("id"): item.get("prerekvizity", []) for item in parsed if isinstance(item, dict)}

    for obj in lo_list:
        pid = obj.get("id")
        if pid in mapping:
            obj["prerekvizity"] = mapping[pid]
        else:
            obj.setdefault("prerekvizity", [])
    if verbose:
        print("Prerekvizity boli doplnene.")
    return lo_list
