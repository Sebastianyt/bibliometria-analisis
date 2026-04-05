# Análisis Matemático y Teórico de los Algoritmos de Similitud Textual

Este documento soporta la justificación del Requerimiento 2 del análisis bibliométrico, documentando matemáticamente cada algoritmo utilizado en la aplicación.

## 1. Algoritmos Matemáticos y Estadísticos Clásicos

### 1.1. Distancia de Levenshtein (Distancia de Edición)
La **distancia de Levenshtein** es una métrica de cadena que mide la cantidad mínima de operaciones (inserciones, eliminaciones o sustituciones) necesarias para transformar una cadena de texto $a$ en otra cadena $b$.

Matemáticamente, se define de manera recursiva utilizando una función indicadora $1_{(a_i \neq b_j)}$:
$$lev_a,b(i, j) = \max(i, j) \quad \text{si } \min(i, j) = 0$$
$$lev_a,b(i, j) = \min \begin{cases} lev_a,b(i-1, j) + 1  \\ lev_a,b(i, j-1) + 1 \\ lev_a,b(i-1, j-1) + 1_{(a_i \neq b_j)} \end{cases} \quad \text{si } \min(i, j) > 0$$

**Funcionamiento paso a paso:**
1. Inicializar una matriz de dimensiones $(|A|+1) \times (|B|+1)$.
2. Comparar los resúmenes iterando los ciclos sobre filas y columnas calculando el costo de mutar un carácter.
3. Se normaliza el número resultante restándolo a la longitud máxima y dividiéndolo para convertir la distancia de matriz bidimensional en un porcentaje comparable (0% a 100%).

---

### 1.2. Similitud de Sets (Índice de Jaccard)
El **Índice de Jaccard** modela los resúmenes de texto (abstracts) de acuerdo a la Teoría de Conjuntos de Cantor, tomando a los documentos como una acumulación global de palabras sin importar el orden verbal gramatical exacto.

La fórmula de intersección sobre la unión es:
$$J(A,B) = \frac{|A \cap B|}{|A \cup B|} = \frac{|A \cap B|}{|A| + |B| - |A \cap B|}$$

**Funcionamiento algorítmico:**
1. Tokenización natural (dividir en palabras) del artículo investigador $A$ y el $B$.
2. Eliminar las palabras repetidas recursivamente dentro de su propio texto para transformarlas a la estructura rígida de *Sets* lógicos en Python.
3. Extraer cardinalidad verificando la cantidad de palabras que existen en común en ambas listas ($A \cap B$).
4. Dividir dicha cifra entre el total del vocabulario combinado en ambas listas menos las coincidencias.

---

### 1.3. Cálculo por Vectorización Espacial (Similitud del Coseno TF-IDF)
Esta táctica convierte todo el contenido lingüístico caótico a matrices netamente matemáticas mediante un balanceo de pesos en minería de texto: **Frecuencia de Término – Frecuencia Inversa de Documento (TF-IDF)**.

Se examina la medida del ángulo físico entre el Vector A y el Vector B proyectados en un hiperespacio topológico de miles de dimensiones:
$$\text{Cosine Similarity} = \cos(\theta) = \frac{A \cdot B}{||A|| ||B||} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

**Paso a paso algorítmico:**
1. Ejecutar el pipeline algorítmico para tabular si ciertas palabras son raras en un corpus y exclusivas en el abstract de turno. Y luego otorgarles fuerte peso estadístico (Ej. "GenAI" pesa 10, "the" pesa 0.01).
2. Posicionar ambos textos vectorizados un un sistema de coordenadas multidimensional de *n* ejes.
3. Trazar líneas hipotéticas directas al hiperespacio de origen y calcular el gradiente del ángulo $\theta$. Un abstract exactamente idéntico superpondrá las líneas, dejando a $\theta = 0^{\circ}$, donde $\cos(0) = 1$ (Interpretado con resultado al 100%).

---

### 1.4. Distancia Euclidiana Normalizada
Usando exactamente las mismas matrices numéricas producidas por el vectorizador estadístico previo (**TF-IDF**), medimos la longitud explícita real de la separación recta o distancia que margina físicamente a los abstracts en el universo de la información. 

Para encontrar la hipotética Distancia $d$:
$$d(A,B) = \sqrt{\sum_{i=1}^{n} (A_i - B_i)^2}$$

Para alinear el margen de valores generados en Python (0 al Infinito) con nuestra interfaz web porcentual estandarizada, la distancia euclídea original se invierte mediante una función métrica de decaimiento:
$$Sim_{euc}(A,B) = \frac{1}{1 + d(A,B)}$$

---

## 2. Redes Neuronales Profundas (Modelos NLP de Inteligencia Artificial)

### 2.1. Embeddings Estáticos de Tensores (Modelo Spacy Core de Word2Vec)
Se base arquitectónicamente en una red neuronal superficial paralela (*GloVe - Shallow Neural Network*) que ha interiorizado el significado social de las palabras por aproximación. La versión empleada fue `en_core_web_md` que se preentabló devorando millones de blogs periodísticos y manuales escritos extraídos directo de internet durante el desarrollo del modelo subyacente.

- **Diseño Algorítmico Interno**: El parser carga el listado semántico, analiza de izquierda a derecha el texto $A$, consulta a las enormes listas de matrices extrayendo tensores de hasta 300 dimensiones fijas independientes por cada vocablo identificado. Posteriormente promedia el tensor completo con todo el documento (Vector Pooling). Las correlaciones se ejecutan mediante simulación del Coseno entre estos tensores definitivos aglutinados. 
- **Ventaja Epistémica**: Soluciona todas las falencias de los métodos clásicos. Conceptos como "Inteligencia Artificial" u "Omnisciencia Virtual" que tendrían similitud **del 0%** con Levenshtein y Jaccard (porque no comparten casi caracteres) serán entendidos matemáticamente como un margen positivo correlacionado gracias a que el peso geométrico se empareja algorítmicamente y en cercanía a ideas idénticas en la base de Word2Vec de la tabla principal de entrenamiento.

### 2.2. Arquitectura de Deep Transformers (Modelo Estructural Contextual BERT)
Este motor utiliza una red de topología profunda basada fundamentalmente en codificadores optimizados *SentenceTransformers* (`all-MiniLM-L6-v2`), impulsada por un subesqueleto semántico BERT (Bidirectional Encoder Representations from Transformers).
- **Mecanismo Distintivo Evaluativo**: Es categóricamente el modelo cognitivo más avanzado que corre la interfaz gráfica. Su diferenciador vitalicio se apoya en la ecuación de ponderación neuronal paralela, denominada **Mecanismo de Autoatención (Self-Attention)**. Analiza todo el contexto perimetral de una oración *hacia ambos* lados direccionales del lenguaje.
- Ecuación del Peso de Multi-Atención Algorítmica:
  $$Attention(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
- Progresa a una asimilación del inglés académico casi emulante al del ser humano actual, puesto a que crea un "embedding sintético fluido". Puede diferenciar que en el texto *"They bank on AI"* la palabra inglesa *Bank* no es un establecimiento financiero (como deduciría el sistema estático **2.1.** de Word2Vec) sino que es un verbo de "confiar en"; alterando todos los parámetros porcentuales del análisis simbiótico del programa web para el Requerimiento 2.
