# 🔬 Bibliometría · IA Generativa en Educación

Un pipeline y dashboard automatizado para la **descarga, unificación, deduplicación y análisis bibliométrico** de artículos científicos sobre Inteligencia Artificial Generativa en Educación, interactuando con los portales de bases de datos científicas a través de la biblioteca digital de la **Universidad del Quindío**.

---

## 🗺️ Estructura del Proyecto

El proyecto está organizado de manera modular para separar la recolección, el procesamiento de datos y la visualización de los resultados:

```text
bibliometria-analisis/
├── .env                     # Variables de entorno y credenciales (crear localmente)
├── requirements.txt         # Dependencias de Python
├── packages.txt             # Dependencias del sistema (para despliegue en Linux/Streamlit Cloud)
├── data/                    # Almacenamiento de datos del pipeline
│   ├── raw/temp/            # Descargas temporales de archivos CSV de EBSCO/IEEE
│   ├── processed/           # Dataset unificado y limpio (unified_articles.csv)
│   └── duplicates/          # Registro de artículos duplicados eliminados
├── scripts/
│   └── update_data.py       # Script de mantenimiento rápido para procesar archivos CSV locales
└── src/
    ├── app.py               # Aplicación principal del Dashboard interactivo (Streamlit)
    ├── main.py              # Script principal del pipeline (Descarga + Parsing + Deduplicación)
    ├── data_collection/     # Recolección y descarga automatizada
    │   ├── downloader.py    # Automatización con Selenium para login y exportación en EBSCO/IEEE
    │   └── parser.py        # Mapeo y análisis de los registros exportados
    ├── preprocessing/       # Limpieza, enriquecimiento y consolidación
    │   ├── cleaner.py       # Limpieza y normalización de texto y metadatos
    │   ├── deduplicator.py  # Detección de duplicados mediante métricas de similitud (Levensthein/Fuzzy)
    │   └── geolocator.py    # Extracción y geolocalización de filiaciones/países
    ├── models/
    │   └── article.py       # Definición de la entidad/modelo 'Article'
    ├── analysis/            # Algoritmos y lógica de análisis matemático/estadístico
    └── views/               # Componentes y pestañas de la interfaz de Streamlit
        ├── req2_similarity.py  # Req 2: Análisis de Similitud Textual
        ├── req3_frequency.py   # Req 3: Frecuencias de palabras y N-grams
        ├── req4_clustering.py  # Req 4: Agrupamiento Jerárquico (Dendrogramas)
        └── req5_visual.py      # Req 5: Análisis Visual, Mapas y Generador de PDF
```

---

## 🛠️ Requisitos Previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:
* **Python 3.8 o superior** (se recomienda Python 3.10 o 3.11).
* **Google Chrome Browser** instalado en tu sistema (necesario para el bot de Selenium).
* Credenciales activas de correo institucional de la **Universidad del Quindío** (para el acceso a bases de datos).

---

## 🚀 Instalación y Configuración

Sigue estos pasos detallados para dejar el proyecto listo para usar:

### 1. Clonar el repositorio
Abre una terminal en tu carpeta de preferencia y clona o ubica el proyecto:
```bash
cd bibliometria-analisis
```

### 2. Configurar el Entorno Virtual
Es altamente recomendable aislar las dependencias del proyecto usando un entorno virtual:

* **En Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
* **En macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar las Dependencias
Con el entorno virtual activo, instala todas las dependencias requeridas ejecutando:
```bash
pip install -r requirements.txt
```

### 4. Configurar las Variables de Entorno
Crea un archivo llamado `.env` en la raíz del proyecto (junto a `requirements.txt`) para almacenar de forma segura tus credenciales institucionales de acceso a Google (utilizadas por Selenium para acceder a la biblioteca virtual). 

El archivo debe tener la siguiente estructura:
```env
GOOGLE_EMAIL=tu_correo@uqvirtual.edu.co
GOOGLE_PASSWORD=tu_contraseña_de_correo
```

