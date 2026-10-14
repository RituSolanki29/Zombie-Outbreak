# Changes

## Continuous-space conversion
- Replaced integer cell coordinates with floating-point `(x, y)` positions.
- Replaced the discrete cell grid with a bounded 2D world and axis-aligned rectangular obstacles.
- Added Euclidean distance, sampled segment collision checks, and circle-radius interactions for resource pickup, rescue, and capture.
- Replaced grid A* with visibility-graph A* using Euclidean edge costs and a Euclidean heuristic.
- Replaced one-cell-per-turn motion with speed-limited continuous movement along route waypoints.
- Reworked near-threat survivor decisions to choose among sampled continuous steering directions.
- Rebuilt the Tkinter GUI for continuous geometry and route rendering.
- Reduced the scenario set to four: Normal Escape, Close Encounter, Resource Detour, Emergency Outbreak.
- Replaced grid-specific tests with continuous-space geometry, path, and movement checks.

## UI refresh (2026-10-13)
- Removed the on-screen event log completely to keep the dashboard focused on the simulation.
- Redesigned the Tkinter GUI as a dark survival-operations dashboard with a field map, terrain grid, worn paths, ruined-building details, supply markers, extraction beacon, route trails, and clearer survivor/zombie markers.
- Added compact mission telemetry and per-unit status cards, plus a scenario selector and streamlined playback controls.
- The underlying continuous-space simulation and four-scenario set are unchanged.

## Alpha-Beta and UI fixes (2026-10-13)
- Added recursive Minimax search with Alpha-Beta bounds over continuous steering actions and alternating survivor/zombie decisions.
- Added search-tree records for MAX/MIN nodes, scores, alpha/beta values, and pruned branches.
- Integrated adversarial action selection into the continuous simulation and added node/pruning metrics.
- Added GUI access to the Alpha-Beta search tree and a highlighted selected movement.
- Fixed scenario-selector foreground/background contrast so text remains readable.
- Expanded the regression suite to cover search-tree construction and pruning behavior.

## A* vs GBFS comparison study (2026-10-13)
- Added Greedy Best-First Search (GBFS) on the same visibility graph used by A*; GBFS prioritizes the Euclidean goal heuristic and does not guarantee minimum route length.
- Added a survivor path-planner selector to the GUI. Changing the selector resets the scenario; zombie navigation remains A* to keep the comparison focused on survivor planning.
- Added per-planner node expansion, planning time, successful planning calls and mean successful route-length metrics.
- Added a GUI comparison-study window that runs A* and GBFS across all four scenarios under identical scenario configurations.
- Added `python main.py --compare` to run both planners on all scenarios and export `comparison_results.csv` (or a user-specified path).
- Extended tests to verify GBFS routes, collision-free waypoints, planner selection and metrics collection.
- The batch comparison uses the same Alpha–Beta depth (2) for both planners so the multi-scenario study remains practical; interactive gameplay keeps the default depth 4.


## UI refinement
- Removed the fast-forward, Alpha–Beta search-tree, and GUI comparison-study buttons.
- Replaced Mission Telemetry with a Path-Planner Performance panel that updates for the selected A* or GBFS planner.
- Displayed metrics: selected algorithm, planning calls, planning success rate, nodes expanded, planning time, mean planned route length, survivor rescue rate, and infections.
- Kept the A* vs GBFS batch study available from the command line with `python main.py --compare`.

## Bug-fix review (2026-10-14)
- **Fixed `environment.segment_clear` (critical):** the parallel-slab test for exactly horizontal/vertical segments was inverted. Clear axis-aligned lines were reported as blocked (visibility graph became disconnected, A*/GBFS returned empty routes, ~5,000 of 20,000 random segments misjudged) and a segment lying inside a building's slab was treated as not colliding for that building.
- **Fixed survivor freezing:** with empty routes survivors stopped moving; planning now retries without the zombie-proximity waypoint filter if that filter disconnects the graph (same for zombie pathing).
- **Fixed head-on deadlock:** two survivors meeting in a corridor blocked each other permanently (`_safe_move`); survivors now sidestep (+/-45/90 deg) when blocked.
- **Fixed `_build_visibility_graph` early returns:** failure/identical-point returns had the wrong tuple shape (`start, goal, [], -1, -1`), which would raise a `TypeError` when unpacked and compared.
- **Docs:** repaired literal `\n` characters in README; regenerated the sample comparison CSV.
- **Tests:** added regression tests for axis-parallel collisions, brute-force collision cross-check, planner connectivity, and end-to-end scenario outcomes for both planners.
