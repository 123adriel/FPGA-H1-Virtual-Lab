import { useState, useEffect, useRef } from "react";
import { Navbar } from "./components/Navbar";
import { DashboardView } from "./components/DashboardView";
import { EditorView } from "./components/EditorView";
import { FloorplanCanvas } from "./components/FloorplanCanvas";
import { LutInspectorView } from "./components/LutInspectorView";
import { WaveformViewer } from "./components/WaveformViewer";
import { BenchmarkView } from "./components/BenchmarkView";
import {
  fetchProjects,
  fetchProject,
  saveProject,
  compileCode,
  stepSimulation,
  fetchBenchmarks,
  createSimulationSocket
} from "./services/api";
import type { ProjectSummary, CompilationResult, SimulationState, BenchmarkItem } from "./types";

export function App() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string>("");
  const [projectName, setProjectName] = useState<string>("alu4");
  const [sourceCode, setSourceCode] = useState<string>("");
  const [compilation, setCompilation] = useState<CompilationResult | null>(null);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);

  // Simulation & Telemetry State
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [simHistory, setSimHistory] = useState<SimulationState[]>([]);
  const [isSimRunning, setIsSimRunning] = useState<boolean>(false);
  const [simSpeed, setSimSpeed] = useState<number>(2.0);

  // Benchmarks
  const [benchmarks, setBenchmarks] = useState<BenchmarkItem[]>([]);
  const [selectedBleName, setSelectedBleName] = useState<string | null>(null);

  const socketRef = useRef<{ socket: WebSocket; send: (msg: any) => void; close: () => void } | null>(null);

  // 1. Initial Data Fetch
  useEffect(() => {
    async function init() {
      try {
        const projList = await fetchProjects();
        setProjects(projList);

        const benchList = await fetchBenchmarks();
        setBenchmarks(benchList);

        // Load ALU4 by default
        const alu4 = projList.find((p) => p.name === "alu4") || projList[0];
        if (alu4) {
          setActiveProjectId(alu4.id);
          const detail = await fetchProject(alu4.id);
          setProjectName(detail.name);
          setSourceCode(detail.source_code);

          // Auto compile on first load
          const comp = await compileCode(detail.source_code, detail.id);
          setCompilation(comp);
        }
      } catch (e) {
        console.error("Initialization error", e);
      }
    }
    init();
  }, []);

  // 2. WebSocket Telemetry Connection
  useEffect(() => {
    const ws = createSimulationSocket(
      (newState) => {
        setSimulation(newState);
        setSimHistory((prev) => {
          const next = [...prev, newState];
          return next.slice(-250);
        });
      },
      (err) => console.warn("Sim WS", err)
    );
    socketRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  // Handle Project Selection
  const handleSelectProject = async (id: string) => {
    try {
      setActiveProjectId(id);
      const detail = await fetchProject(id);
      setProjectName(detail.name);
      setSourceCode(detail.source_code);

      setIsCompiling(true);
      const comp = await compileCode(detail.source_code, detail.id);
      setCompilation(comp);
      setSimHistory([]);
    } catch (e) {
      console.error("Error loading project", e);
    } finally {
      setIsCompiling(false);
    }
  };

  // Handle Save
  const handleSaveProject = async () => {
    try {
      const saved = await saveProject(projectName, sourceCode, "Saved from Lab", "custom", activeProjectId || undefined);
      setActiveProjectId(saved.id);
      const updatedList = await fetchProjects();
      setProjects(updatedList);
    } catch (e) {
      console.error("Save failed", e);
    }
  };

  // Handle Compile
  const handleCompile = async () => {
    setIsCompiling(true);
    try {
      const comp = await compileCode(sourceCode, activeProjectId || undefined);
      setCompilation(comp);
      setSimHistory([]);
    } catch (e) {
      console.error("Compilation failed", e);
    } finally {
      setIsCompiling(false);
    }
  };

  // Sim Controls
  const handleToggleSim = () => {
    if (isSimRunning) {
      socketRef.current?.send({ type: "PAUSE" });
      setIsSimRunning(false);
    } else {
      socketRef.current?.send({ type: "RUN", speed_hz: simSpeed });
      setIsSimRunning(true);
    }
  };

  const handleStepSim = async () => {
    try {
      socketRef.current?.send({ type: "STEP" });
    } catch (e) {
      const res = await stepSimulation();
      setSimulation(res);
      setSimHistory((prev) => [...prev, res].slice(-250));
    }
  };

  const handleResetSim = async () => {
    socketRef.current?.send({ type: "RESET" });
    setIsSimRunning(false);
    setSimHistory([]);
  };

  const handleSpeedChange = (speed: number) => {
    setSimSpeed(speed);
    if (isSimRunning) {
      socketRef.current?.send({ type: "RUN", speed_hz: speed });
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        compilation={compilation}
        simulation={simulation}
        isSimRunning={isSimRunning}
        onToggleSim={handleToggleSim}
        onStepSim={handleStepSim}
        onResetSim={handleResetSim}
        simSpeed={simSpeed}
        onSpeedChange={handleSpeedChange}
        onCompile={handleCompile}
        isCompiling={isCompiling}
      />

      <main className="flex-1 overflow-hidden relative">
        {activeTab === "dashboard" && (
          <DashboardView
            projects={projects}
            activeProjectId={activeProjectId}
            onSelectProject={handleSelectProject}
            compilation={compilation}
            benchmarks={benchmarks}
            onOpenStudio={() => setActiveTab("editor")}
          />
        )}

        {activeTab === "editor" && (
          <EditorView
            sourceCode={sourceCode}
            setSourceCode={setSourceCode}
            projectName={projectName}
            setProjectName={setProjectName}
            onSaveProject={handleSaveProject}
            onCompile={handleCompile}
            isCompiling={isCompiling}
            compilation={compilation}
          />
        )}

        {activeTab === "floorplan" && (
          <FloorplanCanvas
            compilation={compilation}
            simulation={simulation}
            onSelectBle={(bleName) => {
              setSelectedBleName(bleName);
              setActiveTab("lut");
            }}
          />
        )}

        {activeTab === "lut" && (
          <LutInspectorView
            compilation={compilation}
            simulation={simulation}
            selectedBleName={selectedBleName}
            onSelectBleName={setSelectedBleName}
          />
        )}

        {activeTab === "waveform" && (
          <WaveformViewer
            compilation={compilation}
            simulation={simulation}
            history={simHistory}
            onStep={handleStepSim}
            onReset={handleResetSim}
            isSimRunning={isSimRunning}
            onToggleSim={handleToggleSim}
          />
        )}

        {activeTab === "benchmarks" && (
          <BenchmarkView
            benchmarks={benchmarks}
            onRefreshBenchmarks={async () => {
              const b = await fetchBenchmarks();
              setBenchmarks(b);
            }}
          />
        )}
      </main>
    </div>
  );
}

export default App;
