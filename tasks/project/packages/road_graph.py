"""Road network graph for realmap.tscn (KiuPathObj / IntroductionBase).

Navigation model
================
1. Pick **start** and **goal** intersections (A / B / C).
2. Place the Duckiebot on the road, facing the direction you intend to travel.
3. ``plan_route()`` runs Dijkstra and builds an ordered list of **red-line stops**
   — one entry per stop line the bot will cross (start, any intermediates, goal).
4. On the robot: lane-follow until the first red line (start), turn as planned,
   lane-follow to the next red line, repeat.  After crossing the goal red line
   the mission is **DONE**.  On this map the longest route needs at most three
   red lines.

Map layout (top-down, north = top)
====================================
The map tile grid parsed from IntroductionBase.tscn (normalised, 1 cell = 1 mat):

  row 0  C S S X S S C
  row 1  S . . S . C C
  row 2  S . C C . S .
  row 3  S . S . . S .
  row 4  X S X S S C .   ← A(0,4)  B(2,4)
  row 5  S . S . . . .
  row 6  S . S . . . .
  row 7  S . S . . . .
  row 8  C S C . . . .
         col→

  C = curve tile   S = straight tile   X = cross (intersection)
  
Two-sided road, right-hand driving
====================================
Every physical segment has two lanes.  A→B and B→A are separate directed edges.
No U-turns at intersections (enforced inside ``dijkstra()``).
Turns at each stop are derived from cardinal headings via ``compute_turn()``.

Grid compass: row ``z`` increases south, column ``x`` increases east.
Each edge's ``exit_direction`` is inferred from its first tile step.
"""

import heapq
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

MAT_LENGTH_M = 0.6


