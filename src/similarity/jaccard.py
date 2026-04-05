def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calcula similitud basándose en la teoría de conjuntos (Intersección sobre Unión).
    """
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    if not union:
        return 0.0
        
    return len(intersection) / len(union)
