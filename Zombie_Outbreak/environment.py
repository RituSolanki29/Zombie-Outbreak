from __future__ import annotations
from dataclasses import dataclass
from math import hypot
from typing import Dict, Tuple, Iterable

Coord = Tuple[float, float]  # (x, y), continuous world coordinates
WORLD_MIN, WORLD_MAX = 0.0, 15.0
AGENT_RADIUS = 0.16
CLEARANCE = 0.20

@dataclass(frozen=True)
class Resource:
    name: str
    pos: Coord

class ZombieGrid:
    """Continuous 15x15 world. Obstacles are axis-aligned rectangles; positions are floats."""
    RESOURCE_POSITIONS = {"Food": (2.5, 2.5), "Water": (12.5, 6.5), "Medicine": (3.5, 12.5)}
    SAFE_POS: Coord = (13.5, 13.5)
    def __init__(self, rows=15, cols=15, extra_walls: Iterable=()):
        self.rows, self.cols = float(rows), float(cols)
        self.safe_pos = self.SAFE_POS
        self.obstacles = [(4.0,2.0,6.0,5.0),(9.0,2.0,10.0,4.0),(2.0,5.0,4.0,7.0),
                          (7.0,5.0,9.0,7.0),(4.0,9.0,6.0,11.0),(9.0,9.0,11.0,11.0)]
        # Legacy extra_walls are interpreted as unit squares centered on integer coordinates.
        for item in extra_walls:
            if len(item)==2:
                y,x=item; self.obstacles.append((x-.5,y-.5,x+.5,y+.5))
            else: self.obstacles.append(tuple(map(float,item)))
        self.resources = {n: Resource(n, tuple(map(float,xy))) for n,xy in self.RESOURCE_POSITIONS.items()}
    def dist(self, a: Coord, b: Coord) -> float: return hypot(a[0]-b[0], a[1]-b[1])
    def is_passable(self, pos: Coord, radius=AGENT_RADIUS) -> bool:
        x,y=pos
        if x < radius or y < radius or x > self.cols-radius or y > self.rows-radius: return False
        return not any(x1-radius <= x <= x2+radius and y1-radius <= y <= y2+radius for x1,y1,x2,y2 in self.obstacles)
    def segment_clear(self, a: Coord, b: Coord, radius=AGENT_RADIUS) -> bool:
        # Exact segment-vs-expanded-AABB test (clearance for circular agents).
        if not self.is_passable(a, radius) or not self.is_passable(b, radius): return False
        ax, ay = a; bx, by = b; dx, dy = bx-ax, by-ay
        for x1,y1,x2,y2 in self.obstacles:
            lo_x, hi_x = x1-radius, x2+radius
            lo_y, hi_y = y1-radius, y2+radius
            t0, t1 = 0.0, 1.0
            for origin, delta, low, high in ((ax,dx,lo_x,hi_x),(ay,dy,lo_y,hi_y)):
                if abs(delta) < 1e-12:
                    # Segment is parallel to this slab: it can only hit the box if it lies inside the slab.
                    if low <= origin <= high: continue
                    t0, t1 = 1.0, 0.0; break
                t_enter=(low-origin)/delta; t_exit=(high-origin)/delta
                if t_enter>t_exit: t_enter,t_exit=t_exit,t_enter
                t0=max(t0,t_enter); t1=min(t1,t_exit)
                if t0>t1: break
            if t0 <= t1 and t1 >= 0.0 and t0 <= 1.0: return False
        return True
    def nearest_clear(self, pos: Coord) -> Coord:
        if self.is_passable(pos): return pos
        for r in range(1,100):
            for dx in range(-r,r+1):
                for dy in range(-r,r+1):
                    q=(pos[0]+dx*.05,pos[1]+dy*.05)
                    if self.is_passable(q): return q
        return (1.0,1.0)
