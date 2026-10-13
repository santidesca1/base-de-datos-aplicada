# -*- coding: utf-8 -*-
"""Proyecto Final — Metodología HEFESTO — Generación de energía renovable en el MEM.

App de una sola pieza para la presentación: una pestaña por cada paso de
HEFESTO (documentación real de la entrega) y, al final, el dashboard en
vivo con las 9 preguntas de negocio del Paso 1, contra el modelo estrella
cargado en energia.db (SQLite, embebido en el repo — no depende de un
servidor MySQL corriendo en la nube).
"""
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

import queries as q

st.set_page_config(page_title="HEFESTO — Energía Renovable MEM", layout="wide", page_icon="⚡")

ALUMNOS = "Lucas Emiliano Galleguillo (2510484), Ignacio Albizuri (2520657), Santiago Descalzo Glamuzina (2500352), Joaquin Ian Garcia Sequeira (2534906)"
PROFESORES = "Julio Marcelo Gutierrez, Gaston Emilio Severina"

st.title("⚡ Generación de energía renovable en el MEM")
st.caption("Proyecto Final — Metodología HEFESTO · Base de Datos Aplicada · UCC")
st.caption(f"**Alumnos:** {ALUMNOS}  \n**Profesores:** {PROFESORES}")

tab1, tab2, tab3, tab4, tab_dash = st.tabs([
    "Paso 1 · Requerimientos", "Paso 2 · Fuente de Datos", "Paso 3 · Modelo Lógico",
    "Paso 4 · Integración de Datos", "📊 Dashboard",
])

# =====================================================================
# PASO 1 — Análisis de Requerimientos
# =====================================================================
with tab1:
    st.header("Paso 1 — Análisis de Requerimientos")

    st.subheader("1. Presentación del tema y la fuente de datos")
    st.markdown("""
**Tema elegido:** Generación de energía eléctrica a partir de fuentes renovables en el
Mercado Eléctrico Mayorista (MEM) de Argentina.

**Proceso de negocio:** cada mes, cada máquina de generación renovable habilitada en el
MEM reporta la cantidad de energía que generó (en GWh). Este reporte se repite
mensualmente para cada central y cada máquina desde 2011 hasta la actualidad, lo que
constituye un proceso de negocio recurrente que genera un registro histórico de hechos
analizables (generación mensual por central).

**Fuente:** CAMMESA (Compañía Administradora del Mercado Mayorista Eléctrico S.A.),
organismo oficial que administra el despacho eléctrico en Argentina. Archivo descargado
el 9 de septiembre de 2026, con el detalle mensual de energía generada por cada central y
máquina renovable del país, desde enero de 2011 hasta julio de 2026.

**Objetivo:** analizar el comportamiento de la generación de energía eléctrica proveniente
de fuentes renovables en Argentina entre 2011 y 2026, con el fin de identificar patrones de
crecimiento, distribución geográfica, estacionalidad y participación tecnológica dentro del
segmento renovable del MEM.
""")

    st.subheader("2.a) Preguntas de negocio")
    preguntas = [
        "¿Qué centrales generaron muy poca/nula energía?",
        "¿En qué año las energías renovables comenzaron a crecer?",
        "¿Qué provincias producen la mayor/menor cantidad de energía renovable?",
        "¿En qué meses del año generan más las fuentes solares y eólicas vs. las hidro/biomasa?",
        "¿Cuántas centrales nuevas se sumaron cada año, por región?",
        "¿Cuáles son las formas de energía que más/menos se desarrollaron en los últimos 10 años?",
        "¿Qué combinación región + fuente es la más productiva?",
        "¿Qué región fue la que más generó en cada año?",
        "¿Cuál es la central con mayor energía generada acumulada de cada región?",
    ]
    for i, p in enumerate(preguntas, start=1):
        st.markdown(f"**{i}.** {p}")

    st.subheader("2.b) Indicadores y perspectivas")
    col_ind, col_persp = st.columns(2)
    with col_ind:
        st.markdown("**Indicadores**")
        st.markdown("""
- Promedio del total de energía generada
- Suma total de energía generada
- % Participación renovable s/ demanda total (Demanda MEM)
- % Variación interanual de la generación
- % Participación de cada fuente s/ total generado
- Cantidad total de centrales
""")
    with col_persp:
        st.markdown("**Perspectivas**")
        st.markdown("""
- Por provincia / por región
- Por fuente de energía renovable
- Por tiempo (año, mes, estación)
- Por central / por máquina
- Por programa o contrato
- Por habitantes *(no disponible en el dataset)*
""")

    st.subheader("2.c) Modelo Conceptual")
    st.caption("Cada perspectiva se conecta de forma independiente al hecho central — no hay relaciones entre perspectivas.")
    if os.path.exists("modelo_conceptual_hefesto.png"):
        st.image("modelo_conceptual_hefesto.png", use_container_width=True)

