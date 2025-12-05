import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

RUTA_RAIZ = Path(__file__).resolve().parents[2]
if str(RUTA_RAIZ) not in sys.path:
    sys.path.append(str(RUTA_RAIZ))

from src.analitica_spotify.consultas import (
    top_artistas,
    minutos_por_anio_mes,
    indice_obsesion,
)


def cargar_datos():
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
    return {f"top_{n}": indice_obsesion(df, n=n) for n in niveles}


def main():
    st.set_page_config(
        page_title="Spotify Analytics - Elias & Elie",
        layout="wide",
    )

    st.title("🎧 Spotify Analytics — Elias & Elie")
    st.markdown(
        "Comparación de hábitos musicales entre **Elias** y **Elie** "
        "a partir de historiales personales de escucha de Spotify."
    )

    df_elias, df_elie = cargar_datos()
    if df_elias.empty and df_elie.empty:
        st.stop()

    df_conjunto = preparar_df_conjunto(df_elias, df_elie)

    opciones_usuario = []
    if not df_elias.empty:
        opciones_usuario.append("Elias")
    if not df_elie.empty:
        opciones_usuario.append("elie")
    if len(opciones_usuario) == 2:
        opciones_usuario.append("Ambos")

    usuario_sel = st.sidebar.selectbox("Selecciona usuario", opciones_usuario)

    if usuario_sel == "Elias":
        df_sel = df_conjunto[df_conjunto["usuario"] == "Elias"].copy()
    elif usuario_sel == "elie":
        df_sel = df_conjunto[df_conjunto["usuario"] == "elie"].copy()
    else:
        df_sel = df_conjunto.copy()

    st.sidebar.markdown(
        f"**Filtrando:** {usuario_sel}  "
        f"({len(df_sel):,} reproducciones)"
    )

    tab_overview, = st.tabs(["Overview"])

    with tab_overview:
        st.subheader("Visión general")

        col1, col2, col3 = st.columns(3)

        if usuario_sel in ("Elias", "Ambos"):
            minutos_elias = df_conjunto[df_conjunto["usuario"] == "Elias"]["minutos_reproducidos"].sum()
        else:
            minutos_elias = 0

        if usuario_sel in ("elie", "Ambos"):
            minutos_elie = df_conjunto[df_conjunto["usuario"] == "elie"]["minutos_reproducidos"].sum()
        else:
            minutos_elie = 0

        with col1:
            st.metric("Minutos totales — Elias", f"{minutos_elias:,.0f}")
        with col2:
            st.metric("Minutos totales — Elie", f"{minutos_elie:,.0f}")
        with col3:
            st.metric("Minutos totales — Ambos", f"{(minutos_elias + minutos_elie):,.0f}")

        st.markdown("---")

        st.markdown("### Índice de obsesión (Top 1, Top 5 y Top 10)")

        col_a, col_b = st.columns(2)

        if not df_elias.empty:
            df_elias_filtrado = df_conjunto[df_conjunto["usuario"] == "Elias"]
            obs_elias = obsesion_multi(df_elias_filtrado)
        else:
            obs_elias = {"top_1": 0.0, "top_5": 0.0, "top_10": 0.0}

        if not df_elie.empty:
            df_elie_filtrado = df_conjunto[df_conjunto["usuario"] == "elie"]
            obs_elie = obsesion_multi(df_elie_filtrado)
        else:
            obs_elie = {"top_1": 0.0, "top_5": 0.0, "top_10": 0.0}

        with col_a:
            st.markdown("**Elias**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Top 1", f"{obs_elias['top_1']:.1f}%")
            c2.metric("Top 5", f"{obs_elias['top_5']:.1f}%")
            c3.metric("Top 10", f"{obs_elias['top_10']:.1f}%")

        with col_b:
            st.markdown("**Elie**")
            c4, c5, c6 = st.columns(3)
            c4.metric("Top 1", f"{obs_elie['top_1']:.1f}%")
            c5.metric("Top 5", f"{obs_elie['top_5']:.1f}%")
            c6.metric("Top 10", f"{obs_elie['top_10']:.1f}%")

        st.markdown("---")

        st.markdown("### Ritmo del año: minutos por mes")

        df_min_elias = (
            minutos_por_anio_mes(df_conjunto[df_conjunto["usuario"] == "Elias"])
            .assign(usuario="Elias")
            if not df_elias.empty else pd.DataFrame()
        )

        df_min_elie = (
            minutos_por_anio_mes(df_conjunto[df_conjunto["usuario"] == "elie"])
            .assign(usuario="elie")
            if not df_elie.empty else pd.DataFrame()
        )

        df_min_conjunto = pd.concat([df_min_elias, df_min_elie], ignore_index=True)

        if not df_min_conjunto.empty:
            df_min_conjunto["anio_mes"] = pd.to_datetime(
                df_min_conjunto["anio"].astype(str)
                + "-"
                + df_min_conjunto["mes"].astype(str)
                + "-01"
            )

            fig = px.line(
                df_min_conjunto,
                x="anio_mes",
                y="minutos_reproducidos",
                color="usuario",
                markers=True,
                labels={
                    "anio_mes": "Mes",
                    "minutos_reproducidos": "Minutos reproducidos",
                    "usuario": "Usuario",
                },
                title="Minutos reproducidos por mes",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar minutos por mes.")


if __name__ == "__main__":
    main()
