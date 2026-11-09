import React, { useState } from "react";
import type { CompilationResult } from "../types";
import { Download, Save, CheckCircle2, AlertCircle, FileCode, Cpu, ArrowRight } from "lucide-react";

interface EditorViewProps {
  sourceCode: string;
  setSourceCode: (code: string) => void;
  projectName: string;
  setProjectName: (name: string) => void;
  onSaveProject: () => void;
  onCompile: () => void;
  isCompiling: boolean;
  compilation: CompilationResult | null;
}

export const EditorView: React.FC<EditorViewProps> = ({
  sourceCode,
  setSourceCode,
  projectName,
  setProjectName,
  onSaveProject,
  onCompile,
  isCompiling,
  compilation
}) => {
  const [selectedStage, setSelectedStage] = useState<string>("optimizer");

  const lines = sourceCode.split("\n");

  const stageKeys = [
    { id: "lexer", label: "1. Lexer" },
    { id: "parser", label: "2. Parser" },
    { id: "elaborator", label: "3. Elaborator" },
    { id: "optimizer", label: "4. Optimizer" },
    { id: "netlist", label: "5. Netlist" },
    { id: "placement", label: "6. Placement" },
    { id: "routing", label: "7. Routing" },
    { id: "bitstream", label: "8. H1BS Bitstream" },
  ];

  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-slate-950 text-slate-100">
      {/* Left Pane: Code Editor */}
      <div className="flex-1 flex flex-col border-r border-slate-800 h-full min-w-0">
        {/* Editor Toolbar */}
        <div className="h-11 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileCode className="w-4 h-4 text-cyan-400" />
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-0.5 text-xs text-white font-mono focus:outline-none focus:border-cyan-500 w-36"
              placeholder="project_name"
            />
            <span className="text-slate-500 text-xs font-mono">.h1l</span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={onSaveProject}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save</span>
            </button>

            <button
              onClick={onCompile}
              disabled={isCompiling}
              className="flex items-center space-x-1.5 px-3 py-1 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs shadow-sm transition disabled:opacity-50"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>{isCompiling ? "Compiling..." : "Run Pipeline"}</span>
            </button>
          </div>
        </div>

        {/* Editor Code Area with Line Numbers */}
        <div className="flex-1 flex overflow-hidden font-mono text-xs bg-slate-950">
          {/* Line Numbers */}
          <div className="w-12 bg-slate-900/60 py-3 select-none text-right pr-3 text-slate-600 border-r border-slate-800/80">
            {lines.map((_, i) => (
              <div key={i} className="leading-5">
                {i + 1}
              </div>
            ))}
          </div>

          {/* Textarea */}
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            spellCheck={false}
            className="flex-1 p-3 bg-transparent text-slate-200 resize-none focus:outline-none leading-5 font-mono selection:bg-cyan-500/30"
          />
        </div>

        {/* Compiler Status Bar */}
        <div className="h-8 bg-slate-900 border-t border-slate-800 px-4 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center space-x-2">
            {compilation?.success ? (
              <span className="text-emerald-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Compilation Successful ({compilation.total_duration_ms} ms)</span>
              </span>
            ) : compilation?.errors ? (
              <span className="text-rose-400 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Error: {compilation.errors[0]}</span>
              </span>
            ) : (
              <span>Ready to synthesize</span>
            )}
          </div>
          <div>Lines: {lines.length}</div>
        </div>
      </div>

      {/* Right Pane: Pipeline Stage Inspector */}
      <div className="w-full lg:w-[480px] xl:w-[540px] flex flex-col bg-slate-900/40 h-full border-l border-slate-800">
        {/* Stage Tabs Header */}
        <div className="bg-slate-900 border-b border-slate-800 p-2 overflow-x-auto flex space-x-1">
          {stageKeys.map((st) => (
            <button
              key={st.id}
              onClick={() => setSelectedStage(st.id)}
              className={`px-2.5 py-1 rounded text-[11px] whitespace-nowrap font-medium transition ${
                selectedStage === st.id
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>

        {/* Stage Content */}
        <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-slate-300">
          {selectedStage === "lexer" && (
            <div className="space-y-3">
              <div className="text-slate-400 text-xs">
                Tokens generated: <span className="text-cyan-400 font-bold">{compilation?.stages?.lexer?.token_count ?? 0}</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1 max-h-[500px] overflow-y-auto">
                {compilation?.stages?.lexer?.tokens_sample?.map((tok: any, i: number) => (
                  <div key={i} className="flex justify-between py-0.5 border-b border-slate-900 text-[11px]">
                    <span className="text-purple-400">{tok.type}</span>
                    <span className="text-emerald-300 font-semibold">{tok.value}</span>
                    <span className="text-slate-600">L{tok.line}:C{tok.col}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedStage === "parser" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">Parsed Device AST:</div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <div>Device Name: <span className="text-cyan-400 font-bold">{compilation?.stages?.parser?.device_name}</span></div>
                <div>Top-level Statements: <span className="text-white">{compilation?.stages?.parser?.items_count}</span></div>
                <div>Sub-modules: <span className="text-white">{compilation?.stages?.parser?.modules_count}</span></div>
              </div>
            </div>
          )}

          {selectedStage === "elaborator" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">Resolved Signals & Ports:</div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1.5 max-h-[500px] overflow-y-auto">
                {compilation?.stages?.elaborator?.signals &&
                  Object.entries(compilation.stages.elaborator.signals).map(([sigName, details]: any) => (
                    <div key={sigName} className="flex items-center justify-between py-1 border-b border-slate-900 text-[11px]">
                      <span className="text-cyan-300">{sigName}</span>
                      <span className="px-1.5 py-0.2 rounded bg-slate-900 text-slate-400 font-bold text-[10px]">{details.direction}</span>
                      <span className="text-slate-500">[{details.width} bit]</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {selectedStage === "optimizer" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Technology Mapped LUT4s ({compilation?.stages?.optimizer?.lut4_count ?? 0})</span>
                <span>DFFs: {compilation?.stages?.optimizer?.dff_count ?? 0}</span>
              </div>
              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                {compilation?.stages?.optimizer?.luts?.map((lut: any) => (
                  <div key={lut.name} className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-1 text-[11px]">
                    <div className="flex items-center justify-between">
                      <span className="text-cyan-400 font-bold">{lut.name}</span>
                      <span className="text-emerald-400 font-mono font-semibold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60">
                        {lut.mask_hex}
                      </span>
                    </div>
                    <div className="text-slate-500 flex items-center space-x-1">
                      <span>Inputs:</span>
                      <span className="text-slate-300">{lut.inputs.join(", ")}</span>
                      <ArrowRight className="w-3 h-3 text-slate-600" />
                      <span className="text-amber-300">{lut.out}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedStage === "netlist" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">Circuit Simulation Netlist Graph:</div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <div>Graph Nodes: <span className="text-cyan-400 font-bold">{compilation?.stages?.netlist?.nodes_count}</span></div>
                <div>Inputs: <span className="text-white">{compilation?.stages?.netlist?.inputs_count}</span></div>
                <div>Outputs: <span className="text-white">{compilation?.stages?.netlist?.outputs_count}</span></div>
                <div>Configured BLEs: <span className="text-emerald-400 font-bold">{compilation?.stages?.netlist?.bles_count}</span></div>
              </div>
            </div>
          )}

          {selectedStage === "placement" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">2D Island Grid Placement:</div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <div>Grid Dimensions: <span className="text-cyan-400 font-bold">{compilation?.placement?.grid_w} × {compilation?.placement?.grid_h}</span></div>
                <div>Total CLBs: <span className="text-white">{compilation?.placement?.clbs?.length}</span></div>
                <div>Channel Width (W): <span className="text-amber-400 font-mono">{compilation?.placement?.channel_width} tracks</span></div>
              </div>
            </div>
          )}

          {selectedStage === "routing" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-400">Pathfinder Wilton Routing Metrics:</div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <div>Routing Success: <span className="text-emerald-400 font-bold">{compilation?.stages?.routing?.routed_nets_pct}%</span></div>
                <div>Congestion Iterations: <span className="text-white">{compilation?.stages?.routing?.iterations}</span></div>
                <div>Channel Segments Used: <span className="text-cyan-400">{compilation?.stages?.routing?.total_segments_used}</span></div>
              </div>
            </div>
          )}

          {selectedStage === "bitstream" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>H1BS Binary Bitstream</span>
                {compilation?.compilation_id && (
                  <a
                    href={`http://localhost:8000/api/bitstream/download/${compilation.compilation_id}`}
                    download
                    className="flex items-center space-x-1 text-cyan-400 hover:text-cyan-300 font-semibold"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download .h1bs</span>
                  </a>
                )}
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-2">
                <div>Format: <span className="text-cyan-400 font-bold">H1BS v1</span></div>
                <div>Size: <span className="text-white">{compilation?.bitstream_size_bytes} Bytes</span></div>
                <div>CRC-32: <span className="text-emerald-400 font-mono">{compilation?.stages?.bitstream?.crc32_hex}</span></div>
                <div className="mt-2 text-slate-500 text-[10px]">Hex Stream Preview:</div>
                <div className="p-2 bg-slate-900 rounded font-mono text-[10px] text-slate-400 break-all select-all">
                  {compilation?.bitstream_hex?.slice(0, 256)}...
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
