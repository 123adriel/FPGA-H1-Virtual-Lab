"""
Placement Engine - FPGA-H1 Virtual Lab
Places Configurable Logic Blocks (CLBs) on a 2D grid minimizing Half-Perimeter Wirelength (HPWL).
"""

import math
import random
import time
from typing import Dict, List, Tuple, Set, Any, Optional


class PlacedCLB:
    def __init__(self, name: str, clb_id: int):
        self.name = name
        self.clb_id = clb_id
        self.x: int = -1
        self.y: int = -1

    def __repr__(self) -> str:
        return f"PlacedCLB('{self.name}', id={self.clb_id}, at=({self.x}, {self.y}))"


class PlacementEngine:
    """
    Placement Engine for 2D Island-Style FPGA grid.
    
    Supports:
    - Connectivity-driven initial placement.
    - Simulated Annealing / Greedy swap refinement to minimize HPWL and congestion.
    """

    def __init__(self, grid_w: int, grid_h: int):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.capacity = grid_w * grid_h

        # Grid occupancy: (x, y) -> Optional[PlacedCLB]
        self.grid: Dict[Tuple[int, int], Optional[PlacedCLB]] = {
            (x, y): None for x in range(grid_w) for y in range(grid_h)
        }
        self.clbs: Dict[str, PlacedCLB] = {}
        # Netlist connections for wirelength estimation:
        # net_name -> List[clb_name]
        self.net_clbs: Dict[str, List[str]] = {}

    def add_clb(self, name: str, clb_id: int) -> PlacedCLB:
        if len(self.clbs) >= self.capacity:
            raise RuntimeError(
                f"Grid capacity exceeded! Grid size {self.grid_w}x{self.grid_h} ({self.capacity} CLBs), attempting to add CLB #{len(self.clbs) + 1}"
            )
        pclb = PlacedCLB(name, clb_id)
        self.clbs[name] = pclb
        return pclb

    def add_net(self, net_name: str, connected_clb_names: List[str]) -> None:
        """Registers a net connecting multiple CLBs for HPWL calculation."""
        for cname in connected_clb_names:
            if cname not in self.clbs:
                raise KeyError(f"CLB '{cname}' in net '{net_name}' is not registered in placement engine")
        self.net_clbs[net_name] = connected_clb_names

    def compute_hpwl(self) -> float:
        """
        Calculates Half-Perimeter Wirelength (HPWL) across all registered nets:
        HPWL = sum_{net} [ (max(x) - min(x)) + (max(y) - min(y)) ]
        """
        total_hpwl = 0.0
        for net_name, clb_names in self.net_clbs.items():
            if len(clb_names) <= 1:
                continue
            xs = [self.clbs[name].x for name in clb_names if self.clbs[name].x >= 0]
            ys = [self.clbs[name].y for name in clb_names if self.clbs[name].y >= 0]
            if len(xs) > 1:
                total_hpwl += (max(xs) - min(xs)) + (max(ys) - min(ys))
        return total_hpwl

    def initial_placement_heuristic(self) -> None:
        """
        Places CLBs on the grid using a spiral center-of-mass heuristic:
        Highly connected CLBs are placed towards the center of the die.
        """
        # 1. Clear grid
        for pos in self.grid:
            self.grid[pos] = None

        # 2. Rank CLBs by degree (number of connected nets)
        degree: Dict[str, int] = {name: 0 for name in self.clbs}
        for clb_names in self.net_clbs.values():
            for c in clb_names:
                degree[c] += 1

        sorted_clbs = sorted(self.clbs.values(), key=lambda c: degree[c.name], reverse=True)

        # 3. Sort grid cells by distance to center
        cx = (self.grid_w - 1) / 2.0
        cy = (self.grid_h - 1) / 2.0
        all_cells = [(x, y) for x in range(self.grid_w) for y in range(self.grid_h)]
        all_cells.sort(key=lambda pos: (pos[0] - cx)**2 + (pos[1] - cy)**2)

        for i, pclb in enumerate(sorted_clbs):
            pos = all_cells[i]
            pclb.x, pclb.y = pos
            self.grid[pos] = pclb

    def optimize_simulated_annealing(
        self,
        max_moves: int = 500,
        t_init: float = 10.0,
        cooling_rate: float = 0.95,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Refines placement through simulated annealing with pairwise cell swaps.
        """
        random.seed(seed)
        t0 = time.perf_counter()

        current_hpwl = self.compute_hpwl()
        best_hpwl = current_hpwl
        temp = t_init

        accepted_swaps = 0
        total_swaps = 0

        all_cells = [(x, y) for x in range(self.grid_w) for y in range(self.grid_h)]

        for step in range(max_moves):
            # Pick two distinct cells at random
            pos1, pos2 = random.sample(all_cells, 2)
            clb1 = self.grid[pos1]
            clb2 = self.grid[pos2]

            # Perform trial swap
            if clb1:
                clb1.x, clb1.y = pos2
            if clb2:
                clb2.x, clb2.y = pos1
            self.grid[pos1] = clb2
            self.grid[pos2] = clb1

            new_hpwl = self.compute_hpwl()
            delta = new_hpwl - current_hpwl

            # Acceptance condition (Metropolis)
            if delta < 0 or (temp > 1e-4 and random.random() < math.exp(-delta / temp)):
                current_hpwl = new_hpwl
                accepted_swaps += 1
                if current_hpwl < best_hpwl:
                    best_hpwl = current_hpwl
            else:
                # Revert swap
                if clb1:
                    clb1.x, clb1.y = pos1
                if clb2:
                    clb2.x, clb2.y = pos2
                self.grid[pos1] = clb1
                self.grid[pos2] = clb2

            temp *= cooling_rate
            total_swaps += 1

        t1 = time.perf_counter()
        return {
            "initial_hpwl": current_hpwl,
            "final_hpwl": best_hpwl,
            "swaps_attempted": total_swaps,
            "swaps_accepted": accepted_swaps,
            "time_sec": t1 - t0,
            "utilization_pct": 100.0 * len(self.clbs) / self.capacity
        }

    def get_placement_map(self) -> Dict[str, Tuple[int, int]]:
        """Returns mapping: clb_name -> (x, y)."""
        return {name: (clb.x, clb.y) for name, clb in self.clbs.items()}
