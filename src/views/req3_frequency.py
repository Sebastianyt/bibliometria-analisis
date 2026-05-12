"""
req3_frequency.py  —  Requerimiento 3
Página Streamlit con las 4 tareas de análisis de frecuencia y generación
de nuevas palabras para la categoría "Concepts of Generative AI in Education".
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analysis.frequency_analysis.keyword_counter import count_keyword_frequencies
from analysis.frequency_analysis.word_extractor import extract_new_keywords
from analysis.frequency_analysis.precision_evaluator import evaluate_precision, average_precision

# ─────────────────────────────────────────────
# Constantes del requerimiento
# ─────────────────────────────────────────────
CATEGORY = "Concepts of Generative AI in Education"

ORIGINAL_KEYWORDS = [
    "Generative models",
    "Prompting",
    "Machine learning",
    "Multimodality",
    "Fine-tuning",
    "Training data",
    "Algorithmic bias",
    "Explainability",
    "Transparency",
    "Ethics",
    "Privacy",
    "Personalization",
    "Human-AI interaction",
    "AI literacy",
    "Co-creation",
]

# ─────────────────────────────────────────────
# Carga de datos
# ─────────────────────────────────────────────
@st.cache_data
def load_abstracts():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(base_dir, "data", "processed", "unified_articles.csv")
    if not os.path.exists(path):
        return pd.DataFrame(), []
    df = pd.read_csv(path)
    if "abstract" not in df.columns:
        return df, []
    df = df.dropna(subset=["abstract"])
    df = df[df["abstract"].astype(str).str.strip() != ""]
    abstracts = df["abstract"].astype(str).tolist()
    return df, abstracts


# ─────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────
def freq_bar_chart(df_freq: pd.DataFrame, title: str, color: str):
    fig = px.bar(
        df_freq,
        x="doc_freq",
        y="keyword",
        orientation="h",
        text="pct",
        labels={"doc_freq": "Artículos que la contienen", "keyword": "Término"},
        title=title,
        color_discrete_sequence=[color],
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        title_font_size=15,
        height=520,
        margin=dict(l=10, r=40, t=50, b=10),
    )
    return fig


# ─────────────────────────────────────────────
# Página principal
# ─────────────────────────────────────────────
def render():
    st.title("📊 Requerimiento 3: Análisis de Frecuencia y Generación de Palabras Clave")
    st.markdown(
        f"**Categoría analizada:** `{CATEGORY}`  \n"
        "Las frecuencias se calculan sobre los **abstracts** de todos los artículos del corpus."
    )

    df, abstracts = load_abstracts()

    if not abstracts:
        st.error(
            "No se encontraron abstracts. Ejecuta primero `python src/main.py` "
            "para generar `unified_articles.csv`."
        )
        return

    st.info(f"📚 Corpus cargado: **{len(abstracts)} abstracts** disponibles para el análisis.")
    st.divider()

    # ══════════════════════════════════════════════════════════════════
    # TAREA 1 — Frecuencia de palabras originales
    # ══════════════════════════════════════════════════════════════════
    st.subheader("1️⃣ Frecuencia de las Palabras Asociadas Originales")
    st.markdown(
        "Se busca cada término (incluyendo frases multipalabra) en todos los abstracts "
        "de manera **case-insensitive**."
    )

    with st.spinner("Calculando frecuencias originales..."):
        freq_original = count_keyword_frequencies(ORIGINAL_KEYWORDS, abstracts)

    df_orig = pd.DataFrame(freq_original)

    col_t1, col_t2 = st.columns([1, 1.6])
    with col_t1:
        st.markdown("**Tabla de frecuencias**")
        display_orig = df_orig.rename(columns={
            "keyword": "Palabra Clave",
            "doc_freq": "Artículos",
            "abs_freq": "Ocurrencias totales",
            "pct": "% del corpus"
        })
        st.dataframe(display_orig, use_container_width=True, hide_index=True)

    with col_t2:
        fig1 = freq_bar_chart(df_orig, "Presencia de palabras originales en abstracts", "#6C63FF")
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # ══════════════════════════════════════════════════════════════════
    # TAREA 2 — Generación de nuevas palabras con TF-IDF
    # ══════════════════════════════════════════════════════════════════
    st.subheader("2️⃣ Generación de Nuevas Palabras Asociadas (TF-IDF)")

    with st.expander("📖 ¿Cómo funciona el algoritmo de extracción?", expanded=False):
        st.markdown("""
