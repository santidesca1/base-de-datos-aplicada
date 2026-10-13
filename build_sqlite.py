# -*- coding: utf-8 -*-
"""Arma energia.db (SQLite) a partir de base_de_datos.csv.

Es la MISMA lógica (extract -> transform -> load -> verify) que
etl_energia_renovable.ipynb usa contra MySQL, pero apuntada a un archivo
SQLite para no necesitar un servidor de base de datos corriendo en la nube:
el archivo .db resultante se sube tal cual al repositorio y la app lo lee
directamente. Las cifras de control son las mismas que entrega_modelo_logico.sql.
"""
import sys

import pandas as pd
from sqlalchemy import create_engine

CSV_PATH = "base_de_datos.csv"
SCHEMA_PATH = "schema_sqlite.sql"
DB_PATH = "energia.db"

NOMBRE_MES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio",
              8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
ESTACION = {12: "Verano", 1: "Verano", 2: "Verano", 3: "Otoño", 4: "Otoño", 5: "Otoño",
            6: "Invierno", 7: "Invierno", 8: "Invierno", 9: "Primavera", 10: "Primavera", 11: "Primavera"}

MAPEO_COLUMNAS = {
    "AÑO": "anio", "CENTRAL": "central", "CENTRAL DESCRIPCIÓN": "central_descripcion",
    "MAQUINA": "maquina", "FUENTE DE ENERGÍA": "fuente_energia", "REGIÓN": "region",
    "PROVINCIA": "provincia", "MES": "mes", "ENERGÍA GENERADA [GWh]": "energia_generada_gwh",
    "Nueva Generación": "nueva_generacion",
}

ESPERADO = {"dim_tiempo": 187, "dim_central": 281, "dim_maquina": 289, "dim_fuente_energia": 6,
            "dim_region": 9, "dim_provincia": 21, "dim_programa": 7, "fact_generacion": 22592}
TOTAL_ESPERADO_GWH = 163315.980622


def cargar_dimension(engine, tabla, df_dim):
    df_dim.to_sql(tabla, engine, if_exists="append", index=False)
    return pd.read_sql(f"SELECT * FROM {tabla}", engine)