class Intersection(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class Cardinal(str, Enum):
    NORTH = "N"
    EAST  = "E"
    SOUTH = "S"
    WEST  = "W"


class Turn(str, Enum):
    STRAIGHT = "straight"
    LEFT     = "left"
    RIGHT    = "right"
    UTURN    = "uturn"


@dataclass(frozen=True)
class GridTile:
    x: int
    z: int


@dataclass(frozen=True)
class RoadEdge:
    source:         Intersection
    target:         Intersection
    weight:         int
    route_id:       str
    tiles:          Tuple[GridTile, ...]
    exit_direction: Cardinal


@dataclass(frozen=True)
class RedLineStop:
    """One red stop-line event on the drive from start to goal.

  ``turn`` is the manoeuvre executed **after** crossing this line.
  ``None`` means this is the goal — cross the line and finish (no turn).
  ``segment`` is the road edge to follow after this stop (``None`` at goal).
    """
    intersection: Intersection
    turn:         Optional[Turn]
    segment:      Optional[RoadEdge]


@dataclass(frozen=True)
class RoutePlan:
    """Full navigation plan produced once at mission start."""
    start:            Intersection
    goal:             Intersection
    approach_heading: Optional[Cardinal]
    total_mats:       int
    edges:            Tuple[RoadEdge, ...]
    stops:            Tuple[RedLineStop, ...]

    @property
    def num_red_lines(self) -> int:
        return len(self.stops)

    def stop_label(self, index: int) -> str:
        if index < 0 or index >= len(self.stops):
            return "—"
        stop = self.stops[index]
        if stop.turn is None:
            return f"{stop.intersection.value} (goal)"
        return f"{stop.intersection.value} → {stop.turn.value}"

    def summary(self) -> str:
        parts = [self.stop_label(i) for i in range(len(self.stops))]
        segs = " → ".join(f"{e.route_id}({e.weight})" for e in self.edges)
        return (
            f"{self.start.value} → {self.goal.value}: {self.total_mats} mats  "
            f"[{segs}]  red lines ({len(self.stops)}): "
            + " · ".join(parts)
        )


# ── Cardinal helpers ──────────────────────────────────────────────────────────

_OPPOSITE: Dict[Cardinal, Cardinal] = {
    Cardinal.NORTH: Cardinal.SOUTH,
    Cardinal.SOUTH: Cardinal.NORTH,
    Cardinal.EAST:  Cardinal.WEST,
    Cardinal.WEST:  Cardinal.EAST,
}

_TURN_TABLE: Dict[Tuple[Cardinal, Cardinal], Turn] = {
    (Cardinal.NORTH, Cardinal.NORTH): Turn.STRAIGHT,
    (Cardinal.NORTH, Cardinal.EAST):  Turn.RIGHT,
    (Cardinal.NORTH, Cardinal.WEST):  Turn.LEFT,
    (Cardinal.NORTH, Cardinal.SOUTH): Turn.UTURN,

    (Cardinal.EAST,  Cardinal.EAST):  Turn.STRAIGHT,
    (Cardinal.EAST,  Cardinal.SOUTH): Turn.RIGHT,
    (Cardinal.EAST,  Cardinal.NORTH): Turn.LEFT,
    (Cardinal.EAST,  Cardinal.WEST):  Turn.UTURN,

    (Cardinal.SOUTH, Cardinal.SOUTH): Turn.STRAIGHT,
    (Cardinal.SOUTH, Cardinal.WEST):  Turn.RIGHT,
    (Cardinal.SOUTH, Cardinal.EAST):  Turn.LEFT,
    (Cardinal.SOUTH, Cardinal.NORTH): Turn.UTURN,

    (Cardinal.WEST,  Cardinal.WEST):  Turn.STRAIGHT,
    (Cardinal.WEST,  Cardinal.NORTH): Turn.RIGHT,
    (Cardinal.WEST,  Cardinal.SOUTH): Turn.LEFT,
    (Cardinal.WEST,  Cardinal.EAST):  Turn.UTURN,
}


def compute_turn(arriving: Cardinal, departing: Cardinal) -> Turn:
    """Turn needed when changing from ``arriving`` heading to ``departing``."""
    return _TURN_TABLE[(arriving, departing)]


def _tiles(coords: List[Tuple[int, int]]) -> Tuple[GridTile, ...]:
    return tuple(GridTile(x, z) for x, z in coords)


def _compass_heading(tiles: Tuple[GridTile, ...]) -> Cardinal:
    """Compass heading on the first mat leaving the source intersection.

    Grid ``z`` (row) increases toward the south; ``x`` (col) toward the east.
    """
    if len(tiles) < 2:
        raise ValueError("Need at least two tiles to infer heading")
    dx = tiles[1].x - tiles[0].x
    dz = tiles[1].z - tiles[0].z
    if abs(dx) >= abs(dz):
        return Cardinal.EAST if dx > 0 else Cardinal.WEST
    return Cardinal.SOUTH if dz > 0 else Cardinal.NORTH


def _edge(
    source: Intersection,
    target: Intersection,
    weight: int,
    route_id: str,
    coords: List[Tuple[int, int]],
) -> RoadEdge:
    tiles = _tiles(coords)
    return RoadEdge(
        source, target, weight, route_id, tiles,
        exit_direction=_compass_heading(tiles),
    )


_ROAD_EDGES: Tuple[RoadEdge, ...] = (
    _edge(Intersection.A, Intersection.B, 4, "a_to_b",
          [(0, 4), (1, 4), (2, 4)]),
    _edge(Intersection.B, Intersection.A, 4, "b_to_a",
          [(2, 4), (1, 4), (0, 4)]),
    _edge(Intersection.A, Intersection.B, 10, "a_to_b_north",
          [(0,4),(0,5),(0,6),(0,7),(0,8),(1,8),(2,8),(2,7),(2,6),(2,5),(2,4)]),
    _edge(Intersection.B, Intersection.A, 10, "b_to_a_north",
          [(2,4),(2,5),(2,6),(2,7),(2,8),(1,8),(0,8),(0,7),(0,6),(0,5),(0,4)]),
    _edge(Intersection.A, Intersection.C, 7, "a_to_c",
          [(0,4),(0,3),(0,2),(0,1),(0,0),(1,0),(2,0),(3,0)]),
    _edge(Intersection.C, Intersection.A, 7, "c_to_a",
          [(3,0),(2,0),(1,0),(0,0),(0,1),(0,2),(0,3),(0,4)]),
    _edge(Intersection.B, Intersection.C, 2, "b_to_c",
          [(2,4),(2,3),(3,0)]),
    _edge(Intersection.C, Intersection.B, 2, "c_to_b",
          [(3,0),(2,3),(2,4)]),
    _edge(Intersection.B, Intersection.C, 10, "b_to_c_east",
          [(2,4),(3,4),(4,4),(5,4),(5,3),(5,2),(5,1),(6,1),(6,0),(5,0),(4,0),(3,0)]),
    _edge(Intersection.C, Intersection.B, 10, "c_to_b_east",
          [(3,0),(4,0),(5,0),(6,0),(6,1),(5,1),(5,2),(5,3),(5,4),(4,4),(3,4),(2,4)]),
)

_ROUTE_BY_ID: Dict[str, RoadEdge] = {e.route_id: e for e in _ROAD_EDGES}


def build_adjacency() -> Dict[Intersection, List[RoadEdge]]:
    graph: Dict[Intersection, List[RoadEdge]] = {n: [] for n in Intersection}
    for edge in _ROAD_EDGES:
        graph[edge.source].append(edge)
    return graph


def dijkstra(
    start: Intersection,
    goal:  Intersection,
    graph: Optional[Dict[Intersection, List[RoadEdge]]] = None,
) -> Tuple[int, List[RoadEdge]]:
    """Shortest route with no-U-turn constraint.  Returns (mats, edge_list)."""
    if start == goal:
        return 0, []

    adj = graph or build_adjacency()
    INF = 10 ** 9
    dist: Dict[Tuple[Intersection, Optional[str]], int] = {}
    prev: Dict[Tuple[Intersection, Optional[str]], Optional[Tuple]] = {}

    init_state = (start, None)
    dist[init_state] = 0
    prev[init_state] = None
    heap: List[Tuple[int, Intersection, Optional[str]]] = [(0, start, None)]
    best_goal_state = None

    while heap:
        cost, node, last_route_id = heapq.heappop(heap)
        state = (node, last_route_id)
        if cost != dist.get(state, INF):
            continue
        if node == goal:
            best_goal_state = state
            break

        arriving_exit: Optional[Cardinal] = None
        if last_route_id is not None:
            arriving_exit = _ROUTE_BY_ID[last_route_id].exit_direction

        for edge in adj[node]:
            if (arriving_exit is not None and
                    edge.exit_direction == _OPPOSITE[arriving_exit]):
                continue
            new_cost = cost + edge.weight
            new_state = (edge.target, edge.route_id)
            if new_cost < dist.get(new_state, INF):
                dist[new_state] = new_cost
                prev[new_state] = (state, edge)
                heapq.heappush(heap, (new_cost, edge.target, edge.route_id))

    if best_goal_state is None:
        raise ValueError(f"No route from {start.value} to {goal.value}")

    edges: List[RoadEdge] = []
    cur = best_goal_state
    while prev[cur] is not None:
        parent_state, edge = prev[cur]
        edges.append(edge)
        cur = parent_state
    edges.reverse()
    return dist[best_goal_state], edges


def plan_route(
    start: Intersection,
    goal:  Intersection,
    approach_heading: Optional[Cardinal] = None,
) -> RoutePlan:
    """Plan a full mission: Dijkstra path + ordered red-line stop sequence.

    Parameters
    ----------
    start, goal
        Intersection nodes for Dijkstra.
    approach_heading
        Cardinal direction the Duckiebot faces when it crosses the **first**
        red line at ``start``.  Required for a correct turn onto the first
        segment; if omitted, a straight-through start is assumed.
    """
    total_mats, edges = dijkstra(start, goal)
    stops: List[RedLineStop] = []

    if not edges:
        stops.append(RedLineStop(start, None, None))
    else:
        first_turn = (
            compute_turn(approach_heading, edges[0].exit_direction)
            if approach_heading is not None
            else Turn.STRAIGHT
        )
        stops.append(RedLineStop(start, first_turn, edges[0]))

        for i in range(len(edges) - 1):
            turn = compute_turn(edges[i].exit_direction, edges[i + 1].exit_direction)
            stops.append(RedLineStop(edges[i].target, turn, edges[i + 1]))

        stops.append(RedLineStop(goal, None, None))

    return RoutePlan(
        start=start,
        goal=goal,
        approach_heading=approach_heading,
        total_mats=total_mats,
        edges=tuple(edges),
        stops=tuple(stops),
    )


def format_route(
    start: Intersection,
    goal: Intersection,
    approach_heading: Optional[Cardinal] = None,
) -> str:
    return plan_route(start, goal, approach_heading).summary()


# Backward-compatible helpers (used by older call sites / tests).
def start_turn(approach: Cardinal, first_edge: RoadEdge) -> Turn:
    return compute_turn(approach, first_edge.exit_direction)


def route_turns(edges: List[RoadEdge]) -> List[Tuple[Intersection, Turn]]:
    turns = []
    for i in range(len(edges) - 1):
        turns.append((
            edges[i].target,
            compute_turn(edges[i].exit_direction, edges[i + 1].exit_direction),
        ))
    return turns


ADJACENCY = build_adjacency()


if __name__ == "__main__":
    pairs = [
        (Intersection.A, Intersection.B),
        (Intersection.A, Intersection.C),
        (Intersection.B, Intersection.C),
        (Intersection.B, Intersection.A),
        (Intersection.C, Intersection.A),
        (Intersection.C, Intersection.B),
    ]
    for src, dst in pairs:
        for heading in (Cardinal.NORTH, Cardinal.EAST, None):
            label = heading.value if heading else "—"
            print(f"[{label}] {format_route(src, dst, heading)}")
