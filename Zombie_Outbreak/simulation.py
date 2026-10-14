from __future__ import annotations
import math, time
from typing import Dict, List, Optional, Tuple
from agents import Survivor, SurvivorStatus, Zombie, ZombieStatus
from astar import astar, plan_path
from environment import ZombieGrid, AGENT_RADIUS
from metrics import SimulationMetrics
from scenarios import SCENARIOS
Coord=Tuple[float,float]

class ZombieSimulation:
    """Continuous-space simulator. Each tick moves agents by a bounded distance."""
    MOVE_SPEED=.32
    ZOMBIE_SPEED=.16
    CAPTURE_RADIUS=.28
    RESOURCE_RADIUS=.30
    RESCUE_RADIUS=.38
    DANGER_RADIUS=2.8
    AB_DEPTH=4
    def __init__(self, scenario_name='1. Normal Escape', path_algorithm='A*'):
        self.scenario_name=scenario_name; self.path_algorithm=self._normalize_algorithm(path_algorithm); self.ab_depth=self.AB_DEPTH; self.time_step=0; self.max_steps=260
        self.game_over=False; self.events=[]; self.metrics=SimulationMetrics(); self.survivors={}; self.zombies={}; self.selected='S1'; self.last_decisions={}; self._scripted=None
        self.reset(scenario_name)
    @staticmethod
    def _normalize_algorithm(algorithm):
        value = str(algorithm).strip().upper()
        if value in ('A*', 'ASTAR', 'A STAR'): return 'A*'
        if value in ('GBFS', 'GREEDY BEST-FIRST SEARCH', 'GREEDY BEST FIRST SEARCH'): return 'GBFS'
        raise ValueError(f'Unsupported path-planning algorithm: {algorithm!r}')

    def reset(self,scenario_name=None,path_algorithm=None):
        if scenario_name: self.scenario_name=scenario_name
        if path_algorithm is not None: self.path_algorithm=self._normalize_algorithm(path_algorithm)
        cfg=SCENARIOS[self.scenario_name]; self.grid=ZombieGrid(); self.max_steps=cfg['time_limit']; self.time_step=0; self.game_over=False; self.events=[]; self.last_decisions={}; self._scripted=cfg.get('infection')
        self.survivors={sid:Survivor(sid,tuple(map(float,pos)),self.grid.safe_pos,res) for sid,pos,res in cfg['survivors']}
        self.zombies={zid:Zombie(zid,tuple(map(float,pos))) for zid,pos in cfg['zombies']}
        self.metrics=SimulationMetrics(survivors_started=len(self.survivors),zombies_started=len(self.zombies))
        self.log('Simulation started: '+self.scenario_name); self.log(cfg['description'])
        for s in self.active_survivors(): self.plan_survivor(s,count=False)
    def log(self,msg):
        self.events.append(f'[{self.time_step:03d}] {msg}'); self.events=self.events[-300:]
    def active_survivors(self): return [s for s in self.survivors.values() if s.status==SurvivorStatus.ACTIVE]
    def active_zombies(self): return [z for z in self.zombies.values() if z.status==ZombieStatus.HUNTING]
    def current_target(self,s): return self.grid.resources[s.resource_target].pos if s.resource_target else self.grid.safe_pos
    def plan_survivor(self,s,count=True):
        if s.status!=SurvivorStatus.ACTIVE:return
        target=self.current_target(s); t0=time.perf_counter()
        path,nodes=plan_path(self.grid,s.pos,target,algorithm=self.path_algorithm,
                             blocked=[z.pos for z in self.active_zombies()])
        if not path:
            # Zombie-avoidance filtering can disconnect the waypoint graph; retry unfiltered
            # so the survivor still has a route (tactical steering handles the threat).
            path,extra=plan_path(self.grid,s.pos,target,algorithm=self.path_algorithm)
            nodes+=extra
        elapsed=(time.perf_counter()-t0)*1000; s.path=path; s.path_index=1
        if count:
            s.metrics.nodes_expanded+=nodes;s.metrics.decision_time_ms+=elapsed;s.metrics.replans+=1
            self.metrics.nodes_expanded+=nodes;self.metrics.replans+=1;self.metrics.decision_time_ms+=elapsed
            self.metrics.planner_calls+=1
            self.metrics.pathfinding_nodes_expanded+=nodes
            self.metrics.pathfinding_time_ms+=elapsed
            if path:
                self.metrics.planner_successes+=1
                self.metrics.route_length_sum+=sum(self.grid.dist(a,b) for a,b in zip(path,path[1:]))
    def _move_towards(self,pos,target,speed):
        d=self.grid.dist(pos,target)
        if d<=speed:return tuple(target)
        q=(pos[0]+(target[0]-pos[0])*speed/d,pos[1]+(target[1]-pos[1])*speed/d)
        return q if self.grid.segment_clear(pos,q) else pos
    def _safe_move(self,agent,dest,others,goal=None):
        def ok(q): return self.grid.segment_clear(agent.pos,q) and not any(self.grid.dist(q,o.pos)<AGENT_RADIUS*2 for o in others)
        if ok(dest): return dest
        if goal is None: return agent.pos
        # Blocked by a wall corner or another unit: sidestep (+/-45/90 deg off the heading)
        # so two agents meeting head-on in a corridor cannot deadlock forever.
        hx,hy=dest[0]-agent.pos[0],dest[1]-agent.pos[1]; step=math.hypot(hx,hy)
        if step<1e-9: return agent.pos
        base=math.atan2(hy,hx); best=None
        for off in (45,-45,90,-90):
            a=base+math.radians(off); q=(agent.pos[0]+step*math.cos(a),agent.pos[1]+step*math.sin(a))
            if ok(q):
                d=self.grid.dist(q,goal)
                if best is None or d<best[0]: best=(d,q)
        return best[1] if best else agent.pos
    def step(self):
        if self.game_over:return
        self.time_step+=1
        if self._scripted and self.time_step==self._scripted['step']: self.infect_survivor(self._scripted['sid'],'scripted outbreak')
        # Survivors move continuously along visibility-graph waypoints, with local threat steering.
        for s in list(self.active_survivors()):
            self.plan_survivor(s)
            if not s.path: continue
            target=self.current_target(s)
            waypoint=s.path[1] if len(s.path)>1 else target
            zombies=self.active_zombies()
            if zombies:
                nearest=min(zombies,key=lambda z:self.grid.dist(s.pos,z.pos))
                if self.grid.dist(s.pos,nearest.pos)<=self.DANGER_RADIUS:
                    from adversarial import decide
                    others=[z.pos for z in zombies if z.zid!=nearest.zid]
                    result=decide(self.grid,s.pos,nearest.pos,target,depth=self.ab_depth,blocked=[o.pos for o in self.active_survivors() if o.sid!=s.sid],static_zombies=others,prefer=waypoint)
                    self.last_decisions[s.sid]=(self.time_step,nearest.zid,result)
                    self.metrics.steering_calls+=1;self.metrics.steering_candidates+=result.nodes;self.metrics.nodes_expanded+=result.nodes;self.metrics.alpha_beta_nodes+=result.nodes;self.metrics.alpha_beta_prunes+=result.prunes
                    waypoint=result.action
            dest=self._move_towards(s.pos,waypoint,self.MOVE_SPEED)
            others=[o for o in self.active_survivors() if o.sid!=s.sid]
            dest=self._safe_move(s,dest,others,goal=waypoint)
            moved=self.grid.dist(s.pos,dest); s.position_history=(s.position_history+[s.pos])[-12:]; s.pos=dest;s.metrics.path_length+=moved
            if moved<1e-8: s.metrics.waiting_time+=1;self.metrics.waiting_time+=1
            if s.resource_target and self.grid.dist(s.pos,self.grid.resources[s.resource_target].pos)<=self.RESOURCE_RADIUS:
                name=s.resource_target;s.resources=1;s.resource_target=None;s.target=self.grid.safe_pos;self.log(f'{s.sid} collected {name}; heading to rescue')
            if not s.resource_target and self.grid.dist(s.pos,self.grid.safe_pos)<=self.RESCUE_RADIUS:
                s.status=SurvivorStatus.RESCUED;self.metrics.rescued+=1;self.log(f'{s.sid} reached rescue point')
        # Zombies independently pursue closest active survivors using continuous A* paths.
        for z in list(self.active_zombies()):
            survivors=self.active_survivors()
            if not survivors: z.path=[];continue
            target=min(survivors,key=lambda s:self.grid.dist(z.pos,s.pos));z.target_sid=target.sid
            path,n=astar(self.grid,z.pos,target.pos,blocked=[s.pos for s in survivors if s.sid!=target.sid])
            if not path:
                path,extra=astar(self.grid,z.pos,target.pos); n+=extra
            self.metrics.zombie_nodes+=n;z.metrics.nodes_expanded+=n
            z.path=path
            if len(path)>1:
                waypoint=path[1];dest=self._move_towards(z.pos,waypoint,self.ZOMBIE_SPEED)
                otherz=[o for o in self.active_zombies() if o.zid!=z.zid]
                dest=self._safe_move(z,dest,otherz);z.pos=dest
            for s in list(self.active_survivors()):
                if self.grid.dist(z.pos,s.pos)<=self.CAPTURE_RADIUS:
                    self.infect_survivor(s.sid,f'{z.zid} came within capture radius');break
        self._update_metrics()
        if self.time_step>=self.max_steps or not self.active_survivors():self.finish()
    def infect_survivor(self,sid,reason=''):
        s=self.survivors.get(sid)
        if not s or s.status!=SurvivorStatus.ACTIVE:return
        s.status=SurvivorStatus.INFECTED;s.path=[];self.metrics.survivors_infected+=1;self.metrics.zombies_created+=1
        zid=f'Z{len(self.zombies)+1}';self.zombies[zid]=Zombie(zid,s.pos);self.log(f'{sid} infected ({reason}); converted to {zid}')
    def _update_metrics(self):
        self.metrics.time_step=self.time_step;self.metrics.total_cost=sum(s.metrics.path_length+s.metrics.waiting_time for s in self.survivors.values())
    def finish(self):
        if self.game_over:return
        self.game_over=True;self._update_metrics();m=self.metrics
        self.log('Mission complete: all survivors rescued.' if m.rescued==m.survivors_started else f'Mission ended: {m.rescued}/{m.survivors_started} rescued.')
