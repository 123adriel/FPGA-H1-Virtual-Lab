import React, { useState, useEffect } from "react";
import type { CompilationResult, SimulationState } from "../types";
import { Sliders, Activity } from "lucide-react";
import { updateLutMask } from "../services/api";

interface LutInspectorProps {
  compilation: CompilationResult | null;
  simulation: SimulationState | null;
  selectedBleName: string | null;
  onSelectBleName: (name: string) => void;
}

export const LutInspectorView: React.FC<LutInspectorProps> = ({
  compilation,
  simulation,
  selectedBleName,
  onSelectBleName
}) => {
  // Find all available BLEs
  const availableBles = compilation?.stages?.optimizer?.luts || [];
  const currentBleName = selectedBleName || availableBles[0]?.name || "BLE_0";

  // Find live state for current BLE
  const liveBle = simulation?.ble_states?.find((b) => b.name === currentBleName);
  const currentMaskNum = liveBle ? parseInt(liveBle.lut_mask, 16) : 0x0000;

  const [maskState, setMaskState] = useState<number>(currentMaskNum);
  const [isUpdating, setIsUpdating] = useState<boolean>(false);

  useEffect(() => {
    if (liveBle) {
      setMaskState(parseInt(liveBle.lut_mask, 16));
    }
  }, [liveBle?.lut_mask, currentBleName]);

  // Generate 16 truth table rows
  const truthTableRows = [];
  for (let idx = 0; idx < 16; idx++) {
    const i0 = idx & 1;
    const i1 = (idx >> 1) & 1;
    const i2 = (idx >> 2) & 1;
    const i3 = (idx >> 3) & 1;
    const outBit = (maskState >> idx) & 1;
    truthTableRows.push({ idx, i3, i2, i1, i0, outBit });
  }

  // Active minterm index in current simulation state
  const liveInputs = liveBle?.inputs || [0, 0, 0, 0];
  const activeMinterm = liveInputs[0] | (liveInputs[1] << 1) | (liveInputs[2] << 2) | (liveInputs[3] << 3);

  // Toggle single bit in mask
  const handleToggleBit = async (idx: number) => {
    const newMask = maskState ^ (1 << idx);
    setMaskState(newMask);
    setIsUpdating(true);
    try {
      await updateLutMask(currentBleName, newMask);
    } catch (e) {
      console.error("Failed to update LUT mask", e);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto h-full overflow-y-auto text-slate-100 space-y-6">
      {/* Header and BLE Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white">LUT4 Architecture & Truth Table Inspector</h1>
            <p className="text-xs text-slate-400">
              Inspect minterms, toggle truth table bits live, and modify FPGA-H1 silicon logic dynamically.
            </p>
          </div>
        </div>

        {/* Dropdown selector */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Target BLE:</span>
          <select
            value={currentBleName}
            onChange={(e) => onSelectBleName(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-cyan-400 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {availableBles.map((b: any) => (
              <option key={b.name} value={b.name}>
                {b.name} ({b.mask_hex})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid: Status Cards & 16-Row Truth Table */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Live Pin State & Hex Representation */}
        <div className="space-y-4">
          {/* Mask Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="text-xs text-slate-400 uppercase font-mono">16-Bit Configuration Mask</div>
            <div className="text-3xl font-bold font-mono text-cyan-400">
              0x{maskState.toString(16).toUpperCase().padStart(4, "0")}
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Binary: {maskState.toString(2).padStart(16, "0")}
            </div>
          </div>

          {/* Live Pins Indicator Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="text-xs text-slate-400 uppercase font-mono flex items-center justify-between">
              <span>Live Logic Pin States</span>
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
            </div>

            <div className="space-y-2 text-xs">
              {[0, 1, 2, 3].map((pin) => (
                <div key={pin} className="flex items-center justify-between bg-slate-950 px-3 py-1.5 rounded border border-slate-800/80">
                  <span className="text-slate-400 font-mono">Input I{pin}:</span>
                  <span
                    className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
                      liveInputs[pin] ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {liveInputs[pin]}
                  </span>
                </div>
              ))}

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between bg-slate-950 px-3 py-2 rounded border border-cyan-500/30">
                <span className="text-cyan-400 font-bold font-mono">LUT Output (O):</span>
                <span
                  className={`font-mono font-bold px-2.5 py-0.5 rounded text-xs ${
                    liveBle?.lut_out ? "bg-cyan-500 text-slate-950" : "bg-slate-800 text-slate-300"
                  }`}
                >
                  {liveBle?.lut_out ?? 0}
                </span>
              </div>

              <div className="flex items-center justify-between bg-slate-950 px-3 py-2 rounded border border-slate-800/80">
                <span className="text-amber-400 font-medium font-mono">DFF State (Q):</span>
                <span className="text-white font-mono font-bold">{liveBle?.dff_q ?? 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: 16-Row Interactive Truth Table */}
        <div className="md:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
              16-Minterm Truth Table ($2^4 = 16$)
            </h2>
            <span className="text-[10px] text-cyan-400">Click bit to toggle live</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-center border-collapse">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-mono">
                <tr>
                  <th className="py-2 px-2">Idx</th>
                  <th className="py-2 px-2">I3</th>
                  <th className="py-2 px-2">I2</th>
                  <th className="py-2 px-2">I1</th>
                  <th className="py-2 px-2">I0</th>
                  <th className="py-2 px-2 text-cyan-400">Output (O)</th>
                  <th className="py-2 px-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {truthTableRows.map((row) => {
                  const isCurrentActive = row.idx === activeMinterm;
                  return (
                    <tr
                      key={row.idx}
                      className={`transition ${
                        isCurrentActive ? "bg-cyan-500/20 font-bold text-white" : "hover:bg-slate-800/40 text-slate-300"
                      }`}
                    >
                      <td className="py-1.5 px-2 text-slate-500">{row.idx}</td>
                      <td className="py-1.5 px-2">{row.i3}</td>
                      <td className="py-1.5 px-2">{row.i2}</td>
                      <td className="py-1.5 px-2">{row.i1}</td>
                      <td className="py-1.5 px-2">{row.i0}</td>
                      <td className="py-1.5 px-2">
                        <button
                          onClick={() => handleToggleBit(row.idx)}
                          className={`w-8 py-0.5 rounded font-bold text-xs transition ${
                            row.outBit
                              ? "bg-emerald-500 hover:bg-emerald-400 text-slate-950"
                              : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                          }`}
                        >
                          {row.outBit}
                        </button>
                      </td>
                      <td className="py-1.5 px-2 text-[10px]">
                        {isCurrentActive ? (
                          <span className="text-cyan-400 font-semibold uppercase">Active Eval</span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
