# MODELO MATEMÁTICO Y LÓGICO: LUT4 Y BLE

Proyecto: **FPGA-H1 Virtual Lab**  
Documento: `LOGIC_MODEL.md`  
Estado: Fase 0 / Fase 1

---

## 1. Definición Formal de la LUT4

Una **Look-Up Table de 4 entradas (LUT4)** es un circuito combinacional configurable capaz de implementar cualquier función booleana de 4 variables:
$$f: \{0, 1\}^4 \to \{0, 1\}$$

### 1.1 Vector de Entradas y Mapeo de Dirección
Sean las entradas binarias $I_0, I_1, I_2, I_3 \in \{0, 1\}$, donde $I_0$ es el bit menos significativo (LSB) e $I_3$ el bit más significativo (MSB).

El índice de dirección o minitérmino activo $\alpha \in \{0, 1, \dots, 15\}$ se calcula como:
$$\alpha(I) = \sum_{k=0}^{3} I_k \cdot 2^k = I_0 + 2 I_1 + 4 I_2 + 8 I_3$$

### 1.2 Vector de Configuración SRAM
La memoria de configuración de la LUT4 consta de un vector binario de 16 bits:
$$C = [c_0, c_1, c_2, \dots, c_{15}] \in \{0, 1\}^{16}$$
Equivalentemente, $C$ puede representarse como un entero sin signo de 16 bits: $C_{int} \in [0, 65535]$ (o en hexadecimal `0x0000` a `0xFFFF`).

### 1.3 Función de Evaluación Canónica
La salida booleana $Y$ corresponde al valor almacenado en la celda direccionada por $\alpha$:
$$Y(I, C) = c_{\alpha(I)}$$

En términos de álgebra booleana sobre la suma canónica de productos (minitérminos):
$$Y(I, C) = \bigvee_{k=0}^{15} \left( c_k \wedge m_k(I) \right)$$
donde $m_k(I)$ es el $k$-ésimo minitérmino:
$$m_k(I) = \bigwedge_{j=0}^{3} \tilde{I}_j, \quad \text{donde } \tilde{I}_j = \begin{cases} I_j & \text{si el bit } j \text{ de } k \text{ es } 1 \\ \overline{I}_j & \text{si el bit } j \text{ de } k \text{ es } 0 \end{cases}$$

### 1.4 Evaluación Optimizada en Software
En la implementación del motor de simulación, la evaluación de una LUT4 se reduce a una operación bit a bit de tiempo constante $O(1)$:
$$Y = \left( C_{int} \gg \alpha \right) \& 1$$
Esta operación es determinista, libre de ramas condicionales (*branchless*) y altamente vectorizable en arquitecturas x86_64 y SIMD.

---

## 2. Ejemplos Canónicos de Configuración Hexadecimal (16 bits)

Para cualquier función booleana estándar de 2, 3 o 4 entradas conectadas a $I_0, I_1, I_2, I_3$:

