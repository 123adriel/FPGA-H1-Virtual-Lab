import React, { useRef, useEffect, useState } from "react";
import type { CompilationResult, SimulationState } from "../types";
import { ZoomIn, ZoomOut, RotateCcw, Eye } from "lucide-react";

interface FloorplanCanvasProps {
  compilation: CompilationResult | null;
  simulation: SimulationState | null;
  onSelectBle: (bleName: string) => void;
}

export const FloorplanCanvas: React.FC<FloorplanCanvasProps> = ({
  compilation,
  simulation,
  onSelectBle
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Viewport transform
  const [scale, setScale] = useState<number>(1.0);
  const [offset, setOffset] = useState<{ x: number; y: number }>({ x: 80, y: 80 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Overlays
  const [showRoutingNets, setShowRoutingNets] = useState<boolean>(true);
  const [showHeatmap, setShowHeatmap] = useState<boolean>(false);
  const [selectedElement, setSelectedElement] = useState<string | null>(null);

  // Scalable grid override for GW1NR-9 reference exploration
  const [gwScale, setGwScale] = useState<number>(compilation?.placement?.grid_w || 4);

  const gridW = gwScale;
  const gridH = gwScale;

  // Visual layout constants
  const CLB_SIZE = 120;
  const CHANNEL_SIZE = 40;
  const CELL_PITCH = CLB_SIZE + CHANNEL_SIZE;

  // Zoom handlers
  const handleZoom = (delta: number) => {
    setScale((prev) => Math.max(0.15, Math.min(4.0, prev + delta)));
  };

  const handleResetView = () => {
    setScale(1.0);
    setOffset({ x: 80, y: 80 });
  };

  // Drag handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 0.1 : -0.1;
    handleZoom(zoomFactor);
  };

  // Canvas Click Detection
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - offset.x) / scale;
    const clickY = (e.clientY - rect.top - offset.y) / scale;

    const cellX = Math.floor(clickX / CELL_PITCH);
    const cellY = Math.floor(clickY / CELL_PITCH);

    if (cellX >= 0 && cellX < gridW && cellY >= 0 && cellY < gridH) {
      const withinClbX = clickX - cellX * CELL_PITCH;
      const withinClbY = clickY - cellY * CELL_PITCH;

      if (withinClbX < CLB_SIZE && withinClbY < CLB_SIZE) {
        // Clicked inside CLB: determine which BLE (0..3)
        const bleCol = withinClbX > CLB_SIZE / 2 ? 1 : 0;
        const bleRow = withinClbY > CLB_SIZE / 2 ? 1 : 0;
        const bleIdx = bleRow * 2 + bleCol;

        const clb = compilation?.placement?.clbs?.find((c) => c.x === cellX && c.y === cellY);
        const ble = clb?.bles?.[bleIdx];
        if (ble) {
          setSelectedElement(ble.name);
          onSelectBle(ble.name);
        } else {
          setSelectedElement(`CLB_${cellX}_${cellY}`);
        }
      } else {
        setSelectedElement(`SWITCH_${cellX}_${cellY}`);
      }
    }
  };

  // Main Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.parentElement?.clientWidth || 800;
    const height = canvas.parentElement?.clientHeight || 600;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Background Grid
    ctx.save();
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, width, height);

    // Apply Pan & Zoom
    ctx.translate(offset.x, offset.y);
    ctx.scale(scale, scale);

    // Level of Detail (LOD) check: skip micro details if scaled far out
    const isFarOut = scale < 0.35;

    // 1. Draw Routing Channels (Horizontal & Vertical)
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1;

    for (let x = 0; x <= gridW; x++) {
      const channelX = x * CELL_PITCH - CHANNEL_SIZE;
      if (!isFarOut) {
        // Vertical Channel Tracks
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(channelX, -CHANNEL_SIZE, CHANNEL_SIZE, gridH * CELL_PITCH + CHANNEL_SIZE);
        for (let t = 1; t <= 4; t++) {
          ctx.beginPath();
          ctx.moveTo(channelX + (t * CHANNEL_SIZE) / 5, -CHANNEL_SIZE);
          ctx.lineTo(channelX + (t * CHANNEL_SIZE) / 5, gridH * CELL_PITCH + CHANNEL_SIZE);
          ctx.stroke();
        }
      }
    }

    for (let y = 0; y <= gridH; y++) {
      const channelY = y * CELL_PITCH - CHANNEL_SIZE;
      if (!isFarOut) {
        // Horizontal Channel Tracks
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(-CHANNEL_SIZE, channelY, gridW * CELL_PITCH + CHANNEL_SIZE, CHANNEL_SIZE);
        for (let t = 1; t <= 4; t++) {
          ctx.beginPath();
          ctx.moveTo(-CHANNEL_SIZE, channelY + (t * CHANNEL_SIZE) / 5);
          ctx.lineTo(gridW * CELL_PITCH + CHANNEL_SIZE, channelY + (t * CHANNEL_SIZE) / 5);
          ctx.stroke();
        }
      }
    }

    // 2. Draw Wilton Switch Boxes at Intersections
    for (let x = 0; x <= gridW; x++) {
      for (let y = 0; y <= gridH; y++) {
        const sbX = x * CELL_PITCH - CHANNEL_SIZE;
        const sbY = y * CELL_PITCH - CHANNEL_SIZE;

        ctx.fillStyle = "#1e1b4b";
        ctx.fillRect(sbX, sbY, CHANNEL_SIZE, CHANNEL_SIZE);
        ctx.strokeStyle = "#4338ca";
        ctx.strokeRect(sbX, sbY, CHANNEL_SIZE, CHANNEL_SIZE);

        if (!isFarOut) {
          ctx.fillStyle = "#818cf8";
          ctx.font = "8px monospace";
          ctx.textAlign = "center";
          ctx.fillText("SB", sbX + CHANNEL_SIZE / 2, sbY + CHANNEL_SIZE / 2 + 3);
        }
      }
    }

    // 3. Draw CLBs and BLEs
    for (let gy = 0; gy < gridH; gy++) {
      for (let gx = 0; gx < gridW; gx++) {
        const clbX = gx * CELL_PITCH;
        const clbY = gy * CELL_PITCH;

        const clb = compilation?.placement?.clbs?.find((c) => c.x === gx && c.y === gy);
        const isActiveClb = clb && clb.active_bles > 0;

        // CLB Box
        ctx.fillStyle = isActiveClb ? "#0f2338" : "#090d16";
        ctx.fillRect(clbX, clbY, CLB_SIZE, CLB_SIZE);

        ctx.strokeStyle = isActiveClb ? "#0284c7" : "#1e293b";
        ctx.lineWidth = isActiveClb ? 1.5 : 1;
        ctx.strokeRect(clbX, clbY, CLB_SIZE, CLB_SIZE);

        // Header Label
        if (!isFarOut) {
          ctx.fillStyle = isActiveClb ? "#38bdf8" : "#475569";
          ctx.font = "9px monospace";
          ctx.textAlign = "left";
          ctx.fillText(`CLB (${gx}, ${gy})`, clbX + 6, clbY + 12);
        }

        // Draw 4 BLEs inside CLB
        if (!isFarOut) {
          const bleW = (CLB_SIZE - 16) / 2;
          const bleH = (CLB_SIZE - 24) / 2;

          for (let b = 0; b < 4; b++) {
            const bx = clbX + 6 + (b % 2) * (bleW + 4);
            const by = clbY + 16 + Math.floor(b / 2) * (bleH + 4);

            const bleData = clb?.bles?.[b];
            const isBleActive = bleData?.active;
            const isSelected = selectedElement === bleData?.name;

            // Check live state
            const liveBle = simulation?.ble_states?.find((s) => s.name === bleData?.name);
            const liveOut = liveBle?.out ?? 0;

            ctx.fillStyle = isSelected
              ? "#1e3a5f"
              : isBleActive
              ? liveOut
                ? "#064e3b"
                : "#1e293b"
              : "#0b0f17";

            ctx.fillRect(bx, by, bleW, bleH);

            ctx.strokeStyle = isSelected
              ? "#38bdf8"
              : isBleActive
              ? liveOut
                ? "#10b981"
                : "#0284c7"
              : "#1e293b";
            ctx.lineWidth = isSelected ? 2 : 1;
            ctx.strokeRect(bx, by, bleW, bleH);

            // BLE Text
            ctx.fillStyle = isBleActive ? "#e2e8f0" : "#475569";
            ctx.font = "7.5px monospace";
            ctx.fillText(bleData?.name ? bleData.name.slice(0, 7) : `B${b}`, bx + 3, by + 10);

            if (bleData?.lut_mask && bleData.lut_mask !== "0x0000") {
              ctx.fillStyle = "#38bdf8";
              ctx.fillText(bleData.lut_mask, bx + 3, by + 20);
            }

            // Live Output Indicator Dot
            if (isBleActive) {
              ctx.fillStyle = liveOut ? "#34d399" : "#64748b";
              ctx.beginPath();
              ctx.arc(bx + bleW - 6, by + 7, 3, 0, Math.PI * 2);
              ctx.fill();
            }
          }
        }
      }
    }

    // 4. Draw Routed Net Paths Overlay
    if (showRoutingNets && compilation?.routing?.nets) {
      const netColors = ["#ec4899", "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#06b6d4"];

      compilation.routing.nets.forEach((net, idx) => {
        const color = netColors[idx % netColors.length];
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";

        const srcX = net.source.x * CELL_PITCH + CLB_SIZE / 2;
        const srcY = net.source.y * CELL_PITCH + CLB_SIZE / 2;

        net.sinks.forEach((sink) => {
          const dstX = sink.x * CELL_PITCH + CLB_SIZE / 2;
          const dstY = sink.y * CELL_PITCH + CLB_SIZE / 2;

          ctx.beginPath();
          ctx.moveTo(srcX, srcY);
          // Draw Manhattan routing path
          const midX = (srcX + dstX) / 2;
          ctx.lineTo(midX, srcY);
          ctx.lineTo(midX, dstY);
          ctx.lineTo(dstX, dstY);
          ctx.stroke();

          // Draw sink endpoint dot
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(dstX, dstY, 3.5, 0, Math.PI * 2);
          ctx.fill();
        });
      });
    }

    ctx.restore();

    // 5. Draw Viewport Minimap in Bottom Right
    const mmSize = 120;
    const mmX = width - mmSize - 16;
    const mmY = height - mmSize - 16;

    ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
    ctx.fillRect(mmX, mmY, mmSize, mmSize);
    ctx.strokeStyle = "#334155";
    ctx.strokeRect(mmX, mmY, mmSize, mmSize);

    const worldW = gridW * CELL_PITCH;
    const worldH = gridH * CELL_PITCH;
    const mmScaleX = mmSize / worldW;
    const mmScaleY = mmSize / worldH;

    // Draw active CLBs on minimap
    compilation?.placement?.clbs?.forEach((clb) => {
      if (clb.active_bles > 0) {
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(
          mmX + clb.x * CELL_PITCH * mmScaleX,
          mmY + clb.y * CELL_PITCH * mmScaleY,
          CLB_SIZE * mmScaleX,
          CLB_SIZE * mmScaleY
        );
      }
    });

    // Draw current viewport rectangle on minimap
    const vpX = mmX - (offset.x / scale) * mmScaleX;
    const vpY = mmY - (offset.y / scale) * mmScaleY;
    const vpW = (width / scale) * mmScaleX;
    const vpH = (height / scale) * mmScaleY;

    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 1;
    ctx.strokeRect(vpX, vpY, vpW, vpH);

  }, [scale, offset, compilation, simulation, selectedElement, showRoutingNets, showHeatmap, gwScale]);

  return (
    <div className="relative w-full h-full overflow-hidden bg-slate-950 select-none">
      {/* Floating Canvas Toolbar */}
      <div className="absolute top-4 left-4 z-10 flex items-center bg-slate-900/90 backdrop-blur border border-slate-800 rounded-lg p-1.5 space-x-2 text-xs shadow-xl">
        <button
          onClick={() => handleZoom(0.15)}
          className="p-1 rounded text-slate-300 hover:bg-slate-800 hover:text-white"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>

        <button
          onClick={() => handleZoom(-0.15)}
          className="p-1 rounded text-slate-300 hover:bg-slate-800 hover:text-white"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>

        <button
          onClick={handleResetView}
          className="p-1 rounded text-slate-300 hover:bg-slate-800 hover:text-white"
          title="Reset Pan & Zoom"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-slate-800" />

        <button
          onClick={() => setShowRoutingNets(!showRoutingNets)}
          className={`flex items-center space-x-1 px-2 py-0.5 rounded transition ${
            showRoutingNets ? "bg-cyan-500/20 text-cyan-400 font-semibold" : "text-slate-400 hover:text-white"
          }`}
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Nets</span>
        </button>

        <div className="h-4 w-px bg-slate-800" />

        {/* Scalability Dimension Switcher (2x2 up to 47x47 GW1NR-9 reference) */}
        <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
          <span>Grid:</span>
          <select
            value={gwScale}
            onChange={(e) => setGwScale(Number(e.target.value))}
            className="bg-slate-950 border border-slate-800 text-cyan-400 rounded px-1 py-0.5 focus:outline-none"
          >
            <option value={compilation?.placement?.grid_w || 4}>Circuit ({compilation?.placement?.grid_w || 4}×{compilation?.placement?.grid_w || 4})</option>
            <option value={8}>Standard 8×8 (256 LUTs)</option>
            <option value={16}>Medium 16×16 (1,024 LUTs)</option>
            <option value={32}>Large 32×32 (4,096 LUTs)</option>
            <option value={47}>GW1NR-9 47×47 (8,640 LUTs)</option>
          </select>
        </div>
      </div>

      {/* Selected Element Quick Info Panel */}
      {selectedElement && (
        <div className="absolute top-4 right-4 z-10 bg-slate-900/90 backdrop-blur border border-slate-800 rounded-lg p-3 text-xs shadow-xl space-y-1.5 min-w-[200px]">
          <div className="text-[10px] text-slate-500 uppercase font-mono">Selected Element</div>
          <div className="font-bold text-cyan-400 font-mono text-sm">{selectedElement}</div>
          <button
            onClick={() => onSelectBle(selectedElement)}
            className="w-full mt-2 py-1 rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 font-medium text-[11px] transition"
          >
            Open in LUT Inspector
          </button>
        </div>
      )}

      {/* HTML5 Canvas */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onClick={handleCanvasClick}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />
    </div>
  );
};
