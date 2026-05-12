"""
clustering/linkage_methods.py
------------------------------
Información técnica y matemática de cada método de enlace jerárquico.
Usada por la UI de Streamlit para mostrar explicaciones detalladas.
"""


METHODS_INFO = {
    "ward": {
        "name": "Ward (Varianza Mínima)",
        "color": "#6C63FF",
        "emoji": "🟣",
        "description": (
            "El método de Ward minimiza la **varianza total intra-cluster** en cada fusión. "
            "En cada paso, une los dos clusters que producen el menor incremento en la "
            "suma de cuadrados de las distancias dentro del cluster resultante."
        ),
        "formula": r"""
**Criterio de fusión:**

$$\Delta(A, B) = \frac{n_A \cdot n_B}{n_A + n_B} \cdot \|\bar{x}_A - \bar{x}_B\|^2$$

Donde:
- $n_A$, $n_B$ = número de elementos en los clusters A y B
- $\bar{x}_A$, $\bar{x}_B$ = centroides de cada cluster
- $\|\cdot\|$ = norma euclidiana entre centroides
""",
        "pros": [
            "Produce clusters **compactos y equilibrados** en tamaño",
            "Minimiza la heterogeneidad interna de cada cluster",
            "Generalmente el más robusto para datos TF-IDF densos",
        ],
        "cons": [
            "Sensible a **outliers** (abstracts muy cortos o inusuales)",
            "Solo funciona con distancias euclidianas (no coseno directo)",
            "Tiende a crear clusters esféricos, no adecuado para formas irregulares",
        ],
        "use_case": "Ideal cuando se busca agrupar papers por tema de forma equilibrada.",
    },
    "complete": {
        "name": "Complete Linkage (Enlace Completo)",
        "color": "#FF6B6B",
        "emoji": "🔴",
        "description": (
            "El enlace completo define la distancia entre dos clusters como la "
            "**distancia máxima** entre cualquier par de elementos pertenecientes "
            "a distintos clusters. También llamado 'criterio del vecino más lejano'."
        ),
        "formula": r"""
**Criterio de fusión:**

$$d(C_i, C_j) = \max_{x \in C_i,\; y \in C_j} d(x, y)$$

Donde:
- $C_i$, $C_j$ = clusters a fusionar
- $d(x, y)$ = distancia entre los elementos $x$ e $y$
- Se toma el **máximo** de todas las distancias inter-cluster
""",
        "pros": [
            "Genera clusters **bien separados** y compactos",
            "Resistente a la formación de cadenas (chaining effect)",
            "Adecuado cuando se quiere garantizar homogeneidad intra-cluster",
        ],
        "cons": [
            "Muy sensible a **outliers** (un punto lejano puede retardar fusiones)",
            "Puede crear clusters **desequilibrados** en tamaño",
            "No es óptimo cuando los clusters tienen formas elongadas",
        ],
        "use_case": "Útil para identificar grupos de artículos claramente distintos entre sí.",
    },
    "average": {
        "name": "Average Linkage (UPGMA)",
        "color": "#4ECDC4",
        "emoji": "🔵",
        "description": (
            "El enlace promedio (UPGMA — Unweighted Pair Group Method with Arithmetic mean) "
            "define la distancia entre dos clusters como el **promedio de todas las distancias** "
            "entre pares de elementos de ambos clusters."
        ),
        "formula": r"""
**Criterio de fusión:**

$$d(C_i, C_j) = \frac{1}{|C_i| \cdot |C_j|} \sum_{x \in C_i} \sum_{y \in C_j} d(x, y)$$

Donde:
- $|C_i|$, $|C_j|$ = cardinalidad de cada cluster
- La distancia es el **promedio aritmético** de todos los pares posibles
""",
        "pros": [
            "**Balance** entre Ward (compacto) y Complete (separado)",
            "Menos sensible a outliers que Complete Linkage",
            "Buen rendimiento general con datos textuales",
        ],
        "cons": [
            "Puede sufrir efecto de 'dilución' en clusters muy grandes",
            "No minimiza ningún criterio de varianza explícitamente",
            "El CCC puede ser similar al de Ward, dificultando la elección",
        ],
        "use_case": "Buena opción cuando no se tiene certeza sobre la estructura de los clusters.",
    },
}


def get_method_info(method: str) -> dict:
    """
    Retorna el diccionario de información técnica para el método dado.

    Parámetros
    ----------
    method : str
        Uno de: 'ward', 'complete', 'average'

    Retorna
    -------
    dict con claves: name, color, emoji, description, formula, pros, cons, use_case
    """
    return METHODS_INFO.get(method, {})


def get_all_methods() -> list[str]:
    """Lista de métodos disponibles."""
    return list(METHODS_INFO.keys())
