import json
import os

from visualization import visualize_to_png


def save_learning_objects_json_txt(los, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, "learning_objects.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(los, f, ensure_ascii=False, indent=2)

    lines = []
    for obj in los:
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

    return out_path, txt_path


def save_lo_validation_report(validation_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = validation_report.get("stats", {})
    errors = validation_report.get("errors", [])
    warnings = validation_report.get("warnings", [])

    lines = [
        f"is_valid_json: {validation_report.get('is_valid_json')}",
        f"is_valid: {validation_report.get('is_valid')}",
        f"total: {stats.get('total', 0)}",
        f"valid: {stats.get('valid', 0)}",
        f"invalid: {stats.get('invalid', 0)}",
        f"errors_count: {len(errors)}",
        f"warnings_count: {len(warnings)}",
        "",
        "ERRORS:",
    ]

    if errors:
        for error in errors:
            lines.append(f"- {error}")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("WARNINGS:")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "learning_objects_validation_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_topic_coverage_report(coverage_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = coverage_report.get("stats", {})
    topics = coverage_report.get("topics", [])

    lines = [
        f"topics_total: {stats.get('topics_total', 0)}",
        f"topics_covered: {stats.get('topics_covered', 0)}",
        f"coverage_percent: {stats.get('coverage_percent', 0.0)}",
        f"similarity_threshold: {stats.get('similarity_threshold', 0.0)}",
        "",
        "TOPICS:",
    ]

    if topics:
        for topic in topics:
            lines.append(f"- tema: {topic.get('tema', '')}")
            lines.append(f"  covered: {topic.get('covered', False)}")
            lines.append(f"  similarity: {topic.get('similarity', 0.0)}")
            lines.append(f"  best_lo_id: {topic.get('best_lo_id', '-')}")
            lines.append(f"  best_lo_name: {topic.get('best_lo_name', '')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "topic_coverage_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_document_topics_txt(topics, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    lines = []
    if topics:
        for idx, topic in enumerate(topics, start=1):
            lines.append(f"{idx}. {topic.get('tema', '')}")
    else:
        lines.append("Ziadne temy neboli identifikovane.")

    topics_txt_path = os.path.join(output_dir, "document_topics.txt")
    with open(topics_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return topics_txt_path


def save_questions_json_txt(items, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    items_json_path = os.path.join(output_dir, "questions.json")
    with open(items_json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    items_txt_lines = []
    for it in items:
        items_txt_lines.append(f"id: {it.get('id')}")
        items_txt_lines.append(f"lo_id: {it.get('lo_id')}")
        items_txt_lines.append(f"typ: {it.get('typ')}")
        items_txt_lines.append(f"otazka: {it.get('otazka')}")
        items_txt_lines.append(f"odpoved: {it.get('odpoved')}")
        items_txt_lines.append(f"napoveda: {it.get('napoveda')}")
        hodnotenie = it.get("hodnotenie", {})
        if isinstance(hodnotenie, dict):
            skore = hodnotenie.get("skore")
            zdovodnenie = hodnotenie.get("zdovodnenie", "")
        else:
            skore = it.get("hodnotenie_skore")
            zdovodnenie = it.get("hodnotenie_zdovodnenie", "")
        items_txt_lines.append(f"hodnotenie_skore: {'' if skore is None else skore}")
        items_txt_lines.append(f"hodnotenie_zdovodnenie: {zdovodnenie}")
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

    return items_json_path, items_txt_path


def save_lo_graph_png(los, output_dir, layer_gap=10.0, node_gap=6.0):
    os.makedirs(output_dir, exist_ok=True)
    png_path = os.path.join(output_dir, "learning_objects_graph.png")
    visualize_to_png(los, png_path, layer_gap=layer_gap, node_gap=node_gap)
    return png_path
