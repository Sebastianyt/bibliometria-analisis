import pandas as pd
df = pd.read_csv("data/processed/unified_articles.csv")
print("Columns:", df.columns.tolist())
print(df['publisherLocations'].value_counts())
