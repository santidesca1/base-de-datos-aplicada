# -*- coding: utf-8 -*-
"""Funciones de consulta para el dashboard dinámico (Paso 4, estilo Power BI).

Separadas de app.py a propósito: así se pueden probar de forma independiente
(ver test_queries.py) sin levantar Streamlit, pasándole directamente el
'engine' de SQLAlchemy y los valores de los filtros.

Todas devuelven un pandas.DataFrame. Los filtros se aplican con parámetros
ligados (:anio_min, etc.), nunca con f-strings, para que los valores que
vienen de los widgets no puedan romper el SQL.
"""
import pandas as pd
from sqlalchemy import text

ANIO_MIN_DATOS = 2011
ANIO_MAX_DATOS = 2026  # 2026 incompleto (solo ene-jul)


def opciones_filtro(engine):
    """Listas para poblar los selectores del sidebar (regiones y fuentes reales de la base)."""
    regiones = pd.read_sql("SELECT nombre_region FROM dim_region ORDER BY nombre_region", engine)["nombre_region"].tolist()
    fuentes = pd.read_sql("SELECT nombre_fuente FROM dim_fuente_energia ORDER BY nombre_fuente", engine)["nombre_fuente"].tolist()
    return regiones, fuentes


def _in_clause(nombre_param, valores):
    """Arma 'IN (:p0, :p1, ...)' y el dict de parámetros para una lista de valores."""
    params = {f"{nombre_param}{i}": v for i, v in enumerate(valores)}
    clause = f"({', '.join(':' + k for k in params)})"
    return clause, params


# ---------------------------------------------------------------------
# Pregunta 1: centrales con muy poca o nula energía
# ---------------------------------------------------------------------
def q1_centrales_poca_generacion(engine, anio_min, anio_max, n_centrales=28):
    sql = text("""
        SELECT c.codigo_central, c.nombre_central,
               CASE WHEN SUM(fg.energia_generada_gwh) = 0 THEN 'Nula' ELSE 'Muy poca' END AS nivel,
               SUM(fg.energia_generada_gwh) AS gwh_acumulado,
               MIN(CASE WHEN fg.energia_generada_gwh > 0 THEN t.anio END) AS primer_anio
        FROM fact_generacion fg
        JOIN dim_central c ON c.id_central = fg.id_central
        JOIN dim_tiempo  t ON t.id_tiempo  = fg.id_tiempo
        WHERE t.anio BETWEEN :anio_min AND :anio_max
        GROUP BY c.id_central, c.codigo_central, c.nombre_central
        ORDER BY gwh_acumulado, c.codigo_central
        LIMIT :n
    """)
    return pd.read_sql(sql, engine, params={"anio_min": anio_min, "anio_max": anio_max, "n": n_centrales})


# ---------------------------------------------------------------------
# Pregunta 2: año de inicio del crecimiento sostenido
# ---------------------------------------------------------------------
def q2_variacion_anual(engine, anio_min, anio_max, umbral_pct=20.0):
    sql = text("""
        SELECT a.anio, a.gwh, p.gwh AS gwh_anterior
        FROM (SELECT t.anio, SUM(fg.energia_generada_gwh) AS gwh
              FROM fact_generacion fg JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
              WHERE t.anio BETWEEN :anio_min AND :anio_max GROUP BY t.anio) AS a
        LEFT JOIN (SELECT t.anio, SUM(fg.energia_generada_gwh) AS gwh
                   FROM fact_generacion fg JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
                   WHERE t.anio BETWEEN :anio_min AND :anio_max GROUP BY t.anio) AS p
               ON p.anio = a.anio - 1
        ORDER BY a.anio
    """)
    df = pd.read_sql(sql, engine, params={"anio_min": anio_min, "anio_max": anio_max})
    df["variacion_pct"] = (100 * (df["gwh"] / df["gwh_anterior"] - 1)).round(1)
    umbral = 1 + umbral_pct / 100
    cumple = []
    for i, row in df.iterrows():
        if pd.isna(row["gwh_anterior"]) or row["gwh"] < umbral * row["gwh_anterior"]:
            cumple.append(False)
            continue
        posteriores = df[df["anio"] > row["anio"]]
        baja_despues = (posteriores["gwh"] < posteriores["gwh_anterior"]).any()
        cumple.append(not baja_despues)
    df["cumple_criterio"] = cumple
    return df


