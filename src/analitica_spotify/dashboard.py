#streamlit run src/analitica_spotify/dashboard.py
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

from PIL import Image

# Ruta raíz del proyecto (Proyecto_Spotify_Analytics)
RUTA_RAIZ = Path(__file__).resolve().parents[2]
if str(RUTA_RAIZ) not in sys.path:
    sys.path.append(str(RUTA_RAIZ))

from src.analitica_spotify.consultas import (
    top_artistas,
    minutos_por_anio_mes,
    indice_obsesion,
    minutos_por_dia_semana,
    minutos_por_bloque_horario,
    resumen_entre_semana_vs_fin,
    resumen_variabilidad_diaria,
    racha_musical_mas_larga,
    top_canciones,
    artistas_emergentes_y_olvidados,
    velocidad_aburrimiento,
    fidelidad_vs_exploracion
)

def cargar_imagenes_artistas() -> pd.DataFrame:
    """
    Carga el catálogo de imágenes de artistas para el usuario dado.
    Espera un CSV en datos/aux:
      - imagenes_artistas_elias.csv
      - imagenes_artistas_elie.csv
    con columnas: artista, url_imagen
    """
    ruta_aux = RUTA_RAIZ / "datos" / "aux" / "imagenes_artistas.csv"

    if not ruta_aux.exists():
        return pd.DataFrame(columns=["usuario", "artista", "url_imagen"])

    try:
        df_img = pd.read_csv(ruta_aux)
        cols_min = {"usuario", "artista", "url_imagen"}
        if not cols_min.issubset(set(df_img.columns)):
            return pd.DataFrame(columns=["usuario", "artista", "url_imagen"])
        return df_img
    except Exception:
        return pd.DataFrame(columns=["usuario", "artista", "url_imagen"])

def imagen_cuadrada(path, size=100):
    """
    Abre una imagen, la recorta al centro para que sea cuadrada
    y la redimensiona al tamaño especificado.
    """
    try:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        
        # Lado del cuadrado
        side = min(w, h)
        
        # Coordenadas para recorte centrado
        left = (w - side) // 2
        top = (h - side) // 2
        right = left + side
        bottom = top + side

        img = img.crop((left, top, right, bottom))
        img = img.resize((size, size))
        return img
    except Exception as e:
        return None


def cargar_datos():
    """
    Prioridad de lectura:
    1) /data (volumen montado por Docker)
    2) datos/procesados (datos demo del repo)
    """
    ruta_externa = Path("/data")
    ruta_local = RUTA_RAIZ / "datos" / "procesados"

    def leer_csv(ruta, nombre):
        try:
            return pd.read_csv(
                ruta / nombre,
                parse_dates=["fecha_reproduccion"],
            )
        except FileNotFoundError:
            return pd.DataFrame()

    df_elias = leer_csv(ruta_externa, "elias_limpio.csv")
    df_elie  = leer_csv(ruta_externa, "elie_limpio.csv")

    if df_elias.empty and df_elie.empty:
        df_elias = leer_csv(ruta_local, "elias_limpio.csv")
        df_elie  = leer_csv(ruta_local, "elie_limpio.csv")

    return df_elias, df_elie



def preparar_df_conjunto(df_elias: pd.DataFrame, df_elie: pd.DataFrame) -> pd.DataFrame:
    """
    Une los dataframes de Elias y Elie en uno solo,
    con columna 'usuario' = 'Elias' o 'Elie'.
    """
    frames = []

    if not df_elias.empty:
        temp = df_elias.copy()
        temp["usuario"] = "Elias"
        frames.append(temp)

    if not df_elie.empty:
        temp = df_elie.copy()
        temp["usuario"] = "Elie"
        frames.append(temp)

    if not frames:
        return pd.DataFrame()

    df_conjunto = pd.concat(frames, ignore_index=True)
    return df_conjunto


def obsesion_multi(df: pd.DataFrame, niveles=(1, 5, 10)) -> dict:
    """
    Devuelve un dict con índice de obsesión para Top1, Top5 y Top10.
    """
    return {f"top_{n}": indice_obsesion(df, n=n) for n in niveles}

def preparar_pastel_obsesion(df_user: pd.DataFrame) -> pd.DataFrame:
     """
    Construye un dataframe con segmentos para un pastel:
    Top 1, Resto Top 5, Resto Top 10, Otros.
    """
     obs1 = indice_obsesion(df_user, n=1)
     obs5 = indice_obsesion(df_user, n=5)
     obs10 = indice_obsesion(df_user, n=10)
     seg_top1 = obs1
     seg_top5 = max(obs5 - obs1, 0)
     seg_top10 = max(obs10 - obs5, 0)
     seg_otros = max(100 - obs10, 0)
     datos = {
         "segmento": ["Top 1", "Resto Top 5", "Resto Top 10", "Otros"],
         "porcentaje": [seg_top1, seg_top5, seg_top10, seg_otros],
     }
     df_pastel = pd.DataFrame(datos)
     df_pastel = df_pastel[df_pastel["porcentaje"] > 0].reset_index(drop=True)
     return df_pastel

