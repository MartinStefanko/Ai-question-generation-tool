from context_builder import parse_pages
from lo_clustering import cluster_by_core
from lo_faithfulness import analyze_lo_faithfulness
from lo_generation import generate_learning_objects
from lo_relevance_to_segment import analyze_lo_relevance_to_segment
from outputs import (
    save_document_topics_txt,
    save_lo_faithfulness_report,
    save_lo_relevance_to_segment_report,
    save_lo_validation_report,
    save_topic_coverage_report,
)
from lo_validation import validate_learning_objects
from prerequisites import infer_prerequisites
from topic_coverage import analyze_topic_coverage


def _lo_page_sort_key(lo):
    pages = parse_pages(lo.get("citovane_zdroje", []))
    first_page = pages[0] if pages else float("inf")
    return (first_page, lo.get("id", float("inf")))


def generate_lo_pipeline(
    segmenty,
    batch_size=20,
    model="gemini-2.5-flash-lite",
    generation_model=None,
    prerequisites_model=None,
    output_dir=None,
    client=None,
    verbose=True
):
    generation_model = generation_model or model
    prerequisites_model = prerequisites_model or model

    los = generate_learning_objects(
        segmenty,
        batch_size=batch_size,
        model=generation_model,
        client=client,
        verbose=verbose
    )
    if not los:
        empty_report = validate_learning_objects([], allowed_pages=[])
        if output_dir:
            save_lo_validation_report(empty_report, output_dir)
            empty_coverage_report = analyze_topic_coverage(
                segmenty,
                [],
                client=client,
                verbose=verbose,
            )
            save_document_topics_txt(empty_coverage_report.get("topics", []), output_dir)
            save_topic_coverage_report(empty_coverage_report, output_dir)
            empty_relevance_report = analyze_lo_relevance_to_segment(
                segmenty,
                [],
                client=client,
                verbose=verbose,
            )
            save_lo_relevance_to_segment_report(empty_relevance_report, output_dir)
            empty_faithfulness_report = analyze_lo_faithfulness(
                segmenty,
                [],
                client=client,
                verbose=verbose,
            )
            save_lo_faithfulness_report(empty_faithfulness_report, output_dir)
        return []

    los = cluster_by_core(los)
    los.sort(key=_lo_page_sort_key)
    for i, obj in enumerate(los, start=1):
        obj["id"] = i

    los = infer_prerequisites(los, model=prerequisites_model, client=client, verbose=verbose)

    allowed_pages = {seg.get("page") for seg in segmenty if seg.get("page") is not None}
    validation_report = validate_learning_objects(los, allowed_pages=allowed_pages)
    if output_dir:
        save_lo_validation_report(validation_report, output_dir)
        coverage_report = analyze_topic_coverage(
            segmenty,
            los,
            client=client,
            verbose=verbose,
        )
        save_document_topics_txt(coverage_report.get("topics", []), output_dir)
        save_topic_coverage_report(coverage_report, output_dir)
        relevance_report = analyze_lo_relevance_to_segment(
            segmenty,
            los,
            client=client,
            verbose=verbose,
        )
        save_lo_relevance_to_segment_report(relevance_report, output_dir)
        faithfulness_report = analyze_lo_faithfulness(
            segmenty,
            los,
            client=client,
            verbose=verbose,
        )
        save_lo_faithfulness_report(faithfulness_report, output_dir)

    if verbose:
        if validation_report["is_valid"]:
            print(f"Formalna validacia LO uspesna. Overenych LO: {validation_report['stats']['valid']}")
        else:
            print(
                "Formalna validacia LO zlyhala. "
                f"Pocet chyb: {len(validation_report['errors'])}"
            )
            for error in validation_report["errors"][:10]:
                print(f"  - {error}")
    return los
