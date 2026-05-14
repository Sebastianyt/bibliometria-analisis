import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
import plotly.io as pio
import tempfile
import os
from fpdf import FPDF


def save_plotly_fig(fig, filename: str) -> str | None:
    """Exporta una figura Plotly a PNG. Devuelve la ruta o None si falla."""
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    error1 = ""
    # Intento 1: to_image (kaleido 1.x)
    try:
        img_bytes = pio.to_image(fig, format="png", scale=2, width=1100, height=500)
        with open(tmp_path, "wb") as f:
            f.write(img_bytes)
        return tmp_path
    except Exception as e:
        error1 = str(e)
        
    # Intento 2: write_image clásico (kaleido 0.x)
    try:
        fig.write_image(tmp_path, scale=2)
        return tmp_path
    except Exception as e:
        st.warning(f"⚠️ No se pudo exportar el gráfico {filename}. Detalles técnicos (pasale esto a la IA): Error 1: {error1} | Error 2: {str(e)}")
        return None

class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 15)
        self.cell(0, 10, "Reporte de Analisis Bibliometrico - IA Generativa", 0, 1, 'C')
        self.set_line_width(0.5)
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf_report(
    heatmap_img_path,
    wordcloud_img_path,
    timeline_paths: dict,          # {"Conference": path, "Periodical": path, ...}
):
    """Genera el PDF con los 3 gráficos principales del Req 5."""
    pdf = ReportPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=11)
    pdf.multi_cell(
        0, 8,
        "Este reporte contiene el analisis visual de la produccion cientifica en materia "
        "de Inteligencia Artificial Generativa. Incluye el mapa de calor geografico, "
        "la nube de palabras clave y la linea temporal de publicaciones por revista "
        "y tipo de documento."
    )
    pdf.ln(4)

    # ── 1. Mapa de Calor ──────────────────────────────────────────────────────
    if heatmap_img_path and os.path.exists(heatmap_img_path):
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 9, "1. Mapa de Calor - Distribucion Geografica", 0, 1)
        pdf.image(heatmap_img_path, x=10, w=190)
        pdf.ln(4)

    # ── 2. Nube de Palabras ───────────────────────────────────────────────────
    if wordcloud_img_path and os.path.exists(wordcloud_img_path):
        if pdf.get_y() > 160:
            pdf.add_page()
        pdf.set_font("Arial", 'B', 13)
        pdf.cell(0, 9, "2. Nube de Palabras - Abstracts y Keywords", 0, 1)
        pdf.image(wordcloud_img_path, x=10, w=190)
        pdf.ln(4)

    # ── 3. Líneas Temporales ──────────────────────────────────────────────────
    section_labels = {
        "Conference":  "3a. Linea Temporal - Conferencias",
        "Periodical":  "3b. Linea Temporal - Publicaciones Periodicas",
        "Article":     "3c. Linea Temporal - Articulos",
        "Todos":       "3d. Linea Temporal - Todos los Tipos",
    }

    for key, label in section_labels.items():
        path = timeline_paths.get(key)
        if path and os.path.exists(path):
            pdf.add_page()
            pdf.set_font("Arial", 'B', 13)
            pdf.cell(0, 9, label, 0, 1)
            pdf.image(path, x=10, w=190)
            pdf.ln(4)

    return bytes(pdf.output())