def construir_df_rachas(df_user: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la racha musical más larga para distintos umbrales
    de minutos por día y regresa un dataframe.
    """
    umbrales = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120]
    longitudes = []
    for u in umbrales:
        info = racha_musical_mas_larga(df_user, umbral_minutos_dia=u)
        longitudes.append(info.get("longitud_racha", 0))
    return pd.DataFrame(
        {"umbral_minutos_dia": umbrales, "longitud_dias": longitudes}
    )

def inject_premium_css():
    """Inyecta CSS premium para el dashboard estilo Spotify/Apple Music/Notion"""
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* Variables de color premium - Paleta expandida */
        :root {
            --bg-primary: #0a0a0a;
            --bg-secondary: #121212;
            --bg-card: #1a1a1a;
            --bg-card-hover: #242424;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            /* Verde Spotify (principal) */
            --accent-primary: #1db954;
            --accent-secondary: #1ed760;
            /* Colores adicionales para variedad */
            --accent-blue: #509bf5;
            --accent-purple: #af2896;
            --accent-orange: #ff6b35;
            --accent-pink: #ff1168;
            --accent-cyan: #00d4ff;
            --accent-yellow: #ffd700;
            --border-color: #2a2a2a;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        
        /* Fuentes personalizadas */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }
        
        h1, h2, h3, h4, h5, h6, .metric-value {
            font-family: 'Space Grotesk', 'Inter', sans-serif !important;
        }
        
        .artist-name {
            font-family: 'Poppins', 'Inter', sans-serif !important;
        }
        
        /* Fondo principal */
        .stApp {
            background: linear-gradient(180deg, #0a0a0a 0%, #121212 100%);
            color: var(--text-primary);
        }
        
        /* Headers y títulos */
        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em;
            font-family: 'Space Grotesk', sans-serif !important;
        }
        
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
            font-weight: 800 !important;
        }
        
        h2 {
            font-size: 1.75rem !important;
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
            font-weight: 700 !important;
        }
        
        h3 {
            font-size: 1.5rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
            font-weight: 600 !important;
        }
        
        /* Párrafos y texto */
        p, .stMarkdown {
            color: var(--text-secondary) !important;
        }
        
        /* Cards premium */
        .metric-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, var(--accent-primary), var(--accent-blue));
        }
        
        .metric-card:hover {
            background: var(--bg-card-hover);
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
            border-color: var(--accent-primary);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 8px 0;
            letter-spacing: -0.03em;
            font-family: 'Space Grotesk', sans-serif !important;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        /* Contenedores de sección */
        .section-container {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 32px;
            margin: 24px 0;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }
        
        /* Grid de artistas */
        .artist-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            margin-bottom: 16px;
        }
        
        .artist-card:hover {
            background: var(--bg-card-hover);
            box-shadow: var(--shadow-md);
            transform: translateY(-4px);
        }
        
        .artist-card img {
            border-radius: 8px;
            margin-bottom: 12px;
            box-shadow: var(--shadow-sm);
            width: 100px;
            height: 100px;
            object-fit: cover;
            margin: 0 auto 12px auto;
            display: block;
        }
        
        .artist-name {
            font-weight: 700;
            color: var(--text-primary);
            margin: 12px 0 6px 0;
            font-size: 1.15rem;
            font-family: 'Poppins', sans-serif !important;
            letter-spacing: -0.01em;
        }
        
        .artist-minutes {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        /* Gráficas integradas */
        .chart-container {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
        }
        
        /* Tabs personalizados */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: var(--bg-card);
            border-radius: 8px 8px 0 0;
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 12px 24px;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--bg-secondary);
            color: var(--accent-primary);
            border-bottom: 2px solid var(--accent-primary);
            font-weight: 600;
        }
        
        /* Separadores */
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 32px 0;
        }
        
        /* Métricas de Streamlit */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.875rem !important;
            color: var(--text-secondary) !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Info boxes */
        .stInfo {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            color: var(--text-secondary) !important;
        }
        
        /* Dataframes */
        .stDataFrame {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px;
        }
        
        /* Espaciado mejorado */
        .main .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }
        
        /* Mejorar espaciado entre secciones */
        .element-container {
            margin-bottom: 24px;
        }
        
        /* Estilo para dataframes */
        .stDataFrame {
            background: var(--bg-card) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            border: 1px solid var(--border-color) !important;
        }
        
        /* Mejorar visualización de info boxes */
        .stAlert {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            color: var(--text-secondary) !important;
        }
        
        /* Estilizar tablas de dataframes */
        .stDataFrame table {
            background: var(--bg-card) !important;
            border-radius: 12px !important;
            overflow: hidden;
        }
        
        .stDataFrame thead tr th {
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            border-bottom: 2px solid var(--accent-primary) !important;
            padding: 12px !important;
        }
        
        .stDataFrame tbody tr {
            background: var(--bg-card) !important;
            border-bottom: 1px solid var(--border-color) !important;
        }
        
        .stDataFrame tbody tr:hover {
            background: var(--bg-card-hover) !important;
        }
        
        .stDataFrame tbody tr td {
            color: var(--text-secondary) !important;
            padding: 10px 12px !important;
        }
        
        .stDataFrame tbody tr td:first-child {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }
        
        /* Scrollbar personalizado */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #3a3a3a;
        }
    </style>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, help_text: str = None):
    """Renderiza una métrica en una card premium estilizada"""
    help_html = f'<div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 8px;">{help_text}</div>' if help_text else ''
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {help_html}
    </div>
    """, unsafe_allow_html=True)

def render_section_container(content_html: str):
    """Renderiza contenido dentro de un contenedor de sección premium"""
    st.markdown(f'<div class="section-container">{content_html}</div>', unsafe_allow_html=True)

