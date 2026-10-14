from __future__ import annotations
import argparse
import csv
from pathlib import Path
from scenarios import SCENARIOS
from simulation import ZombieSimulation


def run_to_end(name, algorithm='A*'):
    sim = ZombieSimulation(name, path_algorithm=algorithm)
    while not sim.game_over:
        sim.step()
    return sim


def text_mode(args):
    sim = ZombieSimulation(args.scenario, path_algorithm=args.algorithm)
    while not sim.game_over:
        print(f'\nTick {sim.time_step}/{sim.max_steps} | Survivor planner: {sim.path_algorithm}')
        for sid, survivor in sim.survivors.items():
            target = sim.current_target(survivor) if survivor.status.value == 'Active' else '—'
            print(f'{sid}: ({survivor.pos[0]:.2f}, {survivor.pos[1]:.2f}) | {survivor.status.value} | target={target}')
        print('Zombies:', ', '.join(f'{z.zid}@({z.pos[0]:.2f},{z.pos[1]:.2f})' for z in sim.zombies.values()))
        sim.step()
    print('\n'.join(sim.events[-15:]))
    m = sim.metrics
    print(f'\nAlgorithm: {sim.path_algorithm} | Rescued: {m.rescued}/{m.survivors_started} | infected: {m.survivors_infected}')
    print(f'Planner nodes: {m.pathfinding_nodes_expanded} | planner time: {m.pathfinding_time_ms:.2f} ms | '
          f'mean planned route: {m.mean_route_length:.2f} | plan success: {m.planning_success_rate:.1f}%')
    print(f'Alpha-Beta nodes: {m.alpha_beta_nodes} | pruned branches: {m.alpha_beta_prunes} | '
          f'distance/wait cost: {m.total_cost:.2f}')


def batch_mode(algorithm='A*'):
    print(f"Algorithm: {algorithm}")
    print(f"{'Scenario':25s}{'Ticks':>7s}{'Rescued':>10s}{'Infected':>10s}{'Plan nodes':>13s}{'Plan ms':>12s}{'Mean route':>13s}")
    for name in SCENARIOS:
        sim = run_to_end(name, algorithm)
        m = sim.metrics
        print(f'{name:25s}{sim.time_step:7d}{f"{m.rescued}/{m.survivors_started}":>10s}{m.survivors_infected:10d}'
              f'{m.pathfinding_nodes_expanded:13d}{m.pathfinding_time_ms:12.2f}{m.mean_route_length:13.2f}')


def compare_mode(output_path='comparison_results.csv'):
    rows = []
    print('\nA* vs Greedy Best-First Search (GBFS) — survivor path-planning comparison')
    print(f"{'Scenario':24s}{'Algorithm':>10s}{'Ticks':>7s}{'Rescued':>10s}{'Infected':>9s}{'Nodes':>12s}{'Plan ms':>12s}{'Mean route':>12s}")
    for algorithm in ('A*', 'GBFS'):
        for name in SCENARIOS:
            sim = ZombieSimulation(name, path_algorithm=algorithm)
            # Keep tactical decision cost controlled and identical for both planners.
            sim.ab_depth = 2
            while not sim.game_over:
                sim.step()
            m = sim.metrics
            row = {
                'scenario': name, 'algorithm': algorithm, 'ticks': sim.time_step,
                'survivors_started': m.survivors_started, 'rescued': m.rescued,
                'rescue_rate_percent': round(m.survival_rate, 2), 'infected': m.survivors_infected,
                'planner_calls': m.planner_calls, 'planning_success_rate_percent': round(m.planning_success_rate, 2),
                'pathfinding_nodes_expanded': m.pathfinding_nodes_expanded,
                'pathfinding_time_ms': round(m.pathfinding_time_ms, 3),
                'mean_route_length': round(m.mean_route_length, 4),
                'alpha_beta_nodes': m.alpha_beta_nodes, 'alpha_beta_prunes': m.alpha_beta_prunes,
                'distance_wait_cost': round(m.total_cost, 3),
            }
            rows.append(row)
            print(f"{name:24s}{algorithm:>10s}{sim.time_step:7d}{f'{m.rescued}/{m.survivors_started}':>10s}"
                  f'{m.survivors_infected:9d}{m.pathfinding_nodes_expanded:12d}{m.pathfinding_time_ms:12.2f}{m.mean_route_length:12.2f}')
    path = Path(output_path)
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    print(f'\nCSV results saved to: {path.resolve()}')
    print('Interpret timing cautiously; run repeated trials if random behavior or system load affects results.')


def main():
    parser = argparse.ArgumentParser(description='Continuous-space zombie survival simulator with A* / GBFS comparison')
    parser.add_argument('--text', action='store_true', help='run one scenario in the console')
    parser.add_argument('--all', action='store_true', help='run all four scenarios with the selected planner')
    parser.add_argument('--compare', action='store_true', help='run A* and GBFS on all four scenarios and export CSV')
    parser.add_argument('--output', default='comparison_results.csv', help='CSV path for --compare')
    parser.add_argument('--algorithm', choices=('A*', 'GBFS'), default='A*', help='survivor path-planning algorithm')
    parser.add_argument('--scenario', choices=list(SCENARIOS), default='1. Normal Escape')
    args = parser.parse_args()
    if args.compare:
        compare_mode(args.output)
    elif args.all:
        batch_mode(args.algorithm)
    elif args.text:
        text_mode(args)
    else:
        from gui import main as gui_main
        gui_main(args.algorithm)


if __name__ == '__main__':
    main()
