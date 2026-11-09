import React, { useRef, useEffect, useState } from "react";
import type { SimulationState, CompilationResult } from "../types";
import { Play, Pause, StepForward, RotateCcw, Activity } from "lucide-react";
import { updateInputs } from "../services/api";

interface WaveformViewerProps {
  compilation: CompilationResult | null;
  simulation: SimulationState | null;
  history: SimulationState[];
  onStep: () => void;
  onReset: () => void;
  isSimRunning: boolean;
  onToggleSim: () => void;
}

export const WaveformViewer: React.FC<WaveformViewerProps> = ({
  compilation,
  simulation,
  history,
  onStep,
  onReset,
  isSimRunning,
  onToggleSim
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Collect all signals to display
  const inputs = compilation?.inputs || [];
  const outputs = compilation?.outputs || [];
  const clocks = compilation?.clocks?.length ? compilation.clocks : ["CLK"];

  // Combine signal rows
  const signals: { name: string; type: "clk" | "input" | "output" }[] = [
    ...clocks.map((c) => ({ name: c, type: "clk" as const })),
    ...inputs.map((i) => ({ name: i, type: "input" as const })),
    ...outputs.map((o) => ({ name: o, type: "output" as const })),
  ];

  // Stimulus inputs state for interactive toggles
  const [currentInputs, setCurrentInputs] = useState<Record<string, number>>(simulation?.inputs || {});

  useEffect(() => {
    if (simulation?.inputs) {
      setCurrentInputs(simulation.inputs);
    }
  }, [simulation?.inputs]);

  const handleToggleInput = async (name: string) => {
    const newVal = currentInputs[name] ? 0 : 1;
    const updated = { ...currentInputs, [name]: newVal };
    setCurrentInputs(updated);
    try {
      await updateInputs(updated);
    } catch (e) {
      console.error("Failed to update input stimulus", e);
    }
  };

  // Waveform drawing constants
  const ROW_HEIGHT = 32;
  const STEP_WIDTH = 28;
  const WAVE_HEIGHT = 16;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const totalSteps = Math.max(25, history.length);
    const width = Math.max(canvas.parentElement?.clientWidth || 800, totalSteps * STEP_WIDTH + 40);
    const height = signals.length * ROW_HEIGHT + 36;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, width, height);

    // 1. Time / Cycle Grid & Header
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "9px monospace";
    ctx.textAlign = "center";

    for (let s = 0; s < totalSteps; s++) {
      const x = s * STEP_WIDTH + 14;
      ctx.beginPath();
      ctx.moveTo(x, 24);
      ctx.lineTo(x, height);
      ctx.stroke();

      // Cycle numbers on top
      ctx.fillText(`T${s}`, x, 14);
    }

    // 2. Render each signal waveform
    signals.forEach((sig, rowIdx) => {
      const yBase = 28 + rowIdx * ROW_HEIGHT + ROW_HEIGHT / 2;
      const yLow = yBase + WAVE_HEIGHT / 2;
      const yHigh = yBase - WAVE_HEIGHT / 2;

      // Color coding
      let strokeColor = "#38bdf8"; // cyan for clock
      if (sig.type === "input") strokeColor = "#a855f7"; // purple for inputs
      if (sig.type === "output") strokeColor = "#10b981"; // emerald for outputs

      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1.75;
      ctx.beginPath();

      let prevVal: number | null = null;

      history.forEach((state, stepIdx) => {
        const xStart = stepIdx * STEP_WIDTH + 14;
        const xEnd = xStart + STEP_WIDTH;

        let val = 0;
        if (sig.type === "clk") {
          val = state.clk;
        } else if (sig.type === "input") {
          val = state.inputs[sig.name] ?? 0;
        } else {
          val = state.outputs[sig.name] ?? 0;
        }

        const yVal = val ? yHigh : yLow;

        if (stepIdx === 0) {
          ctx.moveTo(xStart, yVal);
          ctx.lineTo(xEnd, yVal);
        } else {
          // Draw transition edge if value changed
          if (prevVal !== null && prevVal !== val) {
            ctx.lineTo(xStart, yVal);
          }
          ctx.lineTo(xEnd, yVal);
        }

        prevVal = val;
      });

      ctx.stroke();
    });

  }, [history, signals]);

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Controls Toolbar */}
      <div className="h-12 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          <h1 className="text-xs font-bold text-white tracking-wide">
            Digital Logic Waveform & Signal Oscilloscope
          </h1>
          <span className="text-slate-500 text-xs">({history.length} cycles recorded)</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleSim}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded text-xs transition ${
              isSimRunning ? "bg-amber-500/20 text-amber-300" : "bg-emerald-500/20 text-emerald-400"
            }`}
          >
            {isSimRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isSimRunning ? "Pause" : "Auto Clock"}</span>
          </button>

          <button
            onClick={onStep}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition"
          >
            <StepForward className="w-3.5 h-3.5" />
            <span>Step Cycle</span>
          </button>

          <button
            onClick={onReset}
            className="flex items-center space-x-1 px-2 py-1 rounded bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 text-xs transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Main Waveform Split: Left Signal Labels / Stimulus vs Right Waveform Canvas */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Signal Tree & Stimulus Toggles */}
        <div className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col pt-7 select-none shrink-0">
          {signals.map((sig) => {
            const isInput = sig.type === "input";
            const val = isInput
              ? currentInputs[sig.name] ?? 0
              : sig.type === "clk"
              ? simulation?.clk ?? 0
              : simulation?.outputs?.[sig.name] ?? 0;

            return (
              <div
                key={sig.name}
                className="h-8 flex items-center justify-between px-3 border-b border-slate-800/60 text-xs font-mono"
              >
                <div className="flex items-center space-x-1.5 truncate">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      sig.type === "clk"
                        ? "bg-cyan-400"
                        : sig.type === "input"
                        ? "bg-purple-400"
                        : "bg-emerald-400"
                    }`}
                  />
                  <span className="truncate text-slate-300 font-medium" title={sig.name}>
                    {sig.name}
                  </span>
                </div>

                {/* Value or Stimulus Button */}
                {isInput ? (
                  <button
                    onClick={() => handleToggleInput(sig.name)}
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold transition ${
                      val ? "bg-purple-500 text-white" : "bg-slate-800 text-slate-400"
                    }`}
                    title="Click to toggle input stimulus"
                  >
                    {val}
                  </button>
                ) : (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      val ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-800 text-slate-500"
                    }`}
                  >
                    {val}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Right Scrollable Canvas Area */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden bg-slate-950">
          <canvas ref={canvasRef} />
        </div>
      </div>
    </div>
  );
};
