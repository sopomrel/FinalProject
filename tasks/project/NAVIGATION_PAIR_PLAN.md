# Navigation Project — Pair Plan (Sopo + Achi)

**Task:** Autonomous navigation from a start intersection to a target intersection (Duckietown / KvatiTown final project).

**Repo:** `KvatiTown` — main code goes in `tasks/project/packages/`.

**Rule for commits:** Work on **different files** until integration. One person = one commit per slice. Pull `main` before each new branch/commit.

---

## Goal (full robot behavior)

1. Given **start** and **goal** intersection IDs → compute **optimal route** (graph + Dijkstra or A*).
2. **Drive** the route: lane follow between intersections, **stop at red line**, **turn** at intersections.
3. **Stop for obstacles** (object detection), resume when clear.
4. On arrival: **victory dance** (spin + flashing LEDs) **or** optional **parking**.
5. Optional: **return trip** (delivery robot).

---

## Where things live in KvatiTown

| What | Path |
|------|------|
| Final agent (integration later) | `tasks/project/packages/agent.py` |
| API contract | `tasks/project/notebooks/01-Project/project.ipynb` |
| Real bot deploy | `python launch.py --run --bot <name> --task project` |
| Sim map (reference) | `GodotSimulation/ducky-bot/scenes/maps/navigator.tscn` |
| Map maker docs | `docs/MAP_MAKER.md` |
| Lane follow (reuse) | `tasks/visual_lane_servoing/packages/` |
| Odometry / PID / turns (reuse) | `tasks/modcon/packages/` |
| Obstacle stop (reuse) | `tasks/object_detection/packages/stop_activity.py` |

**Note:** `project` currently has only `real_server.py`. Sim needs `servers/project/virtual_server.py` later — not blocking Achi’s modules.

---

## Shared interface (agree before coding)

Both sides should use the same types (add `navigation_types.py` in integration commit):

```python
from enum import Enum
from dataclasses import dataclass

class NavState(Enum):
    IDLE = "idle"
    FOLLOW_LANE = "follow_lane"
    APPROACH_INTERSECTION = "approach_intersection"
    STOP_AT_LINE = "stop_at_line"
    TURN = "turn"
    OBSTACLE_STOP = "obstacle_stop"
    GOAL_REACHED = "goal_reached"
    PARKING = "parking"
    VICTORY = "victory"

class TurnDir(Enum):
    LEFT = "left"
    RIGHT = "right"
    STRAIGHT = "straight"

@dataclass
class PathStep:
    to_node: str
    turn: TurnDir  # turn when leaving previous node
```

**Sopo delivers:** `list[PathStep]` from `shortest_path(start_id, goal_id)`.

**Achi delivers:** FSM that accepts `next_turn: TurnDir`, `at_stop_line: bool`, obstacle flags, and drives wheels/LEDs.

---

## Work split

### Sopo (planning & map)

| File | Purpose |
|------|---------|
| `graph_model.py` | Build weighted graph from YAML |
| `path_planner.py` | Dijkstra (+ optional A*) |
| `data/road_network.yaml` | Nodes, edges, measured distances |
| Tests / notebook | Verify paths on paper map |

**Does not edit:** `agent.py`, camera modules on Achi’s side.

---

### Achi (perception, motion, FSM)

| File | Purpose |
|------|---------|
| `intersection_detection.py` | Red stop line / intersection cue |
| `turning.py` | ~90° turn primitive (PID/odometry style) |
| `obstacle_handler.py` | Wrap `should_stop()` from object_detection |
| `navigation_fsm.py` | State machine; mock path until Sopo merges |

**Does not edit:** `graph_model.py`, `path_planner.py`, `road_network.yaml`.

---

## Suggested commit order

1. Sopo: `graph_model.py` + `data/road_network.yaml`
2. **Achi: `intersection_detection.py`**
3. Sopo: `path_planner.py` + tests
4. **Achi: `turning.py` + `obstacle_handler.py`**
5. **Achi: `navigation_fsm.py` (mock `PathStep` list)**
6. Pair: `navigation_types.py` + wire planner into FSM + `agent.py`
7. Either: `victory.py`, parking, return trip

---

## Materials to read

### Everyone

- `tasks/project/notebooks/01-Project/project.ipynb` — `main(camera, wheels, leds, stop_event)`
- Course spec: [duckietown.com](https://duckietown.com) — parking / victory dance if instructor uses official rubric

### Sopo

- `docs/MAP_MAKER.md` — tile grid, intersections
- Measure mat: yardstick or mat count per straight segment

### Achi

- `tasks/visual_lane_servoing/packages/visual_servoing_activity.py` + `agent.py`
- `tasks/modcon/packages/odometry_activity.py`, `pid_controller.py`
- `servers/modcon/virtual_server.py` — `run_turn`, `run_straight` patterns
- `tasks/object_detection/packages/stop_activity.py`
- `config/lane_servoing_config.yaml`, `config/modcon_config.yaml`

---

## State machine (target behavior)

```
FOLLOW_LANE → (red line) → STOP_AT_LINE → TURN or straight → FOLLOW_LANE
FOLLOW_LANE → (obstacle) → OBSTACLE_STOP → (clear) → FOLLOW_LANE
FOLLOW_LANE → (last node) → GOAL_REACHED → VICTORY (or PARKING)
```

---

## Testing without the other person’s code

- **Sopo:** unit tests on graph; print route + turns for start/goal on paper map.
- **Achi:** sim lane follow `python launch.py --sim --task visual_lane_servoing`; saved images for red-line detection; turn-in-place on bot or modcon sim.

---

## Integration checklist (later)

- [ ] FSM reads real `PathStep` list from Sopo’s planner
- [ ] `agent.py` main loop: lane agent + FSM + obstacle check each frame
- [ ] Victory: spin + LED flash
- [ ] Optional: parking, return path (`shortest_path(goal, start)`)

---

## Contact / sync

- Agree intersection **naming** (e.g. `I7_8` from tile names in `navigator.tscn` or letters `A`, `B`, `C`).
- Share YAML node list when Sopo has first draft so Achi can mock turns in FSM.
- Do **not** both edit `agent.py` until step 6.
