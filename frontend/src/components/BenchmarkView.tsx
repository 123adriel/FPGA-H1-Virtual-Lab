import React, { useState } from "react";
import type { BenchmarkItem } from "../types";
import { LineChart, Play, ShieldAlert, Layers } from "lucide-react";
import { runBenchmarks } from "../services/api";

interface BenchmarkViewProps {
  benchmarks: BenchmarkItem[];
  onRefreshBenchmarks: () => void;
}

export const BenchmarkView: React.FC<BenchmarkViewProps> = ({
  benchmarks,
  onRefreshBenchmarks
}) => {
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const handleRunAll = async () => {
    setIsRunning(true);
    try {
      await runBenchmarks();
      onRefreshBenchmarks();
    } catch (e) {
      console.error("Benchmark run failed", e);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto h-full overflow-y-auto text-slate-100 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-medium mb-2 border border-cyan-500/20">
            <LineChart className="w-3.5 h-3.5" />
            <span>Silicon Scalability & Performance Benchmarks</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            FPGA-H1 Architecture vs Gowin GW1NR-9 (Sipeed Tang Nano 9K)
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Empirical benchmark metrics measured across 6 scaling tiers from 4 LUTs to 8,640 LUTs.
            Covers synthesis compilation, 2D spatial placement, Pathfinder Wilton routing, and cycle stepping.
          </p>
        </div>

        <button
          onClick={handleRunAll}
          disabled={isRunning}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50 transition shrink-0"
        >
          <Play className="w-4 h-4" />
          <span>{isRunning ? "Executing Scalability Suite..." : "Execute Scalability Suite"}</span>
        </button>
      </div>

      {/* Tiers Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {benchmarks.slice(-3).map((item) => (
          <div key={item.id} className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm text-cyan-400">{item.scale_name}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                {item.grid_w}×{item.grid_h} Grid
              </span>
            </div>
            <div className="text-2xl font-bold text-white font-mono">{item.target_luts} LUT4</div>
            <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
              <div className="flex justify-between">
                <span>Placement:</span>
                <span className="text-slate-200 font-mono">{item.placement_time_ms} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Routing:</span>
                <span className="text-slate-200 font-mono">{item.routing_time_ms} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Sim Step:</span>
                <span className="text-emerald-400 font-mono">{item.sim_step_us} µs/cycle</span>
              </div>
              <div className="flex justify-between">
                <span>Peak Memory:</span>
                <span className="text-cyan-300 font-mono">{(item.memory_kb / 1024).toFixed(1)} MB</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Complete Scalability Benchmark Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Full Scaling Performance Matrix (SQLite Verified)</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-mono">
              <tr>
                <th className="py-2.5 px-3">Scale Name</th>
                <th className="py-2.5 px-3">Target LUT4</th>
                <th className="py-2.5 px-3">Island Grid</th>
                <th className="py-2.5 px-3">Mapping (ms)</th>
                <th className="py-2.5 px-3">Placement (ms)</th>
                <th className="py-2.5 px-3">Routing (ms)</th>
                <th className="py-2.5 px-3">Bitstream (ms)</th>
                <th className="py-2.5 px-3 text-emerald-400">Sim Step (µs)</th>
                <th className="py-2.5 px-3">Memory (KB)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
              {benchmarks.map((row) => (
                <tr key={row.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-semibold text-white">{row.scale_name}</td>
                  <td className="py-2.5 px-3 text-cyan-400 font-bold">{row.target_luts}</td>
                  <td className="py-2.5 px-3">{row.grid_w}×{row.grid_h}</td>
                  <td className="py-2.5 px-3">{row.compile_time_ms}</td>
                  <td className="py-2.5 px-3">{row.placement_time_ms}</td>
                  <td className="py-2.5 px-3">{row.routing_time_ms}</td>
                  <td className="py-2.5 px-3">{row.bitstream_time_ms}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{row.sim_step_us}</td>
                  <td className="py-2.5 px-3 text-slate-400">{row.memory_kb}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* In-depth Gowin GW1NR-9 Analysis */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>Architectural Equivalence & Silicon Reality Assessment</span>
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          While FPGA-H1 successfully models the exact nominal logic capacity of 8,640 LUT4s and reproduces Island-Style
          Wilton routing with negotiated congestion Pathfinder algorithms, key differences with commercial commercial FPGAs
          (such as Gowin GW1NR-9 on Sipeed Tang Nano 9K) must be documented:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1">
            <div className="font-bold text-cyan-400">Dedicated Hard Blocks (BSRAM & DSP)</div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Gowin GW1NR-9 embeds 26 Block SRAMs (18Kbit each) and dedicated 18x18 hardware DSP multipliers.
              FPGA-H1 achieves memory and arithmetic via distributed LUT4 configurations and carry chains.
            </p>
          </div>
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1">
            <div className="font-bold text-cyan-400">Clock Trees & Phase Locked Loops (PLL)</div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              GW1NR-9 incorporates 2 hard analog PLLs with dynamic phase shift. FPGA-H1 models synchronous global clock networks
              with deterministic rising/falling edge timing in topological simulation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
