import textwrap
import json

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D


BLOOM_COLORS = {
    "Zapamätať si": "#DCEBFF",
    "Pochopiť": "#DDF6F0",
    "Aplikovať": "#E8F7DA",
    "Analyzovať": "#FFF1CC",
    "Hodnotiť": "#FFE0D6",
    "Vytvoriť": "#E9DDF7",
}
DEFAULT_NODE_COLOR = "#F4F6F8"
EDGE_COLOR = "#8A94A6"
TEXT_COLOR = "#1F2937"
SUBTEXT_COLOR = "#5B6575"
NODE_BORDER_COLOR = "#D0D7E2"
LAYER_BG_COLOR = "#F3F6FA"


def _wrap_name(name, width=22, max_lines=3):
    lines = textwrap.wrap(name, width=width, break_long_words=False) or ["Bez názvu"]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;:") + "..."
    return "\n".join(lines)


def _build_graph(parsed):
    graph = nx.DiGraph()
    for item in parsed:
        node_id = str(item.get("id")).strip()
        if not node_id:
            continue
        graph.add_node(
            node_id,
            name=(item.get("vzdelávací_objekt") or "").strip(),
            bloom=(item.get("bloom_level") or "").strip(),
        )

    for item in parsed:
        target = str(item.get("id")).strip()
        prerequisites = item.get("prerekvizity") or []
        if not isinstance(prerequisites, (list, tuple)):
            prerequisites = [prerequisites]
        for prerequisite in prerequisites:
            source = str(prerequisite).strip()
            if source and source in graph.nodes and target in graph.nodes:
                graph.add_edge(source, target)

    return graph


def _reduce_graph(graph):
    if nx.is_directed_acyclic_graph(graph):
        reduced = nx.transitive_reduction(graph)
        for node, data in graph.nodes(data=True):
            reduced.nodes[node].update(data)
        return reduced
    return graph


def _assign_layers(graph):
    if nx.is_directed_acyclic_graph(graph):
        generations = list(nx.topological_generations(graph))
        for layer_index, generation in enumerate(generations):
            for node in generation:
                graph.nodes[node]["layer"] = layer_index
        return generations

    generations = []
    visited = set()
    roots = [node for node, indeg in graph.in_degree() if indeg == 0] or list(graph.nodes)
    current = roots
    layer_index = 0
    while current:
        unique_current = [node for node in current if node not in visited]
        if not unique_current:
            break
        for node in unique_current:
            graph.nodes[node]["layer"] = layer_index
            visited.add(node)
        generations.append(unique_current)
        next_nodes = []
        for node in unique_current:
            next_nodes.extend(graph.successors(node))
        current = next_nodes
        layer_index += 1
    for node in graph.nodes:
        graph.nodes[node].setdefault("layer", layer_index)
    return generations


def _sort_layer_nodes(graph, layer_nodes, previous_positions):
    if not previous_positions:
        return sorted(layer_nodes, key=lambda node: (graph.nodes[node].get("name", ""), str(node)))

    def barycenter(node):
        parents = list(graph.predecessors(node))
        ranked = [previous_positions[parent] for parent in parents if parent in previous_positions]
        if ranked:
            return sum(ranked) / len(ranked)
        return float("inf")

    return sorted(layer_nodes, key=lambda node: (barycenter(node), graph.nodes[node].get("name", ""), str(node)))


def _compute_layout(graph, layer_gap, node_gap):
    generations = _assign_layers(graph)
    layer_map = {}
    for node, data in graph.nodes(data=True):
        layer = data.get("layer", 0)
        layer_map.setdefault(layer, []).append(node)

    if not generations:
        generations = [layer_map[layer] for layer in sorted(layer_map)]

    positions = {}
    previous_positions = {}
    max_layer_size = max((len(nodes) for nodes in layer_map.values()), default=1)

    for layer in sorted(layer_map):
        nodes = _sort_layer_nodes(graph, layer_map[layer], previous_positions)
        count = len(nodes)
        offset = (max_layer_size - count) / 2
        for index, node in enumerate(nodes):
            x = layer * layer_gap
            y = -(index + offset) * node_gap
            positions[node] = (x, y)
        previous_positions = {node: idx for idx, node in enumerate(nodes)}

    return positions, len(layer_map), max_layer_size


