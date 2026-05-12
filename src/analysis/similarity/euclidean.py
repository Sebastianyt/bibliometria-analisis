from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import euclidean_distances

def tfidf_euclidean_similarity(text1: str, text2: str) -> float:
    """
    Similitud Euclidiana. Calcula la distancia física directa en el espacio
    multidimensional y la invierte para normalizar a [0, 1].
    """
    if not text1.strip() or not text2.strip():
        return 0.0
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        # Al extraer la distancia Euclidiana pura,
        # usamos la función de decaimiento 1 / (1 + d) para normalizar a 0 - 100%
        distance = euclidean_distances(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return 1.0 / (1.0 + float(distance))
    except Exception:
        return 0.0
