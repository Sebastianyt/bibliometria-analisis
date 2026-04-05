import streamlit as st
import pandas as pd
import os
import sys

# Permitir ruta a módulos locales
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from similarity.levenshtein import levenshtein_similarity
from similarity.jaccard import jaccard_similarity
from similarity.cosine import tfidf_cosine_similarity
from similarity.euclidean import tfidf_euclidean_similarity
from similarity.bert_model import bert_similarity
from similarity.word2vec_model import word2vec_similarity

st.set_page_config(page_title="Bibliometría - Similitud", layout="wide", page_icon="📊")

st.title("🤖 Requerimiento 2: Análisis de Similitud Textual")
st.markdown("Plataforma interactiva para evaluar correlaciones entre resúmenes (abstracts) mediante 4 algoritmos clásicos y 2 modelos de Inteligencia Artificial profunda.")

@st.cache_data
def load_data():
    # Sube uno a la raíz del proyecto si es que se ejecuta localmente
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "processed", "unified_articles.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("No se encontró el archivo origen de datos. Ejecuta primero `python src/main.py` para generar unified_articles.csv")
else:
    # Filtrar aquellos que no tengan abstract para que no falle al evaluarlos
    df_valid = df.copy()
    if 'abstract' in df_valid.columns:
        df_valid = df_valid.dropna(subset=['abstract', 'title'])
        df_valid = df_valid[df_valid['abstract'].astype(str).str.strip() != '']
    else:
        st.error("El archivo unificado no posee la columna abstract.")
        st.stop()
        
    titles = df_valid['title'].tolist()
    
    st.markdown("### Seleccione los Artículos Científicos a Comparar")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📄 Artículo A**")
        article_a_title = st.selectbox("Selecciona primer título de la librería:", options=titles, key="a")
        
    with col2:
        st.markdown("**📄 Artículo B**")
        article_b_title = st.selectbox("Selecciona segundo título de la librería:", options=titles, key="b")
        
    if article_a_title and article_b_title:
        abstract_a = df_valid[df_valid['title'] == article_a_title]['abstract'].values[0]
        abstract_b = df_valid[df_valid['title'] == article_b_title]['abstract'].values[0]
        
        with st.expander("👁️ Clic aquí para desplegar ambos Abstractos y compararlos leyendo manualmente"):
            col_ab1, col_ab2 = st.columns(2)
            with col_ab1:
                st.info(abstract_a)
            with col_ab2:
                st.info(abstract_b)
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Ejecutar Algoritmos de Similitud", type="primary", use_container_width=True):
            st.divider()
            st.subheader("📊 Resultados Analíticos (Del 0% Divergente al 100% Idéntico)")
            
            with st.spinner('Cargando modelos... calculando matrices y distancias lógicas...'): # Spin animado
                sim_lev = levenshtein_similarity(abstract_a, abstract_b)
                sim_jac = jaccard_similarity(abstract_a, abstract_b)
                sim_cos = tfidf_cosine_similarity(abstract_a, abstract_b)
                sim_euc = tfidf_euclidean_similarity(abstract_a, abstract_b)
                sim_bert = bert_similarity(abstract_a, abstract_b)
                sim_w2v = word2vec_similarity(abstract_a, abstract_b)
                
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.success("📐 Algoritmos Matemáticos Clásicos")
                    st.metric("1. Distancia Levenshtein", f"{sim_lev * 100:.2f}%", help="Calcula cuántos pasos toma mutar un abstract en otro a nivel de carácter.")
                    st.metric("2. Similitud Jaccard", f"{sim_jac * 100:.2f}%", help="Teoría de conjuntos: Mide el tamaño de la intersección entre los tokens del vocabulario.")
                    st.metric("3. Similitud Coseno con TF-IDF", f"{sim_cos * 100:.2f}%", help="Evalúa el ángulo entre vectores de ponderación de frecuencia de términos y documento inverso.")
                    st.metric("4. Distancia Euclidiana (TF-IDF)", f"{sim_euc * 100:.2f}%", help="Mide la línea recta entre arreglos de matrices proyectadas y se normaliza inversamente del 1 al 0.")

                with res_col2:
                    st.info("🧠 Modelos Contextuales de Inteligencia Artificial")
                    st.metric("5. Deep Transformer (BERT MiniLM)", f"{sim_bert * 100:.2f}%", help="Aglutina el significado global profundo. Incluso si usan sinónimos distintos, BERT los entiende igualitarios.")
                    st.metric("6. Core Word2Vec (Spacy GloVe)", f"{sim_w2v * 100:.2f}%", help="Utiliza una tabla estática preentrenada en un inmenso corpus de texto para acercar tensores promediados.")

                st.markdown("---")
                st.markdown("### 📖 Guía de Interpretación de Resultados")
                
                with st.expander("Haz clic aquí para entender cómo leer estos porcentajes y sus límites", expanded=True):
                    st.markdown("""
                    Los algoritmos evalúan los resúmenes desde dos perspectivas completamente distintas: una puramente **ortográfica/estadística** (los clásicos) y una **cognitiva/semántica** (Inteligencia artificial).
                    
                    #### 1️⃣ Algoritmos Clásicos (Límites rígidos de vocabulario)
                    * **Distancia Levenshtein**: Si arroja cerca al **100%**, los textos son clones exactos letra por letra. Si cae por debajo del **40%**, significa que mecanográficamente usan teclados o construcciones muy distintas, ¡incluso aunque hablen de la misma teoría!
                    * **Similitud Jaccard**: Un **100%** indica que ambos autores emplearon exacto el mismo vocabulario de palabras. Un **0%** significa que no repitieron ni una palabra. Es normal que dé valores bajos (**10% - 30%**) en *abstracts* largos, puesto que los científicos tienen estilos de escritura únicos.
                    * **Coseno TF-IDF**: Valores por encima del **40%-50%** ya son considerables, demostrando que ambos artículos comparten la misma densidad de "palabras científicas clave" (ej. *Generative, Transformers, Machine*).
                    * **Distancia Euclidiana**: Mide la longitud de desconexión recta en el espacio matemático. Si ronda un número bajo (como el **30%**), los textos están físicamente marginados en el hiperespacio, tocando subtemas distintos.
                    
                    #### 2️⃣ Modelos de IA (Límites abstractos y neuronales)
                    * **Word2Vec (Tensores fijos)**: Suele arrojar valores sumamente altos (incluso del **80% a 95%**). Esto ocurre porque el modelo sabe que todas las palabras científicas pertenecen al mismo universo de la "Tecnología de la información". Si un artículo diera **10%**, implicaría que el otro artículo está hablando de "Biología marina" o "recetas de cocina".
                    * **Deep Transformer (Atención BERT)**: Es el modelo definitivo y emula el razonamiento humano. Si te arroja un valor por encima del **75% a 80%**, significa que para un humano **sería redundante tener que leer ambos artículos**, ya que concluyen o debaten exactamente los mismos conceptos, independientemente de qué sinónimos rebuscados hayan digitado sus autores.
                    """)
