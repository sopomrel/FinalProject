import heapq
import math
from typing import Dict, List, Optional, Tuple

from tasks.project.packages.graph_model import RoadNetwork
from tasks.project.packages.navigation_types import PathStep, TurnDir

STRAIGHT_TURN_RAD = 0.5  # ~29° — sharper counts as left/right


def dijkstra(network: RoadNetwork, start: str, goal: str) -> List[str]:
    """Shortest node path from start to goal (inclusive)."""
    if start not in network.nodes:
        raise KeyError(f"Unknown intersection: {start}")
    if goal not in network.nodes:
        raise KeyError(f"Unknown intersection: {goal}")
    if start == goal:
        return [start]

    dist: Dict[str, float] = {start: 0.0}
    prev: Dict[str, Optional[str]] = {start: None}
    heap: List[Tuple[float, str]] = [(0.0, start)]

    while heap:
        cost, node = heapq.heappop(heap)
        if cost != dist[node]:
            continue
        if node == goal:
            break
        for neighbor, weight in network.neighbors(node):
            new_cost = cost + weight
            if neighbor not in dist or new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))

    if goal not in dist:
        raise ValueError(f"No path from {start} to {goal}")

    path: List[str] = []
    cur: Optional[str] = goal
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def _bearing(network: RoadNetwork, a: str, b: str) -> float:
    na, nb = network.get_node(a), network.get_node(b)
    return math.atan2(nb.z - na.z, nb.x - na.x)


def _turn_between(in_heading: float, out_heading: float) -> TurnDir:
    delta = math.atan2(
        math.sin(out_heading - in_heading),
        math.cos(out_heading - in_heading),
    )
    if abs(delta) < STRAIGHT_TURN_RAD:
        return TurnDir.STRAIGHT
    return TurnDir.LEFT if delta > 0 else TurnDir.RIGHT


def path_to_steps(network: RoadNetwork, node_path: List[str]) -> List[PathStep]:
    """Convert a node path into PathStep list (turn when leaving each hop node)."""
    if len(node_path) <= 1:
        return []

    steps: List[PathStep] = []
    for i in range(1, len(node_path)):
        current = node_path[i]
        if i < len(node_path) - 1:
            incoming = _bearing(network, node_path[i - 1], current)
            outgoing = _bearing(network, current, node_path[i + 1])
            turn = _turn_between(incoming, outgoing)
        else:
            turn = TurnDir.STRAIGHT
        steps.append(PathStep(to_node=current, turn=turn))
    return steps


def plan_route(
    network: RoadNetwork,
    start: Optional[str] = None,
    goal: Optional[str] = None,
) -> List[PathStep]:
    """Plan optimal route; uses network defaults when start/goal omitted."""
    s = start or network.default_start
    g = goal or network.default_goal
    return path_to_steps(network, dijkstra(network, s, g))
