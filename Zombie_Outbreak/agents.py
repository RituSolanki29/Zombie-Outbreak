from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional
Coord=Tuple[float,float]
class SurvivorStatus(Enum): ACTIVE='Active'; INFECTED='Infected'; RESCUED='Rescued'; DEAD='Caught'
class ZombieStatus(Enum): HUNTING='Hunting'; INFECTED='Converted'
@dataclass
class AgentMetrics:
    path_length:float=0.0; waiting_time:int=0; nodes_expanded:int=0; decision_time_ms:float=0.0; replans:int=0
@dataclass
class Survivor:
    sid:str; pos:Coord; target:Coord; resource_target:Optional[str]=None
    status:SurvivorStatus=SurvivorStatus.ACTIVE; path:List[Coord]=field(default_factory=list); path_index:int=1
    resources:int=0; metrics:AgentMetrics=field(default_factory=AgentMetrics); position_history:List[Coord]=field(default_factory=list)
@dataclass
class Zombie:
    zid:str; pos:Coord; status:ZombieStatus=ZombieStatus.HUNTING; path:List[Coord]=field(default_factory=list)
    path_index:int=1; metrics:AgentMetrics=field(default_factory=AgentMetrics); target_sid:Optional[str]=None
