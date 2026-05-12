from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Cacheamos el modelo pesado en memoria para no cargarlo en cada clic
_model = None

def get_bert_model():
    global _model
    if _model is None:
        # MiniLM es super ligero y veloz para comparar semántica en abstracts
        _model = SentenceTransformer('all-MiniLM-L6-v2') 
    return _model

def bert_similarity(text1: str, text2: str) -> float:
    """
    Crea embeddings densos (vectores matemáticos de significado neuronal)
    para ambos textos y luego halla el margen de similitud del coseno.
    """
    if not text1.strip() or not text2.strip():
        return 0.0
    model = get_bert_model()
    # Genera incrustaciones
    embeddings = model.encode([text1, text2])
    # Distancia cosenoidal de 1x2
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    # Asegura que matemáticamente no pase de 1.0 (100%) o baje de 0
    return float(np.clip(sim, 0.0, 1.0))
