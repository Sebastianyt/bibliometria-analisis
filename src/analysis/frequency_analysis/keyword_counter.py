"""
keyword_counter.py
Calcula la frecuencia de aparición de una lista de palabras (o frases)
dentro de un corpus de abstracts. Soporta búsqueda multi-palabra (bigramas).
"""

import re
from typing import List, Dict


def count_keyword_frequencies(
    keywords: List[str],
    abstracts: List[str]
) -> List[Dict]:
    """
    Para cada keyword, cuenta en cuántos abstracts aparece (frecuencia de documento)
    y cuántas veces aparece en total en todo el corpus (frecuencia absoluta).

    Args:
        keywords:  Lista de palabras o frases a buscar (ej. ["Machine learning", "Ethics"])
        abstracts: Lista de textos (abstracts) donde buscar

    Returns:
        Lista de dicts ordenada de mayor a menor frecuencia:
        [{"keyword": "Machine learning", "doc_freq": 34, "abs_freq": 52, "pct": 68.0}, ...]
    """
    corpus_size = len(abstracts)
    results = []

    for kw in keywords:
        # Patrón regex: escapa la keyword y permite espacios variables (case-insensitive)
        pattern = re.compile(re.escape(kw.strip()), re.IGNORECASE)

        abs_freq = 0   # Total de ocurrencias en todo el corpus
        doc_freq = 0   # Cantidad de abstracts donde aparece al menos una vez

        for abstract in abstracts:
            matches = pattern.findall(abstract)
            if matches:
                doc_freq += 1
                abs_freq += len(matches)

        pct = round((doc_freq / corpus_size) * 100, 2) if corpus_size > 0 else 0.0

        results.append({
            "keyword": kw,
            "doc_freq": doc_freq,      # En cuántos artículos aparece
            "abs_freq": abs_freq,      # Total de veces en todo el corpus
            "pct": pct                 # % de artículos que la contienen
        })

    # Ordenar de mayor a menor frecuencia de documento
    results.sort(key=lambda x: x["doc_freq"], reverse=True)
    return results