# =====================================================================
# PASO 2 — Análisis de la Fuente de Datos
# =====================================================================
with tab2:
    st.header("Paso 2 — Análisis de la Fuente de Datos (OLTP)")
    st.caption("Archivo fuente: 22.784 filas × 10 columnas · Período: enero 2011 a julio 2026")

    st.subheader("Perfil de columnas del archivo fuente")
    perfil = pd.DataFrame([
        ("AÑO", "Año calendario del registro", "2011 a 2026 (16 valores)", "Entero"),
        ("CENTRAL", "Código corto de la central generadora", "283 valores únicos + fila especial \"Demanda MEM\"", "Texto"),
        ("CENTRAL DESCRIPCIÓN", "Nombre descriptivo de la central", "280 valores únicos", "Texto"),
        ("MAQUINA", "Código de la máquina dentro de la central", "291 valores únicos", "Texto"),
        ("FUENTE DE ENERGÍA", "Tipo de fuente renovable", "BIODIESEL, HIDRO ≤50MW, EOLICO, BIOMASA, SOLAR, BIOGAS", "Texto categórico"),
        ("REGIÓN", "Región eléctrica del país", "10 valores (BUENOS AIRES, CUYO, COMAHUE, ...)", "Texto categórico"),
        ("PROVINCIA", "Provincia donde está la central", "21 provincias + placeholder", "Texto categórico"),
        ("MES", "Primer día del mes que reporta", "AAAA-MM-01, 187 valores", "Fecha"),
        ("ENERGÍA GENERADA [GWh]", "Energía generada por esa máquina en ese mes", "0 a 167,82 GWh (renovables)", "Decimal"),
        ("Nueva Generación", "Programa por el que ingresó al mercado", "Resto, RENOVAR, MATER, Renovar 202, SPOT MATER, ...", "Texto categórico"),
    ], columns=["Columna", "Descripción", "Valores posibles", "Tipo de dato"])
    st.dataframe(perfil, use_container_width=True, hide_index=True)

    st.subheader("a) Conformar indicadores")
    indicadores = pd.DataFrame([
        ("Promedio del Total de Energía Generada", "AVG", "Aditivo"),
        ("Suma Total de Energía Generada", "SUM", "Aditivo"),
        ("% Participación Renovable s/ Demanda Total", "SUM + división", "Derivado, no aditivo"),
        ("% Variación Interanual de la Generación", "SUM + división", "Derivado, no aditivo"),
        ("% Participación de cada Fuente s/ Total Generado", "SUM + división", "Derivado, no aditivo"),
        ("Cantidad Total de Centrales", "COUNT DISTINCT", "—"),
    ], columns=["Indicador", "Función de agregación", "Tipo"])
    st.dataframe(indicadores, use_container_width=True, hide_index=True)

    st.subheader("c) Nivel de granularidad")
    st.markdown("""
**Grano del hecho:** una fila = una máquina, dentro de una central, en un mes —
la clave natural del hecho es **CENTRAL + MAQUINA + MES**. Es el nivel más fino
disponible en la fuente (no hay reportes diarios ni horarios).

**Inconsistencias detectadas y su solución:**
- Espacios en blanco inconsistentes en las filas placeholder de "Demanda MEM"
  (ej. `"Demanda MEM"` vs `" Demanda MEM"`) → se corrige con `TRIM()` al cargar
  las dimensiones.
- 5 combinaciones CENTRAL + MAQUINA + MES repetidas (10 de las 22.784 filas),
  con un valor en 0 y otro con el dato real → se deduplica quedándose con el
  **valor más alto** de energía generada.
""")

    st.subheader("d) Modelo Conceptual ampliado")
    st.caption("Mismo modelo del Paso 1, agregando debajo de cada perspectiva las columnas reales que la representan.")
    if os.path.exists("modelo_conceptual_hefesto_v2.png"):
        st.image("modelo_conceptual_hefesto_v2.png", use_container_width=True)

