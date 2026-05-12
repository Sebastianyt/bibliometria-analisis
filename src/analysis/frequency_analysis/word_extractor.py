"""
word_extractor.py
Genera un listado de hasta 15 palabras nuevas relevantes a una categoría
analizando el corpus de abstracts mediante TF-IDF con n-gramas.

Algoritmo:
1. Vectoriza todos los abstracts con TF-IDF (unigramas + bigramas)
2. Calcula el score promedio de cada término en el corpus
3. Filtra términos que ya están en la lista de palabras originales
4. Descarta términos demasiado cortos o numéricos
5. Retorna los top-15 por score TF-IDF
"""

import re
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


# Palabras muy genéricas del dominio académico que no aportan valor semántico
_GENERIC_STOPWORDS = {
    "paper", "study", "research", "article", "result", "results",
    "method", "methods", "approach", "approaches", "model", "models",
    "based", "using", "used", "use", "also", "however", "proposed",
    "show", "shows", "shown", "provide", "provided", "provides",
    "data", "work", "analysis", "different", "new", "two", "three",
    "one", "first", "second", "third", "may", "can", "ability",
    "findings", "finding", "potential", "review", "literature", "framework",
    "system", "systems", "context", "contexts", "level", "levels",
    "tool", "tools", "type", "types", "tasks", "task", "ways", "way",
    "important", "specific", "significant", "general", "possible"
}


def _normalize(text: str) -> str:
    """Limpia el texto de caracteres especiales antes de vectorizar."""
    return re.sub(r"[^a-zA-Z\s]", " ", text.lower())


def extract_new_keywords(
    abstracts: List[str],
    original_keywords: List[str],
    max_new: int = 15
) -> List[dict]:
    """
    Analiza el corpus de abstracts y genera nuevos términos relevantes.

    Args:
        abstracts:         Lista de textos (corpus)
        original_keywords: Palabras ya conocidas (para excluir duplicados)
        max_new:           Máximo de nuevas palabras a retornar (default 15)

    Returns:
        Lista de dicts: [{"term": "natural language", "tfidf_score": 0.342}, ...]
    """
    if not abstracts:
        return []

    # Normalizar textos del corpus
    corpus = [_normalize(a) for a in abstracts if a and a.strip()]
    if not corpus:
        return []

    # Crear un conjunto de términos originales normalizados para comparar
    original_set = {kw.lower().strip() for kw in original_keywords}
    # También incluir palabras individuales de cada frase original
    for kw in original_keywords:
        for word in kw.lower().split():
            original_set.add(word)

    # ── TF-IDF con unigramas y bigramas ──────────────────────────────────────
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),       # Captura "machine learning", "neural network", etc.
        max_features=300,         # Top 300 candidatos antes de filtrar
        stop_words="english",     # Elimina stopwords comunes en inglés
        min_df=2,                 # Debe aparecer en al menos 2 documentos
        max_df=0.95,              # Ignora términos que aparecen en >95% de docs
        sublinear_tf=True         # log(1+tf) para reducir el impacto de términos muy frecuentes
    )

    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()

    # Score promedio de cada término en todo el corpus
    mean_scores = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

    # Crear lista de (término, score) y ordenar
    term_scores = list(zip(feature_names, mean_scores))
    term_scores.sort(key=lambda x: x[1], reverse=True)

    # ── Filtrado ─────────────────────────────────────────────────────────────
    new_keywords = []
    seen = set()

    for term, score in term_scores:
        term_clean = term.strip()

        # Descartar si es demasiado corto (menos de 4 caracteres)
        if len(term_clean) < 4:
            continue

        # Descartar si es completamente numérico
        if term_clean.replace(" ", "").isdigit():
            continue

        # Descartar si ya existe en las palabras originales
        if term_clean in original_set:
            continue

        # Descartar si alguna de sus palabras es un stopword genérico del dominio
        words_in_term = set(term_clean.split())
        if words_in_term & _GENERIC_STOPWORDS:
            continue

        # Descartar duplicados ya añadidos
        if term_clean in seen:
            continue

        seen.add(term_clean)
        new_keywords.append({
            "term": term_clean,
            "tfidf_score": round(float(score), 5)
        })

        if len(new_keywords) >= max_new:
            break

    return new_keywords