# ---------------------------------------------------------------------
# Pregunta 3: provincias por energía acumulada
# ---------------------------------------------------------------------
def q3_provincias(engine, anio_min, anio_max, regiones=None):
    where_region, params = "", {}
    if regiones:
        clause, p = _in_clause("reg", regiones)
        where_region = f"AND r.nombre_region IN {clause}"
        params.update(p)
    sql = text(f"""
        SELECT p.nombre_provincia,
               SUM(fg.energia_generada_gwh) AS gwh_acumulado
        FROM fact_generacion fg
        JOIN dim_provincia p ON p.id_provincia = fg.id_provincia
        JOIN dim_region r    ON r.id_region = fg.id_region
        JOIN dim_tiempo t    ON t.id_tiempo = fg.id_tiempo
        WHERE t.anio BETWEEN :anio_min AND :anio_max
        {where_region}
        GROUP BY p.id_provincia, p.nombre_provincia
        ORDER BY gwh_acumulado DESC
    """)
    params.update({"anio_min": anio_min, "anio_max": anio_max})
    df = pd.read_sql(sql, engine, params=params)
    total = df["gwh_acumulado"].sum()
    df["pct_del_total"] = (100 * df["gwh_acumulado"] / total).round(2) if total else 0
    return df


# ---------------------------------------------------------------------
# Pregunta 4: estacionalidad por fuente (mismas máquinas los 12 meses)
# ---------------------------------------------------------------------
def q4_estacionalidad(engine, anio_min, anio_max, fuentes=None):
    where_fuente, params = "", {}
    if fuentes:
        clause, p = _in_clause("fte", fuentes)
        where_fuente = f"AND f.nombre_fuente IN {clause}"
        params.update(p)
    sql = text(f"""
        SELECT m.nombre_fuente, m.mes, ROUND(100 * AVG(m.gwh / a.gwh_anio), 2) AS pct_del_anio
        FROM (SELECT f.nombre_fuente, t.anio, t.mes, SUM(fg.energia_generada_gwh) AS gwh
              FROM fact_generacion fg
              JOIN dim_tiempo t          ON t.id_tiempo = fg.id_tiempo
              JOIN dim_fuente_energia f  ON f.id_fuente = fg.id_fuente
              JOIN (SELECT fg2.id_maquina, t2.anio FROM fact_generacion fg2
                    JOIN dim_tiempo t2 ON t2.id_tiempo = fg2.id_tiempo
                    GROUP BY fg2.id_maquina, t2.anio HAVING COUNT(*) = 12) AS mc
                ON mc.id_maquina = fg.id_maquina AND mc.anio = t.anio
              WHERE t.anio BETWEEN :anio_min AND :anio_max {where_fuente}
              GROUP BY f.nombre_fuente, t.anio, t.mes) AS m
        JOIN (SELECT f.nombre_fuente, t.anio, SUM(fg.energia_generada_gwh) AS gwh_anio
              FROM fact_generacion fg
              JOIN dim_tiempo t          ON t.id_tiempo = fg.id_tiempo
              JOIN dim_fuente_energia f  ON f.id_fuente = fg.id_fuente
              JOIN (SELECT fg2.id_maquina, t2.anio FROM fact_generacion fg2
                    JOIN dim_tiempo t2 ON t2.id_tiempo = fg2.id_tiempo
                    GROUP BY fg2.id_maquina, t2.anio HAVING COUNT(*) = 12) AS mc
                ON mc.id_maquina = fg.id_maquina AND mc.anio = t.anio
              WHERE t.anio BETWEEN :anio_min AND :anio_max {where_fuente}
              GROUP BY f.nombre_fuente, t.anio) AS a
          ON a.nombre_fuente = m.nombre_fuente AND a.anio = m.anio
        WHERE a.gwh_anio > 0
        GROUP BY m.nombre_fuente, m.mes
        ORDER BY m.nombre_fuente, m.mes
    """)
    params.update({"anio_min": anio_min, "anio_max": anio_max})
    return pd.read_sql(sql, engine, params=params)


