from __future__ import annotations
import heapq, math
from typing import Callable, Optional, Tuple

Coord = Tuple[float, float]


def heuristic(a: Coord, b: Coord) -> float:
    """Euclidean distance: admissible for Euclidean visibility-graph edge costs."""
    return math.dist(a, b)


def _build_visibility_graph(world, start: Coord, goal: Coord, blocked=None):
    start = tuple(map(float, start)); goal = tuple(map(float, goal))
    blocked = list(blocked or [])
    if world.dist(start, goal) < 1e-7:
        return [start], [[]], 0, 0, 1
    eps = .23
    nodes = [start, goal]
    for x1, y1, x2, y2 in world.obstacles:
        nodes.extend([(x1-eps, y1-eps), (x1-eps, y2+eps),
                      (x2+eps, y1-eps), (x2+eps, y2+eps)])
    nodes = [q for q in nodes if world.is_passable(q) or q in (start, goal)]
    nodes = [q for q in nodes if q in (start, goal) or all(world.dist(q, b) > 0.42 for b in blocked)]
    # Preserve start/goal even if equal coordinates were deduplicated.
    unique = []
    for q in nodes:
        if q not in unique: unique.append(q)
    nodes = unique
    if start not in nodes or goal not in nodes:
        return [], [], -1, -1, 0
    idx = {q: i for i, q in enumerate(nodes)}
    si, gi = idx[start], idx[goal]
    adj = [[] for _ in nodes]
    for i, a in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            b = nodes[j]
            if world.segment_clear(a, b):
                distance = world.dist(a, b)
                adj[i].append((j, distance)); adj[j].append((i, distance))
    return nodes, adj, si, gi, len(nodes)


def _route_length(world, path):
    return sum(world.dist(a, b) for a, b in zip(path, path[1:]))


def astar(world, start: Coord, goal: Coord, blocked=None,
          extra_cost: Optional[Callable] = None, max_nodes=10000):
    """A* on the continuous-space visibility graph.

    Priority: f(n) = g(n) + h(n). Returns (waypoint_path, expanded_nodes).
    """
    start = tuple(map(float, start)); goal = tuple(map(float, goal))
    if world.dist(start, goal) < 1e-7:
        return [start], 0
    built = _build_visibility_graph(world, start, goal, blocked)
    nodes, adj, si, gi, _ = built
    if si < 0:
        return [], 0
    heap = [(heuristic(nodes[si], nodes[gi]), 0.0, si)]
    came = {si: None}; g = {si: 0.0}; expanded = 0
    while heap and expanded < max_nodes:
        _, cost, u = heapq.heappop(heap)
        if abs(cost - g.get(u, float('inf'))) > 1e-8:
            continue
        expanded += 1
        if u == gi:
            path = []; k = u
            while k is not None:
                path.append(nodes[k]); k = came[k]
            return path[::-1], expanded
        for v, distance in adj[u]:
            edge_cost = distance + (extra_cost(nodes[v]) if extra_cost else 0.0)
            ng = cost + edge_cost
            if ng < g.get(v, float('inf')):
                g[v] = ng; came[v] = u
                heapq.heappush(heap, (ng + heuristic(nodes[v], nodes[gi]), ng, v))
    return [], expanded


def gbfs(world, start: Coord, goal: Coord, blocked=None, max_nodes=10000):
    """Greedy Best-First Search on the exact same visibility graph as A*.

    Priority: h(n) only. It can find a valid route quickly, but does not
    guarantee minimum geometric path length because it ignores g(n).
    Returns (waypoint_path, expanded_nodes).
    """
    start = tuple(map(float, start)); goal = tuple(map(float, goal))
    if world.dist(start, goal) < 1e-7:
        return [start], 0
    nodes, adj, si, gi, _ = _build_visibility_graph(world, start, goal, blocked)
    if si < 0:
        return [], 0
    counter = 0
    heap = [(heuristic(nodes[si], nodes[gi]), counter, si)]
    came = {si: None}; discovered = {si}; expanded = 0
    while heap and expanded < max_nodes:
        _, _, u = heapq.heappop(heap)
        expanded += 1
        if u == gi:
            path = []; k = u
            while k is not None:
                path.append(nodes[k]); k = came[k]
            return path[::-1], expanded
        # Sort by heuristic for deterministic tie behavior, without using g-cost.
        for v, _distance in sorted(adj[u], key=lambda edge: (heuristic(nodes[edge[0]], nodes[gi]), edge[0])):
            if v in discovered:
                continue
            discovered.add(v); came[v] = u; counter += 1
            heapq.heappush(heap, (heuristic(nodes[v], nodes[gi]), counter, v))
    return [], expanded


def plan_path(world, start: Coord, goal: Coord, algorithm='A*', blocked=None):
    """Shared selector for survivor navigation. Zombies can remain on A* as a control."""
    normalized = algorithm.strip().upper().replace('GREEDY BEST-FIRST SEARCH', 'GBFS').replace('GREEDY BEST FIRST SEARCH', 'GBFS')
    if normalized in ('GBFS', 'GREEDY BEST-FIRST', 'GREEDY BEST FIRST'):
        return gbfs(world, start, goal, blocked=blocked)
    if normalized in ('A*', 'ASTAR', 'A STAR'):
        return astar(world, start, goal, blocked=blocked)
    raise ValueError(f'Unsupported path-planning algorithm: {algorithm!r}')
