import textwrap
import matplotlib.patheffects as pe
import networkx as nx
import matplotlib.pyplot as plt


def visualize_to_png(parsed, out_png_path, layer_gap=8.0, node_gap=5.0):

    G = nx.DiGraph()
    for o in parsed:
        id_obj = str(o.get("id")).strip()
        name = (o.get("vzdelávací_objekt") or "").strip()
        if not id_obj:                                     
            continue
        wrapped = "\n".join(textwrap.wrap(f"{id_obj} - {name}", width=18, break_long_words=False))
        G.add_node(id_obj, label=wrapped)

    for o in parsed:
        tgt = str(o.get("id")).strip()
        pre = o.get("prerekvizity") or []
        if not isinstance(pre, (list, tuple)):
            pre = [pre]
        for p in pre:
            p = str(p).strip()
            if p and p in G.nodes and tgt in G.nodes:
                G.add_edge(p, tgt)

    try:
        for i, gen in enumerate(nx.topological_generations(G)):
            for n in gen:
                G.nodes[n]["layer"] = i
        pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal")
    except nx.NetworkXUnfeasible:
        pos = nx.spring_layout(G, seed=42, k=1.8)

    pos = {n: (x * layer_gap, y * node_gap) for n, (x, y) in pos.items()}

    node_size = 6500  
    plt.figure(figsize=(24, 13.5), dpi=200)

    nx.draw_networkx_nodes(
        G, pos, node_size=node_size, node_color="white", edgecolors="black", linewidths=1.2, node_shape="o")

    nx.draw_networkx_edges(
        G, pos, arrows=True, arrowstyle="-|>", arrowsize=24, width=1.6, edge_color="black", node_size=node_size,
        node_shape="o", min_source_margin=16, min_target_margin=16)

    labels = {n: data.get("label", str(n)) for n, data in G.nodes(data=True)}

    texts = nx.draw_networkx_labels(
        G, pos, labels=labels, font_size=10, font_weight="bold", font_color="black")
    
    for t in texts.values():
        t.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_png_path)
    plt.close()