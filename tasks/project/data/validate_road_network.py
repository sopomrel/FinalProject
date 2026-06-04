"""Quick check for road_network.yaml and graph_model (run from repo root)."""
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

YAML_PATH = Path(__file__).with_name("road_network.yaml")


def _check_yaml():
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    edges = data["edges"]
    names = set(nodes)

    assert data["default_start"] in names
    assert data["default_goal"] in names

    for e in edges:
        assert e["from"] in names and e["to"] in names
        assert e["distance_m"] > 0

    adj = {n: set() for n in names}
    for e in edges:
        adj[e["from"]].add(e["to"])
        adj[e["to"]].add(e["from"])

    assert len(adj[data["default_start"]]) > 0
    assert len(adj[data["default_goal"]]) > 0
    print(f"road_network.yaml: OK ({len(nodes)} nodes, {len(edges)} edges)")


def _check_graph_model():
    from tasks.project.packages.graph_model import RoadNetwork

    g = RoadNetwork.from_yaml(YAML_PATH)
    assert g.default_start == "I_4_7"
    assert g.default_goal == "I_12_9"
    assert len(g.nodes) == 8
    assert g.edge_distance("I_4_7", "I_7_7") == 1.8
    assert g.edge_distance("I_7_7", "I_4_7") == 1.8
    assert len(g.neighbors("I_7_7")) == 5
    assert g.euclidean("I_4_7", "I_12_9") > 0
    print("graph_model.py: OK")


def _check_path_planner():
    from tasks.project.packages.graph_model import RoadNetwork
    from tasks.project.packages.navigation_types import TurnDir
    from tasks.project.packages.path_planner import dijkstra, plan_route

    g = RoadNetwork.from_yaml(YAML_PATH)
    path = dijkstra(g, "I_4_7", "I_12_9")
    assert path == ["I_4_7", "I_7_7", "I_12_9"], path

    steps = plan_route(g, "I_4_7", "I_12_9")
    assert len(steps) == 2
    assert steps[0].to_node == "I_7_7"
    assert steps[1].to_node == "I_12_9"
    assert steps[1].turn is TurnDir.STRAIGHT

    assert plan_route(g, "I_7_7", "I_7_7") == []
    print("path_planner.py: OK")


def main():
    _check_yaml()
    _check_graph_model()
    _check_path_planner()


if __name__ == "__main__":
    main()