# ---------------------------------------------------------------------
# Pregunta 5: centrales nuevas por año y región
# ---------------------------------------------------------------------
def q5_centrales_nuevas(engine, anio_min, anio_max, regiones=None):
    where_region, params = "", {}
    if regiones:
        clause, p = _in_clause("reg", regiones)
        where_region = f"AND r.nombre_region IN {clause}"
        params.update(p)
    sql = text(f"""
        SELECT a.anio_alta, r.nombre_region, COUNT(DISTINCT a.id_central) AS centrales_nuevas
        FROM (SELECT fg.id_central, fg.id_region, MIN(t.fecha_mes) AS primer_registro,
                     MIN(CASE WHEN fg.energia_generada_gwh > 0 THEN t.anio END) AS anio_alta
              FROM fact_generacion fg JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
              GROUP BY fg.id_central, fg.id_region) AS a
        JOIN dim_region r ON r.id_region = a.id_region
        WHERE a.primer_registro > (SELECT MIN(fecha_mes) FROM dim_tiempo)
          AND a.anio_alta IS NOT NULL
          AND a.anio_alta BETWEEN :anio_min AND :anio_max
          {where_region}
        GROUP BY a.anio_alta, r.nombre_region
        ORDER BY a.anio_alta, centrales_nuevas DESC
    """)
    params.update({"anio_min": anio_min, "anio_max": anio_max})
    return pd.read_sql(sql, engine, params=params)


# ---------------------------------------------------------------------
# Pregunta 6: evolución de fuentes entre dos años
# ---------------------------------------------------------------------
def q6_evolucion_fuentes(engine, anio_inicio, anio_fin):
    sql = text("""
        SELECT f.nombre_fuente,
               SUM(CASE WHEN t.anio = :anio_inicio THEN fg.energia_generada_gwh ELSE 0 END) AS gwh_inicio,
               SUM(CASE WHEN t.anio = :anio_fin    THEN fg.energia_generada_gwh ELSE 0 END) AS gwh_fin,
               SUM(CASE WHEN t.anio = :anio_fin    THEN fg.energia_generada_gwh ELSE 0 END)
             - SUM(CASE WHEN t.anio = :anio_inicio THEN fg.energia_generada_gwh ELSE 0 END) AS variacion_gwh
        FROM fact_generacion fg
        JOIN dim_tiempo t          ON t.id_tiempo = fg.id_tiempo
        JOIN dim_fuente_energia f  ON f.id_fuente = fg.id_fuente
        WHERE t.anio IN (:anio_inicio, :anio_fin)
        GROUP BY f.id_fuente, f.nombre_fuente
        ORDER BY variacion_gwh DESC
    """)
    return pd.read_sql(sql, engine, params={"anio_inicio": anio_inicio, "anio_fin": anio_fin})


# ---------------------------------------------------------------------
# Pregunta 7: combinación región + fuente más productiva
# ---------------------------------------------------------------------
def q7_region_fuente(engine, anio_min, anio_max, top_n=15, regiones=None, fuentes=None):
    where_extra, params = "", {}
    if regiones:
        clause, p = _in_clause("reg", regiones)
        where_extra += f" AND r.nombre_region IN {clause}"
        params.update(p)
    if fuentes:
        clause, p = _in_clause("fte", fuentes)
        where_extra += f" AND f.nombre_fuente IN {clause}"
        params.update(p)
    sql = text(f"""
        SELECT r.nombre_region, f.nombre_fuente,
               SUM(fg.energia_generada_gwh) AS gwh_acumulado
        FROM fact_generacion fg
        JOIN dim_region r          ON r.id_region = fg.id_region
        JOIN dim_fuente_energia f  ON f.id_fuente = fg.id_fuente
        JOIN dim_tiempo t          ON t.id_tiempo = fg.id_tiempo
        WHERE t.anio BETWEEN :anio_min AND :anio_max
        {where_extra}
        GROUP BY r.id_region, r.nombre_region, f.id_fuente, f.nombre_fuente
        ORDER BY gwh_acumulado DESC
        LIMIT :top_n
    """)
    params.update({"anio_min": anio_min, "anio_max": anio_max, "top_n": top_n})
    return pd.read_sql(sql, engine, params=params)


