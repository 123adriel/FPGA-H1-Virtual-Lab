// Data Models for FPGA-H1 Virtual Lab

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends ProjectSummary {
  source_code: string;
}

export interface PipelineStageInfo {
  name: string;
  duration_ms: number;
  status: "success" | "warning" | "error";
  error?: string;
  [key: string]: any;
}

export interface BleDetail {
  ble_id: number;
  name: string;
  lut_mask: string;
  bypass_ff: boolean;
  active: boolean;
}

export interface ClbDetail {
  x: number;
  y: number;
  clb_id: string;
  active_bles: number;
  bles: BleDetail[];
}

export interface PlacementData {
  grid_w: number;
  grid_h: number;
  channel_width: number;
  clbs: ClbDetail[];
}

export interface RoutedNetSink {
  x: number;
  y: number;
  input_pin: number;
}

export interface RoutedNet {
  name: string;
  source: { x: number; y: number; ble_pin: number };
  sinks: RoutedNetSink[];
  routed_segments: string[];
}

export interface RoutingData {
  channel_width: number;
  routed_nets_pct: number;
  iterations: number;
  total_segments_used: number;
  nets: RoutedNet[];
}

export interface CompilationResult {
  success: boolean;
  total_duration_ms: number;
  errors?: string[];
  device: string;
  inputs: string[];
  outputs: string[];
  clocks: string[];
  resources: {
    luts_used: number;
    dffs_used: number;
    clbs_used: number;
    io_pins: number;
    bitstream_bytes: number;
  };
  stages: Record<string, PipelineStageInfo>;
  placement: PlacementData;
  routing: RoutingData;
  bitstream_hex: string;
  bitstream_size_bytes: number;
  compilation_id: string | null;
}

export interface BleLiveState {
  name: string;
  ble_id: number;
  lut_mask: string;
  inputs: number[];
  lut_out: number;
  dff_q: number;
  out: number;
  bypass_ff: boolean;
}

export interface SimulationState {
  cycle: number;
  clk: number;
  inputs: Record<string, number>;
  outputs: Record<string, number>;
  ble_states: BleLiveState[];
  timestamp: number;
}

export interface BenchmarkItem {
  id: string;
  scale_name: string;
  target_luts: number;
  grid_w: number;
  grid_h: number;
  compile_time_ms: number;
  placement_time_ms: number;
  routing_time_ms: number;
  bitstream_time_ms: number;
  sim_step_us: number;
  memory_kb: number;
  timestamp: string;
}
