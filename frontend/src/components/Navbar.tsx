import React from "react";
import { Play, Pause, StepForward, RotateCcw, Cpu, Layers, Activity, Code2, Grid3X3, Sliders, LineChart } from "lucide-react";
import type { CompilationResult, SimulationState } from "../types";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  compilation: CompilationResult | null;
  simulation: SimulationState | null;
  isSimRunning: boolean;
  onToggleSim: () => void;
  onStepSim: () => void;
  onResetSim: () => void;
  simSpeed: number;
  onSpeedChange: (speed: number) => void;
  onCompile: () => void;
  isCompiling: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  compilation,
  simulation,
  isSimRunning,
  onToggleSim,
  onStepSim,
  onResetSim,
  simSpeed,
  onSpeedChange,
  onCompile,
  isCompiling,
}) => {
  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 text-white flex items-center justify-between px-4 select-none">
      {/* Brand & Tabs */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
            H1
          </div>
          <div>
            <div className="font-bold text-sm tracking-wide bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              FPGA-H1
            </div>
            <div className="text-[10px] text-slate-400 -mt-0.5">VIRTUAL LAB</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800/80 text-xs font-medium">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "dashboard" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab("editor")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "editor" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>H1L Studio</span>
          </button>

          <button
            onClick={() => setActiveTab("floorplan")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "floorplan" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Grid3X3 className="w-3.5 h-3.5" />
            <span>Floorplan & Routing</span>
          </button>

          <button
            onClick={() => setActiveTab("lut")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "lut" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>LUT Inspector</span>
          </button>

          <button
            onClick={() => setActiveTab("waveform")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "waveform" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Waveform</span>
          </button>

          <button
            onClick={() => setActiveTab("benchmarks")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
              activeTab === "benchmarks" ? "bg-cyan-500/20 text-cyan-400 font-semibold shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            <span>GW1NR-9 Scale</span>
          </button>
        </nav>
      </div>

      {/* Center Hardware Stat Badges */}
      {compilation && (
        <div className="hidden lg:flex items-center space-x-3 text-xs bg-slate-950/40 border border-slate-800/80 px-3 py-1 rounded-full">
          <div className="flex items-center space-x-1 text-slate-300">
            <Cpu className="w-3 h-3 text-cyan-400" />
            <span>Device:</span>
            <span className="font-semibold text-cyan-300">{compilation.device}</span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="text-slate-400">
            LUT4: <span className="text-white font-mono">{compilation.resources.luts_used}</span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="text-slate-400">
            CLB: <span className="text-white font-mono">{compilation.resources.clbs_used}</span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="text-slate-400">
            DFF: <span className="text-white font-mono">{compilation.resources.dffs_used}</span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="text-slate-400">
            CRC32:{" "}
            <span className="text-emerald-400 font-mono">
              {compilation.stages?.bitstream?.crc32_hex || "0x00000000"}
            </span>
          </div>
        </div>
      )}

      {/* Simulator Controls & Compile Trigger */}
      <div className="flex items-center space-x-3">
        {/* Sim Toolbar */}
        <div className="flex items-center bg-slate-800/90 rounded-lg p-1 border border-slate-700/80 space-x-1">
          <button
            onClick={onToggleSim}
            className={`p-1.5 rounded hover:bg-slate-700 transition ${
              isSimRunning ? "text-amber-400 hover:text-amber-300" : "text-emerald-400 hover:text-emerald-300"
            }`}
            title={isSimRunning ? "Pause Simulation" : "Run Simulation"}
          >
            {isSimRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={onStepSim}
            className="p-1.5 rounded text-slate-300 hover:bg-slate-700 hover:text-white transition"
            title="Step Clock Cycle"
          >
            <StepForward className="w-4 h-4" />
          </button>

          <button
            onClick={onResetSim}
            className="p-1.5 rounded text-slate-400 hover:bg-slate-700 hover:text-rose-400 transition"
            title="Reset Simulation"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <div className="h-4 w-px bg-slate-700 mx-1" />

          {/* Speed selector */}
          <select
            value={simSpeed}
            onChange={(e) => onSpeedChange(Number(e.target.value))}
            className="bg-transparent text-[11px] text-slate-300 px-1 py-0.5 rounded cursor-pointer focus:outline-none"
          >
            <option value={0.5} className="bg-slate-900">0.5 Hz</option>
            <option value={1} className="bg-slate-900">1 Hz</option>
            <option value={2} className="bg-slate-900">2 Hz</option>
            <option value={5} className="bg-slate-900">5 Hz</option>
            <option value={10} className="bg-slate-900">10 Hz</option>
          </select>

          <div className="text-[11px] font-mono text-cyan-400 px-2 bg-slate-900/80 rounded py-0.5 border border-slate-800">
            T={simulation?.cycle ?? 0}
          </div>
        </div>

        {/* Compile Button */}
        <button
          onClick={onCompile}
          disabled={isCompiling}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-xs shadow-md shadow-cyan-500/20 disabled:opacity-50 transition"
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>{isCompiling ? "Compiling..." : "Build Bitstream"}</span>
        </button>
      </div>
    </header>
  );
};
