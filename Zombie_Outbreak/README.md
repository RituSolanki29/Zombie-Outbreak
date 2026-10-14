# Zombie Outbreak — Continuous-Space Multi-Agent Simulator

A Python/Tkinter simulation of survivor navigation and zombie pursuit in a continuous two-dimensional environment. Survivors use a selectable path planner—**A* or Greedy Best-First Search (GBFS)**—while zombie navigation remains A* and nearby threat response continues to use Minimax with Alpha–Beta pruning.

## Features
- **Continuous world:** 15 × 15 coordinate plane, floating-point `(x, y)` positions, bounded-speed movement, rectangular obstacles and Euclidean-distance interactions.
- **Two selectable survivor path planners:**
  - **A*:** visibility-graph A* with `f(n) = g(n) + h(n)`, Euclidean edge costs and Euclidean heuristic.
  - **GBFS:** Greedy Best-First Search on the *same* visibility graph, prioritizing `h(n)` only. It can find routes quickly but does not guarantee the shortest geometric path.
- **Fairer comparison setup:** both planners use the same waypoints, collision checks, scenario configurations and initial conditions. Zombie navigation remains A* in both modes; Alpha–Beta tactical steering is shared.
- **Dynamic pursuit and avoidance:** survivors replan toward resources/rescue and use depth-limited Alpha–Beta minimax over sampled continuous steering actions when a zombie is close.
- **Distance-based interactions:** resource collection, rescue and capture use Euclidean-radius checks.
- **GUI:** continuous field map, scenario selector, A*/GBFS selector, playback controls, selected-algorithm performance metrics, and unit status. The on-screen event log is not shown.
- **Four scenarios:** Normal Escape, Close Encounter, Resource Detour and Emergency Outbreak.
- **Comparison study:** run all four scenarios under both planners and export a CSV containing planning nodes/time, mean planned route length, rescue outcomes, infection outcomes, and Alpha–Beta metrics. The batch comparison uses the same Alpha–Beta depth (2) for both planners to keep runtime practical and tactical settings controlled.

## Requirements
- Python 3.10+
- Tkinter (usually included with desktop Python)
- No third-party packages required

## Run
```bash
python main.py                                      # GUI (default survivor planner: A*)
python main.py --algorithm GBFS                      # GUI opens; use the GUI selector to choose the planner
python main.py --text --algorithm A*                 # run one scenario in the terminal with A*
python main.py --text --algorithm GBFS               # run one scenario in the terminal with GBFS
python main.py --all --algorithm A*                 # run all scenarios with A*
python main.py --all --algorithm GBFS               # run all scenarios with GBFS
python main.py --compare                             # compare both planners on all four scenarios
python main.py --compare --output results.csv        # choose CSV output path
python test.py                                       # regression tests
```

## GUI controls
- **Scenario selector:** choose one of the four scenarios.
- **Survivor path-planning algorithm:** select `A*` or `GBFS`; changing it resets the scenario.
- **Step / Play / Reset:** control the simulation.
- **Algorithm performance panel:** shows metrics for the currently selected survivor planner (A* or GBFS), updating as the simulation runs.
- **Command-line comparison study:** run `python main.py --compare` to compare both planners across all four scenarios and export CSV results; comparison is intentionally not a GUI button.

## Comparison methodology
- Only the **survivor global path planner** changes between A* and GBFS. Zombie path planning remains A* and the Alpha–Beta tactical controller is unchanged.
- Both planners search the same finite visibility graph made from the start, goal and clearance-offset obstacle-corner waypoints.
- A* prioritizes `g(n) + h(n)`; GBFS prioritizes `h(n)` only. Edge lengths are Euclidean.
- Reported metrics include survivor-planner nodes expanded, planning time, mean length of successful planned routes, route-planning success rate, survivors rescued, infections, ticks and total movement/wait cost.
- The batch comparison uses Alpha–Beta depth 2 for both planners; the interactive simulation retains the normal depth 4. Planning time is machine-load dependent. For a stronger study, run repeated trials and report mean and standard deviation. Since the current scenarios are deterministic, identical runs may produce the same outcomes apart from timing.
- GBFS does not guarantee a shortest geometric route because it ignores accumulated cost `g(n)`.

## Continuous-space model
- World bounds: `[0, 15] × [0, 15]`.
- Positions and waypoints are floating-point coordinate pairs `(x, y)`.
- Survivor movement speed: `0.32` world units/tick; zombie speed: `0.16` world units/tick.
- Collision clearance is checked along movement segments against axis-aligned rectangular obstacles.
- Capture, resource pickup and rescue use Euclidean radii.
- The world is continuous, while path planning searches a finite visibility graph of geometric waypoints.

## Four scenarios
1. **Normal Escape:** resource collection followed by navigation to rescue while zombies pursue.
2. **Close Encounter:** an initial nearby threat encourages evasive steering and replanning.
3. **Resource Detour:** separated targets and rectangular obstacles test geometric route planning.
4. **Emergency Outbreak:** a scripted infection at tick 45 converts a survivor into another zombie.

## Project layout
- `environment.py` — continuous geometry, obstacle checks and Euclidean distance.
- `astar.py` — shared visibility graph, A* and GBFS implementations.
- `agents.py` — survivor/zombie state and per-agent metrics.
- `adversarial.py` — depth-limited Minimax with Alpha–Beta pruning over continuous steering actions.
- `simulation.py` — continuous movement, selected survivor planner, zombie pursuit, collection, rescue and capture.
- `scenarios.py` — four scenario configurations.
- `gui.py` — Tkinter visualization, A*/GBFS selector, and selected-algorithm performance metrics.
- `metrics.py` — run-level planner, movement and tactical counters.
- `main.py` — GUI, console and CSV comparison modes.
- `test.py` — continuous geometry, planner and movement regression tests.
- `comparison_results_sample.csv` — example output from one A*/GBFS batch comparison; timings are specific to that run and machine.

## Limitations
The visibility graph is a finite geometric representation rather than a full continuous configuration-space planner for arbitrary moving shapes. Agents use simplified collision and threat models. Simulation results are outcomes for these scenarios, not a guarantee that every survivor is rescued.


## Metric update behavior
Performance counters are cumulative for the current run. They update when simulation steps execute and remain frozen when the simulation is paused or reaches a terminal state. Reset starts a fresh set of counters.
