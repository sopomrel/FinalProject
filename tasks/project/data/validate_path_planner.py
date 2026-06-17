"""Validate path_planner.py mission planning (run from repo root)."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tasks.project.packages.graph_model import RoadNetwork
from tasks.project.packages.navigation_types import TurnDir
from tasks.project.packages.path_planner import (
    dijkstra,
    path_to_steps,
    plan_mission,
    plan_parking_route,
    plan_return_route,
    plan_route,
)

YAML_PATH = Path(__file__).with_name("road_network.yaml")


def _nodes(steps):
    return [s.to_node for s in steps]


def main():
    g = RoadNetwork.from_yaml(YAML_PATH)

    # dijkstra picks the shortest hop count / weight path.
    assert dijkstra(g, "I_4_7", "I_12_9") == ["I_4_7", "I_7_7", "I_12_9"]
    assert dijkstra(g, "I_7_7", "I_7_7") == ["I_7_7"]

    # plan_route uses defaults when start/goal omitted.
    default_route = plan_route(g)
    assert _nodes(default_route) == ["I_7_7", "I_12_9"]
    # Last step is always STRAIGHT (you arrive at the goal, no turn out of it).
    assert default_route[-1].turn is TurnDir.STRAIGHT

    # Same node -> empty plan everywhere.
    assert plan_route(g, "I_7_7", "I_7_7") == []
    assert plan_return_route(g, "I_4_7", "I_4_7") == []
    assert plan_parking_route(g, "I_8_1", "I_8_1") == []

    # Return route is the outbound route reversed (node-wise).
    outbound = plan_route(g, "I_4_7", "I_12_9")
    inbound = plan_return_route(g, "I_12_9", "I_4_7")
    assert _nodes(inbound)[-1] == "I_4_7"
    assert _nodes(outbound)[-1] == "I_12_9"

    # plan_mission = outbound, then optional return, then optional parking.
    just_out = plan_mission(g, "I_4_7", "I_12_9")
    assert _nodes(just_out) == ["I_7_7", "I_12_9"]

    round_trip = plan_mission(g, "I_4_7", "I_12_9", return_to_start=True)
    assert _nodes(round_trip) == ["I_7_7", "I_12_9", "I_7_7", "I_4_7"]

    with_park = plan_mission(
        g, "I_4_7", "I_12_9", return_to_start=True, parking="I_8_1"
    )
    assert _nodes(with_park)[-1] == "I_8_1"
    assert len(with_park) > len(round_trip)

    # A route that requires a real turn produces a non-STRAIGHT step.
    turn_steps = path_to_steps(g, ["I_4_9", "I_7_9", "I_7_11"])
    assert any(s.turn is not TurnDir.STRAIGHT for s in turn_steps)

    print("path_planner.py: OK")


if __name__ == "__main__":
    main()
