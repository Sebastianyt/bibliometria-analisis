import pandas as pd
import bibtexparser
import rispy
from typing import List
from models.article import Article

def parse_csv(file_path: str, source: str) -> List[Article]:
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return []
    
    articles = []
    # Handle different column names from EBSCO CSV
    for _, row in df.iterrows():
        # Get column names (case-insensitive matching)
        title = ''
        authors = []
        keywords = []
        abstract = ''
        journal = ''
        ebsco_source_value = ''  # Campo 'source' de EBSCO = nombre de revista
        year = None
        doi = ''
        url = ''
        location = ''
        
        document_type = ''
        
        # Try different column names
        for col in df.columns:
            col_lower = col.lower()
            if 'title' in col_lower and 'publication' not in col_lower and 'journal' not in col_lower:
                title = row[col] if pd.notna(row[col]) else ''
            elif 'author' in col_lower or 'contributors' in col_lower:
                authors = str(row[col]).split(';') if pd.notna(row[col]) else []
                authors = [a.strip() for a in authors]
            elif 'keyword' in col_lower or 'subjects' in col_lower:
                keywords = str(row[col]).split(';') if pd.notna(row[col]) else []
                keywords = [k.strip() for k in keywords]
            elif 'abstract' in col_lower or 'summary' in col_lower:
                abstract = row[col] if pd.notna(row[col]) else ''
            elif 'journal' in col_lower or 'publication title' in col_lower:
                journal = row[col] if pd.notna(row[col]) else ''
            elif col_lower == 'source':
                # EBSCO usa 'source' como nombre de la revista/publicacion.
                # Se guarda como candidato; se usara si no hay columna 'journal'.
                ebsco_source_value = str(row[col]).strip() if pd.notna(row[col]) else ''
            elif 'year' in col_lower or 'publicationdate' in col_lower or 'date' in col_lower:
                if year is None:  # En caso de múltiples columnas de fecha, priorizamos la primera que hallemos
                    try:
                        val_str = str(row[col]).replace(".0", "").strip()
                        if len(val_str) >= 4 and val_str[:4].isdigit():
                            year = int(val_str[:4])
                        else:
                            year = int(float(row[col]))
                    except:
                        pass
            elif 'doi' == col_lower:
                doi = row[col] if pd.notna(row[col]) else ''
            elif 'url' in col_lower or 'link' in col_lower:
                url = row[col] if pd.notna(row[col]) else ''
            elif col_lower in ['type', 'document type', 'item type', 'doctypes']:
                document_type = row[col] if pd.notna(row[col]) else ''
            elif 'publisherlocations' in col_lower or 'location' in col_lower:
                location = row[col] if pd.notna(row[col]) else ''

        # Si no se encontro columna 'journal', usar el campo 'source' de EBSCO
        if not journal and ebsco_source_value:
            journal = ebsco_source_value

        if title:  # Only add if title exists
            article = Article(
                title=str(title).strip(),
                authors=authors,
                keywords=keywords,
                abstract=str(abstract).strip(),
                journal=str(journal).strip(),
                year=year,
                doi=str(doi).strip(),
                source=source,
                url=str(url).strip(),
                document_type=str(document_type).strip() if document_type else "Article",
                location=str(location).strip() if location else ""
            )
            articles.append(article)
    
    return articles

def parse_bibtex(file_path: str, source: str) -> List[Article]:
    with open(file_path, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f)
    articles = []
    for entry in bib_database.entries:
        article = Article(
            title=entry.get('title', ''),
            authors=entry.get('author', '').split(' and ') if entry.get('author') else [],
            keywords=entry.get('keywords', '').split(', ') if entry.get('keywords') else [],
            abstract=entry.get('abstract', ''),
            journal=entry.get('journal', ''),
            year=int(entry.get('year')) if entry.get('year') and entry.get('year').isdigit() else None,
            doi=entry.get('doi', ''),
            source=source,
            url=entry.get('url', ''),
            document_type=entry.get('ENTRYTYPE', 'Article').capitalize()
        )
        articles.append(article)
    return articles

def parse_ris(file_path: str, source: str) -> List[Article]:
    with open(file_path, 'r', encoding='utf-8') as f:
        entries = rispy.load(f)
    articles = []
    for entry in entries:
        article = Article(
            title=entry.get('title', [''])[0] if entry.get('title') else '',
            authors=entry.get('authors', []),
            keywords=entry.get('keywords', []),
            abstract=entry.get('abstract', ''),
            journal=entry.get('journal', ''),
            year=int(entry.get('year')) if entry.get('year') and str(entry.get('year')).isdigit() else None,
            doi=entry.get('doi', ''),
            source=entry.get('db', source),  # Use DB field if available
            url=entry.get('url', ''),
            document_type=entry.get('type_of_reference', 'Article')
        )
        articles.append(article)
    return articles

def parse_file(file_path: str, source: str) -> List[Article]:
    if file_path.endswith('.csv'):
        return parse_csv(file_path, source)
    elif file_path.endswith('.bib'):
        return parse_bibtex(file_path, source)
    elif file_path.endswith('.ris'):
        return parse_ris(file_path, source)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")