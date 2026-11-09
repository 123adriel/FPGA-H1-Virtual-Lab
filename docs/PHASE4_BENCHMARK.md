# FPGA-H1 — Scalability & Performance Benchmarks (Phase 4)

## 1. Overview & Benchmark Scope

Phase 4 of the FPGA-H1 Virtual Lab project benchmarks the full architectural stack across 6 scalability tiers, culminating in the nominal logic capacity equivalent to the **Gowin GW1NR-9** (found on the Sipeed Tang Nano 9K development board): **8,640 LUT4 cells**.

The benchmarks measure:
1. **Logic Synthesis & Technology Mapping**: Parsing and compiling logic into interconnected BLE primitives.
2. **Spatial 2D Placement**: Arranging CLBs into an Island-Style grid $(W \times H)$ with $W = H = \lceil \sqrt{\text{CLBs}} \rceil$.
3. **Pathfinder Negotiated-Congestion Routing**: Resolving interconnections across Wilton $F_s=3$ switch boxes and channel tracks ($W=8$).
4. **H1BS Bitstream Synthesis**: Encoding configuration frames and calculating CRC-32 checksums.
5. **Simulation Clock Stepping Throughput**: Microseconds per clock cycle across 50 simulated cycles.
6. **Peak Memory Footprint**: Heap memory tracked via Python `tracemalloc`.

---

## 2. Empirical Benchmark Results

The following measurements were captured on the development environment and persisted in the SQLite benchmarks table:

| Scale Tier | Nominal LUT4 | Island Grid | Synthesis (ms) | Placement (ms) | Routing (ms) | Bitstream (ms) | Sim Step (µs) | Peak RAM (KB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Nano-4** | 4 | $1 \times 1$ | 0.15 | 4.87 | 1.37 | 0.26 | 24.94 | 135.1 |
| **Micro-64** | 64 | $4 \times 4$ | 1.50 | 53.72 | 1,426.32 | 1.99 | 232.03 | 1,762.7 |
| **Standard-256** | 256 | $8 \times 8$ | 5.30 | 207.71 | 1,468.52 | 7.01 | 986.11 | 6,644.2 |
| **Medium-1024** | 1,024 | $16 \times 16$ | 23.40 | 929.42 | 19,824.88 | 29.56 | 4,428.22 | 26,469.2 |
| **Large-4096** | 4,096 | $32 \times 32$ | 128.88 | 4,326.20 | 12,417.62 | 79.20 | 19,496.45 | 101,649.2 |
| **GW1NR9-8640** | **8,640** | **$47 \times 47$** | **205.67** | **11,116.12** | **28,791.51** | **237.20** | **47,418.83** | **220,604.8** |

---

## 3. Analysis & Key Insights

### 3.1 Scaling Complexity
1. **Synthesis & Mapping**: Scales approximately $O(N)$. Mapping 8,640 LUTs completes in only **205.67 ms**.
2. **Placement**: Scales $O(N \log N)$ to $O(N^{1.2})$ with grid sizing, taking **11.12 seconds** for 2,160 CLBs on a $47 \times 47$ grid.
3. **Pathfinder Routing**: Shows negotiated congestion overhead when routing long nets across large matrices, taking **28.79 seconds** for global nets at full GW1NR-9 scale.
4. **Bitstream Codec**: Highly efficient binary frame serializer, encoding the entire 8,640-LUT matrix with CRC-32 in **237.20 ms**.
5. **Logic Simulation Stepping**: Stepping the complete 8,640-LUT circuit takes **47.4 milliseconds per cycle**, corresponding to an interactive simulation rate of ~21 Hz.
6. **Memory Footprint**: Peak memory is well-bounded, consuming only **220 MB** for the full 8,640-LUT grid and routing graph.

### 3.2 UI Rendering Scalability
- The HTML5 Canvas implementation renders all 6 grid sizes smoothly.
- Viewport culling and Level of Detail (LOD) preserve 60 FPS when panning and zooming even across the $47 \times 47$ matrix.
