# MAPEO A HARDWARE FÍSICO Y ESTIMACIÓN DE COSTOS — FPGA-H1

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `HARDWARE_MAPPING.md`  
Estado: Fase 0

---

## 1. Análisis de Tecnologías de Implementación Física

El objetivo de FPGA-H1 es estudiar la construcción de una arquitectura lógica reconfigurable propia. Para aterrizar el diseño virtual en silicio y hardware tangible, se evalúan 4 vías tecnológicas de implementación:

1. **Vía Discreta TTL/CMOS (Serie 74HC):** Construcción con circuitos integrados comerciales estándar.
2. **Vía Emulada con Microcontroladores Reconfigurables (Dual-Core RP2040 + PIO):** Matriz distribuida de procesadores ejecutando máquinas de estado rápidas.
3. **Vía CPLD / Macroceldas Programables (ej. ATF1508 / XC9500):** Silicio programable simple de puente.
4. **Vía Microelectrónica Integrada Propia (ASIC / MPW vía Tiny Tapeout o SkyWater 130nm):** El camino definitivo para un FPGA propio real.

---

## 2. Análisis Detallado: Implementación con Componentes Discretos (Serie 74HC)

Para construir un único Basic Logic Element (BLE) de FPGA-H1 en lógica discreta:
- **LUT4 (16:1 Multiplexor + 16 bits de SRAM):**
  - Multiplexor de 16 canales: **1x 74HC4067** (Multiplexor/Demultiplexor analógico/digital de 16 vías).
  - Almacenamiento de 16 bits de configuración: **2x 74HC595** (Registros de desplazamiento seriales con latch de 8 bits).
- **DFF y Bypass:**
  - Flip-Flop D con Set/Reset: **½ 74HC74** (Doble Flip-Flop tipo D).
  - Multiplexor de bypass combinacional/secuencial: **¼ 74HC157** (Cuádruple multiplexor 2:1).
- **Matriz de Interconexión por BLE:**
  - Multiplexores de ruteo para seleccionar entradas de canal: **2x 74HC151** (MUX 8:1) por entrada $\approx 8$ CI adicionales.

### 2.1 Escalabilidad Numérica de la Vía Discreta

| Escala Lógica | Cantidad de LUT4 | Circuitos Integrados Requeridos (Aprox.) | Superficie PCB Estimada | Consumo Eléctrico Estimado | Frecuencia Máxima Real | Costo de Componentes (USD) | Viabilidad Práctica |
|---|---|---|---|---|---|---|---|
| **H1-Micro** | **4 LUT4** | ~24 CIs | $10 \times 10 \text{ cm}$ (2 capas) | ~1.5 W | ~12 MHz | ~\$15 USD | **Alta (Excelente para prototipo didáctico)** |
| **H1-Mini** | **16 LUT4** | ~96 CIs | $20 \times 20 \text{ cm}$ (4 capas) | ~6 W | ~8 MHz | ~\$60 USD | **Media (Complejidad de ruteo media)** |
| **H1-64** | **64 LUT4** | ~384 CIs | $40 \times 40 \text{ cm}$ (4 capas) | ~25 W | ~5 MHz | ~\$250 USD | **Baja (Dificultades de señal y crosstalk)** |
| **H1-Full** | **8.640 LUT4** | **> 51.800 CIs** | **> 12 m² de PCB** | **> 3.200 W** | **< 1 MHz** | **> \$35.000 USD** | **TOTALMENTE INVIABLE** |

> [!CAUTION]
> Una arquitectura de 8.640 LUT4 **no puede ser construida con chips discretos**. El retraso de capacitancia parásita de pistas largas, el consumo térmico masivo y las decenas de miles de conexiones soldadas colapsarían la integridad de señal. La vía discreta es exclusivamente válida para validar el concepto funcional en 4 a 16 LUT4.

---

## 3. Vía Híbrida: Matriz de Microcontroladores RP2040

- Cada microcontrolador RP2040 cuenta con 2 núcleos ARM Cortex-M0+ a 133 MHz y 8 máquinas de estado de I/O programable (PIO).
- Un único RP2040 (\$0.80 USD) puede emular con latencia sub-microsegundo un clúster de **16 a 32 LUT4** con sus flip-flops y crossbar interno.
- Para un clúster experimental de 64 a 256 LUTs, un arreglo interconectado por buses SPI/QSPI de bajo costo proporciona una plataforma de validación física muy superior a los chips discretos.

---

## 4. Vía Definitiva de Silicio: Transición a ASIC (Tiny Tapeout / SkyWater 130nm)

Para alcanzar 1.024 a 8.640 LUT4 de manera económicamente viable y con prestaciones de ingeniería reales:
1. **Modelado y Síntesis:** El código desarrollado en el simulador y backend de FPGA-H1 se sintetiza hacia celdas estándar de silicio utilizando la cadena abierta **OpenLane / Silicon Compiler**.
2. **Celdas de Memoria SRAM:** Las celdas de configuración de las LUT4 se sustituyen por bloques compactos de SRAM de 6 transistores (6T SRAM) o registros de configuración estáticos.
3. **Plataformas de Fabricación Accesibles:**
   - **Tiny Tapeout:** Permite validar bloques de 4 a 16 LUTs en procesos SkyWater 130nm o IHP 130nm por menos de \$300 USD por slot.
   - **Multi-Project Wafer (MPW) de Efabless:** Permite fabricar chips completos con más de 1.000 a 4.000 LUTs con costos subsidiados o de escala compartida.
