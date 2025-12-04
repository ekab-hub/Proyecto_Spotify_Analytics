import pandas as pd
import numpy as np


def top_artistas(df: pd.DataFrame, n: int = 20) -> pd.Series:
    """
    Regresa los n artistas más escuchados por minutos.
    """
    return (
        df.groupby("artista")["minutos_reproducidos"]
          .sum()
          .sort_values(ascending=False)
          .head(n)
    )


def minutos_por_hora(df: pd.DataFrame) -> pd.Series:
    """
    Minutos totales reproducidos por hora del día (0-23).
    """
    return (
        df.groupby("hora")["minutos_reproducidos"]
          .sum()
          .sort_values()
    )


def minutos_por_dia_semana(df: pd.DataFrame) -> pd.Series:
    """
    Minutos totales reproducidos por día de la semana.
    """
    orden_dias = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday",
    ]

    serie = df.groupby("dia_semana")["minutos_reproducidos"].sum()
    serie = serie.reindex(orden_dias).dropna()
    return serie


def minutos_por_anio_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minutos totales reproducidos por año y mes.
    """
    tabla = (
        df.groupby(["anio", "mes"])["minutos_reproducidos"]
          .sum()
          .reset_index()
          .sort_values(["anio", "mes"])
    )
    return tabla

def indice_obsesion(df: pd.DataFrame, n: int = 10) -> float:
    """
    Porcentaje de minutos totales concentrados en los n artistas más escuchados.
    """
    total = df["minutos_reproducidos"].sum()
    if total == 0:
        return 0.0

    top_n = (
        df.groupby("artista")["minutos_reproducidos"]
          .sum()
          .sort_values(ascending=False)
          .head(n)
          .sum()
    )
    return round((top_n / total) * 100, 2)

def resumen_entre_semana_vs_fin(
    df: pd.DataFrame,
    umbral_minutos_dia: float = 0.0
) -> pd.DataFrame:
    """
    Compara entre semana (Mon-Thu) vs fin de semana (Fri-Sun).
    Devuelve minutos totales y promedio por día (solo días con minutos >= umbral).
    """
    df = df.copy()
    df["fecha"] = df["fecha_reproduccion"].dt.date

    # Clasificar días
    dias_fin = {"Friday", "Saturday", "Sunday"}
    df["grupo"] = np.where(df["dia_semana"].isin(dias_fin),
                           "fin_de_semana", "entre_semana")

    # Minutos por fecha y grupo
    diarios = (
        df.groupby(["grupo", "fecha"])["minutos_reproducidos"]
          .sum()
          .reset_index()
    )

    if umbral_minutos_dia > 0:
        diarios = diarios[diarios["minutos_reproducidos"] >= umbral_minutos_dia]

    resumen = (
        diarios.groupby("grupo")["minutos_reproducidos"]
        .agg(
            minutos_totales="sum",
            minutos_promedio_por_dia="mean",
            dias_con_musica="count",
        )
        .reset_index()
    )

    return resumen

def minutos_por_bloque_horario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minutos totales por bloque horario con todos los bloques siempre presentes.
    """
    df = df.copy()

    condiciones = [
        df["hora"].between(0, 5),
        df["hora"].between(6, 11),
        df["hora"].between(12, 17),
        df["hora"].between(18, 23),
    ]
    bloques = ["madrugada", "manana", "tarde", "noche"]

    df["bloque_horario"] = np.select(condiciones, bloques, default="desconocido")

    tabla = (
        df.groupby("bloque_horario")["minutos_reproducidos"]
          .sum()
          .reindex(["madrugada", "manana", "tarde", "noche"], fill_value=0)
          .reset_index()
    )

    return tabla

