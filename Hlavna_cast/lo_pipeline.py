from context_builder import parse_pages
from lo_clustering import cluster_by_core
from lo_generation import generate_learning_objects
from prerequisites import infer_prerequisites


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
        return []

    los = cluster_by_core(los)
    los.sort(key=_lo_page_sort_key)
    for i, obj in enumerate(los, start=1):
        obj["id"] = i

    los = infer_prerequisites(los, model=prerequisites_model, client=client, verbose=verbose)
    return los
