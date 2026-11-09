# INFRASTRUCTURE AUDIT — FPGA-H1 VIRTUAL LAB

Fecha: 2026-11-09  
Entorno auditado: Red LAN de Laboratorio y Estaciones de Cómputo

---

## 1. Inventario de Nodos Verificados

Se ejecutó un sondeo de red y auditoría remota mediante SSH/OpenSSH sobre los nodos disponibles respetando la regla estricta de no alterar servicios productivos:

| Nodo / Host | SO / Kernel | CPU / Arquitectura | Memoria RAM | GPU / Acelerador | Estado Operativo | Rol Asignado en FPGA-H1 |
|---|---|---|---|---|---|---|
| **Local Workstation** (Host) | Windows 10/11 x86_64 | Intel Core i7-7700 @ 3.60GHz (4C / 8T) | 16 GB DDR4 | Gráficos integrados / Genérico | Activo (Desarrollo primario) | Compilador H1L, tests unitarios, interfaz local |
| **`srv24`** (`192.168.39.24`) | Debian 12 (Linux 6.1.0-44-amd64) | 16 Cores x86_64 | 24 GB DDR4 (22 GB Libres) | Sin GPU activa | Activo (Excelente headroom) | Motor de simulación paralela, barridos de escalabilidad (8.640 LUT4) |
| **`sycndata`** (`192.168.39.21`) | Ubuntu (Linux 6.8.0-106) | 4 Cores x86_64 | 8 GB RAM (7.4 GB Usados) | **NVIDIA RTX A5000** (24 GB VRAM) | **Productivo (Carga alta)** | **NO TOCAR** (Servicio activo de datos) |
| **`llama`** (`192.168.39.22`) | Ubuntu (Linux 6.8.0-147) | 4 Cores x86_64 | 8 GB RAM (6.6 GB Libres) | **NVIDIA RTX A5000** (24 GB VRAM) | Disponible con reserva | Nodo de reserva para inferencia o aceleración justificada |
| **`servidorowoi`** (`192.168.39.25`) | Ubuntu (Linux 6.8.0-147) | 8 Cores x86_64 | 16 GB RAM (13 GB Libres) | **NVIDIA RTX A5000** (24 GB VRAM) | Disponible | Banco de verificación masiva y pruebas de regresión |
| **`192.168.39.190`** | Windows x86_64 | N/A | N/A | N/A | Activo | Estación secundaria Windows |

---

## 2. Política de Uso de GPUs

Conforme a la directiva técnica:
1. **Prioridad CPU y Paralelismo de Memoria:** La simulación funcional de circuitos lógicos, tablas de verdad de LUT4, evaluación topológica y propagación de grafos es intrínsecamente dependiente de saltos de memoria y baja latencia de branches, donde las CPUs multinúcleo (i7-7700 local y srv24 con 16 núcleos) superan a las GPU en workloads de baja a media escala (< 100.000 puertas).
2. **Restricción de GPUs A5000:** No se utilizarán GPUs de manera predeterminada. Quedan reservadas exclusivamente para barridos masivos de routing monte carlo o place-and-route estocástico a 8.640 LUTs si y solo si la carga en CPU se convierte en cuello de botella.
3. **No interferencia:** El servidor `sycndata` (`192.168.39.21`) tiene 7.4 GB de RAM ocupados en producción y queda completamente excluido de pruebas invasivas.

---

## 3. Distribución de Equipos de Ingeniería

Para organizar la arquitectura del proyecto se asignan responsabilidades lógicas modulares:

- **Equipo A (Compilador H1L):** Lexer, parser, AST, generador de netlist y sintetizador lógico para H1L.
- **Equipo B (Simulador Lógico):** Motor de evaluación determinista de LUT4, flip-flops D, carry chains y resolución topológica de nets.
- **Equipo C (Routing y Arquitectura):** Matrices de conmutación (Switch Boxes Wilton/Subset), Connection Boxes, canales ortogonales $X/Y$, algoritmos de ruteo Pathfinder/A*.
- **Equipo D (Interfaz Visual):** Dashboard interactivo de ingeniería (FastAPI backend + Vite/React frontend), visor de matrices lógicas y diagramas de temporización.
- **Equipo E (Pruebas, Benchmarking y Auditoría):** Suites de test formal, exhaustividad de tablas de verdad, medición de ciclos por segundo, latencia de conmutación y comparación con Gowin GW1NR-9.
