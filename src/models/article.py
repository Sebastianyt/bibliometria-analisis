from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Article:
    title: str
    authors: List[str]
    keywords: List[str]
    abstract: Optional[str]
    journal: Optional[str]
    year: Optional[int]
    doi: Optional[str]
    source: str  # e.g., 'ACM', 'SAGE', 'ScienceDirect'
    url: Optional[str]

    def to_dict(self):
        return {
            'title': self.title,
            'authors': '; '.join(self.authors),
            'keywords': '; '.join(self.keywords),
            'abstract': self.abstract,
            'journal': self.journal,
            'year': self.year,
            'doi': self.doi,
            'source': self.source,
            'url': self.url
        }