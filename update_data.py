import os
import glob
import pandas as pd
import sys

# Ensure src modules can be imported
sys.path.insert(0, 'src')
from data_collection.parser import parse_file
from preprocessing.deduplicator import deduplicate_articles

def update():
    download_dir = "data/raw/temp"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    all_articles = []
    # Usaremos los archivos existentes sin borrarlos
    for file_path in glob.glob(os.path.join(download_dir, "*.csv")):
        print(f"Procesando {file_path}...")
        articles = parse_file(file_path, "EBSCO")
        all_articles.extend(articles)
        
    print(f"Total articulos leidos: {len(all_articles)}")
    
    unique_articles, _ = deduplicate_articles(all_articles, threshold=85)
    
    unified_path = os.path.join(processed_dir, "unified_articles.csv")
    df_unique = pd.DataFrame([a.to_dict() for a in unique_articles])
    df_unique.to_csv(unified_path, index=False, encoding='utf-8')
    print(f"Guardados {len(df_unique)} articulos en {unified_path}")

if __name__ == "__main__":
    update()
