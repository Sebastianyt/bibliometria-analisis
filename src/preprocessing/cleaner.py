"""
preprocessing/cleaner.py
------------------------
Funciones de preprocesamiento de texto reutilizables para todos los módulos
del proyecto de bibliometría.
"""

import re
import string
import nltk

# Descarga silenciosa de recursos NLTK necesarios
for _resource in ("stopwords", "wordnet", "omw-1.4", "punkt"):
    try:
        nltk.data.find(f"corpora/{_resource}" if _resource not in ("punkt",) else f"tokenizers/{_resource}")
    except LookupError:
        nltk.download(_resource, quiet=True)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

_STOPWORDS_EN = set(stopwords.words("english"))
_LEMMATIZER = WordNetLemmatizer()

# Palabras muy frecuentes en abstracts científicos que no aportan discriminación
_DOMAIN_STOPWORDS = {
    "study", "paper", "research", "result", "results", "propose", "proposed",
    "use", "used", "using", "show", "shown", "also", "two", "three", "one",
    "can", "may", "based", "method", "model", "approach", "data", "analysis",
    "system", "new", "different", "provide", "present", "work", "find", "found",
    "article", "examine", "review", "investigate", "explore", "discuss",
}


def clean_text(text: str) -> str:
    """
    Limpieza básica: minúsculas, elimina números y puntuación.
    Retorna el texto como cadena limpia (no tokenizado).
    """
    text = str(text).lower()
    text = re.sub(r"\d+", " ", text)                      # elimina números
    text = text.translate(str.maketrans("", "", string.punctuation))  # elimina puntuación
    text = re.sub(r"\s+", " ", text).strip()              # normaliza espacios
    return text


def tokenize(text: str) -> list[str]:
    """Divide el texto limpio en tokens por espacios."""
    return text.split()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Elimina stopwords en inglés + stopwords de dominio científico."""
    return [
        t for t in tokens
        if t not in _STOPWORDS_EN and t not in _DOMAIN_STOPWORDS and len(t) > 2
    ]


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    """Aplica lematización (WordNetLemmatizer) a cada token."""
    return [_LEMMATIZER.lemmatize(t) for t in tokens]


def preprocess(text: str) -> str:
    """
    Pipeline completo de preprocesamiento:
    1. Limpieza (minúsculas, sin números ni puntuación)
    2. Tokenización
    3. Eliminación de stopwords
    4. Lematización
    5. Retorna como string unificado para TF-IDF

    Parámetros
    ----------
    text : str
        Texto crudo (abstract científico).

    Retorna
    -------
    str
        Texto preprocesado listo para vectorización.
    """
    text = clean_text(text)
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_tokens(tokens)
    return " ".join(tokens)
