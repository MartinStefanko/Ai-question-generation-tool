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


def save_extracted_material_txt(segmenty, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    lines = []
    for seg in segmenty:
        page = seg.get("page", "-")
        text = seg.get("text", "")
        lines.append(f"=== STRANA {page} ===")
        lines.append(str(text))
        lines.append("")

    txt_path = os.path.join(output_dir, "extracted_material.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return txt_path


def save_processing_time_report(report, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)

    lines = [
        f"pipeline: {report.get('pipeline', '')}",
        f"generation_seconds: {report.get('generation_seconds', 0.0)}",
        f"evaluation_seconds: {report.get('evaluation_seconds', 0.0)}",
        f"total_seconds: {report.get('total_seconds', 0.0)}",
    ]

    details = report.get("details", {})
    if details:
        lines.append("")
        lines.append("DETAILS:")
        for key, value in details.items():
            lines.append(f"- {key}: {value}")

    report_txt_path = os.path.join(output_dir, filename)
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


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


def save_item_validation_report(validation_report, output_dir):
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

    report_txt_path = os.path.join(output_dir, "item_validation_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_item_relevance_to_lo_report(relevance_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = relevance_report.get("stats", {})
    items = relevance_report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"items_compared: {stats.get('items_compared', 0)}",
        f"average_similarity: {stats.get('average_similarity', 0.0)}",
        "",
        "ITEM_RELEVANCE_TO_LO:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  lo_name: {item.get('lo_name', '')}")
            lines.append(f"  has_lo: {item.get('has_lo', False)}")
            lines.append(f"  similarity: {item.get('similarity', '-')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "item_relevance_to_lo_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_item_faithfulness_report(faithfulness_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = faithfulness_report.get("stats", {})
    items = faithfulness_report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"items_evaluated: {stats.get('items_evaluated', 0)}",
        f"average_faithfulness_score: {stats.get('average_faithfulness_score', 0.0)}",
        f"faithful_items: {stats.get('faithful_items', 0)}",
        f"faithful_items_percent: {stats.get('faithful_items_percent', 0.0)}",
        "",
        "ITEM_FAITHFULNESS:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  source_pages: {item.get('source_pages', [])}")
            lines.append(f"  faithfulness_score: {item.get('faithfulness_score', '-')}")
            lines.append(f"  faithful: {item.get('faithful', False)}")
            lines.append(f"  reason: {item.get('reason', '')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "item_faithfulness_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_item_answerability_report(answerability_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = answerability_report.get("stats", {})
    items = answerability_report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"items_evaluated: {stats.get('items_evaluated', 0)}",
        f"average_answerability_score: {stats.get('average_answerability_score', 0.0)}",
        f"answerable_items: {stats.get('answerable_items', 0)}",
        f"answerable_items_percent: {stats.get('answerable_items_percent', 0.0)}",
        "",
        "ITEM_ANSWERABILITY:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  source_pages: {item.get('source_pages', [])}")
            lines.append(f"  answerability_score: {item.get('answerability_score', '-')}")
            lines.append(f"  answerable: {item.get('answerable', False)}")
            lines.append(f"  reason: {item.get('reason', '')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "item_answerability_report.txt")
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


def save_lo_relevance_to_segment_report(relevance_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = relevance_report.get("stats", {})
    items = relevance_report.get("items", [])

    lines = [
        f"los_total: {stats.get('los_total', 0)}",
        f"los_compared: {stats.get('los_compared', 0)}",
        f"average_similarity: {stats.get('average_similarity', 0.0)}",
        "",
        "LO_RELEVANCE_TO_SEGMENT:",
    ]

    if items:
        for item in items:
            lines.append(f"- lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  lo_name: {item.get('lo_name', '')}")
            lines.append(f"  has_source_text: {item.get('has_source_text', False)}")
            lines.append(f"  source_pages: {item.get('source_pages', [])}")
            lines.append(f"  similarity: {item.get('similarity', '-')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "lo_relevance_to_segment_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_lo_faithfulness_report(faithfulness_report, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    stats = faithfulness_report.get("stats", {})
    items = faithfulness_report.get("items", [])

    lines = [
        f"los_total: {stats.get('los_total', 0)}",
        f"los_evaluated: {stats.get('los_evaluated', 0)}",
        f"average_faithfulness_score: {stats.get('average_faithfulness_score', 0.0)}",
        "",
        "LO_FAITHFULNESS:",
    ]

    if items:
        for item in items:
            lines.append(f"- lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  lo_name: {item.get('lo_name', '')}")
            lines.append(f"  source_pages: {item.get('source_pages', [])}")
            lines.append(f"  faithfulness_score: {item.get('faithfulness_score', '-')}")
            lines.append(f"  reason: {item.get('reason', '')}")
            lines.append("")
    else:
        lines.append("- none")

    report_txt_path = os.path.join(output_dir, "lo_faithfulness_report.txt")
    with open(report_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return report_txt_path


def save_python_code_syntax_report(report, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    stats = report.get("stats", {})
    items = report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"python_practical_items: {stats.get('python_practical_items', 0)}",
        f"auto_testable_items: {stats.get('auto_testable_items', 0)}",
        f"tested_items: {stats.get('tested_items', 0)}",
        f"syntax_valid_items: {stats.get('syntax_valid_items', 0)}",
        f"syntax_valid_percent: {stats.get('syntax_valid_percent', 0.0)}",
        "",
        "PYTHON_CODE_SYNTAX:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  execution_mode: {item.get('execution_mode', '')}")
            lines.append(f"  syntax_valid: {item.get('syntax_valid', False)}")
            lines.append(f"  error: {item.get('error', '')}")
            lines.append("")
    else:
        lines.append("- none")

    path = os.path.join(output_dir, "python_code_syntax_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def save_python_code_runtime_report(report, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    stats = report.get("stats", {})
    items = report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"python_practical_items: {stats.get('python_practical_items', 0)}",
        f"auto_testable_items: {stats.get('auto_testable_items', 0)}",
        f"tested_items: {stats.get('tested_items', 0)}",
        f"runtime_valid_items: {stats.get('runtime_valid_items', 0)}",
        f"runtime_valid_percent: {stats.get('runtime_valid_percent', 0.0)}",
        "",
        "PYTHON_CODE_RUNTIME:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  execution_mode: {item.get('execution_mode', '')}")
            lines.append(f"  runtime_valid: {item.get('runtime_valid', False)}")
            lines.append(f"  timed_out: {item.get('timed_out', False)}")
            lines.append(f"  error: {item.get('error', '')}")
            lines.append("")
    else:
        lines.append("- none")

    path = os.path.join(output_dir, "python_code_runtime_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def save_python_code_correctness_report(report, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    stats = report.get("stats", {})
    items = report.get("items", [])

    lines = [
        f"items_total: {stats.get('items_total', 0)}",
        f"python_practical_items: {stats.get('python_practical_items', 0)}",
        f"auto_testable_items: {stats.get('auto_testable_items', 0)}",
        f"tested_items: {stats.get('tested_items', 0)}",
        f"correct_items: {stats.get('correct_items', 0)}",
        f"correct_items_percent: {stats.get('correct_items_percent', 0.0)}",
        f"test_cases_total: {stats.get('test_cases_total', 0)}",
        f"test_cases_passed: {stats.get('test_cases_passed', 0)}",
        f"test_pass_rate_percent: {stats.get('test_pass_rate_percent', 0.0)}",
        "",
        "PYTHON_CODE_CORRECTNESS:",
    ]

    if items:
        for item in items:
            lines.append(f"- item_id: {item.get('item_id', '-')}")
            lines.append(f"  lo_id: {item.get('lo_id', '-')}")
            lines.append(f"  execution_mode: {item.get('execution_mode', '')}")
            lines.append(f"  test_cases_total: {item.get('test_cases_total', 0)}")
            lines.append(f"  test_cases_passed: {item.get('test_cases_passed', 0)}")
            lines.append(f"  at_least_one_test_passed: {item.get('at_least_one_test_passed', False)}")
            lines.append(f"  error: {item.get('error', '')}")
            lines.append("")
    else:
        lines.append("- none")

    path = os.path.join(output_dir, "python_code_correctness_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


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
        items_txt_lines.append(f"jazyk: {it.get('jazyk', '')}")
        items_txt_lines.append(f"execution_mode: {it.get('execution_mode', '')}")
        items_txt_lines.append(f"function_name: {it.get('function_name', '')}")
        items_txt_lines.append(f"automaticky_testovatelna: {it.get('automaticky_testovatelna', False)}")
        items_txt_lines.append(f"kod_riesenia: {it.get('kod_riesenia', '')}")
        items_txt_lines.append(f"test_cases: {it.get('test_cases', [])}")
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
