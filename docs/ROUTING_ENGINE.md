# MOTOR DE RUTEO PATHFINDER (NEGOTIATED CONGESTION): FPGA-H1

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/ROUTING_ENGINE.md`  
Estado: Fase 2 Aprobada

---

## 1. El Algoritmo Pathfinder

FPGA-H1 implementa el algoritmo **Pathfinder** (McMurchie & Ebeling), el estándar indiscutido en la industria de FPGAs (utilizado en VPR, Gowin EDA, NextPNR y Vivado).

A diferencia de los enrutadores codiciosos que fallan al primer conflicto de pistas, Pathfinder permite temporalmente la sobreutilización de recursos y la resuelve gradualmente mediante una función de costo de congestión negociada.

---

## 2. Formulación Matemática de Costos

El costo de atravesar un nodo de ruteo $n$ en la iteración $i$ está dado por:

$$c(n) = \left[ b(n) + h(n) \right] \cdot p(n)$$

donde:
- **$b(n)$ (Costo Base):** Retardo intrínseco del recurso (1.0 para pistas de canal `CHANX/CHANY`, 0.8 para llaves de connection box, 0.5 para pines locales `OPIN/IPIN`).
- **$h(n)$ (Penalización Histórica Acumulada):**
  $$h(n)^{(i)} = h(n)^{(i-1)} + \alpha \cdot \max(0, \text{occ}(n) - \text{cap}(n))$$
  con factor de acumulación $\alpha = 0.5$.
- **$p(n)$ (Factor de Penalización Presente):**
  $$p(n) = 1 + \max(0, \text{occ}(n) - \text{cap}(n)) \cdot P_{\text{fac}}^{(i)}$$
  donde $P_{\text{fac}}$ crece exponencialmente en cada iteración:
  $$P_{\text{fac}}^{(i)} = P_{\text{fac}}^{(i-1)} \cdot \beta, \quad \text{con } \beta = 1.3$$

---

## 3. Enrutamiento de Múltiples Sinks y Compartición Steiner

Para una red con 1 fuente y múltiples destinos $\{T_1, T_2, \dots, T_k\}$:
1. Se busca el camino de menor costo desde la fuente al primer destino $T_1$.
2. Los nodos de ese camino se agregan al árbol de la red.
3. Al enrutar hacia el destino $T_2$, la búsqueda Dijkstra se inicializa con todos los nodos del árbol actual con costo cero. Esto permite ramificaciones libres (*branching*) sin penalizar doblemente la ocupación de pistas compartidas.

---

## 4. Detección de Rutas Imposibles

Si tras alcanzar el límite máximo de iteraciones (ej. 30 a 50 iteraciones) persisten recursos con $\text{occ}(n) > \text{cap}(n)$, o si el algoritmo de búsqueda de caminos no encuentra ningún camino topológico entre fuente y sumidero, el enrutador:
1. Aborta la generación del circuito.
2. Identifica la red fallida y los nodos congestionados.
3. No declara nunca éxito hasta que $\text{max\_overuse} = 0$.