def render_heatmap(df):
    st.subheader("🗺️ Mapa de Calor: Distribución Geográfica por Primer Autor")
    st.markdown(
        "País de origen **inferido** a partir del apellido del **primer autor** de cada artículo. "
        "La inferencia se basa en patrones lingüísticos y un diccionario de apellidos."
    )

    if df.empty or "authors" not in df.columns:
        st.warning("El dataset no contiene la columna 'authors' para generar el mapa.")
        return None

    from preprocessing.geolocator import get_country_from_authors

    df_map = df.dropna(subset=["authors"]).copy()
    df_map["inferred_country"] = df_map["authors"].apply(get_country_from_authors)
    df_map = df_map[df_map["inferred_country"] != "Unknown"]

    if df_map.empty:
        st.warning("No se pudo inferir ningún país a partir de los apellidos.")
        return None

    loc_counts = df_map["inferred_country"].value_counts().reset_index()
    loc_counts.columns = ["country", "count"]

    # ── Métrica rápida ────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Artículos analizados", len(df_map))
    col_b.metric("Países identificados", loc_counts["country"].nunique())
    col_c.metric("País más frecuente", loc_counts.iloc[0]["country"])

    # ── Choropleth ────────────────────────────────────────────────────────────
    fig = px.choropleth(
        loc_counts,
        locations="country",
        locationmode="country names",
        color="count",
        hover_name="country",
        hover_data={"count": True},
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Distribución Geográfica de Publicaciones (inferida por apellido del primer autor)",
        template="plotly_dark",
        labels={"count": "Artículos"},
    )

    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Artículos"),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.2)",
            showland=True,
            landcolor="rgba(30,30,60,0.8)",
            showocean=True,
            oceancolor="rgba(10,10,30,0.9)",
            showlakes=False,
            showcountries=True,
            countrycolor="rgba(255,255,255,0.15)",
        ),
    )

    # Etiquetas de país sobre el mapa
    fig.add_scattergeo(
        locations=loc_counts["country"],
        locationmode="country names",
        text=loc_counts.apply(
            lambda r: f"{r['country']}<br>{r['count']} art.", axis=1
        ),
        mode="text",
        textfont=dict(color="white", size=10),
        hoverinfo="skip",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de detalle ──────────────────────────────────────────────────────
    with st.expander("📋 Ver tabla de distribución por país"):
        st.dataframe(
            loc_counts.rename(columns={"country": "País", "count": "Artículos"}),
            use_container_width=True,
            hide_index=True,
        )

    return save_plotly_fig(fig, "heatmap_export.png")

@st.cache_data(show_spinner=False)
def _generate_wordcloud_image(text: str) -> str | None:
    """Genera la nube de palabras y la guarda como PNG. Resultado cacheado."""
    if not text.strip():
        return None
    wordcloud = WordCloud(
        width=900, height=420,
        background_color="white",
        colormap="viridis",
        max_words=150,
    ).generate(text)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    tmp_path = os.path.join(tempfile.gettempdir(), "wordcloud_export.png")
    fig.savefig(tmp_path, bbox_inches="tight", dpi=200)
    plt.close(fig)
    return tmp_path


def render_wordcloud(df):
    st.subheader("☁️ Nube de Palabras: Términos Frecuentes")
    st.markdown(
        "Nube de palabras generada a partir de los campos **Abstract** y **Keywords** "
        "de los estudios cargados. Se genera una sola vez y se almacena en caché."
    )

    if df.empty or ("abstract" not in df.columns and "keywords" not in df.columns):
        st.warning("No hay suficientes datos (abstracts o keywords) para generar la nube de palabras.")
        return None

    # Si ya está en session_state, mostrarla directamente sin spinner ni recálculo
    if "wc_path" in st.session_state and st.session_state["wc_path"] and os.path.exists(st.session_state["wc_path"]):
        st.image(st.session_state["wc_path"], use_container_width=True)
        return st.session_state["wc_path"]

    text_parts = []
    if "abstract" in df.columns:
        text_parts.extend(df["abstract"].dropna().astype(str).tolist())
    if "keywords" in df.columns:
        text_parts.extend(df["keywords"].dropna().astype(str).tolist())
    text = " ".join(text_parts)

    with st.spinner("Generando nube de palabras..."):
        tmp_path = _generate_wordcloud_image(text)

    if not tmp_path:
        st.warning("Los abstracts y keywords están vacíos.")
        return None

    st.session_state["wc_path"] = tmp_path
    st.image(tmp_path, use_container_width=True)
    return tmp_path

def render_timeline(df):
    st.subheader("📈 Línea Temporal de Publicaciones por Año y Revista")
    st.markdown("Distribución de publicaciones científicas por año, revista y tipo de documento.")

    required_cols = {"year", "journal", "document_type"}
    if df.empty or not required_cols.issubset(df.columns):
        st.warning("El dataset no contiene las columnas necesarias (year, journal, document_type).")
        return None

    df_valid = df.dropna(subset=["year"]).copy()
    df_valid["journal"] = df_valid["journal"].fillna("Desconocida").str.strip()
    df_valid["year"] = df_valid["year"].astype(int)
    df_valid["document_type"] = df_valid["document_type"].fillna("Article").str.strip()

    # ── Controles globales ─────────────────────────────────────────────────────
    years = sorted(df_valid["year"].unique())
    col_yr, col_top = st.columns([2, 1])
    with col_yr:
        year_range = st.slider(
            "📅 Rango de años",
            min_value=int(min(years)),
            max_value=int(max(years)),
            value=(int(min(years)), int(max(years))),
            key="tl_year_range"
        )
    with col_top:
        top_n = st.selectbox(
            "🏆 Top N revistas a mostrar",
            options=[5, 10, 15, 20],
            index=1,
            key="tl_top_n"
        )

    df_filtered = df_valid[
        (df_valid["year"] >= year_range[0]) & (df_valid["year"] <= year_range[1])
    ]

    if df_filtered.empty:
        st.warning("No hay publicaciones en el rango de años seleccionado.")
        return None

    # ── Métricas globales ──────────────────────────────────────────────────────
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("📚 Total artículos", len(df_filtered))
    col_m2.metric("🗓️ Años cubiertos", df_filtered["year"].nunique())
    col_m3.metric("📰 Revistas únicas", df_filtered["journal"].nunique())
    col_m4.metric("📂 Tipos de documento", df_filtered["document_type"].nunique())

    st.markdown("---")

    # ── Función auxiliar para un gráfico por tipo de documento ────────────────
    def build_chart(df_sub, doc_type_label, color_seq):
        if df_sub.empty:
            st.info(f"No hay publicaciones del tipo **{doc_type_label}** en el rango seleccionado.")
            return None

        top_journals = (
            df_sub["journal"]
            .value_counts()
            .head(top_n)
            .index
            .tolist()
        )

        df_sub = df_sub.copy()

        def shorten(name, max_len=55):
            return name if len(name) <= max_len else name[:max_len] + "…"

        df_sub["journal_display"] = df_sub["journal"].apply(
            lambda j: shorten(j) if j in top_journals else "Otras revistas / conferencias"
        )

        timeline_data = (
            df_sub.groupby(["year", "journal_display"])
            .size()
            .reset_index(name="count")
        )

        order = sorted([j for j in timeline_data["journal_display"].unique()
                        if j != "Otras revistas / conferencias"])
        if "Otras revistas / conferencias" in timeline_data["journal_display"].values:
            order.append("Otras revistas / conferencias")

        # Métricas del tipo
        top_journal_raw = df_sub["journal"].value_counts().index[0]
        top_journal_display = top_journal_raw[:45] + "…" if len(top_journal_raw) > 45 else top_journal_raw
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total {doc_type_label}", len(df_sub))
        c2.metric("Año con más publicaciones", int(df_sub["year"].value_counts().idxmax()))
        c3.metric("Fuente más frecuente", top_journal_display)

        fig = px.bar(
            timeline_data,
            x="year",
            y="count",
            color="journal_display",
            category_orders={"journal_display": order},
            title=f"Publicaciones por Año y Revista — {doc_type_label}",
            labels={
                "year": "Año de Publicación",
                "count": "Número de Artículos",
                "journal_display": "Revista / Conferencia"
            },
            barmode="stack",
            template="plotly_dark",
            color_discrete_sequence=color_seq,
        )

        fig.update_layout(
            xaxis=dict(tickformat="d", dtick=1),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01,
                font=dict(size=10),
                title_text="Revista / Conferencia"
            ),
            margin=dict(r=280, t=60, b=60),
            height=440,
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"📋 Ver tabla de datos — {doc_type_label}"):
            tbl = (
                df_sub.groupby(["year", "journal"])
                .size()
                .reset_index(name="Artículos")
                .rename(columns={"year": "Año", "journal": "Revista / Conferencia"})
                .sort_values(["Año", "Artículos"], ascending=[True, False])
            )
            st.dataframe(tbl, use_container_width=True, hide_index=True)

        return save_plotly_fig(fig, f"timeline_{doc_type_label.lower()}.png")

    # ── Paletas de color por tipo ──────────────────────────────────────────────
    COLORS_CONF = px.colors.qualitative.Bold
    COLORS_PERI = px.colors.qualitative.Pastel
    COLORS_ART  = px.colors.qualitative.Safe

    # ── Pestañas por tipo de documento ────────────────────────────────────────
    tab_conf, tab_peri, tab_art, tab_all = st.tabs([
        "🎤 Conference",
        "📰 Periodical",
        "📄 Article",
        "🔭 Todos los tipos",
    ])

    tl_paths: dict = {}

    with tab_conf:
        st.markdown("#### Conferencias — publicaciones por año y fuente")
        df_conf = df_filtered[df_filtered["document_type"].str.lower() == "conference"]
        tl_paths["Conference"] = build_chart(df_conf, "Conference", COLORS_CONF)

    with tab_peri:
        st.markdown("#### Publicaciones periódicas — revistas académicas")
        df_peri = df_filtered[df_filtered["document_type"].str.lower() == "periodical"]
        tl_paths["Periodical"] = build_chart(df_peri, "Periodical", COLORS_PERI)

    with tab_art:
        st.markdown("#### Artículos — distribución temporal")
        df_art = df_filtered[df_filtered["document_type"].str.lower() == "article"]
        tl_paths["Article"] = build_chart(df_art, "Article", COLORS_ART)

    with tab_all:
        st.markdown("#### Vista combinada — los tres tipos de documento")
        df_all_grp = (
            df_filtered.groupby(["year", "document_type"])
            .size()
            .reset_index(name="count")
        )

        COLOR_MAP = {
            "Conference": "#6C63FF",
            "Periodical": "#FF6584",
            "Article":    "#43CFAB",
        }

        fig_all = px.bar(
            df_all_grp,
            x="year",
            y="count",
            color="document_type",
            color_discrete_map=COLOR_MAP,
            title="Publicaciones por Año según Tipo de Documento",
            labels={
                "year": "Año",
                "count": "N° de Artículos",
                "document_type": "Tipo"
            },
            barmode="group",
            template="plotly_dark",
        )
        fig_all.update_layout(
            xaxis=dict(tickformat="d", dtick=1),
            height=440,
            legend=dict(title="Tipo de documento"),
        )
        st.plotly_chart(fig_all, use_container_width=True)

        with st.expander("📋 Ver tabla combinada"):
            tbl_all = (
                df_filtered.groupby(["year", "document_type", "journal"])
                .size()
                .reset_index(name="Artículos")
                .rename(columns={
                    "year": "Año",
                    "document_type": "Tipo",
                    "journal": "Revista / Conferencia"
                })
                .sort_values(["Año", "Tipo"], ascending=True)
            )
            st.dataframe(tbl_all, use_container_width=True, hide_index=True)

        tl_paths["Todos"] = save_plotly_fig(fig_all, "timeline_todos.png")

    return tl_paths


