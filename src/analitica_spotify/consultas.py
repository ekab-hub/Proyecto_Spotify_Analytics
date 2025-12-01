import pandas as pd


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
