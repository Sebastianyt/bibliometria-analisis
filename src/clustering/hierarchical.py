"""
clustering/hierarchical.py
---------------------------
Motor de agrupamiento jerárquico para abstracts científicos.

Pipeline:
    Textos crudos
        → preprocess_texts()      (limpieza, stopwords, lematización)
        → compute_distance_matrix() (TF-IDF + distancia coseno)
        → apply_linkage()          (scipy.linkage con ward/complete/average)
        → cophenetic_score()       (coeficiente cofenético de coherencia)
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_distances
from sklearn.preprocessing import normalize
from scipy.cluster.hierarchy import linkage, cophenet
from scipy.spatial.distance import squareform

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from preprocessing.cleaner import preprocess


class HierarchicalClustering:
    """
    Clase que encapsula todo el pipeline de clustering jerárquico sobre abstracts.

    Attributes
    ----------
    labels : list[str]
        Etiquetas (títulos truncados) de cada documento.
    processed_texts : list[str]
        Textos ya preprocesados (listos para TF-IDF).
    distance_matrix : np.ndarray
        Matriz cuadrada de distancias coseno (n x n).
    linkage_results : dict
        Diccionario método → matriz Z de linkage de scipy.
    scores : dict
        Diccionario método → coeficiente cofenético (float 0–1).
    """

    def __init__(self):
        self.labels: list[str] = []
        self.processed_texts: list[str] = []
        self.distance_matrix: np.ndarray | None = None
        self.linkage_results: dict[str, np.ndarray] = {}
        self.scores: dict[str, float] = {}

    # ─── 1. Preprocesamiento ────────────────────────────────────────────────

    def preprocess_texts(self, abstracts: list[str], titles: list[str]) -> "HierarchicalClustering":
        """
        Aplica el pipeline completo de preprocesamiento a cada abstract.

        Parámetros
        ----------
        abstracts : list[str]
            Lista de textos crudos (abstracts de artículos).
        titles : list[str]
            Lista de títulos para usar como etiquetas en el dendrograma.

        Retorna
        -------
        self (fluent API)
        """
        self.processed_texts = [preprocess(a) for a in abstracts]
        # Etiquetas: primeras 45 caracteres del título
        self.labels = [str(t)[:45] + ("…" if len(str(t)) > 45 else "") for t in titles]
        return self

    # ─── 2. Vectorización y matriz de distancias ────────────────────────────

    def compute_distance_matrix(self) -> "HierarchicalClustering":
        """
        Vectoriza los textos con TF-IDF y calcula la matriz de distancias coseno.

        La distancia coseno D se define como:
            D(u, v) = 1 - cos(θ) = 1 - (u · v) / (|u| |v|)

        Retorna
        -------
        self (fluent API)

        Raises
        ------
        ValueError
            Si no se han preprocesado textos previamente.
        """
        if not self.processed_texts:
            raise ValueError("Llama primero a preprocess_texts().")

        vectorizer = TfidfVectorizer(
            max_features=3000,
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,        # log(1+tf) para suavizar frecuencias altas
            ngram_range=(1, 2),       # unigramas + bigramas
        )
        tfidf_matrix = vectorizer.fit_transform(self.processed_texts)

        # Normalizamos L2 para que la distancia coseno sea exactamente 1 - sim_coseno
        tfidf_normalized = normalize(tfidf_matrix, norm="l2")
        self.distance_matrix = cosine_distances(tfidf_normalized)

        # Aseguramos simetría perfecta y diagonal en cero (errores de punto flotante)
        self.distance_matrix = (self.distance_matrix + self.distance_matrix.T) / 2
        np.fill_diagonal(self.distance_matrix, 0.0)

        return self

    # ─── 3. Linkage jerárquico ──────────────────────────────────────────────

    def apply_linkage(self, method: str) -> np.ndarray:
        """
        Aplica el algoritmo de agrupamiento jerárquico con el método dado.

        Parámetros
        ----------
        method : str
            Método de enlace: 'ward', 'complete' o 'average'.
            - 'ward'     : minimiza varianza intra-cluster (usa distancia euclidiana)
            - 'complete' : distancia máxima entre pares de clusters
            - 'average'  : distancia promedio entre todos los pares (UPGMA)

        Retorna
        -------
        Z : np.ndarray  (shape: [n-1, 4])
            Matriz de linkage de scipy:
            Z[i] = [cluster_1, cluster_2, distancia, num_elementos]

        Raises
        ------
        ValueError
            Si la matriz de distancias no ha sido calculada.
        """
        if self.distance_matrix is None:
            raise ValueError("Llama primero a compute_distance_matrix().")

        condensed = squareform(self.distance_matrix, checks=False)

        if method == "ward":
            # Ward requiere distancias euclidianas; usamos la matriz TF-IDF normalizada
            # directamente en forma condensada con method='ward'
            Z = linkage(condensed, method="ward")
        else:
            Z = linkage(condensed, method=method)

        self.linkage_results[method] = Z
        return Z

    # ─── 4. Métrica de coherencia: Coeficiente Cofenético ──────────────────

    def cophenetic_score(self, method: str) -> float:
        """
        Calcula el Coeficiente de Correlación Cofenética (CCC) para el método dado.

        El CCC mide qué tan fielmente el dendrograma preserva las distancias
        originales entre pares de puntos. Se calcula como la correlación de Pearson
        entre:
          - Las distancias originales (matriz de distancias condensada)
          - Las distancias cofenéticas (la altura en el dendrograma a la que
            dos puntos se unen por primera vez)

        Rango: [0, 1]  →  más cercano a 1 = dendrograma más coherente.

        Parámetros
        ----------
        method : str
            Método de enlace ya calculado con apply_linkage().

        Retorna
        -------
        float
            CCC entre 0 y 1.
        """
        if method not in self.linkage_results:
            self.apply_linkage(method)

        Z = self.linkage_results[method]
        condensed = squareform(self.distance_matrix, checks=False)
        c, _ = cophenet(Z, condensed)
        self.scores[method] = float(c)
        return float(c)

    # ─── 5. Pipeline completo para todos los métodos ────────────────────────

    def run_all(self, abstracts: list[str], titles: list[str]) -> "HierarchicalClustering":
        """
        Ejecuta el pipeline completo: preprocesamiento → distancias → linkage x3 → scores.

        Parámetros
        ----------
        abstracts : list[str]
        titles : list[str]

        Retorna
        -------
        self (fluent API)
        """
        self.preprocess_texts(abstracts, titles)
        self.compute_distance_matrix()
        for method in ("ward", "complete", "average"):
            self.apply_linkage(method)
            self.cophenetic_score(method)
        return self

    def best_method(self) -> str:
        """Retorna el método con mayor CCC (más coherente)."""
        if not self.scores:
            raise ValueError("Ejecuta run_all() o cophenetic_score() primero.")
        return max(self.scores, key=lambda m: self.scores[m])
