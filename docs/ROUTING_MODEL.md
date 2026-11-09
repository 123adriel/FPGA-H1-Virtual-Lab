# MODELO Y ANÁLISIS DE INTERCONEXIÓN (ROUTING) — FPGA-H1

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `ROUTING_MODEL.md`  
Estado: Fase 0 / Fase 1

---

## 1. El Problema del Ruteo en Lógica Reconfigurable

El sistema de interconexión (routing) es el subsistema más crítico, costoso y limitante de cualquier arquitectura FPGA. En el silicio físico comercial:
- Ocupa entre el **70% y el 85% del área total del die**.
- Representa más del **60% del consumo de potencia dinámico**.
- Origina entre el **60% y el 80% del retardo crítico** en el camino de propagación de datos.

Un modelo ingenuo o arbitrario (como matrices de adyacencia ilimitadas donde cualquier punto se conecta con cualquier otro mágicamente) desvirtúa el diseño de un FPGA real. FPGA-H1 modela el ruteo con recursos cuantificados y limitados.

---

## 2. Comparación de Tres Arquitecturas de Ruteo

Analizamos las tres grandes familias de topología de interconexión para determinar la arquitectura base de FPGA-H1:

```
[ARQUITECTURA A: Totalmente Conectada]    [ARQUITECTURA B: Jerárquica]        [ARQUITECTURA C: Island-Style (Canales + SB/CB)]
          Crossbar Completo                         Niveles H1, H2, H3                         Grid 2D + Switch/Connection Boxes
           +---------------+                          +---------------+                          +----+     +----+     +----+
           |  N x N Switch |                          | Global Trunk  |                          | CLB|-[CB]| CLB|-[CB]| CLB|
           +---------------+                          +---+-------+---+                          +--+-+     +--+-+     +--+-+
             /   |   |   \                                |       |                                 |          |          |
         CLB0  CLB1 CLB2 CLB3                          Cluster0 Cluster1                              [SB]-------[SB]-------[SB]
     Complejidad: O(N^2) Switches                Complejidad: O(N log N)                     Complejidad: O(N) Switches (Scalable)
```

### Tabla Comparativa Rigurosa

| Parámetro | Arquitectura A: Totalmente Conectada (Full Crossbar) | Arquitectura B: Interconexión Jerárquica (Tree / Hierarchical) | Arquitectura C: Island-Style (Canales Segmentados + SB/CB) |
|---|---|---|---|
| **Número de Switches para $N$ LUTs** | $O(N^2)$ (Inviable para $N > 256$) | $O(N \log N)$ (Moderado) | $O(N \cdot W)$ donde $W$ es el ancho de canal (Óptimo) |
| **Switches para 4 LUTs** | $4 \times 4 = 16$ puntos de cruce | 12 switches | 16 switches |
| **Switches para 256 LUTs** | $256 \times 256 = 65.536$ switches | ~2.048 switches | ~3.072 switches ($W=6$) |
| **Switches para 8.640 LUTs** | **$74.649.600$ switches (PROHIBITIVO)** | ~130.000 switches | **~86.400 - 150.000 switches** |
| **Predecibilidad de Retardo** | Excelente (1 hop constante) | Buena (retardo logarítmico) | Variable (dependiente de cantidad de saltos SB) |
| **Flexibilidad de Fan-Out** | Total | Restringida a subárboles | Alta mediante árboles de Steiner en cuadrícula |
| **Tasa de Congestión a Gran Escala** | Nula (no hay bloqueo) | Media en raíces de jerarquía | Gestionable con ancho de canal adecuado ($W \ge 8$) |
| **Área en Silicio y Costo Físico** | Inviable industrialmente | Media / Compleja en layout 2D | **Estándar de la industria (Gowin, Xilinx, Lattice)** |
| **Complejidad del Algoritmo PnR** | Trivial $O(1)$ | Media $O(N \log N)$ | Alta (Pathfinder / A* negociado) |

---

## 3. Decisión de Arquitectura para FPGA-H1: Modelo Híbrido C+B (Island-Style Agrupado)

Para FPGA-H1 seleccionamos una arquitectura híbrida:
1. **Nivel Local (Intra-CLB - Jerárquico B):**
   - Cada CLB agrupa 4 BLEs.
   - Cuenta con una matriz local compacta (Local Crossbar) de baja latencia donde las salidas de los 4 BLEs pueden realimentarse sin salir a la red global.
2. **Nivel Global (Inter-CLB - Island-Style C):**
   - Cuadrícula 2D rectangular de CLBs.
   - Canales horizontales y verticales de ancho de pista uniforme $W$ (default: $W = 8$ pistas por canal).
   - **Connection Boxes (CB):** Conectan las entradas y salidas de los CLBs a las pistas del canal. Flexibilidad de conexión $F_c(in) = 0.5 \cdot W$, $F_c(out) = 0.25 \cdot W$.
   - **Switch Boxes (SB):** En cada cruce de canales (horizontal y vertical). Emplea la topología **Wilton Switch Box** con flexibilidad $F_s = 3$.

---

## 4. Topología de Conmutación: Wilton Switch Box

En una caja de conmutación de 4 vías (Norte, Sur, Este, Oeste), una pista $i$ ($0 \le i < W$) se interconecta con:
- Dirección opuesta (Straight):
  - $T(T_{North}, i) \leftrightarrow T(T_{South}, i)$
  - $T(T_{East}, i) \leftrightarrow T(T_{West}, i)$
- Giros ortogonales (Turns con desplazamiento Wilton para evitar desconexiones diagonales):
  - $T(T_{North}, i) \leftrightarrow T(T_{West}, (i + 1) \pmod W)$
  - $T(T_{North}, i) \leftrightarrow T(T_{East}, (i + W - 1) \pmod W)$
  - $T(T_{South}, i) \leftrightarrow T(T_{West}, (i + W - 1) \pmod W)$
  - $T(T_{South}, i) \leftrightarrow T(T_{East}, (i + 1) \pmod W)$

Esta topología garantiza que cualquier señal pueda cambiar de plano o pista tras un giro, reduciendo drásticamente la tasa de bloqueo y el índice de congestión.

---

## 5. Algoritmo de Ruteo: Pathfinder Negociado (Negotiated Congestion)

FPGA-H1 implementa el algoritmo **Pathfinder**:
1. En cada iteración, cada net se enruta utilizando búsqueda $A^*$ o Dijkstra sobre el grafo de recursos dirigidos (RR-Graph).
2. Se permite sobreutilización temporal de pistas de ruteo durante las primeras iteraciones.
3. El costo de uso de un recurso $n$ en la iteración $i$ está dado por:
   $$c_n = \left( b_n + h_n \right) \cdot p_n$$
   donde:
   - $b_n$: costo base (retardo intrínseco del switch / pista).
   - $h_n$: penalización histórica acumulada si el recurso sufrió congestión en iteraciones previas ($h_n^{(i)} = h_n^{(i-1)} + \beta \cdot \max(0, \text{ocupación}_n - \text{capacidad}_n)$).
   - $p_n$: penalización presente por sobreutilización instantánea.
4. Las señales en conflicto negocian gradualmente caminos alternativos hasta que toda sobreutilización se extingue.
