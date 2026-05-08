import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
import tempfile
import os
from fpdf import FPDF

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

def create_pdf_report(heatmap_img_path, wordcloud_img_path, timeline_img_path):
    pdf = ReportPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "Este reporte contiene el analisis visual de la produccion cientifica en materia de Inteligencia Artificial Generativa. Incluye el mapa de calor, la nube de palabras clave y la distribucion temporal de publicaciones.")
    pdf.ln(5)
    
    if heatmap_img_path:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "1. Mapa de Calor (Distribucion Geografica)", 0, 1)
        pdf.image(heatmap_img_path, x=10, w=190)
        pdf.ln(5)
        
    if wordcloud_img_path:
        if pdf.get_y() > 150:
            pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "2. Nube de Palabras (Abstracts y Keywords)", 0, 1)
        pdf.image(wordcloud_img_path, x=10, w=190)
        pdf.ln(5)
        
    if timeline_img_path:
        if pdf.get_y() > 150:
            pdf.add_page()
            
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "3. Linea Temporal por Ano y Revista", 0, 1)
        pdf.image(timeline_img_path, x=10, w=190)

    return bytes(pdf.output())

def render_heatmap(df):
    st.subheader("🗺️ Mapa de Calor: Distribución Geográfica")
    st.markdown("Ubicación geográfica de los editores o autores basada en el campo de locación.")

    if df.empty or "publisherLocations" not in df.columns:
        st.warning("El dataset no contiene la columna 'publisherLocations' para generar el mapa.")
        return None
    
    df_loc = df.dropna(subset=["publisherLocations"]).copy()
    df_loc["publisherLocations"] = df_loc["publisherLocations"].astype(str).str.strip()
    df_loc = df_loc[df_loc["publisherLocations"] != ""]
    
    if df_loc.empty:
        st.warning("No se encontraron locaciones válidas en los artículos.")
        return None

    # Count occurrences
    loc_counts = df_loc['publisherLocations'].value_counts().reset_index()
    loc_counts.columns = ['country', 'count']
    
    fig = px.choropleth(
        loc_counts,
        locations="country",
        locationmode="country names",
        color="count",
        hover_name="country",
        color_continuous_scale=px.colors.sequential.Plasma,
        title="Distribución de Publicaciones por País/Locación",
        template='plotly_dark'
    )
    
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    # Añadir los nombres de los países sobre el mapa
    fig.add_scattergeo(
        locations=loc_counts['country'],
        locationmode='country names',
        text=loc_counts['country'],
        mode='text',
        textfont=dict(color='white', size=12, weight='bold')
    )

    st.plotly_chart(fig, use_container_width=True)
    
    tmp_path = os.path.join(tempfile.gettempdir(), "heatmap_export.png")
    try:
        fig.write_image(tmp_path, scale=2)
    except ValueError as e:
        st.error(f"Error al exportar el mapa (se requiere kaleido): {e}")
        return None
        
    return tmp_path

def render_wordcloud(df):
    st.subheader("☁️ Nube de Palabras: Términos Frecuentes")
    st.markdown("Nube de palabras dinámica generada a partir de los campos **Abstract** y **Keywords** de los estudios cargados.")

    if df.empty or ("abstract" not in df.columns and "keywords" not in df.columns):
        st.warning("No hay suficientes datos (abstracts o keywords) para generar la nube de palabras.")
        return None

    text_data = []
    if "abstract" in df.columns:
        text_data.extend(df["abstract"].dropna().astype(str).tolist())
    if "keywords" in df.columns:
        text_data.extend(df["keywords"].dropna().astype(str).tolist())
    
    text = " ".join(text_data)
    
    if not text.strip():
        st.warning("Los abstracts y keywords están vacíos.")
        return None

    wordcloud = WordCloud(
        width=800, height=400,
        background_color='white',
        colormap='viridis',
        max_words=150
    ).generate(text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)
    
    tmp_path = os.path.join(tempfile.gettempdir(), "wordcloud_export.png")
    fig.savefig(tmp_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    return tmp_path

def render_timeline(df):
    st.subheader("📈 Línea Temporal de Publicaciones")
    st.markdown("Distribución de artículos científicos publicados por año y por revista.")

    if df.empty or "year" not in df.columns or "journal" not in df.columns:
        st.warning("El dataset no contiene las columnas necesarias (year, journal) para esta visualización.")
        return None
    
    df_valid = df.dropna(subset=["year"])
    df_valid["journal"] = df_valid["journal"].fillna("Desconocida")
    
    timeline_data = df_valid.groupby(['year', 'journal']).size().reset_index(name='count')
    
    if timeline_data.empty:
        st.warning("No se encontraron publicaciones con año válido.")
        return None

    fig = px.bar(
        timeline_data,
        x='year',
        y='count',
        color='journal',
        title='Publicaciones por Año y Revista',
        labels={'year': 'Año de Publicación', 'count': 'Número de Artículos', 'journal': 'Revista'},
        barmode='stack',
        template='plotly_dark'
    )
    
    fig.update_layout(xaxis=dict(tickformat="d"))

    st.plotly_chart(fig, use_container_width=True)
    
    tmp_path = os.path.join(tempfile.gettempdir(), "timeline_export.png")
    try:
        fig.write_image(tmp_path, scale=2)
    except ValueError as e:
        st.error(f"Error al exportar la imagen de Plotly (se requiere kaleido): {e}")
        return None
        
    return tmp_path

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
    
    col_wc, col_tl = st.columns(2)
    with col_wc:
        wc_path = render_wordcloud(df_vis)
    with col_tl:
        tl_path = render_timeline(df_vis)
        
    st.divider()
    st.subheader("📄 Exportar Reporte a PDF")
    st.info("Haz clic en generar para compilar las imágenes en un documento PDF. Este proceso puede tardar unos segundos.")
    if st.button("Generar PDF con los gráficos actuales", type="primary"):
        if hm_path or wc_path or tl_path:
            with st.spinner("Generando documento PDF..."):
                try:
                    pdf_bytes = create_pdf_report(hm_path, wc_path, tl_path)
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