# ---------------------------------------------------------------------
# Pregunta 8: región líder por año
# ---------------------------------------------------------------------
def q8_region_lider_por_anio(engine, anio_min, anio_max):
    sql = text("""
        SELECT v.anio, v.nombre_region, v.gwh
        FROM (SELECT t.anio, r.nombre_region, SUM(fg.energia_generada_gwh) AS gwh
              FROM fact_generacion fg
              JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
              JOIN dim_region r ON r.id_region = fg.id_region
              WHERE t.anio BETWEEN :anio_min AND :anio_max
              GROUP BY t.anio, r.id_region, r.nombre_region) AS v
        WHERE v.gwh = (SELECT MAX(w.gwh) FROM
                        (SELECT t.anio, r.nombre_region, SUM(fg.energia_generada_gwh) AS gwh
                         FROM fact_generacion fg
                         JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
                         JOIN dim_region r ON r.id_region = fg.id_region
                         WHERE t.anio BETWEEN :anio_min AND :anio_max
                         GROUP BY t.anio, r.id_region, r.nombre_region) AS w
                       WHERE w.anio = v.anio)
        ORDER BY v.anio
    """)
    df = pd.read_sql(sql, engine, params={"anio_min": anio_min, "anio_max": anio_max})
    return df.rename(columns={"nombre_region": "region_lider"})


# ---------------------------------------------------------------------
# Pregunta 9: central con mayor energía acumulada por región
# ---------------------------------------------------------------------
def q9_central_lider_por_region(engine, anio_min, anio_max, regiones=None):
    where_region, params = "", {}
    if regiones:
        clause, p = _in_clause("reg", regiones)
        where_region = f"WHERE v.nombre_region IN {clause}"
        params.update(p)
    sql = text(f"""
        SELECT v.nombre_region, v.codigo_central, v.nombre_central, v.gwh_acumulado
        FROM (SELECT r.nombre_region, c.codigo_central, c.nombre_central,
                     SUM(fg.energia_generada_gwh) AS gwh_acumulado
              FROM fact_generacion fg
              JOIN dim_region r  ON r.id_region = fg.id_region
              JOIN dim_central c ON c.id_central = fg.id_central
              JOIN dim_tiempo t  ON t.id_tiempo = fg.id_tiempo
              WHERE t.anio BETWEEN :anio_min AND :anio_max
              GROUP BY r.id_region, r.nombre_region, c.id_central, c.codigo_central, c.nombre_central) AS v
        {where_region}
        {"AND" if where_region else "WHERE"} v.gwh_acumulado = (
            SELECT MAX(w.gwh_acumulado) FROM
            (SELECT r.nombre_region, c.id_central, SUM(fg.energia_generada_gwh) AS gwh_acumulado
             FROM fact_generacion fg
             JOIN dim_region r  ON r.id_region = fg.id_region
             JOIN dim_central c ON c.id_central = fg.id_central
             JOIN dim_tiempo t  ON t.id_tiempo = fg.id_tiempo
             WHERE t.anio BETWEEN :anio_min AND :anio_max
             GROUP BY r.id_region, c.id_central) AS w
            WHERE w.nombre_region = v.nombre_region)
        ORDER BY v.gwh_acumulado DESC
    """)
    params.update({"anio_min": anio_min, "anio_max": anio_max})
    return pd.read_sql(sql, engine, params=params)
