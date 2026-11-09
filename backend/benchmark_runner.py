"""
Scalability Benchmark Runner - FPGA-H1 Virtual Lab
Executes synthetic and real logic scalability tests from 4 LUTs up to 8,640 LUTs (GW1NR-9 reference scale).
Measures compilation time, placement time, routing throughput, bitstream codec, and simulation stepping.
"""

import time
import math
import tracemalloc
from typing import Dict, Any, List
from architecture.blocks.lut4.ble import BLE
from simulator.logic.engine import CircuitEngine
from simulator.routing.grid_circuit import GridCircuit
from simulator.routing.pathfinder import Net
from compiler.bitstream.bitstream_codec import BitstreamCodec
from backend.database import save_benchmark


SCALABILITY_TARGETS = [
    {"name": "Nano-4", "luts": 4, "grid_side": 1},
    {"name": "Micro-64", "luts": 64, "grid_side": 4},
    {"name": "Standard-256", "luts": 256, "grid_side": 8},
    {"name": "Medium-1024", "luts": 1024, "grid_side": 16},
    {"name": "Large-4096", "luts": 4096, "grid_side": 32},
    {"name": "GW1NR9-8640", "luts": 8640, "grid_side": 47}
]


def run_benchmark_for_scale(scale_info: Dict[str, Any]) -> Dict[str, Any]:
    name = scale_info["name"]
    lut_target = scale_info["luts"]
    grid_side = scale_info["grid_side"]
    clb_count = math.ceil(lut_target / 4)

    tracemalloc.start()
    t_start_all = time.perf_counter()

    # 1. Logic Synthesis / Packing
    t0 = time.perf_counter()
    engine = CircuitEngine(name=f"BENCH_{name}")
    engine.add_input("CLK")
    engine.add_input("RST")
    engine.add_input("DIN")
    engine.add_output("DOUT")

    for i in range(lut_target):
        ble = BLE(name=f"BLE_{i}", ble_id=i, lut_mask=0x6996, bypass_ff=(i % 2 == 0))
        prev = f"BLE_{i-1}.out" if i > 0 else "DIN"
        engine.add_ble(ble, [prev, "CLK", "0", "0"])

    engine.connect_output("DOUT", f"BLE_{lut_target-1}.out")
    engine.compile()
    t_synth = (time.perf_counter() - t0) * 1000

    # 2. Spatial Placement into Grid
    t0 = time.perf_counter()
    grid = GridCircuit(grid_w=grid_side, grid_h=grid_side, channel_width=8)
    for i in range(lut_target):
        clb_idx = i // 4
        ble_idx = i % 4
        gx = clb_idx % grid_side
        gy = clb_idx // grid_side
        grid.configure_ble(gx, gy, ble_idx, mask=0x6996, bypass_ff=(i % 2 == 0))
    t_place = (time.perf_counter() - t0) * 1000

    # 3. Pathfinder Routing (Sample netlist across grid)
    t0 = time.perf_counter()
    nets = []
    # Sample up to 100 representative nets across the chip to benchmark router
    sample_nets = min(lut_target - 1, 64)
    step_stride = max(1, (lut_target - 1) // sample_nets)
    for i in range(0, lut_target - step_stride, step_stride):
        src_clb = i // 4
        src_ble = i % 4
        sx = src_clb % grid_side
        sy = src_clb // grid_side

        dst_idx = i + step_stride
        dst_clb = dst_idx // 4
        dst_ble = dst_idx % 4
        dx = dst_clb % grid_side
        dy = dst_clb // grid_side

        nets.append(Net(name=f"NET_{i}", source_pin=(sx, sy, src_ble), sink_pins=[(dx, dy, dst_ble * 4)]))

    route_res = grid.route_netlist(nets)
    t_route = (time.perf_counter() - t0) * 1000

    # 4. Bitstream Serialization with CRC32
    t0 = time.perf_counter()
    bitstream = grid.to_bitstream(metadata={"scale": name, "luts": lut_target})
    t_bitstream = (time.perf_counter() - t0) * 1000

    # 5. Simulation stepping throughput (100 clock cycles)
    t0 = time.perf_counter()
    for cyc in range(50):
        engine.step({"CLK": cyc % 2, "RST": 0, "DIN": 1 if cyc > 5 else 0}, clk=cyc % 2)
    t_sim_total = time.perf_counter() - t0
    sim_step_us = (t_sim_total / 50.0) * 1_000_000

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    result = {
        "scale_name": name,
        "target_luts": lut_target,
        "clbs": clb_count,
        "grid_w": grid_side,
        "grid_h": grid_side,
        "compile_time_ms": round(t_synth, 2),
        "placement_time_ms": round(t_place, 2),
        "routing_time_ms": round(t_route, 2),
        "bitstream_time_ms": round(t_bitstream, 2),
        "sim_step_us": round(sim_step_us, 2),
        "memory_kb": round(peak_mem / 1024, 2),
        "routed_pct": route_res.get("routed_nets_pct", 100.0),
        "bitstream_bytes": len(bitstream)
    }

    save_benchmark(result)
    return result


def run_all_scalability_benchmarks() -> List[Dict[str, Any]]:
    results = []
    for target in SCALABILITY_TARGETS:
        res = run_benchmark_for_scale(target)
        results.append(res)
    return results
