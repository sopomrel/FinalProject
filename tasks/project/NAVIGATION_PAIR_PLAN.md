# Navigation — task order

**You (Sopo):** do Phase 1 now.  
**Achi:** does Phase 2 when available (continues from your code).

All code: `tasks/project/packages/` (+ `data/road_network.yaml`).

---

## Phase 1 — Sopo (now)

1. `navigation_types.py` — enums + `PathStep`
2. `data/road_network.yaml` — intersections + edge distances (measure mat)
3. `graph_model.py` — load YAML → graph
4. `path_planner.py` — Dijkstra → `list[PathStep]`
5. `intersection_detection.py` — red stop line detect
6. `navigation_fsm.py` — states + transitions (planner hooked up)
7. `agent.py` — main loop shell: lane follow between stops, calls FSM (no turn/obstacle polish yet)

---

## Phase 2 — Achi (later)

8. `turning.py` — 90° turn primitive
9. `obstacle_handler.py` — wrap `stop_activity.should_stop`
10. Wire turn + obstacle into `navigation_fsm.py`
11. Finish `agent.py` — full drive cycle
12. `victory.py` — spin + LED flash on goal
13. Optional: parking, return trip in `path_planner.py`

---

## Handoff note for Achi

Start at step 8. Read Phase 1 files before editing.
