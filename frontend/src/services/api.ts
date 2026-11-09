import type { ProjectSummary, ProjectDetail, CompilationResult, SimulationState, BenchmarkItem } from "../types";

const API_BASE = "http://localhost:8000/api";
const WS_BASE = "ws://localhost:8000/ws/simulate";

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  const res = await fetch(`${API_BASE}/projects`);
  return res.json();
}

export async function fetchProject(id: string): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  return res.json();
}

export async function saveProject(name: string, source_code: string, description = "", category = "custom", project_id?: string): Promise<ProjectDetail> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, source_code, description, category, project_id })
  });
  return res.json();
}

export async function compileCode(source_code: string, project_id?: string, channel_width = 8): Promise<CompilationResult> {
  const res = await fetch(`${API_BASE}/compile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_code, project_id, channel_width })
  });
  return res.json();
}

export async function stepSimulation(inputs?: Record<string, number>): Promise<SimulationState> {
  const res = await fetch(`${API_BASE}/simulate/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inputs })
  });
  return res.json();
}

export async function resetSimulation(): Promise<SimulationState> {
  const res = await fetch(`${API_BASE}/simulate/reset`, { method: "POST" });
  return res.json();
}

export async function updateInputs(inputs: Record<string, number>): Promise<SimulationState> {
  const res = await fetch(`${API_BASE}/simulate/inputs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inputs })
  });
  return res.json();
}

export async function updateLutMask(ble_name: string, mask: number): Promise<any> {
  const res = await fetch(`${API_BASE}/lut/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ble_name, mask })
  });
  return res.json();
}

export async function fetchBenchmarks(): Promise<BenchmarkItem[]> {
  const res = await fetch(`${API_BASE}/benchmarks`);
  return res.json();
}

export async function runBenchmarks(): Promise<BenchmarkItem[]> {
  const res = await fetch(`${API_BASE}/benchmarks/run`, { method: "POST" });
  return res.json();
}

export function createSimulationSocket(
  onState: (state: SimulationState) => void,
  onError?: (err: string) => void
): { socket: WebSocket; send: (msg: any) => void; close: () => void } {
  const socket = new WebSocket(WS_BASE);

  socket.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      if (parsed.type === "STATE" && parsed.data) {
        onState(parsed.data);
      } else if (parsed.type === "ERROR") {
        onError?.(parsed.message);
      }
    } catch (e) {
      console.error("WS Parse error", e);
    }
  };

  socket.onerror = (e) => {
    onError?.("WebSocket connection error");
  };

  return {
    socket,
    send: (msg: any) => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(msg));
      }
    },
    close: () => socket.close()
  };
}
