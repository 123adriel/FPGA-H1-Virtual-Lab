# MOTOR DE PLACEMENT (UBICACIÓN FÍSICA): FPGA-H1

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `docs/PLACEMENT_ENGINE.md`  
Estado: Fase 2 Aprobada

---

## 1. Misión del Motor de Ubicación

El **Placement Engine** recibe una netlist sintetizada de bloques lógicos CLB y sus interconexiones de red, y los asigna a coordenadas discretas $(x, y)$ en la matriz bidimensional del chip:
$$\pi: \text{CLB}_i \longrightarrow (x_i, y_i) \in [0, W_g - 1] \times [0, H_g - 1]$$
sujeto a la restricción de capacidad unitaria:
$$\forall i \ne j, \quad \pi(\text{CLB}_i) \ne \pi(\text{CLB}_j)$$

---

## 2. Función Objetivo: Longitud de Cable de Medio Perímetro (HPWL)

Para minimizar la congestión de ruteo, el retardo parásito y el consumo de pistas, el motor minimiza la función **Half-Perimeter Wirelength (HPWL)**:

$$\text{HPWL} = \sum_{\text{net} \in \mathcal{N}} \left[ \left(\max_{p \in \text{net}} x_p - \min_{p \in \text{net}} x_p\right) + \left(\max_{p \in \text{net}} y_p - \min_{p \in \text{net}} y_p\right) \right]$$

---

## 3. Algoritmo en Dos Fases

### Fase 1: Ubicación Heurística Inicial por Conectividad y Centro de Masa
1. Calcula el grado de interconexión (número de señales incidentes) para cada CLB.
2. Ordena los bloques de mayor a menor conectividad.
3. Asigna los bloques más densamente conectados en una espiral concéntrica hacia el centro de la matriz die, reduciendo la dispersión global de cables.

### Fase 2: Recocido Simulado (Simulated Annealing)
1. En cada paso se seleccionan dos celdas $(x_1, y_1)$ y $(x_2, y_2)$ aleatoriamente y se intercambian sus posiciones.
2. Se calcula la variación de costo:
   $$\Delta \text{HPWL} = \text{HPWL}_{\text{nuevo}} - \text{HPWL}_{\text{actual}}$$
3. Si $\Delta \text{HPWL} < 0$, el intercambio se acepta incondicionalmente.
4. Si $\Delta \text{HPWL} \ge 0$, se acepta con probabilidad de Boltzmann:
   $$P(\text{aceptar}) = \exp\left(-\frac{\Delta \text{HPWL}}{T}\right)$$
5. La temperatura se enfría geométricamente:
   $$T_{k+1} = \gamma \cdot T_k, \quad \text{con } \gamma = 0.95$$
