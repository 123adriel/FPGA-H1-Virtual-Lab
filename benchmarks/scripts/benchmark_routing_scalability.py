"""
Routing & Placement Scalability Benchmark - FPGA-H1 Virtual Lab
Systematically evaluates Placement and Pathfinder Routing across scales:
4, 16, 64, 256, 1,024, and 8,640 LUTs.
Measures time, memory, iterations, congestion, and routability.
"""

import time
import psutil
import os
import sys
import random
import math
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from simulator.routing.rr_graph import RRGraph
from simulator.routing.pathfinder import PathfinderRouter, Net
from simulator.routing.placement import PlacementEngine


try:
    import psutil
    def get_process_memory_mb() -> float:
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
except ImportError:
    try:
        import resource
        def get_process_memory_mb() -> float:
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except ImportError:
        def get_process_memory_mb() -> float:
            return 0.0


def run_benchmark_scale(
    num_luts: int,
    grid_w: int,
    grid_h: int,
    channel_width: int,
    net_density: float = 0.75,
    max_routing_iter: int = 30
) -> Dict[str, Any]:
    """Runs placement and routing on a given scale."""
    clb_count = grid_w * grid_h
    random.seed(42 + num_luts)

    mem_before = get_process_memory_mb()
    t_start_total = time.perf_counter()

    # 1. Placement Phase
    t0_place = time.perf_counter()
    placer = PlacementEngine(grid_w, grid_h)
    for cid in range(clb_count):
        placer.add_clb(f"CLB_{cid}", clb_id=cid)

    # Generate synthetic nets following Rent's rule (local + some global hops)
    num_nets = max(1, int(clb_count * net_density))
    nets_data = []
    for nid in range(num_nets):
        # Pick source CLB
        src_id = random.randint(0, clb_count - 1)
        # Sinks: 1 to 2 sinks biased to nearby CLBs
        num_sinks = 1 if random.random() < 0.75 else 2
        sink_ids = []
        for _ in range(num_sinks):
            if clb_count <= 1:
                target_id = 0
            else:
                target_id = (src_id + random.randint(1, min(5, clb_count - 1))) % clb_count
            sink_ids.append(target_id)
        
        placer.add_net(f"NET_{nid}", [f"CLB_{src_id}"] + [f"CLB_{sid}" for sid in sink_ids])
        nets_data.append((src_id, sink_ids))

    placer.initial_placement_heuristic()
    anneal_moves = min(1000, clb_count * 5)
    place_res = placer.optimize_simulated_annealing(max_moves=anneal_moves, seed=42)
    t1_place = time.perf_counter()
    place_time = t1_place - t0_place

    # 2. Graph Construction
    t0_graph = time.perf_counter()
    rr_graph = RRGraph(grid_w=grid_w, grid_h=grid_h, channel_width=channel_width)
    t1_graph = time.perf_counter()
    graph_time = t1_graph - t0_graph

    # 3. Translate placed nets to Net objects on RRGraph
    placed_map = placer.get_placement_map()
    routed_nets = []
    for nid, (src_id, sink_ids) in enumerate(nets_data):
        src_pos = placed_map[f"CLB_{src_id}"]
        # Connect to OPIN 0 (or modulo 4)
        opin_idx = nid % 4
        sink_pins = []
        for s_idx, sid in enumerate(sink_ids):
            sink_pos = placed_map[f"CLB_{sid}"]
            ipin_idx = (nid + s_idx) % 16
            sink_pins.append((sink_pos[0], sink_pos[1], ipin_idx))

        routed_nets.append(
            Net(name=f"NET_{nid}", source_pin=(src_pos[0], src_pos[1], opin_idx), sink_pins=sink_pins)
        )

    # 4. Pathfinder Routing Phase
    t0_route = time.perf_counter()
    router = PathfinderRouter(rr_graph, max_iterations=max_routing_iter)
    route_res = router.route(routed_nets)
    t1_route = time.perf_counter()
    route_time = t1_route - t0_route

    mem_after = get_process_memory_mb()
    t_end_total = time.perf_counter()

    return {
        "num_luts": num_luts,
        "clb_count": clb_count,
        "grid": f"{grid_w}x{grid_h}",
        "channel_width": channel_width,
        "nets_count": num_nets,
        "rr_nodes": len(rr_graph.nodes),
        "placement_time_sec": place_time,
        "graph_time_sec": graph_time,
        "routing_time_sec": route_time,
        "total_time_sec": t_end_total - t_start_total,
        "iterations": route_res["iterations"],
        "success": route_res["success"],
        "max_overuse": route_res.get("max_overuse", 0),
        "routed_pct": route_res.get("routed_nets_pct", 0.0),
        "mem_delta_mb": mem_after - mem_before,
        "mem_peak_mb": mem_after
    }