> [!WARNING]
> Nunca compartas ni subas tu archivo `.env` a repositorios públicos como GitHub. Este archivo ya se encuentra en el `.gitignore`.

---

## 📊 Instrucciones de Uso

El sistema cuenta con tres formas principales de ejecución dependiendo de tus necesidades:

### Opción A: Ejecutar el Pipeline Completo (Automatización de Descarga y Procesamiento)
Este comando iniciará el navegador de forma automática (Selenium), iniciará sesión en el portal de la Universidad del Quindío, buscará la consulta *"generative artificial intelligence"*, filtrará y descargará las bases de datos de **Academic Search Ultimate** e **IEEE Xplore**, y luego limpiará y deduplicará los resultados de forma automática.

```bash
python src/main.py
```
* **Salida del proceso:**
  * Archivo unificado sin duplicados: `data/processed/unified_articles.csv`
  * Registro de duplicados descartados: `data/duplicates/removed_duplicates.csv`

---

### Opción B: Procesar Descargas Locales (Actualizar Datos Existentes)
Si ya has descargado los archivos CSV de EBSCO/IEEE manualmente y los has colocado en la carpeta temporal (`data/raw/temp/`), puedes ejecutar este script de mantenimiento rápido para procesarlos, deduplicarlos y generar el dataset unificado sin necesidad de volver a ejecutar el bot de Selenium.

```bash
python scripts/update_data.py
```

---

### Opción C: Iniciar el Dashboard Interactivo de Streamlit
Para visualizar los resultados del análisis bibliométrico, generar gráficos premium, mapas de calor geográficos, dendrogramas y exportar reportes ejecutivos en PDF, inicia la aplicación web interactiva:

```bash
streamlit run src/app.py
```

Una vez ejecutado, se abrirá de manera automática una pestaña en tu navegador web (usualmente en `http://localhost:8501`).

---

## 🎨 Características del Dashboard de Streamlit

El dashboard está dividido en cuatro secciones de análisis avanzado que cubren todos los requerimientos bibliométricos:

1. **📐 Req 2 · Similitud Textual:** Permite comparar pares de artículos y calcular métricas de similitud (Similitud del Coseno, Jaccard, distancia Levenshtein) basadas en sus títulos y resúmenes (*Abstracts*).
2. **📊 Req 3 · Frecuencia y Generación de Palabras:** Gráficos dinámicos de palabras más frecuentes, análisis de N-grams (Bigramas y Trigramas) y nubes de palabras interactivas que destacan las tendencias conceptuales.
3. **🌳 Req 4 · Agrupamiento Jerárquico:** Generación en tiempo real de dendrogramas interactivos aplicando algoritmos de Machine Learning (`SciPy` y `Scikit-Learn`) para agrupar los artículos temáticamente por su similitud semántica.
4. **📈 Req 5 · Análisis Visual y Reportes:** Gráficos estilizados en formato oscuro (*dark mode*), visualización geográfica interactiva de la producción científica por países (mediante geolocalización) y un **Generador de Reporte PDF** premium para exportar los hallazgos en un solo clic.

---

## 🛠️ Tecnologías Utilizadas

* **Procesamiento de Lenguaje Natural (NLP):** `NLTK`, `spaCy`, `scikit-learn` (TF-IDF y matrices de similitud).
* **Análisis de Datos:** `Pandas`, `NumPy`, `SciPy` (Clustering jerárquico y cálculo de distancias).
* **Visualización Dinámica:** `Plotly`, `Matplotlib`, `Altair`, `WordCloud`.
* **Automatización / Scraping:** `Selenium WebDriver` con soporte nativo de `webdriver-manager`.
* **Generación de Reportes:** `FPDF2` (Diseño limpio y profesional en PDF).
* **Interfaz de Usuario:** `Streamlit` personalizado con CSS oscuro.