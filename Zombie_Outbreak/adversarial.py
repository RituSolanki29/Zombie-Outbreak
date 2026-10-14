"""Continuous-space adversarial movement using depth-limited Alpha-Beta minimax.

MAX is the survivor, which prefers to stay far from the zombie and move toward
its target. MIN is the zombie, which chooses a legal continuous move that
minimizes the survivor's evaluation. Candidate actions are sampled steering
vectors; positions themselves remain floating-point coordinates.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from math import cos, sin, radians
from typing import Any

@dataclass
class DecisionResult:
    action: tuple[float, float]
    score: float
    nodes: int = 0
    prunes: int = 0
    depth: int = 0
    tree: dict[str, Any] = field(default_factory=dict)
    pv: list = field(default_factory=list)


def _actions(world, pos, speed, blocked=(), count=12):
    """Generate collision-free continuous candidate positions."""
    result = []
    for i in range(count):
        angle = radians(i * 360.0 / count)
        q = (pos[0] + speed*cos(angle), pos[1] + speed*sin(angle))
        if world.is_passable(q) and world.segment_clear(pos, q) and all(world.dist(q, b) > .42 for b in blocked):
            result.append(q)
    # A stationary action avoids crashing into a corner with no legal moves.
    result.append(tuple(pos))
    return result


def decide(world, survivor_pos, zombie_pos, target, depth=4, blocked=(), static_zombies=(), prefer=None):
    """Return a survivor move chosen with real Alpha-Beta pruning.

    `depth` is the number of alternating MAX/MIN plies. The tree contains
    evaluated and pruned nodes so the GUI can render the actual search.
    """
    survivor_speed = .32
    zombie_speed = .16
    max_depth = max(2, int(depth))
    nodes = 0
    prunes = 0

    def evaluate(sp, zp):
        nearest = min([world.dist(sp, zp)] + [world.dist(sp, z) for z in static_zombies])
        progress = world.dist(sp, target)
        # Distance from threat dominates, but progress prevents aimless fleeing.
        return 2.6 * nearest - 1.15 * progress

    def legal_survivor(sp):
        moves = _actions(world, sp, survivor_speed, blocked=blocked, count=12)
        if prefer and world.is_passable(prefer) and world.segment_clear(sp, prefer):
            if world.dist(sp, prefer) <= survivor_speed * 1.6:
                moves.append(tuple(prefer))
        # Stable deduplication and prioritization by proximity to target.
        uniq = list(dict.fromkeys((round(x, 5), round(y, 5)) for x, y in moves))
        return [tuple(q) for q in sorted(uniq, key=lambda q: world.dist(q, target))]

    def legal_zombie(zp, sp):
        # The zombie can choose any collision-free steering direction. Sorting
        # by closeness to survivor improves pruning without changing semantics.
        moves = _actions(world, zp, zombie_speed, blocked=(), count=12)
        uniq = list(dict.fromkeys((round(x, 5), round(y, 5)) for x, y in moves))
        return [tuple(q) for q in sorted(uniq, key=lambda q: world.dist(q, sp))]

    root = {'label': 'Survivor (MAX)', 'player': 'MAX', 'children': [], 'value': None, 'pruned': False}

    def search(sp, zp, ply, alpha, beta, node):
        nonlocal nodes, prunes
        nodes += 1
        if ply >= max_depth:
            value = evaluate(sp, zp)
            node.update(label=f'Eval {value:.2f}', value=value)
            return value, sp
        maximizing = ply % 2 == 0
        node['player'] = 'MAX' if maximizing else 'MIN'
        node['label'] = 'Survivor (MAX)' if maximizing else 'Zombie (MIN)'
        actions = legal_survivor(sp) if maximizing else legal_zombie(zp, sp)
        if not actions:
            value = evaluate(sp, zp)
            node.update(label=f'No moves · {value:.2f}', value=value)
            return value, sp
        best_value = float('-inf') if maximizing else float('inf')
        best_action = sp
        for idx, action in enumerate(actions):
            child = {'label': f'{"S" if maximizing else "Z"} → ({action[0]:.1f}, {action[1]:.1f})',
                     'player': 'MAX' if maximizing else 'MIN', 'move': action,
                     'children': [], 'value': None, 'pruned': False}
            node['children'].append(child)
            if maximizing:
                value, first_move = search(action, zp, ply + 1, alpha, beta, child)
                if value > best_value:
                    best_value, best_action = value, action if ply == 0 else first_move
                alpha = max(alpha, best_value)
            else:
                value, first_move = search(sp, action, ply + 1, alpha, beta, child)
                if value < best_value:
                    best_value, best_action = value, first_move
                beta = min(beta, best_value)
            child['value'] = value
            if alpha >= beta:
                remaining = actions[idx+1:]
                if remaining:
                    prunes += len(remaining)
                    child['cutoff'] = True
                    for skipped in remaining:
                        node['children'].append({'label': f'PRUNED {"S" if maximizing else "Z"} → ({skipped[0]:.1f}, {skipped[1]:.1f})',
                            'player': 'MAX' if maximizing else 'MIN', 'move': skipped,
                            'children': [], 'value': None, 'pruned': True})
                break
        node['value'] = best_value
        node['alpha'] = alpha
        node['beta'] = beta
        return best_value, best_action

    score, action = search(tuple(survivor_pos), tuple(zombie_pos), 0, float('-inf'), float('inf'), root)
    root['value'] = score
    root['alpha'] = score
    root['beta'] = None
    return DecisionResult(tuple(action), score, nodes, prunes, max_depth, root, [tuple(action)])
