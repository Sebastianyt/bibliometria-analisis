import sys
sys.path.insert(0, 'src')
from src.data_collection.parser import parse_csv

articles = parse_csv("data/raw/temp/EBSCO-Metadata-04_30_2026 (1).csv", "test")
count = 0
for a in articles:
    if a.location:
        print(f"Found location: {a.location} in article: {a.title[:30]}")
        count += 1
print(f"Total locations found: {count}")