def _figure_size(node_count, layer_count, max_layer_size):
    width = max(15, min(34, 6 + layer_count * 4.2))
    height = max(8, min(24, 3.5 + max_layer_size * 2.2))
    return width, height


def _draw_nodes(ax, graph, positions):
    for node, (x, y) in positions.items():
        data = graph.nodes[node]
        bloom = data.get("bloom", "")
        face_color = BLOOM_COLORS.get(bloom, DEFAULT_NODE_COLOR)
        name = data.get("name", "")

        title = f"LO {node}"
        wrapped_name = _wrap_name(name, width=18, max_lines=2)
        label_lines = [title, wrapped_name]
        if bloom:
            label_lines.append(bloom)
        label = "\n".join(label_lines)

        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=9.5,
            color=TEXT_COLOR,
            linespacing=1.25,
            bbox={
                "boxstyle": "round,pad=0.45,rounding_size=0.18",
                "facecolor": face_color,
                "edgecolor": NODE_BORDER_COLOR,
                "linewidth": 1.2,
            },
            zorder=3,
        )


def _draw_legend(ax, graph):
    used_levels = []
    for _, data in graph.nodes(data=True):
        bloom = data.get("bloom", "")
        if bloom and bloom in BLOOM_COLORS and bloom not in used_levels:
            used_levels.append(bloom)

    if not used_levels:
        return

    handles = [
        Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor=BLOOM_COLORS[level],
            markeredgecolor=NODE_BORDER_COLOR,
            markersize=10,
            label=level,
        )
        for level in used_levels
    ]
    ax.legend(
        handles=handles,
        title="Bloom level",
        loc="upper right",
        frameon=False,
        fontsize=8,
        title_fontsize=10,
    )


def _draw_layer_guides(ax, layer_count, max_layer_size, layer_gap, node_gap):
    for layer_index in range(layer_count):
        x_center = layer_index * layer_gap
        rect = plt.Rectangle(
            (x_center - layer_gap * 0.35, -(max_layer_size - 0.25) * node_gap),
            layer_gap * 0.7,
            (max_layer_size + 0.5) * node_gap,
            facecolor=LAYER_BG_COLOR,
            edgecolor="none",
            alpha=0.45,
            zorder=0,
        )
        ax.add_patch(rect)
        ax.text(
            x_center,
            node_gap * 0.8,
            f"Vrstva {layer_index + 1}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=SUBTEXT_COLOR,
        )


