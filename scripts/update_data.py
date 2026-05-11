"""
update_data.py
--------------
Script de mantenimiento del pipeline de datos.

Uso (desde la raíz del proyecto):
    python scripts/update_data.py

Descripción:
    Lee todos los archivos .csv de data/raw/temp/, los parsea con el
    parser de EBSCO, deduplica los artículos y guarda el resultado
    limpio en data/processed/unified_articles.csv.
"""

import sys
import glob
import pandas as pd
from pathlib import Path

# ── Rutas absolutas relativas a este script ────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent   # raíz del proyecto
SRC_DIR  = ROOT_DIR / "src"
RAW_DIR  = ROOT_DIR / "data" / "raw" / "temp"
OUT_DIR  = ROOT_DIR / "data" / "processed"

sys.path.insert(0, str(SRC_DIR))

from data_collection.parser import parse_file
from preprocessing.deduplicator import deduplicate_articles


def update() -> None:
    """Ejecuta el pipeline completo: parseo → deduplicación → exportación CSV."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = list(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print(f"[WARN] No se encontraron archivos CSV en: {RAW_DIR}")
        return

    all_articles = []
    for file_path in csv_files:
        print(f"[INFO] Procesando {file_path.name}...")
        articles = parse_file(str(file_path), "EBSCO")
        all_articles.extend(articles)

    print(f"[INFO] Total artículos leídos : {len(all_articles)}")

    unique_articles, _ = deduplicate_articles(all_articles, threshold=85)
    print(f"[INFO] Artículos tras deduplicar: {len(unique_articles)}")

    unified_path = OUT_DIR / "unified_articles.csv"
    df_unique = pd.DataFrame([a.to_dict() for a in unique_articles])
    df_unique.to_csv(unified_path, index=False, encoding="utf-8")
    print(f"[OK]   Dataset guardado en: {unified_path}")


if __name__ == "__main__":
    update()