def main():
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # recarga completa, igual que el DROP DATABASE del ETL contra MySQL

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = f.read()
    with engine.begin() as conn:
        for stmt in [s.strip() for s in schema.split(";") if s.strip() and not s.strip().startswith("--")]:
            conn.exec_driver_sql(stmt)

    # 1. Extract (igual que el notebook: todo como texto, sin tocar valores)
    df_raw = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df_raw.columns = [c.strip() for c in df_raw.columns]
    assert set(df_raw.columns) == set(MAPEO_COLUMNAS), f"Columnas inesperadas: {list(df_raw.columns)}"
    df = df_raw.rename(columns=MAPEO_COLUMNAS)
    print(f"Leídas {len(df)} filas del CSV original.")

    # 3. Transform (mismas reglas del Paso 2/3: trim, tipos, excluir Demanda MEM, deduplicar, unificar nombres)
    cols_texto = [c for c in df.columns]
    for c in cols_texto:
        df[c] = df[c].str.strip().str.replace(r"\s+", " ", regex=True)
    df["energia_generada_gwh"] = pd.to_numeric(df["energia_generada_gwh"]).round(6)
    df["fecha_mes"] = pd.to_datetime(df["mes"], format="%Y-%m-%d")

    generacion = df[df["central"] != "Demanda MEM"].copy()

    generacion = generacion.sort_values(["central", "maquina", "fecha_mes", "energia_generada_gwh"],
                                        ascending=[True, True, True, False])
    es_duplicada = generacion.duplicated(["central", "maquina", "fecha_mes"], keep="first")
    n_dup = int(es_duplicada.sum())
    generacion = generacion[~es_duplicada].copy()

    orden = generacion.sort_values("fecha_mes")
    nombre_central = (orden.drop_duplicates(["central", "central_descripcion"])
                      .groupby("central")["central_descripcion"].agg(" / ".join))
    generacion["nombre_central"] = generacion["central"].map(nombre_central)

    print(f"Generación limpia: {len(generacion)} filas (se excluyeron {int((df['central'] == 'Demanda MEM').sum())} "
          f"de Demanda MEM y se deduplicaron {n_dup} filas repetidas).")

    # 4. Load — dimensiones primero (claves subrogadas las genera SQLite con AUTOINCREMENT)
    meses = pd.Series(sorted(set(generacion["fecha_mes"])))
    d_tiempo = pd.DataFrame({
        "fecha_mes": meses.dt.strftime("%Y-%m-%d"), "anio": meses.dt.year, "mes": meses.dt.month,
        "nombre_mes": meses.dt.month.map(NOMBRE_MES), "estacion": meses.dt.month.map(ESTACION),
    })
    dim_tiempo = cargar_dimension(engine, "dim_tiempo", d_tiempo)

    d_central = (generacion[["central", "nombre_central"]].drop_duplicates().sort_values("central")
                 .rename(columns={"central": "codigo_central"}))
    assert d_central["codigo_central"].is_unique
    dim_central = cargar_dimension(engine, "dim_central", d_central)

    dim_maquina = cargar_dimension(engine, "dim_maquina",
        pd.DataFrame({"codigo_maquina": sorted(generacion["maquina"].unique())}))
    dim_fuente = cargar_dimension(engine, "dim_fuente_energia",
        pd.DataFrame({"nombre_fuente": sorted(generacion["fuente_energia"].unique())}))
    dim_region = cargar_dimension(engine, "dim_region",
        pd.DataFrame({"nombre_region": sorted(generacion["region"].unique())}))
    dim_provincia = cargar_dimension(engine, "dim_provincia",
        pd.DataFrame({"nombre_provincia": sorted(generacion["provincia"].unique())}))
    dim_programa = cargar_dimension(engine, "dim_programa",
        pd.DataFrame({"nombre_programa": sorted(generacion["nueva_generacion"].unique())}))

    fact = (generacion
            .merge(dim_tiempo[["id_tiempo", "fecha_mes"]], left_on=generacion["fecha_mes"].dt.strftime("%Y-%m-%d"),
                   right_on="fecha_mes", how="left")
            .merge(dim_central[["id_central", "codigo_central"]], left_on="central", right_on="codigo_central", how="left")
            .merge(dim_maquina, left_on="maquina", right_on="codigo_maquina", how="left")
            .merge(dim_fuente, left_on="fuente_energia", right_on="nombre_fuente", how="left")
            .merge(dim_region, left_on="region", right_on="nombre_region", how="left")
            .merge(dim_provincia, left_on="provincia", right_on="nombre_provincia", how="left")
            .merge(dim_programa, left_on="nueva_generacion", right_on="nombre_programa", how="left"))

    claves = ["id_tiempo", "id_central", "id_maquina", "id_fuente", "id_region", "id_provincia", "id_programa"]
    sin_resolver = int(fact[claves].isna().any(axis=1).sum())
    assert sin_resolver == 0, f"{sin_resolver} filas sin alguna dimensión resuelta"
    assert len(fact) == len(generacion), "El merge no debe multiplicar ni perder filas"

    fact_generacion = fact[claves + ["energia_generada_gwh"]].astype({k: "int64" for k in claves})
    fact_generacion.to_sql("fact_generacion", engine, if_exists="append", index=False)

    # 5. Verificación (mismas cifras de control que entrega_modelo_logico.sql)
    ok = True
    for tabla, esperado in ESPERADO.items():
        real = int(pd.read_sql(f"SELECT COUNT(*) AS n FROM {tabla}", engine)["n"][0])
        estado = "OK" if real == esperado else "DIFERENCIA"
        if real != esperado:
            ok = False
        print(f"  {tabla}: {real} filas (esperado {esperado}) -> {estado}")

    total_real = float(pd.read_sql("SELECT SUM(energia_generada_gwh) AS s FROM fact_generacion", engine)["s"][0])
    diff = round(total_real - TOTAL_ESPERADO_GWH, 6)
    print(f"  SUM(energia_generada_gwh): {total_real:.6f} (esperado {TOTAL_ESPERADO_GWH}) -> diferencia {diff}")
    if abs(diff) > 1e-4:
        ok = False

    print("\nRESULTADO:", "OK — energia.db listo." if ok else "REVISAR — algo no coincide con lo esperado.")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
