import streamlit as st
import pandas as pd
import os

from analysis.similarity.levenshtein import levenshtein_similarity
from analysis.similarity.jaccard import jaccard_similarity
from analysis.similarity.cosine import tfidf_cosine_similarity
from analysis.similarity.euclidean import tfidf_euclidean_similarity
from analysis.similarity.bert_model import bert_similarity
from analysis.similarity.word2vec_model import word2vec_similarity

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_dir, "data", "processed", "unified_articles.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

def render():
    st.subheader("🤖 Análisis de Similitud Textual entre Artículos")
    st.markdown(
        "Selecciona dos artículos para comparar sus **abstracts** con 4 algoritmos "
        "clásicos y 2 modelos de Inteligencia Artificial."
    )

    df = load_data()

    if df.empty:
        st.error(
            "No se encontró el archivo de datos. "
            "Ejecuta primero `python src/main.py` para generar unified_articles.csv."
        )
    else:
        df_valid = df.copy()
        if "abstract" in df_valid.columns:
            df_valid = df_valid.dropna(subset=["abstract", "title"])
            df_valid = df_valid[df_valid["abstract"].astype(str).str.strip() != ""]
        else:
            st.error("El archivo unificado no posee la columna abstract.")
            st.stop()

        titles = df_valid["title"].tolist()

        st.markdown("### Seleccione los Artículos Científicos a Comparar")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📄 Artículo A**")
            article_a_title = st.selectbox("Selecciona primer título:", options=titles, key="a")

        with col2:
            st.markdown("**📄 Artículo B**")
            article_b_title = st.selectbox("Selecciona segundo título:", options=titles, key="b")

        if article_a_title and article_b_title:
            abstract_a = df_valid[df_valid["title"] == article_a_title]["abstract"].values[0]
            abstract_b = df_valid[df_valid["title"] == article_b_title]["abstract"].values[0]

            with st.expander("👁️ Ver ambos Abstracts para comparación manual"):
                col_ab1, col_ab2 = st.columns(2)
                with col_ab1:
                    st.info(abstract_a)
                with col_ab2:
                    st.info(abstract_b)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Ejecutar Algoritmos de Similitud", type="primary", use_container_width=True):
                st.divider()
                st.subheader("📊 Resultados (0% = Divergente · 100% = Idéntico)")

                with st.spinner("Cargando modelos y calculando similitudes..."):
                    sim_lev  = levenshtein_similarity(abstract_a, abstract_b)
                    sim_jac  = jaccard_similarity(abstract_a, abstract_b)
                    sim_cos  = tfidf_cosine_similarity(abstract_a, abstract_b)
                    sim_euc  = tfidf_euclidean_similarity(abstract_a, abstract_b)
                    sim_bert = bert_similarity(abstract_a, abstract_b)
                    sim_w2v  = word2vec_similarity(abstract_a, abstract_b)

                    res_col1, res_col2 = st.columns(2)

                    with res_col1:
                        st.success("📐 Algoritmos Matemáticos Clásicos")
                        st.metric("1. Distancia Levenshtein",      f"{sim_lev  * 100:.2f}%", help="Ediciones carácter a carácter para transformar un texto en otro.")
                        st.metric("2. Similitud Jaccard",          f"{sim_jac  * 100:.2f}%", help="Intersección / Unión del vocabulario de ambos abstracts.")
                        st.metric("3. Similitud Coseno (TF-IDF)",  f"{sim_cos  * 100:.2f}%", help="Ángulo entre vectores TF-IDF de los dos textos.")
                        st.metric("4. Distancia Euclidiana (TF-IDF)", f"{sim_euc * 100:.2f}%", help="Distancia geométrica en espacio vectorial TF-IDF, normalizada inversamente.")

                    with res_col2:
                        st.info("🧠 Modelos de Inteligencia Artificial")
                        st.metric("5. Deep Transformer (BERT MiniLM)", f"{sim_bert * 100:.2f}%", help="Embeddings contextuales de 384 dims. Detecta similitud semántica profunda.")
                        st.metric("6. Word2Vec (SpaCy / GloVe)",       f"{sim_w2v  * 100:.2f}%", help="Promedio de vectores estáticos de 300 dims por token.")

                    st.markdown("---")
                    st.markdown("### 📖 Guía de Interpretación")

                    with st.expander("Haz clic para entender cómo leer estos porcentajes", expanded=True):
                        st.markdown("""
#### 1️⃣ Algoritmos Clásicos
* **Levenshtein**: ~100% = textos casi idénticos letra a letra. Bajo 40% = vocabulario muy distinto aunque traten el mismo tema.
* **Jaccard**: 100% = mismo vocabulario exacto. Valores de 10–30% son normales en abstracts largos de diferentes autores.
* **Coseno TF-IDF**: Sobre 40–50% indica vocabulario científico compartido (*Generative, Transformers, Machine*).
* **Euclidiana TF-IDF**: valores bajos = textos alejados en el espacio estadístico, tocando subtemas distintos.

#### 2️⃣ Modelos de IA
* **Word2Vec**: Suele ser alto (80–95%) porque todos los papers de IA comparten el mismo universo semántico.
* **BERT**: El más confiable. Si supera 75–80%, los artículos son redundantes para un lector humano.
                        """)