def main():
    print("=" * 80)
    print("FPGA-H1 ROUTING & PLACEMENT SCALABILITY BENCHMARK")
    print("=" * 80)

    # Test scales up to 8,640 LUTs (Gowin GW1NR-9 reference)
    benchmarks = [
        {"luts": 4,     "w": 1,  "h": 1,  "W": 4},
        {"luts": 16,    "w": 2,  "h": 2,  "W": 6},
        {"luts": 64,    "w": 4,  "h": 4,  "W": 8},
        {"luts": 256,   "w": 8,  "h": 8,  "W": 8},
        {"luts": 1024,  "w": 16, "h": 16, "W": 10},
        {"luts": 4096,  "w": 32, "h": 32, "W": 12},
        {"luts": 8640,  "w": 48, "h": 45, "W": 16},  # 2160 CLBs = 8640 LUTs
    ]

    results = []
    for b in benchmarks:
        print(f"\n---> Benchmarking {b['luts']} LUT4 ({b['w']}x{b['h']} CLBs, Channel W={b['W']})...", flush=True)
        try:
            max_iter = 5 if b["luts"] >= 4096 else 20
            res = run_benchmark_scale(
                num_luts=b["luts"],
                grid_w=b["w"],
                grid_h=b["h"],
                channel_width=b["W"],
                max_routing_iter=max_iter
            )
            results.append(res)
            print(f"     [STATUS] {'SUCCESS' if res['success'] else 'UNROUTED/CONGESTED'}", flush=True)
            print(f"     Placement Time: {res['placement_time_sec']:.3f}s | Routing Time: {res['routing_time_sec']:.3f}s", flush=True)
            print(f"     Iterations: {res['iterations']} | Routed: {res['routed_pct']:.1f}% | RR Nodes: {res['rr_nodes']:,}", flush=True)
            print(f"     Memory: {res['mem_peak_mb']:.1f} MB (Delta: +{res['mem_delta_mb']:.1f} MB)", flush=True)
        except Exception as e:
            print(f"     [LIMIT REACHED / ERROR]: {e}", flush=True)
            results.append({"num_luts": b["luts"], "error": str(e), "success": False})

    print("\n" + "=" * 80, flush=True)
    print("BENCHMARK SUMMARY TABLE", flush=True)
    print("=" * 80, flush=True)
    header = f"{'LUTs':>6} | {'Grid':>7} | {'RR Nodes':>10} | {'Place (s)':>10} | {'Route (s)':>10} | {'Iters':>5} | {'Routed%':>7} | {'RAM (MB)':>8}"
    print(header, flush=True)
    print("-" * len(header), flush=True)
    for r in results:
        if r.get("success"):
            print(f"{r['num_luts']:>6} | {r['grid']:>7} | {r['rr_nodes']:>10,} | {r['placement_time_sec']:>10.3f} | {r['routing_time_sec']:>10.3f} | {r['iterations']:>5} | {r['routed_pct']:>6.1f}% | {r['mem_peak_mb']:>8.1f}", flush=True)
        else:
            print(f"{r['num_luts']:>6} | FAILED / LIMIT: {r.get('error', 'Unrouted')}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