# =====================================================================
# PASO 3 — Modelo Lógico del DW
# =====================================================================
with tab3:
    st.header("Paso 3 — Modelo Lógico del Data Warehouse")
    st.markdown("""
**Esquema elegido:** estrella (*star schema*) — 1 tabla de hechos (`fact_generacion`) y
7 tablas de dimensión, todas conectadas directamente al hecho, sin niveles intermedios.
""")

    col_dim, col_fact = st.columns([3, 2])
    with col_dim:
        st.markdown("**Dimensiones**")
        st.markdown("""
- `dim_tiempo` — fecha, año, mes, nombre del mes, estación (derivada)
- `dim_central` — código y nombre de la central
- `dim_maquina` — código de la máquina
- `dim_fuente_energia` — tipo de fuente renovable
- `dim_region` — región eléctrica
- `dim_provincia` — provincia
- `dim_programa` — programa/contrato de ingreso al mercado
""")
    with col_fact:
        st.markdown("**Tabla de hechos**")
        st.markdown("""
`fact_generacion`
- Clave: `id_tiempo + id_central + id_maquina`
- Medida aditiva: `energia_generada_gwh`
- 7 claves foráneas, una por dimensión
""")

    st.subheader("DDL (entrega_modelo_logico.sql)")
    st.caption("Motor original: MySQL 8. El dashboard de abajo corre contra una versión SQLite del mismo modelo, para poder publicarlo sin un servidor de base de datos aparte.")
    if os.path.exists("entrega_modelo_logico.sql"):
        with open("entrega_modelo_logico.sql", encoding="utf-8") as f:
            st.code(f.read(), language="sql", line_numbers=True)

# =====================================================================
# PASO 4 — Integración de Datos
# =====================================================================
with tab4:
    st.header("Paso 4 — Integración de Datos (ETL)")
    st.markdown("""
Proceso **Extract → Transform → Load**, implementado en `etl_energia_renovable.ipynb`
con pandas y SQLAlchemy.
""")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("1. Preparación", "DDL del Paso 3")
    c2.metric("2. Extract", "22.784 filas")
    c3.metric("3. Calidad", "7 chequeos")
    c4.metric("4. Transform", "22.592 filas")
    c5.metric("5. Load + Verify", "0 diferencias")

    st.markdown("""
**1. Extract:** el CSV se lee tal cual (todo como texto, sin tocar valores) a una tabla
intermedia, para tener una copia fiel y poder auditar qué se transforma después.

**2. Calidad de datos:** sobre esa copia se chequean vacíos, valores no numéricos o
negativos, fechas inválidas, espacios de más, duplicados de la clave del grano
(CENTRAL + MAQUINA + MES), y consistencia entre columnas (una máquina siempre
pertenece a la misma central/fuente/región/provincia).

**3. Transform:** se aplican las reglas que surgieron de esos chequeos — TRIM en todo
el texto, conversión de tipos, **exclusión de las 187 filas "Demanda MEM"** (no son
generación de una central, quedan fuera del grano), **deduplicación** de las 5
combinaciones repetidas quedándose con el valor más alto, y se derivan año/mes/estación
de la fecha.

**4. Load:** primero se cargan las 7 dimensiones (generan sus claves subrogadas), y
después, cruzando (`merge`) los datos limpios contra cada dimensión, se arma y carga
`fact_generacion`.

**5. Verificación:** se concilia que cada fila del archivo original haya terminado en el
hecho o en los descartes (sin perderse ni duplicarse), y se recalculan los totales de
forma **independiente** desde el CSV para contrastarlos contra lo cargado.
""")

    st.success(
        "Resultado verificado: 22.592 filas cargadas en `fact_generacion` "
        "(187 descartadas por ser \"Demanda MEM\" + 5 duplicados), "
        "SUM(energía generada) = 163.315,980622 GWh, diferencia contra el cálculo "
        "independiente = 0."
    )

