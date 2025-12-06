import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

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
    artistas_emergentes_y_olvidados
)


def cargar_datos():
    """
    Carga elias_limpio.csv y elie_limpio.csv desde datos/procesados.
    """
    ruta_datos = RUTA_RAIZ / "datos" / "procesados"

    try:
        df_elias = pd.read_csv(
            ruta_datos / "elias_limpio.csv",
            parse_dates=["fecha_reproduccion"],
        )
    except FileNotFoundError:
        st.error("No se encontró el archivo elias_limpio.csv en datos/procesados.")
        df_elias = pd.DataFrame()

    try:
        df_elie = pd.read_csv(
            ruta_datos / "elie_limpio.csv",
            parse_dates=["fecha_reproduccion"],
        )
    except FileNotFoundError:
        st.error("No se encontró el archivo elie_limpio.csv en datos/procesados.")
        df_elie = pd.DataFrame()

    return df_elias, df_elie


def preparar_df_conjunto(df_elias: pd.DataFrame, df_elie: pd.DataFrame) -> pd.DataFrame:
    """
    Une los dataframes de Elias y elie en uno solo,
    con columna 'usuario' = 'Elias' o 'elie'.
    """
    frames = []

    if not df_elias.empty:
        temp = df_elias.copy()
        temp["usuario"] = "Elias"
        frames.append(temp)

    if not df_elie.empty:
        temp = df_elie.copy()
        temp["usuario"] = "elie"
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


def render_tab_usuario(df_conjunto: pd.DataFrame, usuario: str, etiqueta: str):
    """
    Renderiza la vista individual de un usuario (solo sus datos).
    """
    df_user = df_conjunto[df_conjunto["usuario"] == usuario].copy()

    if df_user.empty:
        st.info(f"No hay datos para {etiqueta}.")
        return

    st.subheader(f"Visión general — {etiqueta}")

    col1, col2, col3 = st.columns(3)

    minutos_totales = df_user["minutos_reproducidos"].sum()
    dias_unicos = df_user["fecha_reproduccion"].dt.date.nunique()
    artistas_unicos = df_user["artista"].nunique()

    with col1:
        st.metric("Minutos totales", f"{minutos_totales:,.0f}")
    with col2:
        st.metric("Días con música", f"{dias_unicos:,}")
    with col3:
        st.metric("Artistas distintos", f"{artistas_unicos:,}")

    st.markdown("---")

    st.markdown("### Índice de obsesión (Top 1 / Top 5 / Top 10)")
    obs = obsesion_multi(df_user)
    c1, c2, c3 = st.columns(3)
    c1.metric("Top 1", f"{obs['top_1']:.1f}%")
    c2.metric("Top 5", f"{obs['top_5']:.1f}%")
    c3.metric("Top 10", f"{obs['top_10']:.1f}%")

    st.markdown("---")

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
            color_discrete_sequence=["#FF4B4B"],
        )
        st.plotly_chart(fig, use_container_width=True)
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
                color_discrete_sequence=["#1f77b4"],
            )
            fig_dia.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_dia, use_container_width=True)

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
                color_discrete_sequence=["#ff7f0e"],
            )
            st.plotly_chart(fig_bloques, use_container_width=True)

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
            st.metric(
                "¿Eres más de entre semana o de finde?",
                f"{ratio:.2f}x",
                help="Mayor que 1 significa que escuchas más entre semana que en fines de semana.",
            )
        else:
            st.metric("¿Eres más de entre semana o de finde?", "N/A")

    with col_i2:
        st.metric(
            "Promedio min/día",
            f"{var_diaria.get('promedio_minutos_por_dia', 0):.1f}",
        )

    with col_i3:
        long_racha = racha_30.get("longitud_racha", 0)
        st.metric(
            "Racha más larga (≥30 min/día)",
            f"{long_racha} días",
        )
    
    st.markdown("---")
    st.markdown("## Artistas y canciones")
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("**Top canciones del año**")
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
                    color_discrete_sequence=["#9467bd"],
                )
                fig_top_songs.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_top_songs, use_container_width=True)
            df_top_songs = top_canciones(df_user, n=10)
    
    with col_a2:
        st.markdown("**Artistas emergentes y artistas olvidados**")
        res_artistas = artistas_emergentes_y_olvidados(df_user, top_n = 5)
        df_emergentes = res_artistas.get("emergentes", pd.DataFrame())
        df_olvidados = res_artistas.get("olvidados", pd.DataFrame())
        tabs_art = st.tabs(["Emergentes", "Olvidados"])
        with tabs_art[0]:
            if not df_emergentes.empty:
                st.markdown("Artistas que **ganaron peso** en la segunda mitad del año.")
                st.dataframe(df_emergentes, use_container_width=True)
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
                        color_discrete_sequence=["#2ca02c"],
                    )
                    fig_em.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_em, use_container_width=True)
            else:
                st.info("No se detectaron artistas emergentes.")
        with tabs_art[1]:
            if not df_olvidados.empty:
                st.markdown("Artistas que **perdieron peso** en la segunda mitad del año.")
                st.dataframe(df_olvidados, use_container_width=True)
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
                        labels={x_col: "Artista", y_col: "Camio en minutos primera mitad vs segunda mitad."},
                        color_discrete_sequence=["#d62728"],
                    )
                    fig_ol.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_ol, use_container_width=True)
            else:
                st.info("No se detectaron artistas olvidados.")