def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_dir, "data", "processed", "unified_articles.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()


def render():
    df_vis = load_data()

    hm_path = render_heatmap(df_vis)
    st.markdown("<br>", unsafe_allow_html=True)

    wc_path = render_wordcloud(df_vis)
    st.markdown("<br>", unsafe_allow_html=True)

    tl_paths = render_timeline(df_vis)   # dict: {"Conference": path, ...}
    if not isinstance(tl_paths, dict):
        tl_paths = {}

    st.divider()
    st.subheader("📄 Exportar Reporte a PDF")
    st.info(
        "El PDF incluirá: **Mapa de Calor**, **Nube de Palabras** y "
        "**4 gráficos de la Línea Temporal** (Conference, Periodical, Article, Todos)."
    )

    any_path = hm_path or wc_path or any(tl_paths.values())
    if st.button("Generar PDF con los gráficos actuales", type="primary"):
        if any_path:
            with st.spinner("Generando documento PDF con todos los gráficos..."):
                try:
                    pdf_bytes = create_pdf_report(hm_path, wc_path, tl_paths)
                    graficos_ok = (["Mapa de Calor"] if hm_path else []) + \
                                  (["Nube de Palabras"] if wc_path else []) + \
                                  [f"Timeline {k}" for k, v in tl_paths.items() if v]
                    st.success(f"PDF generado con: {', '.join(graficos_ok)}")
                    st.download_button(
                        label="⬇️ Descargar Reporte PDF",
                        data=pdf_bytes,
                        file_name="reporte_visual.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"Error al generar el PDF: {e}")
        else:
            st.warning("No hay gráficos disponibles para exportar.")

