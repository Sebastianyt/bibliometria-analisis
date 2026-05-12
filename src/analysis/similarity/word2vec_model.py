import spacy
from spacy.cli import download as spacy_download
import numpy as np

# Cache global para no cargar ~40MB cada vez que se hace un cálculo
_nlp = None

def get_spacy_model():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_md")
        except OSError:
            # Fallback por si la máquina no lo tiene, lo bajamos la primera vez
            spacy_download("en_core_web_md")
            _nlp = spacy.load("en_core_web_md")
    return _nlp

def word2vec_similarity(text1: str, text2: str) -> float:
    """
    Similitud basada en vectores estables (Word2Vec con tensores promedio).
    Spacy calcula la similitud cosenoidal entre los promedios de los 
    vectores de cada token pre-entrenado.
    """
    if not text1.strip() or not text2.strip():
        return 0.0
    nlp = get_spacy_model()
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    # Comparación de vectores embebidos en el modelo inglés MD
    sim = doc1.similarity(doc2)
    return float(np.clip(sim, 0.0, 1.0))
