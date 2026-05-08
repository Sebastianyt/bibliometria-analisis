import streamlit as st
import pandas as pd
import os
import sys

# Permitir ruta a módulos locales
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Bibliometría — Análisis de IA Generativa",
    layout="wide",
    page_icon="🔬"
)

# ─── Estilos globales ────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0d0d1a; }
[data-testid="stSidebar"]          { background: #111126; }
.stTabs [data-baseweb="tab-list"]  { gap: 12px; }
.stTabs [data-baseweb="tab"] {
    background: #1a1a35;
    border-radius: 8px 8px 0 0;
    padding: 8px 20px;
    color: #a0a0cc;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: #6C63FF !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔬 Bibliometría · IA Generativa en Educación")
st.markdown("Sistema de análisis bibliométrico automatizado · *Streamlit Dashboard*")
st.divider()

tab2, tab3, tab4, tab5 = st.tabs([
    "📐 Req 2 · Similitud Textual",
    "📊 Req 3 · Frecuencia y Generación de Palabras",
    "🌳 Req 4 · Agrupamiento Jerárquico",
    "📈 Req 5 · Análisis Visual",
])

# ════════════════════════════════════════════════════════════════════════════
# REQUERIMIENTO 2 — Similitud Textual
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    from modules.req2_similarity import render as render_req2
    render_req2()

# ════════════════════════════════════════════════════════════════════════════
# REQUERIMIENTO 3 — Frecuencia y Generación de Palabras
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    from modules.req3_frequency import render as render_req3
    render_req3()

# ════════════════════════════════════════════════════════════════════════════
# REQUERIMIENTO 4 — Agrupamiento Jerárquico y Dendrogramas
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    from modules.req4_clustering import render as render_req4
    render_req4()

# ════════════════════════════════════════════════════════════════════════════
# REQUERIMIENTO 5 — Análisis Visual y Reporte PDF
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    from modules.req5_visual import render as render_req5
    render_req5()
