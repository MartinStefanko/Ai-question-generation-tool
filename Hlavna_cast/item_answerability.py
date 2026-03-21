from context_builder import build_page_map, parse_pages
from json_load import safe_load_json
from llm_client import generate_with_retry


ANSWERABILITY_MODEL = "gemini-2.5-flash-lite"


def analyze_item_answerability(segmenty, items, client=None, model: str = ANSWERABILITY_MODEL, verbose: bool = True):
    report = {
        "stats": {
            "items_total": len(items),
            "items_evaluated": 0,
            "average_answerability_score": 0.0,
            "answerable_items": 0,
            "answerable_items_percent": 0.0,
        },
        "items": [],
    }

    if not items:
        return report

    page_map = build_page_map(segmenty)
    scores = []
    answerable_items = 0

    for item in items:
        source_text = _build_context_for_item(item, page_map)
        row = {
            "item_id": item.get("id"),
            "lo_id": item.get("lo_id"),
            "source_pages": item.get("citovane_zdroje", []),
            "answerability_score": None,
            "answerable": False,
            "reason": "",
        }

        if not source_text.strip():
            report["items"].append(row)
            continue

        question_text = _question_to_text(item)
        evaluation = _evaluate_item_answerability(
            question_text,
            source_text,
            client=client,
            model=model,
            verbose=verbose,
        )
        if evaluation:
            row["answerability_score"] = evaluation.get("skore")
            row["reason"] = evaluation.get("zdovodnenie", "")
            if isinstance(row["answerability_score"], int):
                scores.append(row["answerability_score"])
                row["answerable"] = row["answerability_score"] >= 4
                if row["answerable"]:
                    answerable_items += 1

        report["items"].append(row)

    report["stats"]["items_evaluated"] = len(scores)
    if scores:
        report["stats"]["average_answerability_score"] = round(sum(scores) / len(scores), 4)
        report["stats"]["answerable_items"] = answerable_items
        report["stats"]["answerable_items_percent"] = round((answerable_items / len(scores)) * 100, 2)
    return report


def _evaluate_item_answerability(question_text, source_text, client=None, model: str = ANSWERABILITY_MODEL, verbose: bool = True):
    prompt = f"""
Posud answerability otazky voci zdroju.

Otazka:
\"\"\"{question_text}\"\"\"

Zdroj:
\"\"\"{source_text}\"\"\"

Skore 1-5:
1 = na otazku sa zo zdroja neda spolahlivo odpovedat
5 = na otazku sa da zo zdroja jasne a jednoznacne odpovedat

Vrat LEN validny JSON:
{{"skore": 1, "zdovodnenie": "kratke zdovodnenie"}}
"""

    try:
        response = generate_with_retry(prompt, client=client, model=model, verbose=verbose)
        parsed = safe_load_json(response.text if response else "")
    except Exception as e:
        if verbose:
            print(f"Answerability hodnotenie otazky zlyhalo: {e}")
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


def _question_to_text(item):
    return f"otazka: {item.get('otazka', '')}"


def _build_context_for_item(item, page_map, max_chars=8000):
    pages = parse_pages(item.get("citovane_zdroje", []))
    if not pages:
        return ""

    texts = []
    total_len = 0
    for page in pages:
        txt = page_map.get(page, "")
        if not txt:
            continue
        if total_len + len(txt) > max_chars:
            remaining = max_chars - total_len
            if remaining > 200:
                texts.append(txt[:remaining])
            break
        texts.append(txt)
        total_len += len(txt)
    return "\n\n".join(texts)
