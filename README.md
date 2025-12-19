# Spotify Self Analytics — Elias & Elie

## Descripción general

Spotify Self Analytics es un proyecto de análisis y visualización de datos que explora hábitos de escucha musical a partir del historial personal de Spotify. El proyecto procesa datos crudos exportados desde Spotify, genera métricas representativas sobre el comportamiento musical de los usuarios y presenta los resultados en un dashboard interactivo.

El enfoque del proyecto combina análisis de datos, visualización, diseño de experiencia de usuario y buenas prácticas de ingeniería de software, integrando Python, Pandas, Streamlit, GitHub y Docker.

---

## Objetivos del proyecto

- Procesar y limpiar historiales de escucha de Spotify usando Python y Pandas.
- Generar métricas e indicadores relevantes sobre hábitos musicales.
- Construir un dashboard interactivo y visualmente estructurado con Streamlit.
- Permitir la comparación de hábitos entre dos usuarios.
- Garantizar reproducibilidad y facilidad de ejecución mediante Docker.
- Mantener un flujo de trabajo colaborativo y versionado con GitHub.

---

## Tecnologías utilizadas

- Python  
- Pandas  
- Streamlit  
- Plotly  
- Pillow (PIL)  
- GitHub  
- Docker  

---

## Estructura del proyecto

```
Proyecto_Spotify_Analytics/
│
├── assets/
│   └── artistas/
│       └── *.jpg
│
├── datos/
│   ├── aux/
│   │   └── imagenes_artistas.csv
│   └── procesados/
│       ├── elias_limpio.csv
│       └── elie_limpio.csv
│
├── src/
│   └── analitica_spotify/
│       ├── consultas.py
│       └── dashboard.py
│
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

---

## Métricas y análisis incluidos

- Minutos totales de escucha.
- Días con actividad musical.
- Artistas distintos escuchados.
- Top artistas y top canciones.
- Índice de obsesión musical (Top 1, Top 5, Top 10).
- Patrones temporales de escucha (mes, día de la semana, bloque horario).
- Rachas de consistencia musical.
- Comparaciones directas entre usuarios.

---

## Ejecución local (sin Docker)

1. Crear un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar el dashboard:
```bash
streamlit run src/analitica_spotify/dashboard.py
```

---

## Ejecución con Docker

### Build de la imagen

```bash
docker build -t spotify-analytics:dev .
```

---

### Run (modo demo)

```bash
docker run --rm -p 8501:8501 spotify-analytics:dev
```

Abrir en el navegador:
```
http://localhost:8501
```

---

### Run (modo datos externos)

Coloca los archivos `elias_limpio.csv` y/o `elie_limpio.csv` en una carpeta local y ejecuta:

```bash
docker run --rm -p 8501:8501 \
  -v /RUTA/A/TU/CARPETA:/data \
  spotify-analytics:dev
```

El dashboard prioriza la lectura desde `/data`.  
Si no encuentra archivos, utiliza los datos incluidos en `datos/procesados`.

---

## Colaboración y versionado

- Desarrollo en ramas individuales.
- Integración mediante Pull Requests.
- Control de versiones con GitHub.
- Ejecución consistente mediante Docker.

---

## Estado del proyecto

Proyecto funcional y completo, con análisis reproducible, dashboard interactivo y ejecución contenerizada.

