import os
import sys
sys.path.insert(0, 'src')

from data_collection.downloader import download_all_data
from data_collection.parser import parse_file
from preprocessing.deduplicator import deduplicate_articles
import pandas as pd

def main():
    query = "generative artificial intelligence"
    download_dir = "data/raw/temp"
    processed_dir = "data/processed"
    duplicates_dir = "data/duplicates"
    
    # Create directories
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(duplicates_dir, exist_ok=True)

    # Download data
    print("\n=== Starting Download ===")
    downloaded_files = download_all_data(query, download_dir)
    
    if not downloaded_files:
        print("No files downloaded. Exiting.")
        return
    
    print(f"\nDownloaded {len(downloaded_files)} file(s)")
    for source, file_path in downloaded_files:
        print(f"  - {source}: {file_path}")

    # Parse all files
    print("\n=== Starting Parsing ===")
    all_articles = []
    for source, file_path in downloaded_files:
        print(f"Parsing {source} from {file_path}...")
        articles = parse_file(file_path, source)
        print(f"  Found {len(articles)} articles from {source}")
        all_articles.extend(articles)
    
    print(f"Total articles parsed: {len(all_articles)}")

    # Deduplicate
    print("\n=== Starting Deduplication ===")
    unique_articles, duplicates = deduplicate_articles(all_articles, threshold=85)

    # Save unified file
    print("\n=== Saving Results ===")
    unified_path = os.path.join(processed_dir, "unified_articles.csv")
    df_unique = pd.DataFrame([a.to_dict() for a in unique_articles])
    df_unique.to_csv(unified_path, index=False, encoding='utf-8')
    print(f"Unified articles saved to: {unified_path}")
    print(f"  Total: {len(df_unique)} unique articles")

    # Save duplicates
    duplicates_path = os.path.join(duplicates_dir, "removed_duplicates.csv")
    if duplicates:
        df_duplicates = pd.DataFrame([a.to_dict() for a in duplicates])
        df_duplicates.to_csv(duplicates_path, index=False, encoding='utf-8')
        print(f"Removed duplicates saved to: {duplicates_path}")
        print(f"  Total: {len(df_duplicates)} removed duplicates")
    else:
        print("No duplicates found.")
    
    print("\n=== Process Complete ===")
    print(f"Summary:")
    print(f"  Original articles: {len(all_articles)}")
    print(f"  Unique articles: {len(unique_articles)}")
    print(f"  Duplicates removed: {len(duplicates)}")

if __name__ == "__main__":
    main()