def visualize_to_png(parsed, out_png_path, layer_gap=9.5, node_gap=6.5):
    graph = _reduce_graph(_build_graph(parsed))
    if graph.number_of_nodes() == 0:
        fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
        ax.axis("off")
        ax.text(0.5, 0.5, "Nie sú dostupné žiadne vzdelávacie objekty.", ha="center", va="center", fontsize=14)
        fig.savefig(out_png_path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return

    positions, layer_count, max_layer_size = _compute_layout(graph, layer_gap=layer_gap, node_gap=node_gap)
    fig_w, fig_h = _figure_size(graph.number_of_nodes(), layer_count, max_layer_size)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=220)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FBFCFE")
    _draw_layer_guides(ax, layer_count, max_layer_size, layer_gap, node_gap)

    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=14,
        width=1.2,
        edge_color=EDGE_COLOR,
        alpha=0.5,
        connectionstyle="arc3,rad=0.0",
        min_source_margin=28,
        min_target_margin=28,
    )

    _draw_nodes(ax, graph, positions)
    _draw_legend(ax, graph)

    ax.set_title(
        "Vzdelávacie objekty a prerekvizity",
        fontsize=16,
        color=TEXT_COLOR,
        pad=16,
        loc="left",
    )
    ax.text(
        0.0,
        1.01,
        "Zobrazené sú len priame prerekvizity, aby graf nebol zahltený redundantnými hranami.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=SUBTEXT_COLOR,
    )

    ax.axis("off")
    plt.tight_layout(pad=1.2)
    fig.savefig(out_png_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def build_lo_mindmap_html(parsed):
    items = {}
    for item in parsed:
        node_id = str(item.get("id", "")).strip()
        if not node_id:
            continue
        items[node_id] = {
            "id": node_id,
            "name": (item.get("vzdelávací_objekt") or "Bez názvu").strip() or "Bez názvu",
            "bloom": (item.get("bloom_level") or "").strip(),
            "prerequisites": [str(v).strip() for v in (item.get("prerekvizity") or []) if str(v).strip()],
            "dependents": [],
        }

    for node_id, item in items.items():
        for prerequisite_id in item.get("prerequisites", []):
            if prerequisite_id in items:
                items[prerequisite_id]["dependents"].append(node_id)

    if not items:
        return None

    root_candidates = sorted(
        node_id for node_id, item in items.items() if not item.get("prerequisites")
    )
    virtual_root_id = "__start__"
    items[virtual_root_id] = {
        "id": virtual_root_id,
        "name": "Začiatok",
        "bloom": "",
        "prerequisites": [],
        "dependents": root_candidates,
    }

    palette = {**BLOOM_COLORS, "_default": DEFAULT_NODE_COLOR}
    data_json = json.dumps(items, ensure_ascii=False)
    palette_json = json.dumps(palette, ensure_ascii=False)
    root_json = json.dumps(virtual_root_id, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="utf-8" />
  <style>
    body {{
      margin: 0;
      background: #10141b;
      color: #e5e7eb;
      font-family: Arial, sans-serif;
    }}
    .wrap {{
      height: 720px;
      display: flex;
      flex-direction: column;
      background:
        radial-gradient(circle at top left, rgba(72, 95, 122, 0.22), transparent 32%),
        radial-gradient(circle at bottom right, rgba(45, 74, 58, 0.20), transparent 28%),
        #10141b;
      border: 1px solid #1f2937;
      border-radius: 16px;
      overflow: hidden;
    }}
    .toolbar {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      font-size: 13px;
      color: #cbd5e1;
      background: rgba(15, 23, 42, 0.75);
    }}
    .canvas {{
      position: relative;
      flex: 1;
      overflow: auto;
      cursor: grab;
    }}
    .canvas.dragging {{
      cursor: grabbing;
    }}
    .scene {{
      position: relative;
      width: 2600px;
      height: 1800px;
      transform-origin: 0 0;
    }}
    svg {{
      position: absolute;
      inset: 0;
      overflow: visible;
    }}
    .node {{
      position: absolute;
      min-width: 190px;
      max-width: 230px;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow: 0 12px 28px rgba(0,0,0,0.22);
      color: #111827;
      user-select: none;
      transition: transform 0.12s ease, box-shadow 0.12s ease;
    }}
    .node:hover {{
      transform: translateY(-1px);
      box-shadow: 0 16px 34px rgba(0,0,0,0.26);
    }}
    .node.focus {{
      outline: 2px solid #93c5fd;
      outline-offset: 3px;
    }}
    .node.virtual-root {{
      background: linear-gradient(135deg, #c7d2fe 0%, #a5b4fc 100%) !important;
      color: #111827;
    }}
    .node-id {{
      font-size: 12px;
      font-weight: 700;
      opacity: 0.75;
      margin-bottom: 6px;
    }}
    .node-name {{
      font-size: 16px;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 8px;
    }}
    .node-meta {{
      font-size: 12px;
      opacity: 0.75;
    }}
    .node-toggle {{
      position: absolute;
      right: -10px;
      top: 50%;
      transform: translateY(-50%);
      width: 24px;
      height: 24px;
      border-radius: 999px;
      border: none;
      background: #111827;
      color: #f9fafb;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 6px 18px rgba(0,0,0,0.22);
    }}
    .legend {{
      position: absolute;
      right: 16px;
      top: 14px;
      font-size: 12px;
      color: #cbd5e1;
      background: rgba(15, 23, 42, 0.82);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 10px 12px;
      z-index: 5;
      max-width: 250px;
    }}
    .legend strong {{
      display: block;
      margin-bottom: 6px;
      color: #f8fafc;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="canvas" id="canvas">
      
      <div class="scene" id="scene">
        <svg id="edges"></svg>
        <div id="nodes"></div>
      </div>
    </div>
  </div>
  <script>
    const data = {data_json};
    const palette = {palette_json};
    const rootId = {root_json};
    const expanded = {{}};
    expanded[rootId] = true;

    const canvas = document.getElementById("canvas");
    const scene = document.getElementById("scene");
    const nodesEl = document.getElementById("nodes");
    const edgesEl = document.getElementById("edges");

    let scale = 1;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let scrollLeftStart = 0;
    let scrollTopStart = 0;

    function wrapName(name, maxLen = 24) {{
      if (!name) return "Bez názvu";
      const words = name.split(/\\s+/);
      const lines = [];
      let current = "";
      for (const word of words) {{
        const next = current ? current + " " + word : word;
        if (next.length > maxLen && current) {{
          lines.push(current);
          current = word;
          if (lines.length === 2) break;
        }} else {{
          current = next;
        }}
      }}
      if (current && lines.length < 2) lines.push(current);
      if (lines.length === 2 && words.join(" ").length > (lines[0].length + lines[1].length)) {{
        lines[1] = lines[1].replace(/[ .,;:]+$/, "") + "...";
      }}
      return lines.join("<br>");
    }}

    function buildTree(nodeId, visited = new Set()) {{
        const key = String(nodeId);
        const node = data[key];
        if (!node) return null;
      const nextVisited = new Set(visited);
      nextVisited.add(key);
      const children = [];
      if (expanded[key]) {{
        for (const childId of (node.dependents || [])) {{
          if (nextVisited.has(childId)) continue;
          const childTree = buildTree(childId, nextVisited);
          if (childTree) children.push(childTree);
        }}
      }}
      return {{ ...node, children }};
    }}

    function layoutTree(tree, depth = 0, yState = {{ value: 0 }}, startX = 180) {{
      const x = startX + depth * 310;
      let y;
      if (!tree.children.length) {{
        y = 120 + yState.value * 140;
        yState.value += 1;
      }} else {{
        const childLayouts = tree.children.map(child => layoutTree(child, depth + 1, yState, startX));
        const firstY = childLayouts[0].y;
        const lastY = childLayouts[childLayouts.length - 1].y;
        y = (firstY + lastY) / 2;
        tree.children = childLayouts;
      }}
      return {{ ...tree, x, y }};
    }}

    function collectBounds(tree, bounds = {{ maxX: 0, maxY: 0 }}) {{
      bounds.maxX = Math.max(bounds.maxX, tree.x + 260);
      bounds.maxY = Math.max(bounds.maxY, tree.y + 120);
      for (const child of tree.children || []) collectBounds(child, bounds);
      return bounds;
    }}

    function drawForest(forest) {{
      nodesEl.innerHTML = "";
      edgesEl.innerHTML = "";

      const bounds = forest.reduce((acc, tree) => collectBounds(tree, acc), {{ maxX: 0, maxY: 0 }});
      scene.style.width = Math.max(1600, bounds.maxX + 240) + "px";
      scene.style.height = Math.max(900, bounds.maxY + 180) + "px";
      edgesEl.setAttribute("width", scene.style.width);
      edgesEl.setAttribute("height", scene.style.height);

      function drawNode(node, parent = null) {{
        if (parent) {{
          const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
          const x1 = parent.x + 210;
          const y1 = parent.y + 42;
          const x2 = node.x;
          const y2 = node.y + 42;
          const mx = (x1 + x2) / 2;
          path.setAttribute("d", `M ${{x1}} ${{y1}} C ${{mx}} ${{y1}}, ${{mx}} ${{y2}}, ${{x2}} ${{y2}}`);
          path.setAttribute("fill", "none");
          path.setAttribute("stroke", "rgba(148, 163, 184, 0.55)");
          path.setAttribute("stroke-width", "2");
          edgesEl.appendChild(path);
        }}

        const el = document.createElement("div");
        el.className = "node" + (node.id === rootId ? " focus virtual-root" : "");
        el.style.left = node.x + "px";
        el.style.top = node.y + "px";
        el.style.background = palette[node.bloom] || palette._default;
        el.innerHTML = `
          <div class="node-id">${{node.id === rootId ? "Koreň mapy" : `LO ${{node.id}}`}}</div>
          <div class="node-name">${{wrapName(node.name)}}</div>
          <div class="node-meta">${{node.id === rootId ? "Vstupný bod do grafu" : (node.bloom || "Bez Bloom levelu")}}</div>
        `;

        if ((node.dependents || []).length) {{
          const btn = document.createElement("button");
          btn.className = "node-toggle";
          btn.textContent = expanded[node.id] ? "−" : "+";
          btn.title = expanded[node.id] ? "Zbaliť nadväzujúce LO" : "Rozbaliť nadväzujúce LO";
          btn.addEventListener("click", (event) => {{
            event.stopPropagation();
            expanded[node.id] = !expanded[node.id];
            render();
          }});
          el.appendChild(btn);
        }}

        el.addEventListener("click", () => {{
          if ((node.dependents || []).length) {{
            expanded[node.id] = !expanded[node.id];
            render();
          }}
        }});

        nodesEl.appendChild(el);
        for (const child of node.children || []) drawNode(child, node);
      }}

      for (const tree of forest) {{
        drawNode(tree);
      }}
    }}

    function render() {{
      const tree = buildTree(rootId);
      const laidOut = layoutTree(tree);
      drawForest([laidOut]);
    }}

    canvas.addEventListener("wheel", (event) => {{
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const offsetX = event.clientX - rect.left + canvas.scrollLeft;
      const offsetY = event.clientY - rect.top + canvas.scrollTop;
      const zoom = event.deltaY < 0 ? 1.1 : 0.9;
      const nextScale = Math.min(1.9, Math.max(0.55, scale * zoom));
      if (nextScale === scale) return;
      scale = nextScale;
      scene.style.transform = `scale(${{scale}})`;
      canvas.scrollLeft = offsetX * zoom - (event.clientX - rect.left);
      canvas.scrollTop = offsetY * zoom - (event.clientY - rect.top);
    }}, {{ passive: false }});

    canvas.addEventListener("mousedown", (event) => {{
      if (event.target.closest(".node")) return;
      isDragging = true;
      canvas.classList.add("dragging");
      dragStartX = event.clientX;
      dragStartY = event.clientY;
      scrollLeftStart = canvas.scrollLeft;
      scrollTopStart = canvas.scrollTop;
    }});

    window.addEventListener("mousemove", (event) => {{
      if (!isDragging) return;
      canvas.scrollLeft = scrollLeftStart - (event.clientX - dragStartX);
      canvas.scrollTop = scrollTopStart - (event.clientY - dragStartY);
    }});

    window.addEventListener("mouseup", () => {{
      isDragging = false;
      canvas.classList.remove("dragging");
    }});

    render();
    setTimeout(() => {{
      canvas.scrollLeft = 0;
      canvas.scrollTop = 160;
    }}, 30);
  </script>
</body>
</html>"""
