from context_builder import build_context_for_lo, build_page_map
from json_load import safe_load_json
from llm_client import generate_with_retry


FAITHFULNESS_MODEL = "gemini-2.5-flash-lite"


def analyze_lo_faithfulness(segmenty, los, client=None, model: str = FAITHFULNESS_MODEL, verbose: bool = True):
    report = {
        "stats": {
            "los_total": len(los),
            "los_evaluated": 0,
            "average_faithfulness_score": 0.0,
        },
        "items": [],
    }

    if not los:
        return report

    page_map = build_page_map(segmenty)
    scores = []

    for lo in los:
        source_text = build_context_for_lo(lo, page_map, max_chars=8000)
        item = {
            "lo_id": lo.get("id"),
            "lo_name": lo.get("vzdelávací_objekt", ""),
            "source_pages": lo.get("citovane_zdroje", []),
            "faithfulness_score": None,
            "reason": "",
        }

        if not source_text.strip():
            report["items"].append(item)
            continue

        lo_text = _lo_to_text(lo)
        evaluation = _evaluate_lo_faithfulness(
            lo_text,
            source_text,
            client=client,
            model=model,
            verbose=verbose,
        )
        if evaluation:
            item["faithfulness_score"] = evaluation.get("skore")
            item["reason"] = evaluation.get("zdovodnenie", "")
            if isinstance(item["faithfulness_score"], int):
                scores.append(item["faithfulness_score"])

        report["items"].append(item)

    report["stats"]["los_evaluated"] = len(scores)
    if scores:
        report["stats"]["average_faithfulness_score"] = round(sum(scores) / len(scores), 4)
    return report


def _evaluate_lo_faithfulness(lo_text, source_text, client=None, model: str = FAITHFULNESS_MODEL, verbose: bool = True):
    prompt = f"""
Posud faithfulness LO voci zdroju.

LO:
\"\"\"{lo_text}\"\"\"

Zdroj:
\"\"\"{source_text}\"\"\"

Skore 1-5:
1 = tvrdenia LO nie su podlozene zdrojom
5 = LO je plne podlozene zdrojom

Vrat LEN validny JSON:
{{"skore": 1, "zdovodnenie": "kratke zdovodnenie"}}
"""

    try:
        response = generate_with_retry(prompt, client=client, model=model, verbose=verbose)
        parsed = safe_load_json(response.text if response else "")
    except Exception as e:
        if verbose:
            print(f"Faithfulness hodnotenie LO zlyhalo: {e}")
        return None

    if not isinstance(parsed, dict):
        return None

    try:
        score = int(parsed.get("skore"))
    except (TypeError, ValueError):
        return None

    score = max(1, min(5, score))
    reason = str(parsed.get("zdovodnenie", "")).strip()
    return {"skore": score, "zdovodnenie": reason}


def _lo_to_text(lo):
    parts = [
        f"vzdelavaci_objekt: {lo.get('vzdelávací_objekt', '')}",
        f"bloom_level: {lo.get('bloom_level', '')}",
        f"odporucane_aktivity: {lo.get('odporúčané_aktivity', [])}",
        f"odporucane_zadania: {lo.get('odporúčané_zadania', [])}",
    ]
    return "\n".join(parts)