# =====================================================================
# DASHBOARD — Paso 4, las 9 preguntas de negocio del Paso 1
# =====================================================================
with tab_dash:

    @st.cache_resource
    def get_engine():
        db_path = os.getenv("ENERGIA_DB_PATH", "energia.db")
        return create_engine(f"sqlite:///{db_path}")

    try:
        engine = get_engine()
        with engine.begin() as conn:
            total_filas = conn.exec_driver_sql("SELECT COUNT(*) FROM fact_generacion").scalar()
    except Exception as e:
        st.error(
            "No se pudo abrir `energia.db`. Confirmá que el archivo esté commiteado junto "
            "al resto de los archivos del repositorio.\n\n"
            f"Detalle técnico: {e}"
        )
        st.stop()

    regiones_todas, fuentes_todas = q.opciones_filtro(engine)

    st.sidebar.title("⚡ Filtros del Dashboard")
    st.sidebar.caption(f"{total_filas:,} filas en fact_generacion".replace(",", "."))

    anio_min, anio_max = st.sidebar.slider(
        "Rango de años (acumulados / por año, según el gráfico)",
        min_value=q.ANIO_MIN_DATOS, max_value=q.ANIO_MAX_DATOS,
        value=(q.ANIO_MIN_DATOS, q.ANIO_MAX_DATOS),
    )
    regiones_sel = st.sidebar.multiselect("Región", regiones_todas, default=regiones_todas)
    fuentes_sel = st.sidebar.multiselect("Fuente de energía", fuentes_todas, default=fuentes_todas)
    st.sidebar.caption("No todos los gráficos usan los tres filtros — cada pestaña aclara cuáles le aplican.")

    regiones_arg = regiones_sel if regiones_sel and len(regiones_sel) < len(regiones_todas) else None
    fuentes_arg = fuentes_sel if fuentes_sel and len(fuentes_sel) < len(fuentes_todas) else None

    st.subheader("Las 9 preguntas de negocio, en vivo contra el modelo estrella")

    sub_tabs = st.tabs([f"P{i}" for i in range(1, 10)])

    with sub_tabs[0]:
        st.markdown("**1. ¿Qué centrales generaron muy poca o nula energía?**")
        n = st.slider("Cantidad de centrales a mostrar", 5, 60, 28, key="n_q1")
        df1 = q.q1_centrales_poca_generacion(engine, anio_min, anio_max, n)
        if df1.empty:
            st.info("No hay centrales en el rango de años elegido.")
        else:
            fig = px.bar(df1.sort_values("gwh_acumulado", ascending=True),
                         x="gwh_acumulado", y="codigo_central", color="nivel", orientation="h",
                         hover_data=["nombre_central", "primer_anio"],
                         color_discrete_map={"Nula": "#d62728", "Muy poca": "#1f77b4"},
                         labels={"gwh_acumulado": "GWh acumulados", "codigo_central": "Central", "nivel": "Nivel"})
            fig.update_layout(height=max(400, 18 * len(df1)))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df1, use_container_width=True, hide_index=True)

    with sub_tabs[1]:
        st.markdown("**2. ¿En qué año las energías renovables comenzaron a crecer?**")
        umbral = st.slider("Umbral de crecimiento anual para 'inicio sostenido' (%)", 5, 50, 20, key="umbral_q2")
        df2 = q.q2_variacion_anual(engine, anio_min, min(anio_max, 2025), umbral_pct=umbral)
        inicio = df2.loc[df2["cumple_criterio"], "anio"].min() if df2["cumple_criterio"].any() else None
        c1, c2 = st.columns(2)
        with c1:
            fig_gwh = px.bar(df2, x="anio", y="gwh", labels={"anio": "Año", "gwh": "GWh"}, title="Generación anual")
            st.plotly_chart(fig_gwh, use_container_width=True)
        with c2:
            colores = df2["cumple_criterio"].map({True: "#ff7f0e", False: "#1f77b4"})
            fig_var = go.Figure(go.Bar(x=df2["anio"], y=df2["variacion_pct"], marker_color=colores))
            fig_var.add_hline(y=umbral, line_dash="dash", annotation_text=f"umbral {umbral}%")
            fig_var.update_layout(title="Variación anual (%) — naranja = cumple el criterio", xaxis_title="Año", yaxis_title="%")
            st.plotly_chart(fig_var, use_container_width=True)
        if inicio:
            st.success(f"Con un umbral de {umbral}%, el crecimiento sostenido empieza en **{int(inicio)}**.")
        else:
            st.warning("Ningún año cumple ese umbral con crecimiento sostenido hasta el final del rango.")
        st.dataframe(df2, use_container_width=True, hide_index=True)

    with sub_tabs[2]:
        st.markdown("**3. ¿Qué provincias producen la mayor y la menor cantidad de energía renovable?**")
        df3 = q.q3_provincias(engine, anio_min, anio_max, regiones=regiones_arg)
        if df3.empty:
            st.info("No hay datos para esos filtros.")
        else:
            fig = px.bar(df3.sort_values("gwh_acumulado", ascending=True),
                         x="gwh_acumulado", y="nombre_provincia", orientation="h",
                         hover_data=["pct_del_total"],
                         labels={"gwh_acumulado": "GWh acumulados", "nombre_provincia": "Provincia"})
            fig.update_layout(height=max(400, 22 * len(df3)))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df3, use_container_width=True, hide_index=True)

    with sub_tabs[3]:
        st.markdown("**4. ¿En qué meses del año generan más las fuentes solar y eólica, frente a hidro y biomasa?**")
        df4 = q.q4_estacionalidad(engine, anio_min, anio_max, fuentes=fuentes_arg)
        if df4.empty:
            st.info("No hay datos para esos filtros (probá un rango con al menos un año completo).")
        else:
            MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                     7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
            df4 = df4.copy()
            df4["mes_nombre"] = df4["mes"].map(MESES)
            fig = px.line(df4, x="mes", y="pct_del_anio", color="nombre_fuente", markers=True,
                          labels={"mes": "Mes", "pct_del_anio": "% de la generación anual", "nombre_fuente": "Fuente"})
            fig.update_xaxes(tickmode="array", tickvals=list(MESES.keys()), ticktext=list(MESES.values()))
            fig.add_hline(y=100 / 12, line_dash="dash", annotation_text="reparto parejo (8,33%)")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df4, use_container_width=True, hide_index=True)

    with sub_tabs[4]:
        st.markdown("**5. ¿Cuántas centrales nuevas se sumaron cada año, por región?**")
        df5 = q.q5_centrales_nuevas(engine, anio_min, anio_max, regiones=regiones_arg)
        if df5.empty:
            st.info("No hay altas de centrales para esos filtros.")
        else:
            fig = px.bar(df5, x="anio_alta", y="centrales_nuevas", color="nombre_region",
                        labels={"anio_alta": "Año de alta", "centrales_nuevas": "Centrales nuevas", "nombre_region": "Región"})
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Total de centrales nuevas en el rango filtrado", int(df5["centrales_nuevas"].sum()))
            st.dataframe(df5, use_container_width=True, hide_index=True)

    with sub_tabs[5]:
        st.markdown("**6. ¿Qué formas de energía se desarrollaron más y cuáles menos entre dos años?**")
        c1, c2 = st.columns(2)
        anio_a = c1.number_input("Año base", min_value=q.ANIO_MIN_DATOS, max_value=q.ANIO_MAX_DATOS, value=2016, key="q6_a")
        anio_b = c2.number_input("Año de comparación", min_value=q.ANIO_MIN_DATOS, max_value=q.ANIO_MAX_DATOS, value=2025, key="q6_b")
        df6 = q.q6_evolucion_fuentes(engine, int(anio_a), int(anio_b))
        fig = go.Figure()
        fig.add_bar(x=df6["nombre_fuente"], y=df6["gwh_inicio"], name=str(int(anio_a)))
        fig.add_bar(x=df6["nombre_fuente"], y=df6["gwh_fin"], name=str(int(anio_b)))
        fig.update_layout(barmode="group", xaxis_title="Fuente", yaxis_title="GWh en el año")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df6, use_container_width=True, hide_index=True)

    with sub_tabs[6]:
        st.markdown("**7. ¿Qué combinación región + fuente es la más productiva?**")
        top_n = st.slider("Top N combinaciones", 5, 33, 15, key="top_q7")
        df7 = q.q7_region_fuente(engine, anio_min, anio_max, top_n=top_n, regiones=regiones_arg, fuentes=fuentes_arg)
        if df7.empty:
            st.info("No hay datos para esos filtros.")
        else:
            df7 = df7.copy()
            df7["combo"] = df7["nombre_region"] + " + " + df7["nombre_fuente"]
            fig = px.bar(df7.sort_values("gwh_acumulado"), x="gwh_acumulado", y="combo", orientation="h",
                        labels={"gwh_acumulado": "GWh acumulados", "combo": "Región + Fuente"})
            fig.update_layout(height=max(400, 24 * len(df7)))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df7, use_container_width=True, hide_index=True)

    with sub_tabs[7]:
        st.markdown("**8. ¿Qué región fue la que más generó en cada año?**")
        df8 = q.q8_region_lider_por_anio(engine, anio_min, min(anio_max, 2025))
        if df8.empty:
            st.info("No hay datos para ese rango.")
        else:
            fig = px.bar(df8, x="anio", y="gwh", color="region_lider",
                        labels={"anio": "Año", "gwh": "GWh de la región líder", "region_lider": "Región líder"})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df8, use_container_width=True, hide_index=True)

    with sub_tabs[8]:
        st.markdown("**9. ¿Cuál es la central con mayor energía generada acumulada de cada región?**")
        df9 = q.q9_central_lider_por_region(engine, anio_min, anio_max, regiones=regiones_arg)
        if df9.empty:
            st.info("No hay datos para esos filtros.")
        else:
            df9 = df9.copy()
            df9["etiqueta"] = df9["nombre_region"] + " (" + df9["codigo_central"] + ")"
            fig = px.bar(df9.sort_values("gwh_acumulado"), x="gwh_acumulado", y="etiqueta", orientation="h",
                        hover_data=["nombre_central"],
                        labels={"gwh_acumulado": "GWh acumulados", "etiqueta": "Región (central)"})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df9, use_container_width=True, hide_index=True)

    st.divider()
    st.caption(
        "Cada pestaña vuelve a consultar el modelo estrella con los filtros elegidos — no son "
        "imágenes estáticas. Las consultas son las mismas, verificadas, del dashboard original."
    )
