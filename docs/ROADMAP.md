# ROADMAP DE INGENIERÍA: FPGA-H1 VIRTUAL LAB

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `ROADMAP.md`

---

## Fases de Desarrollo

```
+-----------+     +-----------+     +-----------+     +-----------+     +-----------+
| FASE 0    | --> | FASE 1    | --> | FASE 2    | --> | FASE 3    | --> | FASE 4    |
| Infra &   |     | LUT4 Core |     | Registros |     | Routing   |     | Compilador|
| Arq Docs  |     | & Sim Func|     | Secuencial|     | Switch/CB |     | Leng H1L  |
+-----------+     +-----------+     +-----------+     +-----------+     +-----------+
      |                 |                 |                 |                 |
      v                 v                 v                 v                 v
+-----------+     +-----------+     +-----------+     +-----------+     +-----------+
| FASE 5    | --> | FASE 6    | --> | FASE 7    | --> | FASE 8    | --> | FASE 9/10 |
| ALU4      |     | Interfaz  |     | Simulación|     | Escala    |     | GW1NR-9 vs|
| Funcional |     | Visual Web|     | Temporal  |     | 8.640 LUT |     | Hardware  |
+-----------+     +-----------+     +-----------+     +-----------+     +-----------+
```

### FASE 0 — Auditoría de Infraestructura y Especificaciones Arquitectónicas
- [x] Inventario de equipos de cómputo y servidores (`docs/INFRASTRUCTURE_AUDIT.md`).
- [x] Verificación de repositorios, herramientas de compilación y pruebas.
- [x] Especificación de arquitectura general (`docs/ARCHITECTURE.md`).
- [x] Modelo matemático canónico de LUT4 y lógica combinacional (`docs/LOGIC_MODEL.md`).
- [x] Modelo y análisis comparativo de ruteo (`docs/ROUTING_MODEL.md`).
- [x] Definición formal del bitstream binario H1BS (`docs/CONFIGURATION_FORMAT.md`).
- [x] Estimación de mapeo a componentes físicos (`docs/HARDWARE_MAPPING.md`).

### FASE 1 — LUT4 y Simulador Funcional Base
- [x] Implementación orientada a objetos de la celda elemental LUT4 (`architecture/blocks/lut4/lut4_core.py`).
- [x] Motor de evaluación funcional determinista sin ramas (`simulator/logic/engine.py`).
- [x] Suite de pruebas exhaustiva con 100% de cobertura en tablas de verdad estándar (AND, OR, XOR, NAND, NOR, XNOR, MUX2, Full Adder).
- [x] Verificación de los 65.536 minitérminos posibles.

### FASE 2 — Registros Secuenciales y Basic Logic Element (BLE)
- [ ] Implementación de Flip-Flop D con reloj ascendente, reset asíncrono y síncrono, y clock enable.
- [ ] Integración del Basic Logic Element (BLE: LUT4 + DFF + Bypass Mux + Carry).
- [ ] Banco de pruebas unitarias para contadores síncronos y registros de desplazamiento.

### FASE 3 — Red de Interconexión y Routing Engine
- [ ] Implementación de Switch Boxes (SB) tipo Wilton con $F_s = 3$.
- [ ] Implementación de Connection Boxes (CB) y Crossbar local dentro del CLB (Cluster de 4 BLEs).
- [ ] Ruteador Pathfinder con resolución de congestión negociada.

### FASE 4 — Lenguaje H1L y Cadena de Compilación
- [ ] Gramática formal EBNF del lenguaje de descripción de circuitos H1L.
- [ ] Lexer y Parser sintáctico.
- [ ] Elaborador, optimizador lógico y generador de netlist.
- [ ] Ensamblador de bitstreams binarios `.h1b` con cálculo de CRC32.

### FASE 5 — Primer Circuito Completo: ALU4
- [ ] Implementación de ALU de 4 bits (ADD, SUB, AND, OR, XOR, NOT, CMP, Registrada) en recursos puros de FPGA-H1.
- [ ] Verificación exhaustiva de vectores de prueba y flags de salida (Cero, Desbordamiento, Acarreo, Signo).

### FASE 6 — Interfaz Visual de Ingeniería
- [ ] Backend FastAPI para gestión de proyectos, simulación y telemetría.
- [ ] Frontend interactivo (Vite/React) con visor de matriz lógica, editor de código H1L y osciloscopio virtual.

### FASE 7 — Motor de Simulación Temporal y Modelo de Retardos
- [ ] Modelo de retardos RC y tiempos de propagación de compuertas ($t_{pd}, t_{setup}, t_{hold}$).
- [ ] Simulación guiada por eventos temporales y detección de carreras críticas (*hazards*).

### FASE 8 — Pruebas de Escalabilidad (4 a 8.640 LUT4)
- [ ] Benchmarking sistemático a 4, 16, 64, 256, 1.024, 4.096 y 8.640 LUTs.
- [ ] Medición de tiempos de compilación, latencia de simulación, consumo de RAM y tamaño de bitstream.

### FASE 9 — Comparación con FPGAs Comerciales
- [ ] Cotejo detallado contra Gowin GW1NR-9 (Sipeed Tang Nano 9K), Lattice iCE40, ECP5 y Xilinx Artix-7.

### FASE 10 — Mapeo a Hardware Físico y Prototipado
- [ ] Prototipo físico modular con chips discretos / microcontroladores y diseño esquemático para placa de desarrollo.
