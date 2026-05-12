"""
clustering/dendrogram.py
------------------------
Construcción de dendrogramas interactivos con Plotly a partir de la
matriz de linkage generada por scipy.

Usa plotly.figure_factory.create_dendrogram() para renderizar el árbol
jerárquico en un gráfico interactivo compatible con Streamlit.
"""

import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
from scipy.cluster.hierarchy import linkage as scipy_linkage
from scipy.spatial.distance import squareform


def build_plotly_dendrogram(
    distance_matrix: np.ndarray,
    labels: list[str],
    method: str,
    title: str,
    color_threshold: float | None = None,
    colorscale: list[str] | None = None,
) -> go.Figure:
    """
    Construye un dendrograma interactivo con Plotly.

    Plotly's create_dendrogram() recibe la matriz de datos original (no la
    linkage matrix) y calcula internamente el linkage. Le pasamos la
    distancia precomputada como matriz cuadrada usando un enlace predefinido.

    Parámetros
    ----------
    distance_matrix : np.ndarray
        Matriz cuadrada de distancias (n x n).
    labels : list[str]
        Etiquetas para las hojas del dendrograma.
    method : str
        Método de enlace: 'ward', 'complete', 'average'.
    title : str
        Título del gráfico.
    color_threshold : float | None
        Umbral de color para pintar los clusters. Si None, se calcula automáticamente
        como 70% de la distancia máxima.
    colorscale : list[str] | None
        Lista de colores para las ramas. Si None usa la paleta por defecto.

    Retorna
    -------
    go.Figure
        Figura Plotly lista para st.plotly_chart().
    """
    # Colores por defecto según el método
    _DEFAULT_COLORS = {
        "ward": ["#6C63FF", "#9B59B6", "#3498DB", "#1ABC9C"],
        "complete": ["#FF6B6B", "#E74C3C", "#F39C12", "#E67E22"],
        "average": ["#4ECDC4", "#1ABC9C", "#2ECC71", "#27AE60"],
    }

    link_colors = colorscale or _DEFAULT_COLORS.get(method, ["#6C63FF", "#9B59B6"])

    # Calculamos linkage sobre la forma condensada
    condensed = squareform(distance_matrix, checks=False)
    Z = scipy_linkage(condensed, method=method)

    # Umbral de color automático = 70% de la distancia de enlace máxima
    if color_threshold is None:
        color_threshold = 0.70 * float(Z[:, 2].max())

    # Plotly crea el dendrograma a partir de la matrix de distancias directamente
    # pasando una función de linkage personalizada
    def _custom_linkage(x):
        return Z

    fig = ff.create_dendrogram(
        distance_matrix,
        orientation="bottom",
        labels=labels,
        linkagefun=_custom_linkage,
        color_threshold=color_threshold,
    )

    # ─── Estilización ───────────────────────────────────────────────────────
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 18, "color": "#FFFFFF", "family": "Inter, sans-serif"},
            "x": 0.5,
        },
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#111126",
        font={"color": "#c0c0e0", "family": "Inter, sans-serif", "size": 10},
        height=520,
        margin={"l": 10, "r": 10, "t": 60, "b": 140},
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showticklabels": True,
            "tickfont": {"size": 9, "color": "#a0a0cc"},
            "tickangle": -45,
        },
        yaxis={
            "title": "Distancia de enlace",
            "gridcolor": "#1e1e3a",
            "gridwidth": 1,
            "zeroline": False,
            "tickfont": {"size": 10, "color": "#a0a0cc"},
            "title_font": {"size": 12, "color": "#c0c0e0"},
        },
        hoverlabel={
            "bgcolor": "#1a1a35",
            "font_size": 11,
            "font_family": "Inter, sans-serif",
        },
    )

    # Aplica colores personalizados a las líneas del dendrograma
    _apply_colors(fig, link_colors)

    return fig


def _apply_colors(fig: go.Figure, colors: list[str]) -> None:
    """Asigna colores de la paleta del método a las trazas del dendrograma."""
    # Las trazas de Plotly dendrogram tienen colores por defecto; las recoloreamos
    color_cycle = colors * (len(fig.data) // len(colors) + 1)
    for i, trace in enumerate(fig.data):
        if hasattr(trace, "line"):
            trace.line.color = color_cycle[i % len(color_cycle)]
            trace.line.width = 2


def build_comparison_summary(scores: dict[str, float]) -> go.Figure:
    """
    Crea un gráfico de barras horizontal comparando los Coeficientes Cofenéticos
    de los tres métodos.

    Parámetros
    ----------
    scores : dict
        {'ward': 0.85, 'complete': 0.76, 'average': 0.81}

    Retorna
    -------
    go.Figure
        Gráfico de barras horizontal Plotly.
    """
    _COLORS = {
        "ward": "#6C63FF",
        "complete": "#FF6B6B",
        "average": "#4ECDC4",
    }
    _NAMES = {
        "ward": "Ward",
        "complete": "Complete Linkage",
        "average": "Average Linkage",
    }

    methods = list(scores.keys())
    values = [scores[m] for m in methods]
    colors = [_COLORS.get(m, "#aaaaaa") for m in methods]
    names = [_NAMES.get(m, m) for m in methods]

    best = max(scores, key=lambda m: scores[m])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=colors,
        marker_line_color="#ffffff",
        marker_line_width=0,
        text=[f"{v:.4f}" for v in values],
        textposition="outside",
        textfont={"color": "#ffffff", "size": 13, "family": "Inter, sans-serif"},
        hovertemplate="<b>%{y}</b><br>CCC: %{x:.4f}<extra></extra>",
    ))

    fig.update_layout(
        title={
            "text": f"🏆 Comparación de Coherencia · Mejor: <b>{_NAMES.get(best, best)}</b>",
            "font": {"size": 16, "color": "#FFFFFF"},
            "x": 0.5,
        },
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#111126",
        font={"color": "#c0c0e0", "family": "Inter, sans-serif"},
        height=260,
        margin={"l": 160, "r": 80, "t": 60, "b": 30},
        xaxis={
            "title": "Coeficiente de Correlación Cofenética (CCC)",
            "range": [0, 1.05],
            "gridcolor": "#1e1e3a",
            "tickfont": {"size": 11},
            "title_font": {"size": 12, "color": "#c0c0e0"},
        },
        yaxis={
            "showgrid": False,
            "tickfont": {"size": 12, "color": "#c0c0e0"},
        },
    )

    return fig
