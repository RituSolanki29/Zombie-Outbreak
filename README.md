# Zombie Outbreak: A* vs GBFS Multi-Agent Survival Simulator

A Python/Tkinter simulation of survivors escaping a zombie outbreak in a continuous 2D world. Survivors plan routes with a selectable **A\*** or **Greedy Best-First Search (GBFS)** planner, steer away from nearby zombies with **Minimax + Alpha–Beta pruning**, and the project includes a reproducible **A\* vs GBFS comparison study** across four scenarios.

## Highlights

- **Continuous world:** 15 × 15 plane, floating-point `(x, y)` positions, bounded-speed movement, rectangular buildings and Euclidean-distance interactions.
- **Two survivor path planners** on the *same* visibility graph, so the comparison is controlled:
  - **A\*** orders nodes by `f(n) = g(n) + h(n)` and returns the shortest route.
  - **GBFS** orders nodes by `h(n)` only, so it is greedy and does not guarantee the shortest route.
- **Tactical AI:** when a zombie is within the danger radius, survivors pick a steering action using depth-limited Alpha–Beta minimax.
- **Zombie pursuit:** zombies chase the nearest survivor using A* (kept fixed so only the survivor planner varies).
- **Four scenarios** that test escape, evasion, obstacle-aware routing and a mid-run infection.
- **Tkinter GUI** with scenario and algorithm selectors, playback controls and live performance metrics.
- **CLI comparison mode** that runs both planners on every scenario and exports a CSV.
- **Regression tests** covering geometry, planners, movement and end-to-end scenario outcomes.

## Requirements

- Python 3.10+
- Tkinter (included with most desktop Python installs)
- No third-party packages

## Quick start

```bash
python main.py                                    # GUI (default planner: A*)
python main.py --algorithm GBFS                   # GUI, starting with GBFS selected
python main.py --text --algorithm A*              # one scenario in the terminal
python main.py --all --algorithm GBFS             # all scenarios in the terminal
python main.py --compare                          # A* vs GBFS on all scenarios, writes a CSV
python main.py --compare --output results.csv     # choose the CSV path
python test.py                                    # run the test suite
```

## How it works

### World model

| Parameter | Value |
|---|---|
| World bounds | `[0, 15] × [0, 15]` |
| Agent radius | 0.16 |
| Survivor speed | 0.32 units/tick |
| Zombie speed | 0.16 units/tick |
| Capture radius | 0.28 |
| Resource pickup radius | 0.30 |
| Rescue radius | 0.38 |
| Zombie danger radius | 2.8 |
| Alpha–Beta depth | 4 in the GUI, 2 in the batch comparison |

### Path planning

1. **Visibility graph:** nodes are the start, the goal and four clearance-offset corners of each building (corners inside buildings or near zombies are dropped). Two nodes are connected if the straight segment between them is collision-free; the edge cost is its Euclidean length.
2. **Search:** A* or GBFS finds a waypoint route through this graph. Euclidean distance is an admissible and consistent heuristic here, so A* is optimal on the graph.
3. **Replanning:** survivors replan every tick. If filtering out zombie-adjacent waypoints disconnects the graph, the planner retries without the filter.

### Tactical layer

When the nearest zombie is inside the danger radius, the survivor evaluates sampled steering actions with depth-limited minimax and Alpha–Beta pruning, then moves toward the best one. Survivors that block each other in a corridor sidestep rather than deadlock.

### Scenarios

| # | Scenario | What it tests |
|---|---|---|
| 1 | **Normal Escape** | Collect a resource, then reach extraction while zombies pursue (short trips for two survivors) |
| 2 | **Close Encounter** | A nearby initial threat forces evasive steering and replanning |
| 3 | **Resource Detour** | Separated resources and buildings test obstacle-aware routing; survivors cross paths in a corridor |
| 4 | **Emergency Outbreak** | A scripted infection at tick 45 turns a survivor into another zombie |

## Comparison study

`python main.py --compare` runs each scenario once per planner (deterministic, Alpha–Beta depth 2) and writes `comparison_results.csv`. Example output from the bundled `comparison_results_sample.csv`:

