"""
Pathfinder Router - FPGA-H1 Virtual Lab
Negotiated Congestion Routing Engine based on McMurchie & Ebeling's Pathfinder algorithm.
"""

import heapq
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from simulator.routing.rr_graph import RRGraph, RRNode, NodeType


class Net:
    """A net to be routed, consisting of one source pin and one or more sink pins."""

    __slots__ = ('name', 'source_pin', 'sink_pins', 'routed_tree')

    def __init__(self, name: str, source_pin: Tuple[int, int, int], sink_pins: List[Tuple[int, int, int]]):
        self.name = name
        # source_pin: (clb_x, clb_y, opin_idx)
        self.source_pin = source_pin
        # sink_pins: list of (clb_x, clb_y, ipin_idx)
        self.sink_pins = sink_pins
        # Set of node IDs currently belonging to this net's routed tree
        self.routed_tree: Set[int] = set()

    def __repr__(self) -> str:
        return f"Net('{self.name}', src={self.source_pin}, sinks={len(self.sink_pins)})"


class PathfinderRouter:
    """
    Pathfinder negotiated congestion router.
    Resolves track sharing through iterative rip-up and reroute with historical penalties.
    """

    def __init__(
        self,
        rr_graph: RRGraph,
        max_iterations: int = 50,
        initial_pres_fac: float = 1.0,
        pres_fac_mult: float = 1.3,
        acc_fac: float = 0.5
    ):
        self.graph = rr_graph
        self.max_iterations = max_iterations
        self.initial_pres_fac = initial_pres_fac
        self.pres_fac_mult = pres_fac_mult
        self.acc_fac = acc_fac

    def _dijkstra_route_sink(
        self,
        source_nodes: Set[int],
        target_node_id: int,
        pres_fac: float,
        existing_net_nodes: Set[int]
    ) -> Optional[List[int]]:
        """
        A* directed shortest path search from any node in source_nodes to target_node_id.
        Uses an admissible Manhattan distance heuristic to guide search directly towards the sink.
        Allows path reuse: traversing nodes already in existing_net_nodes incurs zero incremental cost.
        """
        target_node = self.graph.nodes[target_node_id]
        tx, ty = target_node.x, target_node.y

        # Priority queue entries: (f_score, current_node_id)
        pq: List[Tuple[float, int]] = []
        g_score: Dict[int, float] = {}
        prev: Dict[int, int] = {}

        for src in source_nodes:
            g_score[src] = 0.0
            src_node = self.graph.nodes[src]
            h = 0.5 * (abs(src_node.x - tx) + abs(src_node.y - ty))
            heapq.heappush(pq, (h, src))

        visited: Set[int] = set()

        while pq:
            f, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            if u == target_node_id:
                # Reconstruct path
                path = []
                curr = u
                while curr in prev:
                    path.append(curr)
                    curr = prev[curr]
                path.append(curr)
                path.reverse()
                return path

            u_node = self.graph.nodes[u]
            u_g = g_score[u]

            for v, edge_cost in u_node.edges.items():
                v_node = self.graph.nodes[v]
                if v in existing_net_nodes:
                    node_cost = 0.0
                else:
                    node_cost = v_node.get_cost(pres_fac)

                tentative_g = u_g + edge_cost + node_cost
                if v not in g_score or tentative_g < g_score[v]:
                    g_score[v] = tentative_g
                    prev[v] = u
                    h = 0.5 * (abs(v_node.x - tx) + abs(v_node.y - ty))
                    heapq.heappush(pq, (tentative_g + h, v))

        return None  # Unreachable

    def _rip_up_net(self, net: Net) -> None:
        """Removes a net from the routing graph, decrementing occupancy."""
        for nid in net.routed_tree:
            self.graph.nodes[nid].occ = max(0, self.graph.nodes[nid].occ - 1)
        net.routed_tree.clear()

    def _add_path_to_net(self, net: Net, path: List[int]) -> None:
        """Adds a path of node IDs to the net, incrementing occupancy for newly used nodes."""
        for nid in path:
            if nid not in net.routed_tree:
                net.routed_tree.add(nid)
                self.graph.nodes[nid].occ += 1

    def route(self, nets: List[Net]) -> Dict[str, Any]:
        """
        Executes the Pathfinder routing loop.
        Returns detailed routing report and status.
        """
        t0 = time.perf_counter()
        pres_fac = self.initial_pres_fac

        # Reset occupancy
        self.graph.reset_occupancies()
        for net in nets:
            net.routed_tree.clear()

        # Map each net's source and sinks to RRNode IDs
        net_mapped_pins: List[Tuple[Net, int, List[int]]] = []
        for net in nets:
            src_nid = self.graph.opin_lookup.get(net.source_pin)
            if src_nid is None:
                raise ValueError(f"Net '{net.name}' source pin {net.source_pin} not found in RRGraph")
            sink_nids = []
            for sink in net.sink_pins:
                snid = self.graph.ipin_lookup.get(sink)
                if snid is None:
                    raise ValueError(f"Net '{net.name}' sink pin {sink} not found in RRGraph")
                sink_nids.append(snid)
            net_mapped_pins.append((net, src_nid, sink_nids))

        iteration = 0
        success = False
        max_overuse = 0

        while iteration < self.max_iterations:
            iteration += 1

            # 1. Route all nets
            for net, src_nid, sink_nids in net_mapped_pins:
                # Rip up net
                self._rip_up_net(net)

                # Route to each sink
                source_tree: Set[int] = {src_nid}
                for sink_nid in sink_nids:
                    path = self._dijkstra_route_sink(
                        source_nodes=source_tree,
                        target_node_id=sink_nid,
                        pres_fac=pres_fac,
                        existing_net_nodes=net.routed_tree
                    )
                    if path is None:
                        # Impossible route detected
                        t1 = time.perf_counter()
                        return {
                            "success": False,
                            "iterations": iteration,
                            "time_sec": t1 - t0,
                            "reason": f"Pathfinder: Cannot find valid path for net '{net.name}' to sink {sink_nid}",
                            "failed_net": net.name,
                            "routed_nets_pct": 0.0,
                            "max_overuse": -1
                        }

                    self._add_path_to_net(net, path)
                    # Expand source tree with new path nodes
                    source_tree.update(path)

            # 2. Check for overused nodes (congestion)
            overused_nodes = 0
            max_overuse = 0
            for node in self.graph.nodes.values():
                overuse = max(0, node.occ - node.capacity)
                if overuse > 0:
                    overused_nodes += 1
                    if overuse > max_overuse:
                        max_overuse = overuse

            # 3. If zero overused nodes, routing is legally completed!
            if overused_nodes == 0:
                success = True
                break

            # 4. Update historical costs and present penalty factor
            for node in self.graph.nodes.values():
                overuse = max(0, node.occ - node.capacity)
                if overuse > 0:
                    node.historical_cost += self.acc_fac * overuse

            pres_fac *= self.pres_fac_mult

        t1 = time.perf_counter()
        elapsed = t1 - t0

        # Apply physical switch configurations to SB and CB objects
        if success:
            self._apply_physical_switches(nets)

        # Calculate statistics
        total_wire_segments = sum(len(net.routed_tree) for net in nets)

        return {
            "success": success,
            "iterations": iteration,
            "time_sec": elapsed,
            "max_overuse": max_overuse,
            "total_nets": len(nets),
            "routed_nets_pct": 100.0 if success else (100.0 * (len(nets) - overused_nodes) / max(1, len(nets))),
            "total_segments_used": total_wire_segments,
            "final_pres_fac": pres_fac
        }

    def _apply_physical_switches(self, nets: List[Net]) -> None:
        """Configures all physical SwitchBoxes and ConnectionBoxes from the routed net paths."""
        # Clear all switches
        for sb in self.graph.switch_boxes.values():
            sb.clear()
        for cb in self.graph.cb_x.values():
            cb.clear()
        for cb in self.graph.cb_y.values():
            cb.clear()

        # Traverse every edge used in routed trees
        for net in nets:
            net_nodes = set(net.routed_tree)
            for u in net.routed_tree:
                u_node = self.graph.nodes[u]
                for v in u_node.edges:
                    if v in net_nodes:
                        meta = u_node.edge_switches.get(v)
                        if not meta:
                            continue
                        if meta["type"] == "SB":
                            sb = meta["sb"]
                            sb.connect(meta["s1"], meta["t1"], meta["s2"], meta["t2"])
                        elif meta["type"] == "CB_OUT":
                            cb = meta["cb"]
                            cb.connect_output_pin(meta["pin"], meta["track"])
                        elif meta["type"] == "CB_IN":
                            cb = meta["cb"]
                            cb.connect_input_pin(meta["pin"], meta["track"])
