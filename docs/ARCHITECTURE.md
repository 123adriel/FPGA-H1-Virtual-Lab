# ARQUITECTURA GENERAL: FPGA-H1

Proyecto: **FPGA-H1 Virtual Lab**  
Estado: En desarrollo activo — Fase 0 / Fase 1  
Objetivo: Arquitectura de lógica programable propia, modular y escalable (4 LUT4 a 8.640 LUT4).

---

## 1. Visión y Principios de Diseño

El proyecto **FPGA-H1** persigue el diseño y simulación de una arquitectura de matriz lógica programable (FPGA) experimental, abierta y de bajo costo. 

A diferencia de un enfoque basado en adquirir silicio comercial cerrado y programarlo con herramientas propietarias opacas, FPGA-H1 modela en profundidad:
1. **La celda elemental:** La celda de búsqueda de 4 entradas (LUT4) acoplada a un registro secuencial (DFF) y lógica de acarreo rápido.
2. **El bloque lógico configurable (CLB / Cluster):** Agrupamiento de 4 BLEs con interconexión local rápida de baja latencia.
3. **La red de interconexión (Island-Style Routing):** Matrices de conmutación orientadas en cuadrícula con switch boxes y connection boxes configurables.
4. **El motor de configuración binario:** Bitstream estructurado por tramas con validación por redundancia cíclica (CRC32).

---

## 2. Bloque Lógico Básico: BLE (Basic Logic Element)

Cada BLE en FPGA-H1 está compuesto por:
- **1x LUT4 (Look-Up Table de 4 entradas):** Permite implementar cualquier función booleana $f: \{0, 1\}^4 \to \{0, 1\}$ mediante un vector de configuración de 16 bits $C \in \{0, 1\}^{16}$.
- **1x D-Flip-Flop (DFF):** Registro secuencial disparado por flanco ascendente de reloj, con entradas de `Clock Enable` (CE), `Reset Asíncrono` (ARST) y `Reset Síncrono` (SRST).
- **1x Multiplexor de Bypass:** Bit de configuración `BYPASS_FF` que selecciona si la salida del BLE $Y$ proviene directamente de la salida combinacional de la LUT4 o de la salida registrada $Q$ del DFF.
- **Lógica de Acarreo Rápido (Carry Logic):** MUX de acarreo dedicado para cascada de sumadores/restadores sin consumir el ruteo general.

```
          +-----------------------+
  I[0] -->|                       |
  I[1] -->|      LUT4 Core        |---+
  I[2] -->| (16-bit Configuration)|   |
  I[3] -->|                       |   |
          +-----------------------+   |
                                      |
                      +---------------+------+
                      |                      |
                      |          +--------+  |
                      |          |  DFF   |  |
                      +--------->|D      Q|--+
                                 |        |  |
             CLK --------------->|>       |  |
              CE --------------->|CE      |  |
            ARST --------------->|CLR     |  |
                                 +--------+  |
                                             |
                                        +----+----+
                                        \   MUX   |-----> OUT (Y)
                                         \       /
                                          +--+--+
                                             |
                                        BYPASS_FF
```

---

## 3. Bloque Lógico Configurable: CLB (Cluster de Lógica)

Un CLB de FPGA-H1 agrupa:
- **4 BLEs (BLE_0 a BLE_3)**.
- **Crossbar Local (Local Interconnect):** Permite conectar las salidas de los BLEs internos de regreso a las entradas de los BLEs vecinos con retardo mínimo ($t_{local} \ll t_{global}$).
- **Entradas Externas:** 12 entradas independientes de interconexión global.
- **Línea de Acarreo Acelerado:** Entrada `CIN` y salida `COUT` en cascada directa vertical.
- **Líneas de Reloj y Control Global:** 1 reloj global, 1 habilitador global, 1 reset global.

---

## 4. Red de Interconexión: Arquitectura Island-Style

FPGA-H1 adopta una topología de isla clásica (Island-Style FPGA):
- **Canales de Ruteo $X$ e $Y$:** Pistas metálicas segmentadas que recorren la matriz horizontal y verticalmente.
- **Connection Boxes (CB):** Bloques de multiplexores configurables que conectan los pines de entrada/salida de los CLBs a las pistas de los canales adyacentes.
- **Switch Boxes (SB):** Cajas de conmutación ubicadas en los cruces de canales horizontales y verticales. Emplea topología **Wilton / Subset** para permitir giros ortogonales (Norte-Sur-Este-Oeste) con un factor de flexibilidad $F_s = 3$.

---

## 5. Comparación Cuantitativa: FPGA-H1 vs Gowin GW1NR-9 (Tang Nano 9K)

El objetivo de referencia para escalabilidad máxima de FPGA-H1 es igualar la capacidad lógica nominal de la **Gowin GW1NR-9**. La siguiente tabla documenta las diferencias arquitectónicas clave:

| Parámetro / Característica | Gowin GW1NR-9 (Sipeed Tang Nano 9K) | FPGA-H1 (Modelo Virtual Lab) | Análisis de Brecha Arquitectónica |
|---|---|---|---|
| **LUTs Nominales** | 8.640 LUT4 | 8.640 LUT4 (Escalable: 4 a 8.640) | Equivalencia numérica 1:1 en celdas booleanas de 4 variables. |
| **Flip-Flops (DFF)** | 6.480 DFFs | 8.640 DFFs (1 DFF por LUT4 en cada BLE) | FPGA-H1 ofrece mayor densidad de registros por celda lógica básica. |
| **Topología CLB / Slice** | 4 LUT4 + 4 DFF por Slice | 4 BLEs por CLB (2.160 CLBs totales a 8.640 LUTs) | Estructura homogénea y simétrica. |
| **Memoria Embebida (BSRAM)** | 26 bloques de 18 Kbit (~468 Kbit) | Modelada como bloques dedicados de memoria de 16 Kbit | En FPGA-H1 los primeros hitos priorizan LUT-RAM antes de bloques dedicados. |
| **Multiplicadores / DSP** | 20 DSP blocks (18x18) | Sintetizados mediante LUT4 (futuro bloque DSP opcional) | En FPGA-H1 inicial, la multiplicación consume LUTs. |
| **Red de Reloj (Clock Trees)** | 8 redes de reloj global + 2 PLLs | 4 redes de reloj global balanceadas virtuales | Simuladas con modelo de skew programable. |
| **Tecnología de Fabricación** | TSMC 55nm / 40nm LP CMOS comercial | Virtual (Simulación de nivel puerta y RTL) | Emulación de retardo de compuerta basada en tecnología 65nm / 180nm. |
| **$F_{max}$ Estimada** | 150 MHz - 250 MHz | Virtual: hasta 100 MHz en simulación temporal | El ruteo virtualizado modela resistencia RC estimada. |
| **Tiempo de Compilación PnR** | ~15 a 45 seg (Gowin EDA) | Enfoque híbrido CPU multithread (Fast Routing) | Optimizado para ejecución en servidores locales (`srv24` 16T). |
| **Consumo Eléctrico Estimado** | ~120 mW - 350 mW dinámico | Estimado por transición de compuerta ($P = \frac{1}{2} C V^2 f$) | Modelo de potencia dinámico dependiente de actividad de conmutación. |
| **Costo Físico Estimado** | ~\$4.50 USD (Chip volumen) | N/A en simulación; prohibitivo en discretos, bajo en MPW ASIC | Véase `docs/HARDWARE_MAPPING.md`. |
