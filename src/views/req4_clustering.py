"""
modules/req4_clustering.py
---------------------------
Módulo Streamlit para el Requerimiento 4:
Agrupamiento jerárquico de abstracts científicos con tres algoritmos
(Ward, Complete Linkage, Average Linkage) y visualización mediante
dendrogramas interactivos.
"""

import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis.clustering.hierarchical import HierarchicalClustering
from analysis.clustering.dendrogram import build_plotly_dendrogram, build_comparison_summary
from analysis.clustering.linkage_methods import get_method_info, get_all_methods


# ─── Carga de datos (cacheada) ──────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _load_articles() -> pd.DataFrame:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(base_dir, "data", "processed", "unified_articles.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def _get_valid_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra filas con abstract y título válidos."""
    if "abstract" not in df.columns or "title" not in df.columns:
        return pd.DataFrame()
    df = df.dropna(subset=["abstract", "title"])
    df = df[df["abstract"].astype(str).str.strip().str.len() > 50]
    df = df[df["title"].astype(str).str.strip() != ""]
    return df.reset_index(drop=True)


# ─── Render principal ───────────────────────────────────────────────────────

def render():
    st.subheader("🌳 Agrupamiento Jerárquico de Abstracts Científicos")
    st.markdown(
        "Aplica **tres algoritmos de clustering jerárquico** sobre los abstracts del dataset "
        "para construir dendrogramas que representan la similitud temática entre artículos. "
        "Se utiliza **TF-IDF** como representación vectorial y **distancia coseno** como métrica."
    )

    # ─── Carga de datos ──────────────────────────────────────────────────────
    with st.spinner("Cargando artículos..."):
        df_raw = _load_articles()

    if df_raw.empty:
        st.error(
            "❌ No se encontró `unified_articles.csv`. "
            "Ejecuta primero `python src/main.py` para generar los datos."
        )
        return

    df = _get_valid_df(df_raw)
    total = len(df)

    if total < 5:
        st.warning(f"Solo hay {total} artículos con abstract válido. Se necesitan al menos 5.")
        return

    st.success(f"✅ **{total}** artículos con abstract válido encontrados.")
    st.divider()

    # ─── Controles ───────────────────────────────────────────────────────────
    st.markdown("### ⚙️ Configuración del Análisis")

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        n_articles = st.slider(
            "Número de artículos a agrupar",
            min_value=5,
            max_value=min(total, 120),
            value=min(40, total),
            step=5,
            help=(
                "Más artículos = dendrograma más rico, pero más lento. "
                "Para exploración inicial se recomiendan 30–50."
            ),
        )
    with col_ctrl2:
        sampling = st.selectbox(
            "Selección de artículos",
            options=["Primeros N", "Muestra aleatoria"],
            index=0,
            help="'Primeros N' toma los primeros artículos del CSV. 'Muestra aleatoria' elige N al azar.",
        )

    if sampling == "Muestra aleatoria":
        df_sel = df.sample(n=n_articles, random_state=42).reset_index(drop=True)
    else:
        df_sel = df.head(n_articles).reset_index(drop=True)

    abstracts = df_sel["abstract"].astype(str).tolist()
    titles = df_sel["title"].astype(str).tolist()

    st.markdown(f"*Se analizarán **{n_articles}** artículos.*")
    st.divider()

    # ─── Ejecución ───────────────────────────────────────────────────────────
    if st.button(
        "🚀 Ejecutar Agrupamiento Jerárquico",
        type="primary",
        use_container_width=True,
        key="btn_clustering",
    ):
        with st.spinner("Preprocesando textos y calculando clusters... esto puede tomar unos segundos."):
            hc = HierarchicalClustering()
            try:
                hc.run_all(abstracts, titles)
            except Exception as e:
                st.error(f"Error durante el clustering: {e}")
                return

        # Guardamos en session_state para no recalcular al interactuar con la UI
        st.session_state["hc_result"] = hc
        st.session_state["hc_n"] = n_articles

    # ─── Resultados ──────────────────────────────────────────────────────────
    if "hc_result" not in st.session_state:
        st.info("👆 Configura los parámetros y presiona **Ejecutar Agrupamiento Jerárquico**.")
        return

    hc: HierarchicalClustering = st.session_state["hc_result"]

    _render_results(hc)


