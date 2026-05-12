"""
precision_evaluator.py
Evalúa la precisión semántica de palabras nuevas respecto a una categoría,
usando embeddings de BERT (sentence-transformers) y similitud coseno.

Lógica:
- La "categoría" es la frase: "Concepts of Generative AI in Education"
- Cada nueva palabra se compara semánticamente contra esa frase
- El score de similitud coseno se interpreta como precisión (0% a 100%)
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict


# Cacheamos el modelo globalmente (reutiliza la misma instancia de bert_model.py)
_model = None

def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _classify_precision(score: float) -> tuple[str, str]:
    """
    Clasifica el score de precisión en tres niveles con emoji y color CSS.
    Returns: (label, css_color)
    """
    if score >= 0.70:
        return ("🟢 Alta", "#2ecc71")
    elif score >= 0.40:
        return ("🟡 Media", "#f39c12")
    else:
        return ("🔴 Baja", "#e74c3c")


def evaluate_precision(
    new_terms: List[str],
    category: str = "Concepts of Generative AI in Education"
) -> List[Dict]:
    """
    Evalúa la precisión semántica de cada término nuevo respecto a la categoría.

    Args:
        new_terms: Lista de términos nuevos generados por TF-IDF
        category:  Frase que describe la categoría objetivo

    Returns:
        Lista de dicts ordenada por precisión descendente:
        [
          {
            "term": "natural language processing",
            "precision": 0.823,
            "pct": 82.3,
            "label": "🟢 Alta",
            "color": "#2ecc71"
          }, ...
        ]
    """
    if not new_terms:
        return []

    model = _get_model()

    # Generar embedding de la categoría (1 vez)
    category_embedding = model.encode([category])[0]

    # Generar embeddings de todos los términos en batch (más eficiente)
    term_embeddings = model.encode(new_terms)

    results = []
    for i, term in enumerate(new_terms):
        sim = cosine_similarity(
            [term_embeddings[i]],
            [category_embedding]
        )[0][0]
        sim = float(np.clip(sim, 0.0, 1.0))
        label, color = _classify_precision(sim)

        results.append({
            "term": term,
            "precision": round(sim, 4),
            "pct": round(sim * 100, 2),
            "label": label,
            "color": color
        })

    # Ordenar por precisión descendente
    results.sort(key=lambda x: x["precision"], reverse=True)
    return results


def average_precision(evaluations: List[Dict]) -> float:
    """
    Calcula la precisión promedio del conjunto de palabras generadas.
    Returns: float entre 0.0 y 1.0
    """
    if not evaluations:
        return 0.0
    return round(sum(e["precision"] for e in evaluations) / len(evaluations), 4)
