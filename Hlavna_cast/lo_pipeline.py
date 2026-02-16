from lo_clustering import cluster_by_core
from lo_generation import generate_learning_objects
from prerequisites import infer_prerequisites


def generate_lo_pipeline(segmenty, batch_size=20, model="gemini-2.5-flash-lite", client=None, verbose=True):
    los = generate_learning_objects(
        segmenty,
        batch_size=batch_size,
        model=model,
        client=client,
        verbose=verbose
    )
    if not los:
        return []

    los = cluster_by_core(los)
    for i, obj in enumerate(los, start=1):
        obj["id"] = i

    los = infer_prerequisites(los, model=model, client=client, verbose=verbose)
    return los
