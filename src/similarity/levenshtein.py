import Levenshtein

def levenshtein_similarity(text1: str, text2: str) -> float:
    """
    Similitud basada en la distancia de edición matemática de un caracter a otro.
    Calcula cuántos pasos toma convertir string A en string B.
    """
    if not text1 and not text2:
        return 1.0
    return Levenshtein.ratio(text1.lower(), text2.lower())