**Algoritmo TF-IDF con N-Gramas** (implementado en `word_extractor.py`):

1. **Vectorización**: Se aplica `TfidfVectorizer` con `ngram_range=(1,2)` para capturar
   tanto palabras simples (*"curriculum"*) como bigramas (*"language model"*).
2. **Ponderación**: Cada término recibe un score = `TF × IDF`:
   - **TF** (Term Frequency): cuántas veces aparece en ese abstract
   - **IDF** (Inverse Document Frequency): penaliza palabras demasiado comunes
3. **Score promedio**: Se calcula el score medio de cada término en todo el corpus.
4. **Filtrado triple**:
   - Se descartan términos que ya existen en la lista original
   - Se descartan stopwords académicas genéricas (*"paper"*, *"study"*, *"method"*...)
   - Se descartan términos de menos de 4 caracteres o numéricos
5. **Top-15**: Se retornan los 15 términos con mayor score promedio.
        """)

    with st.spinner("Analizando corpus con TF-IDF... generando nuevas palabras..."):
        new_kw_data = extract_new_keywords(abstracts, ORIGINAL_KEYWORDS, max_new=15)

    new_terms = [d["term"] for d in new_kw_data]
    new_scores = [d["tfidf_score"] for d in new_kw_data]

    if not new_kw_data:
        st.warning("No se pudieron generar palabras nuevas. El corpus puede ser muy pequeño.")
        return

    st.success(f"✅ Se generaron **{len(new_kw_data)} nuevas palabras** asociadas a la categoría.")

    df_new_gen = pd.DataFrame(new_kw_data).rename(columns={
        "term": "Nuevo Término",
        "tfidf_score": "Score TF-IDF"
    })

    col_g1, col_g2 = st.columns([1, 1.4])
    with col_g1:
        st.markdown("**Nuevos términos generados**")
        st.dataframe(df_new_gen, use_container_width=True, hide_index=True)
    with col_g2:
        fig2 = px.bar(
            df_new_gen,
            x="Score TF-IDF",
            y="Nuevo Término",
            orientation="h",
            title="Score TF-IDF de los nuevos términos",
            color="Score TF-IDF",
            color_continuous_scale="Plasma",
        )
        fig2.update_layout(
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            height=520,
            margin=dict(l=10, r=10, t=50, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ══════════════════════════════════════════════════════════════════
    # TAREA 3 — Frecuencia de las nuevas palabras
    # ══════════════════════════════════════════════════════════════════
    st.subheader("3️⃣ Frecuencia de las Nuevas Palabras en el Corpus")
    st.markdown("Se aplica el mismo algoritmo de conteo que en la Tarea 1, ahora sobre los términos generados.")

    with st.spinner("Calculando frecuencias de nuevas palabras..."):
        freq_new = count_keyword_frequencies(new_terms, abstracts)

    df_freq_new = pd.DataFrame(freq_new)
    df_freq_new.rename(columns={"keyword": "keyword"}, inplace=True)

    col_f1, col_f2 = st.columns([1, 1.6])
    with col_f1:
        st.markdown("**Tabla de frecuencias — nuevos términos**")
        display_new = df_freq_new.rename(columns={
            "keyword": "Término Nuevo",
            "doc_freq": "Artículos",
            "abs_freq": "Ocurrencias totales",
            "pct": "% del corpus"
        })
        st.dataframe(display_new, use_container_width=True, hide_index=True)
    with col_f2:
        fig3 = freq_bar_chart(df_freq_new, "Presencia de nuevos términos en abstracts", "#00C9A7")
        st.plotly_chart(fig3, use_container_width=True)

    # Comparativa original vs nuevas
    st.markdown("#### 📈 Comparativa: Palabras originales vs. nuevas palabras")
    df_orig_cmp = df_orig[["keyword", "doc_freq"]].copy()
    df_orig_cmp["grupo"] = "Originales"
    df_freq_new_cmp = df_freq_new[["keyword", "doc_freq"]].copy()
    df_freq_new_cmp["grupo"] = "Nuevas (TF-IDF)"
    df_compare = pd.concat([df_orig_cmp, df_freq_new_cmp], ignore_index=True)

    fig_cmp = px.bar(
        df_compare,
        x="keyword",
        y="doc_freq",
        color="grupo",
        barmode="group",
        labels={"keyword": "Término", "doc_freq": "Artículos", "grupo": "Grupo"},
        title="Comparativa de frecuencias: Originales vs. Nuevas",
        color_discrete_map={"Originales": "#6C63FF", "Nuevas (TF-IDF)": "#00C9A7"},
    )
    fig_cmp.update_layout(
        xaxis_tickangle=-40,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0"),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_cmp, use_container_width=True)
    st.divider()

    # ══════════════════════════════════════════════════════════════════
    # TAREA 4 — Evaluación de precisión
    # ══════════════════════════════════════════════════════════════════
    st.subheader("4️⃣ Evaluación de Precisión de las Nuevas Palabras")

    with st.expander("📖 ¿Cómo se mide la precisión?", expanded=False):
        st.markdown(f"""
