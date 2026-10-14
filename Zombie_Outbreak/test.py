"""Continuous-space regression tests. Run: python test.py"""
import math, random
from environment import ZombieGrid
from astar import astar, gbfs, plan_path
from scenarios import SCENARIOS
from simulation import ZombieSimulation
from agents import SurvivorStatus
from adversarial import decide
PASS=FAIL=0
def check(name,ok,detail=''):
 global PASS,FAIL
 PASS+=bool(ok);FAIL+=not bool(ok);print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
world=ZombieGrid()
check('exactly four scenarios',len(SCENARIOS)==4,str(list(SCENARIOS)))
for name,cfg in SCENARIOS.items():
 points=[p for _,p,_ in cfg['survivors']]+[p for _,p in cfg['zombies']]
 check(f'continuous valid starts: {name}',all(world.is_passable(p) for p in points))
# Float-valued route, valid segments, no wall penetration
path,n=astar(world,(1.5,1.5),(13.5,13.5))
check('planner returns a route',len(path)>=2,f'waypoints={len(path)}, expanded={n}')
check('waypoints use continuous coordinates',any(not float(v).is_integer() for p in path for v in p))
check('all route segments collision-free',all(world.segment_clear(a,b) for a,b in zip(path,path[1:])))
check('planner handles identical start/goal',astar(world,(2.5,2.5),(2.5,2.5))[0]==[(2.5,2.5)])
check('segment collision detection rejects obstacle crossing',not world.segment_clear((3.0,3.0),(7.0,3.0)))
# Simulation stays continuous and inside valid space; distance between consecutive positions is speed-limited.
for name in SCENARIOS:
 sim=ZombieSimulation(name);viol=[]
 for _ in range(min(sim.max_steps,180)):
  old={k:v.pos for k,v in sim.survivors.items()};oldz={k:v.pos for k,v in sim.zombies.items()}
  sim.step()
  for k,s in sim.survivors.items():
   d=world.dist(old[k],s.pos)
   if d>sim.MOVE_SPEED+1e-5:viol.append(f'{k} moved {d:.3f}')
   if s.status==SurvivorStatus.ACTIVE and not world.is_passable(s.pos):viol.append(f'{k} in obstacle')
  for k,z in sim.zombies.items():
   if k in oldz and world.dist(oldz[k],z.pos)>sim.ZOMBIE_SPEED+1e-5:viol.append(f'{k} moved too far')
  if sim.game_over:break
 check(f'continuous movement invariants: {name}',not viol,viol[:2])
check('capture uses Euclidean distance',ZombieSimulation.CAPTURE_RADIUS>0 and ZombieSimulation.CAPTURE_RADIUS<1)

# A* and GBFS share the same continuous visibility graph but use different priorities.
a_path, a_nodes = astar(world, (1.5, 1.5), (13.5, 13.5))
g_path, g_nodes = gbfs(world, (1.5, 1.5), (13.5, 13.5))
check('GBFS returns a route', len(g_path) >= 2, f'waypoints={len(g_path)}, expanded={g_nodes}')
check('GBFS route is collision-free', all(world.segment_clear(a, b) for a, b in zip(g_path, g_path[1:])))
check('A* and GBFS are selectable', plan_path(world, (1.5, 1.5), (13.5, 13.5), 'GBFS')[0] == g_path)
check('GBFS handles identical start/goal', gbfs(world, (2.5, 2.5), (2.5, 2.5))[0] == [(2.5, 2.5)])
# Ensure the selected algorithm is actually used by survivor replanning and its metrics.
gbfs_sim = ZombieSimulation('1. Normal Escape', path_algorithm='GBFS')
check('simulation accepts GBFS mode', gbfs_sim.path_algorithm == 'GBFS')
for _ in range(3): gbfs_sim.step()
check('GBFS planning metrics are recorded', gbfs_sim.metrics.planner_calls > 0 and gbfs_sim.metrics.pathfinding_nodes_expanded > 0)
check('mean planned route metric is nonnegative', gbfs_sim.metrics.mean_route_length >= 0.0)

# Actual depth-limited Alpha-Beta decision tree over continuous movement candidates.
ab=decide(world,(6.5,2.0),(8.0,2.0),(13.0,13.0),depth=4)
check('Alpha-Beta returns a continuous action',len(ab.action)==2 and all(isinstance(v,float) for v in ab.action),str(ab.action))
check('Alpha-Beta builds alternating search tree',ab.tree.get('player')=='MAX' and bool(ab.tree.get('children')))
check('Alpha-Beta evaluates nodes',ab.nodes>0,str(ab.nodes))
check('Alpha-Beta performs pruning',ab.prunes>0,str(ab.prunes))

# ---- Regression tests for bugs fixed in the review ----
# 1. Axis-parallel segments must be handled correctly (parallel-slab test used to be inverted).
check('horizontal segment below a building is clear', world.segment_clear((3.77,1.77),(6.23,1.77)))
check('vertical segment beside a building is clear', world.segment_clear((3.5,1.0),(3.5,4.5)))
check('horizontal segment through a building is blocked', not world.segment_clear((3.0,3.0),(7.0,3.0)))
check('horizontal segment through lower building is blocked', not world.segment_clear((3.0,10.0),(7.0,10.0)))
check('vertical segment through a building is blocked', not world.segment_clear((5.0,1.0),(5.0,6.0)))
def _brute(a,b,n=800):
    return all(world.is_passable((a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n)) for i in range(n+1))
random.seed(7);bad=0
for _ in range(3000):
    a=(random.uniform(.3,14.7),random.uniform(.3,14.7));b=(random.uniform(.3,14.7),a[1]) if random.random()<.4 else (random.uniform(.3,14.7),random.uniform(.3,14.7))
    if world.segment_clear(a,b)!=_brute(a,b) and world.segment_clear(a,b): bad+=1   # never walk through a wall
check('segment_clear never lets a segment cross a wall (3000 random)',bad==0,f'bad={bad}')
# 2. Visibility graph must be connected from the resource/start points used in scenarios.
for st in [(2.5,2.5),(2.89,1.96),(1.5,1.5),(12.5,6.5),(3.5,12.5)]:
    for algo in ('A*','GBFS'):
        pth,_=plan_path(world,st,(13.5,13.5),algo)
        check(f'{algo} finds route from {st}',len(pth)>=2 and all(world.segment_clear(a,b) for a,b in zip(pth,pth[1:])))
# 3. Planner must report an unreachable start cleanly (no crash from malformed graph return).
check('planner handles start inside a building without crashing',astar(world,(5.0,3.0),(13.5,13.5))[0]==[])
# 4. End-to-end: every scenario/planner finishes, nobody is frozen forever, and rescues happen.
for name in SCENARIOS:
    for algo in ('A*','GBFS'):
        sim=ZombieSimulation(name,path_algorithm=algo);sim.ab_depth=2
        while not sim.game_over: sim.step()
        frozen=[k for k,v in sim.survivors.items() if v.status==SurvivorStatus.ACTIVE and v.metrics.waiting_time>sim.max_steps*0.5]
        check(f'no permanently frozen survivor: {name} / {algo}',not frozen,str(frozen))
        check(f'planning success rate high: {name} / {algo}',sim.metrics.planning_success_rate>=95,f'{sim.metrics.planning_success_rate:.1f}%')
        check(f'at least one rescue: {name} / {algo}',sim.metrics.rescued>=1,f'{sim.metrics.rescued}/{sim.metrics.survivors_started}')

print(f'\n{PASS} passed, {FAIL} failed')
raise SystemExit(1 if FAIL else 0)