def dia_mas_musical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve el día con más minutos reproducidos en todo el dataset,
    junto con su top artista de ese día.
    """
    df = df.copy()
    df["fecha"] = df["fecha_reproduccion"].dt.date

    # Minutos por fecha
    diarios = (
        df.groupby("fecha")["minutos_reproducidos"]
          .sum()
          .reset_index()
    )

    if diarios.empty:
        return diarios

    fila_top = diarios.loc[diarios["minutos_reproducidos"].idxmax()]
    fecha_top = fila_top["fecha"]

    # Top artista de ese día
    en_dia = df[df["fecha"] == fecha_top]
    artista_top = (
        en_dia.groupby("artista")["minutos_reproducidos"]
        .sum()
        .sort_values(ascending=False)
        .head(1)
        .reset_index()
    )

    resultado = pd.DataFrame({
        "fecha": [fecha_top],
        "minutos_reproducidos": [fila_top["minutos_reproducidos"]],
        "top_artista": [artista_top.loc[0, "artista"]],
        "minutos_top_artista": [artista_top.loc[0, "minutos_reproducidos"]],
    })

    return resultado

def racha_musical_mas_larga(
    df: pd.DataFrame,
    umbral_minutos_dia: float = 10.0
) -> dict:
    """
    Encuentra la racha más larga de días consecutivos con minutos >= umbral.
    Regresa un dict con longitud, fecha_inicio y fecha_fin.
    """
    df = df.copy()
    df["fecha"] = df["fecha_reproduccion"].dt.date

    diarios = (
        df.groupby("fecha")["minutos_reproducidos"]
          .sum()
          .reset_index()
    )

    activos = diarios[diarios["minutos_reproducidos"] >= umbral_minutos_dia].copy()
    if activos.empty:
        return {
            "longitud_racha": 0,
            "fecha_inicio": None,
            "fecha_fin": None,
        }

    activos = activos.sort_values("fecha").reset_index(drop=True)
    fechas = pd.to_datetime(activos["fecha"])

    max_len = 1
    curr_len = 1
    start_idx = 0
    best_start_idx = 0

    for i in range(1, len(fechas)):
        if (fechas[i] - fechas[i - 1]).days == 1:
            curr_len += 1
        else:
            if curr_len > max_len:
                max_len = curr_len
                best_start_idx = start_idx
            curr_len = 1
            start_idx = i

    if curr_len > max_len:
        max_len = curr_len
        best_start_idx = start_idx

    fecha_inicio = fechas.iloc[best_start_idx].date()
    fecha_fin = (fechas.iloc[best_start_idx + max_len - 1]).date()

    return {
        "longitud_racha": int(max_len),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }

def resumen_variabilidad_diaria(df: pd.DataFrame) -> dict:
    """
    Calcula resumen de minutos por día:
    - promedio
    - desviacion_estandar
    - percentiles 25, 50, 75
    - dias_altos ( > 1.5 * promedio )
    - dias_bajos ( < 0.5 * promedio )
    """
    df = df.copy()
    df["fecha"] = df["fecha_reproduccion"].dt.date

    diarios = (
        df.groupby("fecha")["minutos_reproducidos"]
          .sum()
    )

    if diarios.empty:
        return {}

    promedio = diarios.mean()
    std = diarios.std()

    p25 = diarios.quantile(0.25)
    p50 = diarios.quantile(0.50)
    p75 = diarios.quantile(0.75)

    dias_altos = int((diarios > 1.5 * promedio).sum())
    dias_bajos = int((diarios < 0.5 * promedio).sum())

    return {
        "promedio_minutos_por_dia": float(round(promedio, 2)),
        "desviacion_estandar": float(round(std, 2)) if not pd.isna(std) else 0.0,
        "percentil_25": float(round(p25, 2)),
        "percentil_50": float(round(p50, 2)),
        "percentil_75": float(round(p75, 2)),
        "dias_altos": dias_altos,
        "dias_bajos": dias_bajos,
        "total_dias": int(len(diarios)),
    }

def top_canciones(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """
    Top n canciones por minutos, incluyendo artista.
    """
    tabla = (
        df.groupby(["cancion", "artista"])["minutos_reproducidos"]
          .sum()
          .reset_index()
          .sort_values("minutos_reproducidos", ascending=False)
          .head(n)
    )
    return tabla

def artistas_emergentes_y_olvidados(df: pd.DataFrame, top_n: int = 10) -> dict:
    """
    Divide el año en dos mitades (según fecha mínima y máxima)
    y calcula minutos por artista en cada mitad.
    Regresa dos tablas:
    - emergentes: suben mas (H2 - H1 positivo)
    - olvidados: bajan mas (H2 - H1 negativo)
    """
    df = df.copy()

    fecha_min = df["fecha_reproduccion"].min()
    fecha_max = df["fecha_reproduccion"].max()
    if pd.isna(fecha_min) or pd.isna(fecha_max):
        return {"emergentes": pd.DataFrame(), "olvidados": pd.DataFrame()}

    corte = fecha_min + (fecha_max - fecha_min) / 2

    df["mitad"] = np.where(df["fecha_reproduccion"] <= corte, "H1", "H2")

    tabla = (
        df.groupby(["artista", "mitad"])["minutos_reproducidos"]
          .sum()
          .reset_index()
    )

    pivot = tabla.pivot(index="artista", columns="mitad", values="minutos_reproducidos").fillna(0)

    pivot["delta"] = pivot.get("H2", 0) - pivot.get("H1", 0)

    emergentes = (
        pivot.sort_values("delta", ascending=False)
             .head(top_n)
             .reset_index()
    )

    olvidados = (
        pivot.sort_values("delta", ascending=True)
             .head(top_n)
             .reset_index()
    )

    return {"emergentes": emergentes, "olvidados": olvidados}