def render_tab_usuario(df_conjunto: pd.DataFrame, usuario: str, etiqueta: str):
    """
    Renderiza la vista individual de un usuario (solo sus datos).
    """
    df_user = df_conjunto[df_conjunto["usuario"] == usuario].copy()

    if df_user.empty:
        st.info(f"No hay datos para {etiqueta}.")
        return

    st.markdown(f"<h2 style='margin-top: 0;'>Visión general — {etiqueta}</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    minutos_totales = df_user["minutos_reproducidos"].sum()
    dias_unicos = df_user["fecha_reproduccion"].dt.date.nunique()
    artistas_unicos = df_user["artista"].nunique()

    with col1:
        render_metric_card("Minutos totales", f"{minutos_totales:,.0f}")
    with col2:
        render_metric_card("Días con música", f"{dias_unicos:,}")
    with col3:
        render_metric_card("Artistas distintos", f"{artistas_unicos:,}")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    st.markdown("## Top artistas y canciones")
    # ---------- TOP ARTISTAS CON FOTO ----------
    st.markdown("### Tus artistas más escuchados")
    
    st.markdown("""
    <style>
        .artist-grid-container {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 32px;
            margin: 24px 0;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
        }
    </style>
    """, unsafe_allow_html=True)

    df_top_art = top_artistas(df_user, n=10)

    df_img_all = cargar_imagenes_artistas()

    if not df_img_all.empty:
        df_img_all = df_img_all.copy()
        df_img_all["usuario"] = df_img_all["usuario"].astype(str).str.strip().str.lower()
        df_img_all["artista"] = df_img_all["artista"].astype(str).str.strip()
    else:
        df_img_all = pd.DataFrame(columns=["usuario", "artista", "url_imagen"])

    usuario_key = str(usuario).strip().lower()
    df_img_art = df_img_all[df_img_all["usuario"] == usuario_key]


    if isinstance(df_top_art, pd.Series):
        df_top_art = df_top_art.rename_axis("artista").reset_index(name="minutos_reproducidos")
    elif isinstance(df_top_art, pd.DataFrame) and not df_top_art.empty:
        cols_art = list(df_top_art.columns)
        col_artista = next((c for c in cols_art if "artista" in c.lower()), cols_art[0])
        col_min = next((c for c in cols_art if "minuto" in c.lower()), None)
        if col_min is None and len(cols_art) > 1:
            col_min = cols_art[1]
        df_top_art = df_top_art.rename(
            columns={col_artista: "artista", col_min: "minutos_reproducidos"}
        )
    else:
        df_top_art = pd.DataFrame(columns=["artista", "minutos_reproducidos"])

    if not df_top_art.empty:
        df_top_art = df_top_art.copy()
        df_top_art["artista"] = df_top_art["artista"].astype(str).str.strip()

        df_merge = df_top_art.merge(
            df_img_art[["artista", "url_imagen"]],
            on="artista",
            how="left",
        )

        # Grid de tarjetas (2 filas x 5 columnas máx) con estilo premium
        for i in range(0, len(df_merge), 5):
            fila = df_merge.iloc[i:i+5]
            cols = st.columns(len(fila))
            for col_st, (_, row) in zip(cols, fila.iterrows()):
                with col_st:
                    url = row.get("url_imagen")
                    artist_name = row['artista']
                    minutes = row['minutos_reproducidos']
                    
                    # Contenedor de card
                    st.markdown('<div class="artist-card" style="text-align: center;">', unsafe_allow_html=True)
                    
                    # Renderizar imagen (tamaño reducido)
                    if isinstance(url, str) and url.strip() != "":
                        if url.startswith("http://") or url.startswith("https://"):
                            st.image(url, width=100, use_container_width=False)
                        else:
                            ruta_img = RUTA_RAIZ / url
                            if ruta_img.exists():
                                img_proc = imagen_cuadrada(str(ruta_img), size=100)
                                if img_proc is not None:
                                    st.image(img_proc, width=100, use_container_width=False)
                                else:
                                    st.markdown('<div style="width: 100px; height: 100px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="width: 100px; height: 100px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="width: 100px; height: 100px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="artist-name">{artist_name}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="artist-minutes">{minutes:.0f} min</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No se pudo calcular el top de artistas.")


    st.markdown("### Top canciones del año")
    df_top_songs = top_canciones(df_user, n=10)
    if not df_top_songs.empty:
        cols = list(df_top_songs)
        if len(cols) >= 2:
            posibles_y = [c for c in cols if "minutos" in c.lower()]
            if posibles_y:
                y_col = posibles_y[0]
                x_posibles = [c for c in cols if c != y_col]
                x_col = x_posibles[0] if x_posibles else cols[0]
            else:
                x_col, y_col = cols[0], cols[1]
            
            fig_top_songs = px.bar(
                df_top_songs,
                x=x_col,
                y=y_col,
                title = "Tus canciones más escuchadas",
                labels={x_col: "Canción", y_col: "Minutos reproducidos"},
                color_discrete_sequence=["#1db954"],  # Verde principal
            )
            fig_top_songs.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#b3b3b3',
                title_font_color='#ffffff',
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_top_songs, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        df_top_songs = top_canciones(df_user, n=10)

    st.markdown("### Índice de obsesión (Top 1 / Top 5 / Top 10)")
    obs = obsesion_multi(df_user)
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Top 1", f"{obs['top_1']:.1f}%")
    with c2:
        render_metric_card("Top 5", f"{obs['top_5']:.1f}%")
    with c3:
        render_metric_card("Top 10", f"{obs['top_10']:.1f}%")
    st.markdown("<p style='color: var(--text-secondary); margin: 16px 0 24px 0;'>Como se concentra tu escucha</p>", unsafe_allow_html=True)
    df_pastel = preparar_pastel_obsesion(df_user)
    if not df_pastel.empty:
        fig_pastel = px.pie(
            df_pastel,
            names="segmento",
            values="porcentaje",
            hole=0.4,
            title="Distribución de minutos entre tus artistas",
            color_discrete_sequence=["#1db954", "#509bf5", "#af2896", "#ff6b35"],  # Verde + azul + púrpura + naranja
        )
        fig_pastel.update_traces(textposition="inside", textinfo="percent+label", textfont_color='#ffffff')
        fig_pastel.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_pastel, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay información suficiente para el pastel de obsesión.")
    

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    st.markdown("### Ritmo del año: minutos por mes")
    df_min = minutos_por_anio_mes(df_user)

    if not df_min.empty:
        df_min["anio_mes"] = pd.to_datetime(
            df_min["anio"].astype(str)
            + "-"
            + df_min["mes"].astype(str)
            + "-01"
        )

        fig = px.line(
            df_min,
            x="anio_mes",
            y="minutos_reproducidos",
            markers=True,
            labels={
                "anio_mes": "Mes",
                "minutos_reproducidos": "Minutos reproducidos",
            },
            title=f"Minutos reproducidos por mes — {etiqueta}",
            color_discrete_sequence=["#ff6b35"],  # Naranja para variedad
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            xaxis_gridcolor='rgba(255,255,255,0.1)',
            yaxis_gridcolor='rgba(255,255,255,0.1)',
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay datos suficientes para mostrar minutos por mes.")

    
    st.markdown("## Hábitos de escucha")

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.markdown("**Minutos por día de la semana**")
        df_dia = minutos_por_dia_semana(df_user)

        if df_dia is None or len(df_dia) == 0:
            st.info("No hay datos para días de la semana.")
        else:
            if isinstance(df_dia, pd.Series):
                df_dia = df_dia.rename_axis("dia_semana").reset_index(name="minutos_reproducidos")
            else:
                if "dia_semana" not in df_dia.columns:
                    df_dia = df_dia.reset_index()
                    df_dia.columns = ["dia_semana", "minutos_reproducidos"]

            fig_dia = px.bar(
                df_dia,
                x="dia_semana",
                y="minutos_reproducidos",
                labels={
                    "dia_semana": "Día de la semana",
                    "minutos_reproducidos": "Minutos reproducidos",
                },
                title="¿Qué días escuchas más?",
                color_discrete_sequence=["#509bf5"],  # Azul para variedad
            )
            fig_dia.update_layout(
                xaxis_tickangle=-30,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#b3b3b3',
                title_font_color='#ffffff',
                xaxis_gridcolor='rgba(255,255,255,0.1)',
                yaxis_gridcolor='rgba(255,255,255,0.1)',
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_dia, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_h2:
        st.markdown("**Minutos por bloque horario**")
        df_bloques = minutos_por_bloque_horario(df_user)

        if df_bloques is None or len(df_bloques) == 0:
            st.info("No hay datos para bloques horarios.")
        else:
            if isinstance(df_bloques, pd.Series):
                df_bloques = df_bloques.rename_axis("bloque_horario").reset_index(name="minutos_reproducidos")
            else:
                if "bloque_horario" not in df_bloques.columns:
                    df_bloques = df_bloques.reset_index()
                    df_bloques.columns = ["bloque_horario", "minutos_reproducidos"]

            fig_bloques = px.bar(
                df_bloques,
                x="bloque_horario",
                y="minutos_reproducidos",
                labels={
                    "bloque_horario": "Bloque horario",
                    "minutos_reproducidos": "Minutos reproducidos",
                },
                title="¿En qué momento del día escuchas más?",
                color_discrete_sequence=["#af2896"],  # Púrpura para variedad
            )
            fig_bloques.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#b3b3b3',
                title_font_color='#ffffff',
                xaxis_gridcolor='rgba(255,255,255,0.1)',
                yaxis_gridcolor='rgba(255,255,255,0.1)',
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_bloques, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("## Intensidad y consistencia")

    col_i1, col_i2, col_i3 = st.columns(3)

    resumen_semana = resumen_entre_semana_vs_fin(df_user)
    var_diaria = resumen_variabilidad_diaria(df_user)
    racha_30 = racha_musical_mas_larga(df_user, umbral_minutos_dia=30)

    if not resumen_semana.empty:
        fila_entre = resumen_semana[resumen_semana["grupo"] == "entre_semana"]
        fila_fin = resumen_semana[resumen_semana["grupo"] == "fin_de_semana"]

        if not fila_entre.empty and not fila_fin.empty:
            ratio = (
                fila_entre["minutos_promedio_por_dia"].iloc[0]
                / fila_fin["minutos_promedio_por_dia"].iloc[0]
                if fila_fin["minutos_promedio_por_dia"].iloc[0] > 0
                else None
            )
        else:
            ratio = None
    else:
        ratio = None

    with col_i1:
        if ratio is not None:
            render_metric_card(
                "¿Eres más de entre semana o de finde?",
                f"{ratio:.2f}x",
                "Mayor que 1 significa que escuchas más entre semana que en fines de semana."
            )
        else:
            render_metric_card("¿Eres más de entre semana o de finde?", "N/A")

    with col_i2:
        render_metric_card(
            "Promedio min/día",
            f"{var_diaria.get('promedio_minutos_por_dia', 0):.1f}",
        )

    with col_i3:
        long_racha = racha_30.get("longitud_racha", 0)
        render_metric_card(
            "Racha más larga (≥30 min/día)",
            f"{long_racha} días",
        )
    
    st.markdown("### Rachas según intensidad mínima")
    df_rachas = construir_df_rachas(df_user)
    if not df_rachas.empty:
        fig_rachas = px.bar(
            df_rachas,
            x="umbral_minutos_dia",
            y="longitud_dias",
            labels={
                "umbral_minutos_dia": "Umbral (min/día)",
                "longitud_dias": "Duración de la racha (días)",
            },
            title="Tu racha más larga según el requisito mínimo de minutos/día",
            color_discrete_sequence=["#00d4ff"],  # Cyan para variedad
        )
        fig_rachas.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            xaxis_gridcolor='rgba(255,255,255,0.1)',
            yaxis_gridcolor='rgba(255,255,255,0.1)',
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_rachas, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No se pudieron calcular las rachas por umbral.")
    
    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    st.markdown("## Artistas emergentes y artistas olvidados")
    res_artistas = artistas_emergentes_y_olvidados(df_user, top_n = 5)
    df_emergentes = res_artistas.get("emergentes", pd.DataFrame())
    df_olvidados = res_artistas.get("olvidados", pd.DataFrame())
    tabs_art = st.tabs(["Emergentes", "Olvidados"])
    with tabs_art[0]:
        if not df_emergentes.empty:
            st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Artistas que <strong style='color: var(--accent-primary);'>ganaron peso</strong> en la segunda mitad del año.</p>", unsafe_allow_html=True)
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.dataframe(df_emergentes, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            cols_em = list(df_emergentes.columns)
            if len(cols_em) >= 2:
                posibles_y = [c for c in cols_em if "minutos" in c.lower() or "delta" in c.lower()]
                if posibles_y:
                    y_col = posibles_y[0]
                    x_posibles = [c for c in cols_em if c != y_col]
                    x_col = x_posibles[0] if x_posibles else cols_em[0]
                else:
                    x_col, y_col = cols_em[0], cols_em[1]
                fig_em = px.bar(
                    df_emergentes,
                    x=x_col,
                    y=y_col,
                    title="Artistas emergentes",
                    labels = {
                        x_col: "Artista",
                        y_col: "Cambio en minutos primera mitad vs segunda mitad"
                    },
                    color_discrete_sequence=["#1db954"],  # Verde para emergentes (positivo)
                )
                fig_em.update_layout(
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#b3b3b3',
                    title_font_color='#ffffff',
                    xaxis_gridcolor='rgba(255,255,255,0.1)',
                    yaxis_gridcolor='rgba(255,255,255,0.1)',
                )
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig_em, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No se detectaron artistas emergentes.")
    with tabs_art[1]:
        if not df_olvidados.empty:
            st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Artistas que <strong style='color: var(--accent-pink);'>perdieron peso</strong> en la segunda mitad del año.</p>", unsafe_allow_html=True)
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.dataframe(df_olvidados, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            cols_ol = list(df_olvidados.columns)
            if len(cols_ol) >= 2:
                posibles_y = [c for c in cols_ol if "minutos" in c.lower() or "delta" in c.lower()]
                if posibles_y:
                    y_col = posibles_y[0]
                    x_posibles = [c for c in cols_ol if c != y_col]
                    x_col = x_posibles[0] if x_posibles else cols_ol[0]
                else:
                    x_col, y_col = cols_ol[0], cols_ol[1]
                fig_ol = px.bar(
                    df_olvidados,
                    x=x_col,
                    y=y_col,
                    title="Artistas olvidados",
                    labels={x_col: "Artista", y_col: "Cambio en minutos primera mitad vs segunda mitad"},
                    color_discrete_sequence=["#e22134"],
                )
                fig_ol.update_layout(
                    xaxis_tickangle=-45,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#b3b3b3',
                    title_font_color='#ffffff',
                    xaxis_gridcolor='rgba(255,255,255,0.1)',
                    yaxis_gridcolor='rgba(255,255,255,0.1)',
                )
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig_ol, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No se detectaron artistas olvidados.")

def render_tab_ambos(df_conjunto: pd.DataFrame):
    """
    Renderiza la pestaña comparativa Elias vs Elie.
    """
    df_elias = df_conjunto[df_conjunto["usuario"] == "Elias"].copy()
    df_elie = df_conjunto[df_conjunto["usuario"] == "Elie"].copy()

    if df_elias.empty or df_elie.empty:
        st.info("Se necesitan datos de Elias y de Elie para mostrar la comparación.")
        return

    st.markdown("<h2 style='margin-top: 0;'>Comparación general — Elias vs Elie</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    minutos_elias = df_elias["minutos_reproducidos"].sum()
    minutos_elie = df_elie["minutos_reproducidos"].sum()

    with col1:
        render_metric_card("Minutos totales — Elias", f"{minutos_elias:,.0f}")
    with col2:
        render_metric_card("Minutos totales — Elie", f"{minutos_elie:,.0f}")
    with col3:
        render_metric_card("Minutos totales — Ambos", f"{(minutos_elias + minutos_elie):,.0f}")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    # ---------- ARTISTAS COMPARTIDOS ----------
    st.markdown("<h3 style='text-align: center;'>Artistas que ambos escuchamos</h3>", unsafe_allow_html=True)
    
    # Obtener top artistas de ambos (usamos un N mayor para encontrar intersección)
    top_elias_ser = top_artistas(df_elias, n=50)
    top_elie_ser = top_artistas(df_elie, n=50)
    
    artistas_elias = set(top_elias_ser.index)
    artistas_elie = set(top_elie_ser.index)
    
    compartidos = list(artistas_elias.intersection(artistas_elie))
    
    if compartidos:
        # Ordenar por minutos totales combinados en ambos datasets
        minutos_compartidos = (
            df_conjunto[df_conjunto["artista"].isin(compartidos)]
            .groupby("artista")["minutos_reproducidos"]
            .sum()
            .sort_values(ascending=False)
        )
        compartidos = minutos_compartidos.index.tolist()[:3]

    if len(compartidos) >= 2:
        df_img_all = cargar_imagenes_artistas()
        
        # Columnas para centrar
        if len(compartidos) == 2:
            cols_shared = st.columns([1, 2, 2, 1])
            idx_cols = [1, 2]
        else: # 3
            cols_shared = st.columns([1, 2, 2, 2, 1])
            idx_cols = [1, 2, 3]
            
        for i, artista in enumerate(compartidos):
            with cols_shared[idx_cols[i]]:
                # Buscar imagen
                img_row = df_img_all[df_img_all["artista"] == artista].head(1)
                url = img_row["url_imagen"].iloc[0] if not img_row.empty else None
                
                st.markdown('<div class="artist-card" style="text-align: center;">', unsafe_allow_html=True)
                
                if isinstance(url, str) and url.strip() != "":
                    if url.startswith("http://") or url.startswith("https://"):
                        st.image(url, width=120, use_container_width=False)
                    else:
                        ruta_img = RUTA_RAIZ / url
                        if ruta_img.exists():
                            img_proc = imagen_cuadrada(str(ruta_img), size=120)
                            if img_proc is not None:
                                st.image(img_proc, width=120, use_container_width=False)
                            else:
                                st.markdown('<div style="width: 120px; height: 120px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="width: 120px; height: 120px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="width: 120px; height: 120px; background: #2a2a2a; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin: 0 auto;">🖼️</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div class="artist-name">{artista}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="artist-minutes">Gusto compartido</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay suficientes artistas en común para mostrar esta sección.")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)
    
    # ---------- COMPARATIVA DE MINUTOS POR ARTISTA COMPARTIDO ----------
    if len(compartidos) >= 2:
        st.markdown("### Comparativa de minutos por artista compartido")
        st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Minutos que cada uno escuchó de los artistas que ambos comparten.</p>", unsafe_allow_html=True)
        
        # Crear dataframe comparativo
        datos_comparativa = []
        for artista in compartidos:
            minutos_elias_art = df_elias[df_elias["artista"] == artista]["minutos_reproducidos"].sum()
            minutos_elie_art = df_elie[df_elie["artista"] == artista]["minutos_reproducidos"].sum()
            datos_comparativa.append({
                "artista": artista,
                "Elias": minutos_elias_art,
                "Elie": minutos_elie_art
            })
        
        df_comparativa = pd.DataFrame(datos_comparativa)
        
        # Transformar a formato largo para la gráfica
        df_comparativa_melt = df_comparativa.melt(
            id_vars=["artista"],
            value_vars=["Elias", "Elie"],
            var_name="usuario",
            value_name="minutos_reproducidos"
        )
        
        # Crear gráfica de barras agrupadas
        fig_comparativa = px.bar(
            df_comparativa_melt,
            x="artista",
            y="minutos_reproducidos",
            color="usuario",
            barmode="group",
            title="Minutos escuchados por artista compartido",
            labels={
                "artista": "Artista",
                "minutos_reproducidos": "Minutos reproducidos",
                "usuario": "Usuario"
            },
            color_discrete_sequence=["#1db954", "#509bf5"],
        )
        
        fig_comparativa.update_layout(
            xaxis_tickangle=-30,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            xaxis_gridcolor='rgba(255,255,255,0.1)',
            yaxis_gridcolor='rgba(255,255,255,0.1)',
            legend_bgcolor='rgba(0,0,0,0)',
        )
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_comparativa, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    st.markdown("### Comparación de obsesión musical")

    obs_elias = obsesion_multi(df_elias)
    obs_elie = obsesion_multi(df_elie)
    
    # Tarjetas de métricas de obsesión (Top 1, Top 5, Top 10)
    st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Índice de obsesión por categoría</p>", unsafe_allow_html=True)
    
    col_obs1, col_obs2 = st.columns(2)
    
    with col_obs1:
        st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 16px; text-align: center;'>Elias</h4>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Top 1", f"{obs_elias['top_1']:.1f}%")
        with c2:
            render_metric_card("Top 5", f"{obs_elias['top_5']:.1f}%")
        with c3:
            render_metric_card("Top 10", f"{obs_elias['top_10']:.1f}%")
    
    with col_obs2:
        st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 16px; text-align: center;'>Elie</h4>", unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        with c4:
            render_metric_card("Top 1", f"{obs_elie['top_1']:.1f}%")
        with c5:
            render_metric_card("Top 5", f"{obs_elie['top_5']:.1f}%")
        with c6:
            render_metric_card("Top 10", f"{obs_elie['top_10']:.1f}%")
    
    st.markdown("<p style='color: var(--text-secondary); margin: 24px 0 16px 0; text-align: center;'>Distribución de minutos entre artistas</p>", unsafe_allow_html=True)

    def donut_obsesion(obs_dict, usuario):
        # Usar la misma lógica que preparar_pastel_obsesion
        seg_top1 = obs_dict["top_1"]
        seg_top5 = max(obs_dict["top_5"] - obs_dict["top_1"], 0)
        seg_top10 = max(obs_dict["top_10"] - obs_dict["top_5"], 0)
        seg_otros = max(100 - obs_dict["top_10"], 0)
        
        df = pd.DataFrame({
            "segmento": ["Top 1", "Resto Top 5", "Resto Top 10", "Otros"],
            "porcentaje": [seg_top1, seg_top5, seg_top10, seg_otros],
        })
        
        # Filtrar segmentos con valor 0
        df = df[df["porcentaje"] > 0].reset_index(drop=True)

        fig = px.pie(
            df,
            names="segmento",
            values="porcentaje",
            hole=0.4,
            title=usuario,
            color_discrete_sequence=["#1db954", "#509bf5", "#af2896", "#ff6b35"],
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            showlegend=True,
            margin=dict(t=60, b=0, l=0, r=0),
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            textfont_color='#ffffff',
        )

        return fig

    col_a, col_b = st.columns(2)

    with col_a:
        fig_elias = donut_obsesion(obs_elias, "Elias")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_elias, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        fig_elie = donut_obsesion(obs_elie, "Elie")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_elie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)


    st.markdown("### Minutos por mes — comparativo")

    df_min_elias = minutos_por_anio_mes(df_elias).assign(usuario="Elias")
    df_min_elie = minutos_por_anio_mes(df_elie).assign(usuario="Elie")

    df_min = pd.concat([df_min_elias, df_min_elie], ignore_index=True)

    if not df_min.empty:
        df_min["anio_mes"] = pd.to_datetime(
            df_min["anio"].astype(str)
            + "-"
            + df_min["mes"].astype(str)
            + "-01"
        )

        fig = px.line(
            df_min,
            x="anio_mes",
            y="minutos_reproducidos",
            color="usuario",
            markers=True,
            labels={
                "anio_mes": "Mes",
                "minutos_reproducidos": "Minutos reproducidos",
                "usuario": "Usuario",
            },
            title="Minutos reproducidos por mes — Elias vs Elie",
            color_discrete_sequence=["#1db954", "#509bf5"],  # Verde + azul para comparación
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            xaxis_gridcolor='rgba(255,255,255,0.1)',
            yaxis_gridcolor='rgba(255,255,255,0.1)',
            legend_bgcolor='rgba(0,0,0,0)',
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay datos suficientes para mostrar minutos por mes.")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    # ---------- COMPARATIVA DE HÁBITOS HORARIOS ----------
    st.markdown("### ¿Quién es más de mañana o de noche?")
    
    df_bloques_elias = minutos_por_bloque_horario(df_elias).assign(usuario="Elias")
    df_bloques_elie = minutos_por_bloque_horario(df_elie).assign(usuario="Elie")
    df_bloques_comp = pd.concat([df_bloques_elias, df_bloques_elie], ignore_index=True)

    if not df_bloques_comp.empty:
        fig_habitos = px.bar(
            df_bloques_comp,
            x="bloque_horario",
            y="minutos_reproducidos",
            color="usuario",
            barmode="group",
            title="Distribución de escucha por bloques horarios",
            labels={
                "bloque_horario": "Bloque del día",
                "minutos_reproducidos": "Minutos totales",
                "usuario": "Usuario"
            },
            color_discrete_sequence=["#1db954", "#509bf5"],
        )
        fig_habitos.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b3b3b3',
            title_font_color='#ffffff',
            xaxis_gridcolor='rgba(255,255,255,0.1)',
            yaxis_gridcolor='rgba(255,255,255,0.1)',
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_habitos, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Resumen comparativo en cards
        c1, c2 = st.columns(2)
        
        # Encontrar quién lidera en mañana y noche
        manana_data = df_bloques_comp[df_bloques_comp["bloque_horario"] == "manana"]
        noche_data = df_bloques_comp[df_bloques_comp["bloque_horario"] == "noche"]
        
        if not manana_data.empty:
            lider_manana = manana_data.loc[manana_data["minutos_reproducidos"].idxmax(), "usuario"]
            with c1:
                render_metric_card("Rey de la Manana", lider_manana, "Usuario con más minutos entre las 6:00 y las 12:00")
        
        if not noche_data.empty:
            lider_noche = noche_data.loc[noche_data["minutos_reproducidos"].idxmax(), "usuario"]
            with c2:
                render_metric_card("Rey de la noche", lider_noche, "Usuario con más minutos entre las 18:00 y las 00:00")
    else:
        st.info("No hay datos suficientes para comparar hábitos horarios.")

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    # ---------- VELOCIDAD DE ABURRIMIENTO ----------
    st.markdown("### Velocidad de aburrimiento")
    st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Promedio de días consecutivos que escuchan una canción antes de dejarla. Un valor más bajo indica que se aburre más rápido de las canciones.</p>", unsafe_allow_html=True)
    
    vel_elias = velocidad_aburrimiento(df_elias)
    vel_elie = velocidad_aburrimiento(df_elie)
    
    col_vel1, col_vel2 = st.columns(2)
    
    with col_vel1:
        render_metric_card("Promedio de racha — Elias", f"{vel_elias:.2f} días", "Días consecutivos promedio antes de dejar una canción")
    
    with col_vel2:
        render_metric_card("Promedio de racha — Elie", f"{vel_elie:.2f} días", "Días consecutivos promedio antes de dejar una canción")
    
    # Determinar quién se aburre más rápido
    if vel_elias > 0 and vel_elie > 0:
        if vel_elias < vel_elie:
            mensaje_aburrimiento = "Elias se aburre más rápido de las canciones"
            color_ganador = "#1db954"
        elif vel_elie < vel_elias:
            mensaje_aburrimiento = "Elie se aburre más rápido de las canciones"
            color_ganador = "#509bf5"
        else:
            mensaje_aburrimiento = "Ambos tienen la misma velocidad de aburrimiento"
            color_ganador = "#b3b3b3"
        
        st.markdown(f"""
        <div style="background: var(--bg-card); border-radius: 16px; padding: 24px; margin: 16px 0; border: 1px solid var(--border-color); text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 600; color: {color_ganador};">
                {mensaje_aburrimiento}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

    # ---------- FIDELIDAD VS EXPLORACIÓN ----------
    st.markdown("### ¿Explorador o Fiel?")
    st.markdown("<p style='color: var(--text-secondary); margin-bottom: 16px;'>Porcentaje de canciones nuevas vs ya escuchadas antes. Explorador = siempre buscando música nueva. Fiel = regresa a lo que le gusta.</p>", unsafe_allow_html=True)
    
    df_fidelidad_elias = fidelidad_vs_exploracion(df_elias)
    df_fidelidad_elie = fidelidad_vs_exploracion(df_elie)
    
    # Ordenar para consistencia de colores: "Nuevas" primero (verde), luego "Ya escuchadas" (púrpura)
    if not df_fidelidad_elias.empty:
        df_fidelidad_elias["orden"] = df_fidelidad_elias["tipo"].map({"Nuevas": 0, "Ya escuchadas": 1})
        df_fidelidad_elias = df_fidelidad_elias.sort_values("orden").drop("orden", axis=1)
    if not df_fidelidad_elie.empty:
        df_fidelidad_elie["orden"] = df_fidelidad_elie["tipo"].map({"Nuevas": 0, "Ya escuchadas": 1})
        df_fidelidad_elie = df_fidelidad_elie.sort_values("orden").drop("orden", axis=1)
    
    col_fid1, col_fid2 = st.columns(2)
    
    with col_fid1:
        st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 16px; text-align: center;'>Elias</h4>", unsafe_allow_html=True)
        if not df_fidelidad_elias.empty:
            fig_elias = px.pie(
                df_fidelidad_elias,
                values="porcentaje",
                names="tipo",
                hole=0.4,
                title="Elias",
                color_discrete_sequence=["#1db954", "#af2896"],  # Verde para nuevas, púrpura para fieles
            )
            fig_elias.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont_color='#ffffff',
                textfont_size=14
            )
            fig_elias.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#b3b3b3',
                title_font_color='#ffffff',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_elias, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes para mostrar fidelidad vs exploración.")
    
    with col_fid2:
        st.markdown("<h4 style='color: var(--text-primary); margin-bottom: 16px; text-align: center;'>Elie</h4>", unsafe_allow_html=True)
        if not df_fidelidad_elie.empty:
            fig_elie = px.pie(
                df_fidelidad_elie,
                values="porcentaje",
                names="tipo",
                hole=0.4,
                title="Elie",
                color_discrete_sequence=["#1db954", "#af2896"],  # Verde para nuevas, púrpura para fieles
            )
            fig_elie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont_color='#ffffff',
                textfont_size=14
            )
            fig_elie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#b3b3b3',
                title_font_color='#ffffff',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(fig_elie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes para mostrar fidelidad vs exploración.")


def main():
    st.set_page_config(
        page_title="Spotify Analytics - Elias & Elie",
        layout="wide",
    )
    
    # Inyectar CSS premium
    inject_premium_css()

    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; margin-bottom: 2rem;">
        <h1 style="background: linear-gradient(135deg, #1db954 0%, #509bf5 50%, #af2896 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 3rem;
                    font-weight: 800;
                    letter-spacing: -0.03em;
                    margin-bottom: 0.5rem;
                    font-family: 'Space Grotesk', sans-serif;">🎧 Spotify Analytics</h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin-top: 0.5rem; font-weight: 400;">
            Dashboard interactivo para explorar y comparar los hábitos musicales de 
            <strong style="color: var(--text-primary); font-weight: 600;">Elias</strong> y 
            <strong style="color: var(--text-primary); font-weight: 600;">Elie</strong> a partir de sus historiales personales de Spotify.
        </p>
    </div>
    """, unsafe_allow_html=True)

    df_elias, df_elie = cargar_datos()
    if df_elias.empty and df_elie.empty:
        st.stop()

    df_conjunto = preparar_df_conjunto(df_elias, df_elie)
    if df_conjunto.empty:
        st.info("No se pudo construir el dataframe conjunto.")
        st.stop()

    tab_elias, tab_elie, tab_ambos = st.tabs(["Elias", "Elie", "Ambos"])

    with tab_elias:
        render_tab_usuario(df_conjunto, usuario="Elias", etiqueta="Elias")

    with tab_elie:
        render_tab_usuario(df_conjunto, usuario="Elie", etiqueta="Elie")

    with tab_ambos:
        render_tab_ambos(df_conjunto)


if __name__ == "__main__":
    main()