| Función Lógica | Ecuación Booleana | Minitérminos Activos | Máscara Binaria ($c_{15} \dots c_0$) | Config Hexadecimal |
|---|---|---|---|---|
| **Cero constante** | $0$ | Ninguno | `0000 0000 0000 0000` | `0x0000` |
| **Uno constante** | $1$ | Todos ($0..15$) | `1111 1111 1111 1111` | `0xFFFF` |
| **Buffer $I_0$** | $I_0$ | Impares ($1,3,5,7,9,11,13,15$) | `1010 1010 1010 1010` | `0xAAAA` |
| **Buffer $I_1$** | $I_1$ | $2,3,6,7,10,11,14,15$ | `1100 1100 1100 1100` | `0xCCCC` |
| **Buffer $I_2$** | $I_2$ | $4..7, 12..15$ | `1111 0000 1111 0000` | `0xF0F0` |
| **Buffer $I_3$** | $I_3$ | $8..15$ | `1111 1111 0000 0000` | `0xFF00` |
| **NOT($I_0$)** | $\overline{I}_0$ | Pares ($0,2,4,6,8,10,12,14$) | `0101 0101 0101 0101` | `0x5555` |
| **AND($I_0, I_1$)** | $I_0 \wedge I_1$ | $3, 7, 11, 15$ | `1000 1000 1000 1000` | `0x8888` |
| **OR($I_0, I_1$)** | $I_0 \vee I_1$ | Todos excepto $0,4,8,12$ | `1110 1110 1110 1110` | `0xEEEE` |
| **XOR($I_0, I_1$)** | $I_0 \oplus I_1$ | $1,2, 5,6, 9,10, 13,14$ | `0110 0110 0110 0110` | `0x6666` |
| **NAND($I_0, I_1$)** | $\overline{I_0 \wedge I_1}$ | Inverso de AND | `0111 0111 0111 0111` | `0x7777` |
| **NOR($I_0, I_1$)** | $\overline{I_0 \vee I_1}$ | Inverso de OR | `0001 0001 0001 0001` | `0x1111` |
| **XNOR($I_0, I_1$)** | $\overline{I_0 \oplus I_1}$ | Inverso de XOR | `1001 1001 1001 1001` | `0x9999` |
| **MUX 2:1** | $(I_0 \wedge \overline{I_2}) \vee (I_1 \wedge I_2)$ | Select=$I_2$, D0=$I_0$, D1=$I_1$ | `1100 1010 1100 1010` | `0xCACA` |
| **Full Adder SUM** | $A \oplus B \oplus C_{in}$ ($I_0 \oplus I_1 \oplus I_2$) | $1, 2, 4, 7, 9, 10, 12, 15$ | `1001 0110 1001 0110` | `0x9696` |
| **Full Adder CARRY** | $(A \wedge B) \vee (A \wedge C) \vee (B \wedge C)$ | $3, 5, 6, 7, 11, 13, 14, 15$ | `1110 1000 1110 1000` | `0xE8E8` |

---

## 3. Modelo del Flip-Flop D (DFF)

El registro secuencial almacena 1 bit de estado $Q \in \{0, 1\}$.

### 3.1 Ecuación de Estado
El comportamiento temporal responde a la siguiente máquina de estados:

$$Q(t^+) = \begin{cases}
0 & \text{si } ARST(t) = 1 \quad (\text{Reset asíncrono, prioritario}) \\
0 & \text{si } CLK \uparrow \wedge ARST = 0 \wedge SRST(t) = 1 \quad (\text{Reset síncrono}) \\
D(t) & \text{si } CLK \uparrow \wedge ARST = 0 \wedge SRST = 0 \wedge CE(t) = 1 \quad (\text{Captura}) \\
Q(t) & \text{en cualquier otro caso (Retención)}
\end{cases}$$

Donde $CLK \uparrow$ denota la transición del reloj de $0 \to 1$ (flanco ascendente).

---

## 4. Estructura de Salida del BLE (Basic Logic Element)

La salida final del BLE, denotada $Y_{BLE}$, está determinada por la señal de configuración `BYPASS_FF`:
$$Y_{BLE} = \begin{cases}
Y_{LUT4} & \text{si } \text{BYPASS\_FF} = 1 \quad (\text{Modo Combinacional puro}) \\
Q_{DFF} & \text{si } \text{BYPASS\_FF} = 0 \quad (\text{Modo Registrado / Secuencial})
\end{cases}$$
O algebraicamente:
$$Y_{BLE} = (\text{BYPASS\_FF} \wedge Y_{LUT4}) \vee (\overline{\text{BYPASS\_FF}} \wedge Q_{DFF})$$

---

## 5. Lógica Multinivel (IEEE 1164 Model)

Para verificación formal y detección de fallas de conexión o carreras críticas, las señales admiten 4 valores lógicos canónicos:
- `'0'`: Cero lógico bajo (GND).
- `'1'`: Uno lógico alto ($V_{DD}$).
- `'X'`: Desconocido / Indeterminado (Conflicto de bus o estado no inicializado).
- `'Z'`: Alta impedancia (Pin desconectado o tri-state flotante).

En caso de que alguna entrada de la LUT contenga `'X'` o `'Z'`, el motor evalúa si la salida depende críticamente de dicha entrada. Si todos los caminos que cubren la máscara $C$ producen el mismo valor para los sub-árboles de decisión, se resuelve de forma conservadora a `'0'` o `'1'`; en caso contrario se propaga `'X'`.
