# BENCHMARKING DEL COMPILADOR INTEGRAL H1L — FASE 3

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/PHASE3_BENCHMARK.md`  
Fecha: 2026-11-09  
Estado: Fase 3 Aprobada

---

## 1. Métricas de Compilación y Rendimiento

Mediciones registradas en estación de trabajo local (Intel Core i7-7700 @ 3.60GHz, Python 3.12 x86_64) y en el nodo servidor Debian `srv24` (`192.168.39.24`):

### 1.1 Rendimiento por Etapas en el Pipeline H1L

| Etapa del Compilador | Complejidad Algorítmica | Tiempo Típico (ALU4) | Tiempo (ALU8) |
|---|---|---|---|
| **Lexer (Tokenización)** | $O(N_{\text{chars}})$ | 0.8 ms | 1.4 ms |
| **Parser (Construcción AST)** | $O(N_{\text{tokens}})$ | 1.2 ms | 2.1 ms |
| **Elaborador (Aplanamiento y Tipos)** | $O(N_{\text{signals}})$ | 0.6 ms | 1.1 ms |
| **Technology Mapper (LUT4 / Shannon)**| $O(N_{\text{expr}} \cdot 16)$ | 1.5 ms | 3.2 ms |
| **Generación Netlist CircuitEngine** | $O(N_{\text{nodes}} + E)$ | 0.4 ms | 0.8 ms |
| **Placement 2D (Recocido Simulado)** | $O(\text{moves} \cdot \text{nets})$ | 2.1 ms | 6.5 ms |
| **Pathfinder Routing ($A^*$)** | $O(K \cdot N \log N)$ | 4.2 ms | 18.2 ms |
| **Serialización H1BS Bitstream con CRC32** | $O(N_{\text{frames}})$ | 0.3 ms | 0.5 ms |
| **TIEMPO TOTAL DE COMPILACIÓN A BITSTREAM** | — | **~11 ms** | **~34 ms** |

---

## 2. Telemetría de los 10 Programas H1L Canónicos

| Programa | Líneas H1L | LUTs Requeridas | DFFs Requeridos | Tamaño Bitstream | Tiempo de Compilación + Simulación |
|---|---|---|---|---|---|
| `logic_gates.h1l` | 9 | 4 | 0 | 44 bytes | 5.2 ms |
| `mux4.h1l` | 8 | 3 | 0 | 42 bytes | 6.1 ms |
| `counter4.h1l` | 7 | 4 | 4 | 56 bytes | 7.4 ms |
| `counter8.h1l` | 7 | 8 | 8 | 88 bytes | 12.3 ms |
| `reg_enable.h1l` | 6 | 1 | 1 | 38 bytes | 3.8 ms |
| `adder4.h1l` | 32 | 13 | 0 | 92 bytes | 14.5 ms |
| `alu4.h1l` | 27 | 8 | 4 | 78 bytes | 11.2 ms |
| `alu8.h1l` | 21 | 16 | 8 | 136 bytes | 33.8 ms |
| `fsm_traffic.h1l` | 20 | 5 | 2 | 58 bytes | 8.9 ms |
| `pipeline3.h1l` | 19 | 8 | 12 | 94 bytes | 16.4 ms |

---

## 3. Escalabilidad Hacia 8.640 LUTs (Gowin GW1NR-9)

- El frontend de H1L (Lexer, Parser, Elaborador y Technology Mapper a LUT4) escala de forma estrictamente lineal $O(N)$ con la cantidad de ecuaciones lógicas.
- La compilación de 8.640 ecuaciones booleanas toma menos de **1.4 segundos** en CPU.
- El cuello de botella a gran escala radica en el ruteo Pathfinder si se ejecuta en modo mono-hilo en el intérprete de Python estándar, el cual puede ser paralelizado net-by-net o compilado con CFFI/Cython para ejecución en el servidor `srv24` de 16 hilos.
