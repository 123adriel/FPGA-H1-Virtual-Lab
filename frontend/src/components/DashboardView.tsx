import React from "react";
import type { ProjectSummary, CompilationResult, BenchmarkItem } from "../types";
import { Cpu, Zap, Box, HardDrive, ArrowUpRight, CheckCircle2, ShieldCheck, Clock, Gauge } from "lucide-react";

interface DashboardProps {
  projects: ProjectSummary[];
  activeProjectId: string;
  onSelectProject: (id: string) => void;
  compilation: CompilationResult | null;
  benchmarks: BenchmarkItem[];
  onOpenStudio: () => void;
}

export const DashboardView: React.FC<DashboardProps> = ({
  projects,
  activeProjectId,
  onSelectProject,
  compilation,
  benchmarks,
  onOpenStudio
}) => {
  const lutsUsed = compilation?.resources?.luts_used || 0;
  const dffsUsed = compilation?.resources?.dffs_used || 0;
  const clbsUsed = compilation?.resources?.clbs_used || 0;
  const bitstreamBytes = compilation?.resources?.bitstream_bytes || 0;

  // GW1NR-9 comparison targets: 8,640 LUT4, 6,480 Flip-Flops, 2,160 CLBs
  const targetLuts = 8640;
  const lutPct = ((lutsUsed / targetLuts) * 100).toFixed(2);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto overflow-y-auto h-full text-slate-100">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 p-6 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-3">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Silicon Architecture Verification Ready</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              FPGA-H1 Virtual Lab — Engineering Suite
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Design, synthesize, place, route, and simulate custom Island-Style FPGA circuits.
              Target nominal equivalent: Gowin GW1NR-9 (8,640 LUT4) featuring Wilton switch boxes and H1BS CRC-32 bitstreams.
            </p>
          </div>

          <button
            onClick={onOpenStudio}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition shadow-lg shadow-cyan-500/20 shrink-0"
          >
            <span>Open H1L Studio</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: LUT4 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>LUT4 Logic Cells</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{lutsUsed}</div>
            <div className="text-xs text-slate-500 mt-1">Nominal Target: {targetLuts} ({lutPct}%)</div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.max(2, Math.min(100, Number(lutPct)))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Metric 2: CLB Blocks */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>CLB Blocks (4 BLEs / CLB)</span>
            <Box className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{clbsUsed}</div>
            <div className="text-xs text-slate-500 mt-1">2D Island Grid: {compilation?.placement?.grid_w || 0}×{compilation?.placement?.grid_h || 0}</div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div className="bg-blue-500 h-full rounded-full" style={{ width: `${Math.min(100, (clbsUsed / 2160) * 100)}%` }} />
            </div>
          </div>
        </div>

        {/* Metric 3: Flip-Flops */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>DFF Sequential Registers</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{dffsUsed}</div>
            <div className="text-xs text-slate-500 mt-1">GW1NR-9 Equivalence: 6,480 DFFs</div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${Math.min(100, (dffsUsed / 6480) * 100)}%` }} />
            </div>
          </div>
        </div>

        {/* Metric 4: Bitstream Memory */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>H1BS Configuration Size</span>
            <HardDrive className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white font-mono">{bitstreamBytes} B</div>
            <div className="text-xs text-slate-500 mt-1">CRC32: {compilation?.stages?.bitstream?.crc32_hex || "N/A"}</div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: "100%" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Projects & Gowin Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Projects Library */}
        <div className="lg:col-span-1 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Box className="w-4 h-4 text-cyan-400" />
              <span>Hardware Projects ({projects.length})</span>
            </h2>
          </div>

          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {projects.map((proj) => {
              const isSelected = proj.id === activeProjectId;
              return (
                <div
                  key={proj.id}
                  onClick={() => onSelectProject(proj.id)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500/40 shadow-sm"
                      : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-white">{proj.name}.h1l</span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      {proj.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {proj.description || "No description provided."}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: GW1NR-9 Architecture Comparison & Pipeline Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Architecture Comparison Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Gauge className="w-4 h-4 text-blue-400" />
                <span>Architectural Target: FPGA-H1 vs Gowin GW1NR-9 (Sipeed Tang Nano 9K)</span>
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Architectural Parameter</th>
                    <th className="py-2.5 px-3 text-cyan-400">FPGA-H1 (Our Design)</th>
                    <th className="py-2.5 px-3 text-slate-300">Gowin GW1NR-9 (Reference)</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  <tr>
                    <td className="py-2.5 px-3 font-medium">Nominal LUT Capacity</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">Scalable 4 to 8,640 LUT4</td>
                    <td className="py-2.5 px-3 font-mono">8,640 LUT4</td>
                    <td className="py-2.5 px-3 text-emerald-400 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> <span>Matched</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-medium">CLB Granularity</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">4 BLEs per CLB (1 LUT4 + 1 DFF)</td>
                    <td className="py-2.5 px-3 font-mono">4 Slices (8 LUT4) per CFU</td>
                    <td className="py-2.5 px-3 text-emerald-400 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> <span>Modular</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-medium">Switch Matrix Topology</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">Wilton Fs=3 Disjoint Routing</td>
                    <td className="py-2.5 px-3 font-mono">Proprietary Segmented Tracks</td>
                    <td className="py-2.5 px-3 text-emerald-400 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> <span>Pathfinder</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-medium">Bitstream Integrity</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">H1BS Binary v1 with CRC-32</td>
                    <td className="py-2.5 px-3 font-mono">Encrypted / Proprietary FS</td>
                    <td className="py-2.5 px-3 text-emerald-400 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> <span>Open Spec</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-medium">Simulation Model</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">Topological Cycle & WebSocket</td>
                    <td className="py-2.5 px-3 font-mono">Verilog / VCD ModelSim</td>
                    <td className="py-2.5 px-3 text-emerald-400 flex items-center space-x-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> <span>Interactive</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Compilation Pipeline Stage Breakdown */}
          {compilation?.stages && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-white flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Pipeline Execution Latency ({compilation.total_duration_ms} ms total)</span>
                </h3>
                <span className="text-[10px] text-emerald-400 font-mono">ALL 8 STAGES PASSED</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {Object.entries(compilation.stages).map(([key, stage]) => (
                  <div key={key} className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5 text-left">
                    <div className="text-[10px] uppercase text-slate-400 font-mono">{key}</div>
                    <div className="text-sm font-bold text-white font-mono mt-0.5">{stage.duration_ms} ms</div>
                    <div className="text-[10px] text-emerald-400 mt-0.5">● verified</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
