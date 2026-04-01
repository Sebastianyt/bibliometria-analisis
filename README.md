# Bibliometria Analisis

Proyecto para automatizar la descarga y unificación de datos bibliográficos de bases de datos científicas.

## Requerimientos

- Python 3.8+
- Chrome browser (para Selenium)

## Instalación

1. Crear entorno virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

## Uso

Ejecutar el script principal:
```
python src/main.py
```

Esto automatizará la descarga de datos de ACM, SAGE y ScienceDirect para la consulta "generative artificial intelligence", unificará los datos eliminando duplicados por título, y guardará los resultados en `data/processed/unified_articles.csv` y los duplicados en `data/duplicates/removed_duplicates.csv`.

## Notas

- El downloader usa Selenium para navegar por el portal de la biblioteca de la Universidad del Quindío. Asegúrate de estar logueado o proporcionar credenciales.
- Los selectores en el código pueden necesitar ajustes según la estructura actual de los sitios web.
- Para exportar, se asume formato CSV; ajustar si es necesario.