"""
Benchmark Script - FPGA-H1 Virtual Lab
Measures raw LUT4 evaluations/sec, ALU4 simulation cycles/sec, and memory footprint.
"""

import time
import sys
import psutil
import os
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from architecture.blocks.lut4.lut4_core import LUT4
from architecture.blocks.lut4.clb import CLB
from examples.alu4.alu4_circuit import ALU4Circuit


def benchmark_lut4_raw(iterations: int = 1_000_000) -> float:
    lut = LUT4(initial_mask=0x9696)
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = (lut._mask >> 5) & 1  # inlined inner loop
    t1 = time.perf_counter()
    elapsed = t1 - t0
    ops_per_sec = iterations / elapsed
    print(f"[LUT4 RAW EVAL] {iterations:,} evals in {elapsed:.4f}s -> {ops_per_sec:,.0f} evals/sec")
    return ops_per_sec


def benchmark_alu4_cycles(iterations: int = 5_000) -> float:
    alu = ALU4Circuit()
    t0 = time.perf_counter()
    for i in range(iterations):
        a = i & 0x0F
        b = (i >> 4) & 0x0F
        op = i % 6
        alu.execute(a, b, op)
    t1 = time.perf_counter()
    elapsed = t1 - t0
    cycles_per_sec = iterations / elapsed
    print(f"[ALU4 FULL SIMULATION] {iterations:,} full circuit cycles in {elapsed:.4f}s -> {cycles_per_sec:,.0f} cycles/sec")
    return cycles_per_sec


def get_memory_usage() -> float:
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"[MEMORY FOOTPRINT] Python Process RSS: {mem_mb:.2f} MB")
    return mem_mb


if __name__ == "__main__":
    print("=" * 60)
    print("FPGA-H1 BENCHMARK SUITE — PHASE 1")
    print("=" * 60)
    mem_start = get_memory_usage()
    lut_speed = benchmark_lut4_raw(5_000_000)
    alu_speed = benchmark_alu4_cycles(10_000)
    mem_end = get_memory_usage()
    print("=" * 60)