**Método: Similitud Semántica con BERT (MiniLM)**

1. Se genera un **embedding de la categoría**: `"{CATEGORY}"`
   usando el modelo `all-MiniLM-L6-v2` (384 dimensiones).
2. Se genera un **embedding de cada nuevo término** con el mismo modelo.
3. Se calcula la **similitud coseno** entre el vector del término y el de la categoría.
4. El resultado se interpreta como **precisión %**:
   - 🟢 **Alta** (≥ 70%): el término está claramente relacionado con la categoría
   - 🟡 **Media** (40–70%): relacionado pero en el borde del dominio
   - 🔴 **Baja** (< 40%): término poco pertinente para la categoría

> La similitud coseno mide el ángulo entre dos vectores de 384 dimensiones.
> Si apuntan en la misma dirección, el significado es equivalente → precisión alta.
        """)

    try:
        with st.spinner("Calculando precisión semántica con BERT MiniLM..."):
            eval_results = evaluate_precision(new_terms, CATEGORY)

        avg_prec = average_precision(eval_results)

        # KPI global
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        high = sum(1 for e in eval_results if e["precision"] >= 0.70)
        mid  = sum(1 for e in eval_results if 0.40 <= e["precision"] < 0.70)
        low  = sum(1 for e in eval_results if e["precision"] < 0.40)

        kpi_col1.metric("🎯 Precisión Promedio", f"{avg_prec * 100:.1f}%")
        kpi_col2.metric("🟢 Alta precisión", f"{high} términos")
        kpi_col3.metric("🟡 Media / 🔴 Baja", f"{mid + low} términos")

        st.markdown("#### Detalle por término")

        # Tabla con colores
        for e in eval_results:
            cols = st.columns([3, 2, 2])
            cols[0].markdown(f"**{e['term']}**")
            cols[1].progress(e["precision"], text=f"{e['pct']:.1f}%")
            cols[2].markdown(f"{e['label']}")

        st.markdown("---")

        # Gráfico de radar / gauge de precisión promedio
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_prec * 100,
            title={"text": "Precisión Promedio del Conjunto Generado", "font": {"size": 16}},
            delta={"reference": 50, "suffix": "%"},
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#6C63FF"},
                "steps": [
                    {"range": [0, 40],  "color": "#3d1a1a"},
                    {"range": [40, 70], "color": "#3d3010"},
                    {"range": [70, 100],"color": "#0f3d20"},
                ],
                "threshold": {
                    "line": {"color": "#ffffff", "width": 3},
                    "thickness": 0.8,
                    "value": avg_prec * 100,
                },
            },
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            height=320,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.caption(
            "💡 Una precisión promedio ≥ 70% indica que el algoritmo TF-IDF generó palabras "
            "semánticamente coherentes con la categoría analizada."
        )

    except Exception as _bert_err:
        st.warning(
            f"⚠️ No se pudo cargar el modelo BERT para la evaluación de precisión. "
            f"Las demás tareas funcionan correctamente.\n\n"
            f"*Detalle técnico: {_bert_err}*"
        )

