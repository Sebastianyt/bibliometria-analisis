from typing import List, Tuple
from fuzzywuzzy import fuzz
from models.article import Article

def deduplicate_articles(articles: List[Article], threshold: int = 85) -> Tuple[List[Article], List[Article]]:
    """
    Remove duplicates based on title similarity.
    Returns (unique_articles, duplicates)
    
    Args:
        articles: List of articles to deduplicate
        threshold: Similarity threshold (0-100). Default 85% match = duplicate
    """
    print(f"Starting deduplication with {len(articles)} articles, threshold: {threshold}%")
    
    unique = []
    duplicates = []
    
    for i, article in enumerate(articles):
        is_duplicate = False
        
        # Compare with each unique article found so far
        for unique_article in unique:
            # Compare titles
            title_similarity = fuzz.ratio(
                article.title.lower().strip(),
                unique_article.title.lower().strip()
            )
            
            # If titles are very similar, it's likely a duplicate
            if title_similarity >= threshold:
                is_duplicate = True
                print(f"Duplicate found: '{article.title[:50]}...' (similarity: {title_similarity}%)")
                break
        
        if is_duplicate:
            duplicates.append(article)
        else:
            unique.append(article)
    
    print(f"Deduplication complete: {len(unique)} unique, {len(duplicates)} duplicates")
    return unique, duplicates