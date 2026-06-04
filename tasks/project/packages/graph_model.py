from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

DEFAULT_NETWORK_PATH = Path(__file__).resolve().parent.parent / "data" / "road_network.yaml"

Neighbor = Tuple[str, float]


@dataclass(frozen=True)
class IntersectionNode:
    node_id: str
    x: float
    z: float
    tile: str
    kind: str


class RoadNetwork:
    """Weighted undirected graph loaded from road_network.yaml."""

    def __init__(
        self,
        nodes: Dict[str, IntersectionNode],
        adjacency: Dict[str, List[Neighbor]],
        tile_size_m: float,
        default_start: str,
        default_goal: str,
    ):
        self.nodes = nodes
        self.adjacency = adjacency
        self.tile_size_m = tile_size_m
        self.default_start = default_start
        self.default_goal = default_goal

    @classmethod
    def from_yaml(cls, path: Optional[Path] = None) -> "RoadNetwork":
        yaml_path = Path(path) if path else DEFAULT_NETWORK_PATH
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

        nodes: Dict[str, IntersectionNode] = {}
        for node_id, attrs in data["nodes"].items():
            nodes[node_id] = IntersectionNode(
                node_id=node_id,
                x=float(attrs["x"]),
                z=float(attrs["z"]),
                tile=str(attrs["tile"]),
                kind=str(attrs["kind"]),
            )

        adjacency: Dict[str, List[Neighbor]] = {node_id: [] for node_id in nodes}
        for edge in data["edges"]:
            a, b = edge["from"], edge["to"]
            dist = float(edge["distance_m"])
            if a not in nodes or b not in nodes:
                raise ValueError(f"Unknown node in edge: {edge}")
            adjacency[a].append((b, dist))
            adjacency[b].append((a, dist))

        return cls(
            nodes=nodes,
            adjacency=adjacency,
            tile_size_m=float(data["tile_size_m"]),
            default_start=str(data["default_start"]),
            default_goal=str(data["default_goal"]),
        )

    def get_node(self, node_id: str) -> IntersectionNode:
        try:
            return self.nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown intersection: {node_id}") from exc

    def neighbors(self, node_id: str) -> List[Neighbor]:
        if node_id not in self.adjacency:
            raise KeyError(f"Unknown intersection: {node_id}")
        return list(self.adjacency[node_id])

    def edge_distance(self, a: str, b: str) -> Optional[float]:
        for neighbor, dist in self.adjacency.get(a, []):
            if neighbor == b:
                return dist
        return None

    def euclidean(self, a: str, b: str) -> float:
        """Straight-line distance in meters (for A* heuristic)."""
        na, nb = self.get_node(a), self.get_node(b)
        return ((na.x - nb.x) ** 2 + (na.z - nb.z) ** 2) ** 0.5
