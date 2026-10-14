from dataclasses import dataclass

@dataclass
class SimulationMetrics:
    time_step: int = 0
    total_cost: float = 0.0
    waiting_time: int = 0
    conflicts: int = 0
    replans: int = 0
    nodes_expanded: int = 0
    zombie_nodes: int = 0
    steering_calls: int = 0
    steering_candidates: int = 0
    alpha_beta_nodes: int = 0
    alpha_beta_prunes: int = 0
    decision_time_ms: float = 0.0
    # Survivor path-planner metrics used for A* vs GBFS comparisons.
    planner_calls: int = 0
    planner_successes: int = 0
    pathfinding_nodes_expanded: int = 0
    pathfinding_time_ms: float = 0.0
    route_length_sum: float = 0.0
    rescued: int = 0
    survivors_started: int = 0
    survivors_infected: int = 0
    zombies_started: int = 0
    zombies_created: int = 0

    @property
    def survival_rate(self):
        return self.rescued / self.survivors_started * 100 if self.survivors_started else 0.0

    @property
    def planning_success_rate(self):
        return self.planner_successes / self.planner_calls * 100 if self.planner_calls else 0.0

    @property
    def mean_route_length(self):
        return self.route_length_sum / self.planner_successes if self.planner_successes else 0.0
