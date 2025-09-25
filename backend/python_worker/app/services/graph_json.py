import re
from typing import Dict, List, Tuple


def _parse_label_and_strength(raw_label: str) -> Tuple[str, int]:
    match = re.match(r"^(.*)\s*\((★{1,3})\)\s*$", raw_label)
    if not match:
        return raw_label.strip(), 0
    label_text, stars = match.groups()
    return label_text.strip(), len(stars)


def mermaid_to_json(mermaid_text: str) -> Dict:
    """
    Convert a constrained Mermaid flowchart text into a JSON graph.

    Expected syntax (as produced by our extractor):
      - Node lines:   Node_ID["Label (★★★)"]
      - Pos edges:    A -- "relationship (★★☆)" --> B
      - Neg edges:    A -. "does_not_relationship (★☆☆)" .-> B
    """
    nodes_by_id: Dict[str, Dict] = {}
    edges: List[Dict] = []

    node_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*\[\"([^\"]+)\"\]\s*$")
    edge_pos_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*--\s*\"([^\"]+)\"\s*-->\s*([A-Za-z0-9_]+)\s*$")
    edge_neg_re = re.compile(r"^\s*([A-Za-z0-9_]+)\s*-\\.\s*\"([^\"]+)\"\s*\.->\s*([A-Za-z0-9_]+)\s*$")

    for raw_line in mermaid_text.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("%%") or line.startswith("graph"):
            continue

        m_node = node_re.match(line)
        if m_node:
            node_id, raw_label = m_node.groups()
            label, strength = _parse_label_and_strength(raw_label)
            nodes_by_id[node_id] = {
                "id": node_id,
                "label": label,
                "strength": strength,
                "type": "concept",
                "meta": {},
            }
            continue

        m_pos = edge_pos_re.match(line)
        if m_pos:
            source, raw_rel, target = m_pos.groups()
            relation_label, confidence = _parse_label_and_strength(raw_rel)
            edge_id = f"{source}__{relation_label}__{target}"
            edges.append({
                "id": edge_id,
                "source": source,
                "target": target,
                "relation": relation_label,
                "polarity": "negative" if relation_label.startswith("does_not_") else "positive",
                "confidence": confidence,
                "meta": {},
            })
            continue

        m_neg = edge_neg_re.match(line)
        if m_neg:
            source, raw_rel, target = m_neg.groups()
            relation_label, confidence = _parse_label_and_strength(raw_rel)
            edge_id = f"{source}__{relation_label}__{target}"
            edges.append({
                "id": edge_id,
                "source": source,
                "target": target,
                "relation": relation_label,
                "polarity": "negative",
                "confidence": confidence,
                "meta": {},
            })
            continue

    graph = {
        "nodes": list(nodes_by_id.values()),
        "edges": edges,
        "meta": {"format": "graph-json-v1"},
    }
    return graph