| Scenario | Algorithm | Planning calls | Success rate | Nodes expanded | Planning time (ms) | Mean route length | Rescued | Infected |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1. Normal Escape | A* | 285 | 100% | 921 | 468.22 | 9.04 | 3/3 | 0 |
| | GBFS | 293 | 100% | 759 | 478.81 | 8.77 | 3/3 | 0 |
| 2. Close Encounter | A* | 349 | 100% | 907 | 560.50 | 8.38 | 3/3 | 0 |
| | GBFS | 366 | 100% | 975 | 584.84 | 9.33 | 3/3 | 0 |
| 3. Resource Detour | A* | 376 | 100% | 1,306 | 569.83 | 7.65 | 3/3 | 0 |
| | GBFS | 388 | 100% | 1,154 | 588.99 | 10.13 | 2/3 | 1 |
| 4. Emergency Outbreak | A* | 257 | 100% | 767 | 426.11 | 8.53 | 1/3 | 2 |
| | GBFS | 519 | 100% | 1,180 | 875.78 | 7.71 | 2/3 | 1 |

**Reading the results**

- A* tends to give shorter, more reliable routes (mean 8.40 vs 8.99 units), most visibly in Resource Detour where GBFS's greedy choices lead to detours.
- GBFS expands slightly fewer nodes per planning call in most scenarios, but on a graph of about 24 nodes this barely changes planning time, because building the visibility graph dominates each call.
- Rescue and infection counts depend on where survivors and zombies happen to meet, so treat them as scenario outcomes rather than evidence for one algorithm.
- Totals are not directly comparable per call: runs diverge and last different numbers of ticks, so GBFS can show more calls and nodes simply because the game ran longer.
- Each result is a single deterministic run. Planning times depend on machine load. For a stronger study, add repeated or randomized trials and report mean ± SD.

## Project structure

```
environment.py   Continuous geometry, obstacle checks, Euclidean distance
astar.py         Shared visibility graph, A* and GBFS
agents.py        Survivor and zombie state, per-agent metrics
adversarial.py   Depth-limited minimax with Alpha–Beta pruning
simulation.py    Movement, planner selection, zombie pursuit, collection, rescue, capture
scenarios.py     The four scenario configurations
metrics.py       Run-level planner, movement and tactical counters
gui.py           Tkinter visualization and controls
main.py          GUI, console and CSV comparison modes
test.py          Regression tests
comparison_results_sample.csv   Example comparison output
CHANGES.md       Change log
```

## GUI controls

- **Scenario selector:** choose one of the four scenarios.
- **Survivor path-planning algorithm:** `A*` or `GBFS` (changing it resets the scenario).
- **Play / Pause / Step / Reset** and an animation speed slider.
- **Performance panel:** live planner metrics, frozen when paused or finished; Reset starts fresh counters.

The A* vs GBFS comparison is intentionally a command-line feature, not a GUI button.

## Limitations

- The visibility graph assumes axis-aligned rectangular obstacles and a fixed agent radius; it is not a full configuration-space planner.
- Zombies always use A*, so results describe each planner as a *survivor* planner against an A* opponent.
- The Alpha–Beta evaluation has no wall or corner awareness, so threatened survivors sometimes flee toward map edges instead of toward extraction.
- Scenarios are deterministic and results are single runs; outcomes are not a guarantee that every survivor is rescued.
- Collected resources remain drawn on the map and can be shared between survivors.

## Possible extensions

- Add BFS, Dijkstra and Weighted A\* to compare uninformed, informed and greedy search.
- Let zombies use the selected planner as an option, for a second experiment.
- Penalize wall and corner positions in the tactical evaluation.
- Randomized starts with repeated trials and mean ± SD reporting.

## Testing

```bash
python test.py
```

The suite checks geometry and collision logic (including a brute-force cross-check of `segment_clear`), planner connectivity from key start points, movement limits, metric behaviour, and end-to-end outcomes for every scenario and both planners.