def _render_results(hc: HierarchicalClustering):
    """Renderiza todos los resultados del clustering."""

    scores = hc.scores
    best = hc.best_method()
    methods = get_all_methods()

    # ─── Tabla comparativa de coherencia ─────────────────────────────────────
    st.markdown("## 📊 Comparación de Coherencia entre Algoritmos")
    st.markdown(
        "El **Coeficiente de Correlación Cofenética (CCC)** mide qué tan fielmente el "
        "dendrograma preserva las distancias originales entre artículos. "
        "**Mayor CCC → agrupamiento más coherente.**"
    )

    fig_comparison = build_comparison_summary(scores)
    st.plotly_chart(fig_comparison, use_container_width=True)

    # Tabla de scores
    _NAMES = {"ward": "Ward", "complete": "Complete Linkage", "average": "Average Linkage"}
    rows = []
    for m in methods:
        ccc = scores.get(m, 0.0)
        es_mejor = "🏆 Más coherente" if m == best else ""
        interpretacion = (
            "Excelente" if ccc >= 0.85
            else "Bueno" if ccc >= 0.75
            else "Moderado" if ccc >= 0.65
            else "Bajo"
        )
        rows.append({
            "Algoritmo": _NAMES[m],
            "CCC": f"{ccc:.4f}",
            "Interpretación": interpretacion,
            "Evaluación": es_mejor,
        })

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
    )

    best_name = _NAMES.get(best, best)
    best_ccc = scores.get(best, 0)
    st.success(
        f"✅ **El método más coherente es {best_name}** con CCC = {best_ccc:.4f}. "
        f"Este algoritmo preserva mejor la estructura de similitud entre los abstracts."
    )

    st.divider()

    # ─── Dendrogramas por método ─────────────────────────────────────────────
    st.markdown("## 🌳 Dendrogramas Interactivos")
    st.markdown(
        "Cada pestaña muestra el dendrograma del método correspondiente. "
        "Puedes hacer **zoom**, **hover** sobre las ramas y ver las etiquetas de cada artículo."
    )

    tab_ward, tab_complete, tab_average = st.tabs([
        "🟣 Ward",
        "🔴 Complete Linkage",
        "🔵 Average Linkage",
    ])

    tab_map = {
        "ward": tab_ward,
        "complete": tab_complete,
        "average": tab_average,
    }

    for method, tab in tab_map.items():
        with tab:
            _render_method_tab(hc, method, scores)


def _render_method_tab(hc: HierarchicalClustering, method: str, scores: dict):
    """Renderiza el contenido completo de un tab de método."""
    info = get_method_info(method)
    _NAMES = {"ward": "Ward", "complete": "Complete Linkage", "average": "Average Linkage"}
    name = _NAMES.get(method, method)

    # Cabecera
    ccc = scores.get(method, 0.0)
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"### {info.get('emoji', '')} Método: {name}")
        st.markdown(info.get("description", ""))
    with col_h2:
        st.metric(
            label="Coeficiente Cofenético (CCC)",
            value=f"{ccc:.4f}",
            delta="Más alto = más coherente",
            delta_color="off",
        )

    # Dendrograma
    st.markdown("#### Dendrograma")
    try:
        fig = build_plotly_dendrogram(
            distance_matrix=hc.distance_matrix,
            labels=hc.labels,
            method=method,
            title=f"Dendrograma — {name} · CCC: {ccc:.4f}",
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al generar el dendrograma: {e}")

    st.caption(
        "📌 Eje X: artículos ordenados por el agrupamiento. "
        "Eje Y: distancia de enlace (mayor = más diferentes)."
    )

    # Explicación matemática
    with st.expander("📐 Fundamento matemático del método", expanded=False):
        st.markdown(info.get("formula", ""))

        col_p, col_c = st.columns(2)
        with col_p:
            st.markdown("**✅ Ventajas**")
            for p in info.get("pros", []):
                st.markdown(f"- {p}")
        with col_c:
            st.markdown("**⚠️ Limitaciones**")
            for c in info.get("cons", []):
                st.markdown(f"- {c}")

        st.info(f"💡 **Caso de uso:** {info.get('use_case', '')}")

    # Explicación del CCC
    with st.expander("📖 ¿Cómo interpretar el CCC?", expanded=False):
        st.markdown("""
El **Coeficiente de Correlación Cofenética (CCC)** es la correlación de Pearson entre:

1. La **matriz de distancias original** (distancias coseno TF-IDF entre artículos)
2. La **matriz cofenética** (altura del dendrograma en la que dos artículos se unen)

$$CCC = \\text{corr}(d_{ij},\\; c_{ij})$$

| Rango CCC | Interpretación |
|---|---|
| 0.85 – 1.00 | ✅ Excelente coherencia |
| 0.75 – 0.84 | 🟡 Buena coherencia |
| 0.65 – 0.74 | 🟠 Coherencia moderada |
| < 0.65 | 🔴 Baja coherencia |

> Un CCC alto indica que el dendrograma es un buen resumen visual
> de la estructura de similitud real entre los abstracts.
        """)