def render_tab_ambos(df_conjunto: pd.DataFrame):
    """
    Renderiza la pestaña comparativa Elias vs elie.
    """
    df_elias = df_conjunto[df_conjunto["usuario"] == "Elias"].copy()
    df_elie = df_conjunto[df_conjunto["usuario"] == "elie"].copy()

    if df_elias.empty or df_elie.empty:
        st.info("Se necesitan datos de Elias y de elie para mostrar la comparación.")
        return

    st.subheader("Comparación general — Elias vs elie")

    col1, col2, col3 = st.columns(3)

    minutos_elias = df_elias["minutos_reproducidos"].sum()
    minutos_elie = df_elie["minutos_reproducidos"].sum()

    with col1:
        st.metric("Minutos totales — Elias", f"{minutos_elias:,.0f}")
    with col2:
        st.metric("Minutos totales — elie", f"{minutos_elie:,.0f}")
    with col3:
        st.metric("Minutos totales — Ambos", f"{(minutos_elias + minutos_elie):,.0f}")

    st.markdown("---")

    st.markdown("### Comparación de obsesión (Top 1 / Top 5 / Top 10)")

    obs_elias = obsesion_multi(df_elias)
    obs_elie = obsesion_multi(df_elie)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Elias**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Top 1", f"{obs_elias['top_1']:.1f}%")
        c2.metric("Top 5", f"{obs_elias['top_5']:.1f}%")
        c3.metric("Top 10", f"{obs_elias['top_10']:.1f}%")

    with col_b:
        st.markdown("**elie**")
        c4, c5, c6 = st.columns(3)
        c4.metric("Top 1", f"{obs_elie['top_1']:.1f}%")
        c5.metric("Top 5", f"{obs_elie['top_5']:.1f}%")
        c6.metric("Top 10", f"{obs_elie['top_10']:.1f}%")

    st.markdown("---")

    st.markdown("### Minutos por mes — comparativo")

    df_min_elias = minutos_por_anio_mes(df_elias).assign(usuario="Elias")
    df_min_elie = minutos_por_anio_mes(df_elie).assign(usuario="elie")

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
            title="Minutos reproducidos por mes — Elias vs elie",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar minutos por mes.")


def main():
    st.set_page_config(
        page_title="Spotify Analytics - Elias & Elie",
        layout="wide",
    )

    st.title("🎧 Spotify Analytics — Elias & Elie")
    st.markdown(
        "Dashboard interactivo para explorar y comparar los hábitos musicales de "
        "**Elias** y **elie** a partir de sus historiales personales de Spotify."
    )

    df_elias, df_elie = cargar_datos()
    if df_elias.empty and df_elie.empty:
        st.stop()

    df_conjunto = preparar_df_conjunto(df_elias, df_elie)
    if df_conjunto.empty:
        st.info("No se pudo construir el dataframe conjunto.")
        st.stop()

    tab_elias, tab_elie, tab_ambos = st.tabs(["Elias", "elie", "Ambos"])

    with tab_elias:
        render_tab_usuario(df_conjunto, usuario="Elias", etiqueta="Elias")

    with tab_elie:
        render_tab_usuario(df_conjunto, usuario="elie", etiqueta="elie")

    with tab_ambos:
        render_tab_ambos(df_conjunto)


if __name__ == "__main__":
    main()
