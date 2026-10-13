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

st.set_page_config(page_title="HEFESTO — Energía Renovable MEM", layout="wide")

# Paleta única (azules y grises neutros) para todos los gráficos de la app —
# reemplaza el arcoíris por default de Plotly. El tema de los widgets de
# Streamlit (sliders, tabs, botones) se define en .streamlit/config.toml.
AZUL = "#2E5C8A"
AZUL_CLARO = "#8AA4C2"
GRIS = "#6B7280"
GRIS_CLARO = "#C3C9D1"
PALETA = [AZUL, GRIS, AZUL_CLARO, "#374151", GRIS_CLARO, "#17324F", "#9CA3AF", "#5B7FA6"]
px.defaults.color_discrete_sequence = PALETA
px.defaults.color_continuous_scale = "Blues"

ALUMNOS = "Lucas Emiliano Galleguillo (2510484), Ignacio Albizuri (2520657), Santiago Descalzo Glamuzina (2500352), Joaquin Ian Garcia Sequeira (2534906)"
PROFESORES = "Julio Marcelo Gutierrez, Gaston Emilio Severina"

st.title("Generación de energía renovable en el MEM")
st.caption("Proyecto Final — Metodología HEFESTO · Base de Datos Aplicada · UCC")
st.caption(f"**Alumnos:** {ALUMNOS}  \n**Profesores:** {PROFESORES}")

tab1, tab2, tab3, tab4, tab_dash = st.tabs([
    "Paso 1 · Requerimientos", "Paso 2 · Fuente de Datos", "Paso 3 · Modelo Lógico",
    "Paso 4 · Integración de Datos", "Dashboard",
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
        "¿En qué año las energías renovables comenzaron a crecer? (el \"por qué\" queda fuera del DW, es contexto/investigación, no un indicador)",
        "¿Qué provincias producen la mayor/menor cantidad de energía renovable?",
        "¿En qué meses del año generan más las fuentes solares y eólicas (patrón estacional esperable) vs las hidro/biomasa?",
        "¿Cuántas centrales nuevas (primer año con generación > 0, sin contar las que ya figuraban en el primer mes del archivo) se sumaron cada año, por región?",
        "¿Cuáles son las formas de energía que más/menos se desarrollaron en los últimos 10 años (2016-2026)?",
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
- Suma total de energía generada
- Porcentaje de variación de la generación entre años (interanual)
- Porcentaje de participación sobre el total generado
- Cantidad de centrales nuevas
""")
    with col_persp:
        st.markdown("**Perspectivas**")
        st.markdown("""
- Por provincia
- Por región
- Por fuentes de energía renovable
- Por tiempo (año, mes y estación)
- Por central
- Por máquina
- Por programa / contrato
""")

    st.subheader("Qué indicador responde cada pregunta")
    mapa_preg_ind = pd.DataFrame([
        (1, "Centrales con muy poca o nula energía", "Suma total", "Central"),
        (2, "Año en que las renovables comenzaron a crecer", "% Variación entre años", "Tiempo (año)"),
        (3, "Provincias que más y menos producen", "Suma total, % Participación", "Provincia"),
        (4, "Meses de mayor generación por fuente", "% Participación (de cada mes sobre el total anual)", "Fuente, Tiempo (mes), Máquina"),
        (5, "Centrales nuevas por año y región", "Cantidad de centrales nuevas", "Tiempo (año), Región, Central"),
        (6, "Fuentes que más y menos se desarrollaron en 10 años", "Suma total, % Variación entre años", "Fuente, Tiempo (año)"),
        (7, "Combinación región + fuente más productiva", "Suma total, % Participación", "Región, Fuente"),
        (8, "Región que más generó en cada año", "Suma total, % Participación", "Región, Tiempo (año)"),
        (9, "Central con mayor energía acumulada de cada región", "Suma total", "Región, Central"),
    ], columns=["#", "Pregunta", "Indicador(es)", "Perspectivas"])
    st.dataframe(mapa_preg_ind, use_container_width=True, hide_index=True)
    st.caption(
        "Cada indicador responde al menos una pregunta y cada pregunta se responde con los "
        "indicadores de la lista. La perspectiva Programa/Contrato no la pide ninguna pregunta: "
        "se conserva como dato descriptivo de cada registro (con qué mecanismo ingresó la central "
        "al mercado)."
    )
    st.info(
        "El archivo trae además 187 filas **\"Demanda MEM\"** (una por mes): no son generación de "
        "una central sino la demanda total del sistema eléctrico (todo el SADI), sin desglose "
        "geográfico. Ninguna pregunta las necesita, así que no se usan como indicador ni forman "
        "parte de este Data Mart (el tratamiento se detalla en el Paso 2)."
    )

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
    st.caption(
        "Verificación del archivo (misma copia usada en el análisis, sin modificaciones): "
        "codificación UTF-8 con BOM, 2.179.926 bytes, "
        "SHA-256 `cf50fe8d5d8ea093bcbfcd1c0b0cdd6a22b460ef83b656fb89754a64e3ac3e3e`."
    )

    st.subheader("Perfil de columnas del archivo fuente")
    perfil = pd.DataFrame([
        ("AÑO", "Año calendario del registro", "2011 a 2026 (16 valores)", "Entero"),
        ("CENTRAL", "Código corto de la central generadora", "283 valores únicos + fila especial \"Demanda MEM\"", "Texto"),
        ("CENTRAL DESCRIPCIÓN", "Nombre descriptivo de la central", "280 valores únicos", "Texto"),
        ("MAQUINA", "Código de la máquina dentro de la central", "291 valores únicos", "Texto"),
        ("FUENTE DE ENERGÍA", "Tipo de fuente renovable", "7 valores: BIODIESEL, HIDRO ≤50MW, EOLICO, BIOMASA, SOLAR, BIOGAS + placeholder \"Demanda MEM\"", "Texto categórico"),
        ("REGIÓN", "Región eléctrica del país", "10 valores (BUENOS AIRES, GRAN BS.AS., CUYO, COMAHUE, ...) + \"Demanda MEM\"", "Texto categórico"),
        ("PROVINCIA", "Provincia donde está la central", "21 provincias + placeholder (22 valores)", "Texto categórico"),
        ("MES", "Primer día del mes que reporta", "AAAA-MM-01, 187 valores", "Fecha"),
        ("ENERGÍA GENERADA [GWh]", "Energía generada por esa máquina en ese mes", "0 a 167,82 GWh en filas renovables; 8.537,20 a 13.996,90 GWh en filas \"Demanda MEM\" (demanda total del SADI)", "Decimal"),
        ("Nueva Generación", "Programa por el que ingresó al mercado", "8 valores: Resto, RENOVAR, MATER, Renovar 202, SPOT MATER, MATER AG, RenMDI, Demanda", "Texto categórico"),
    ], columns=["Columna", "Descripción", "Valores posibles", "Tipo de dato"])
    st.dataframe(perfil, use_container_width=True, hide_index=True)

    st.subheader("a) Conformar indicadores")
    indicadores = pd.DataFrame([
        ("Suma Total de Energía Generada", "SUM(GWh), excluyendo \"Demanda MEM\"", "SUM", "Aditivo"),
        ("% Variación de la Generación entre Años (interanual)", "(SUM año B − SUM año A) / SUM año A × 100", "SUM + división", "No aditivo (derivado)"),
        ("% Participación sobre el Total Generado", "SUM(grupo) / SUM(total de referencia) × 100", "SUM + división", "No aditivo (derivado)"),
        ("Cantidad de Centrales Nuevas", "COUNT DISTINCT central cuyo primer año con energía > 0 es el año analizado", "COUNT DISTINCT", "No se obtiene sumando filas del hecho"),
    ], columns=["Indicador", "Fórmula", "Función de agregación", "Aditividad"])
    st.dataframe(indicadores, use_container_width=True, hide_index=True)
    st.caption(
        "La Suma Total es el único indicador aditivo. Los otros tres se calculan al consultar: "
        "dos son cocientes (no aditivos) y el tercero es un conteo de centrales distintas que "
        "depende del primer año con generación de cada central. Ninguno se almacena como columna "
        "del hecho — todos se calculan a partir de la única medida almacenada, ENERGÍA GENERADA [GWh]."
    )

    st.subheader("c) Nivel de granularidad")
    st.markdown("""
**Grano del hecho:** una fila = una máquina, dentro de una central, en un mes —
la clave natural del hecho es **CENTRAL + MAQUINA + MES**. Es el nivel más fino
disponible en la fuente (no hay reportes diarios ni horarios).

**Filas fuera del grano:** las 187 filas "Demanda MEM" no corresponden a una
máquina sino a la demanda total del SADI (1 fila por mes a nivel país). No son
generación renovable y ninguna pregunta de negocio las necesita, por lo que
**no se cargan en el Data Mart** — en el Paso 4 quedan registradas en
`stg_descartes`, con su motivo.

**Inconsistencias de espacios detectadas y su solución:**
- CENTRAL, MAQUINA, FUENTE DE ENERGÍA y PROVINCIA: inconsistencias concentradas
  en las filas placeholder de "Demanda MEM" (ej. `"Demanda MEM"` vs
  `" Demanda MEM"`).
- CENTRAL DESCRIPCIÓN: espacios sobrantes (al inicio, al final o dobles entre
  palabras) en **435 filas de centrales reales** — no generan nombres
  distintos para una misma central, pero hay que limpiarlos igual.
- Solución: aplicar `TRIM()` a todas las columnas de texto y reemplazar los
  espacios múltiples por uno solo, durante la carga y antes de comparar o
  agrupar valores.

**Duplicados:** 5 combinaciones CENTRAL + MAQUINA + MES repetidas (10 de las
22.784 filas), con un valor distinto para el mismo mes (en tres casos, 0 vs.
el valor real) → se deduplica quedándose con el **valor más alto** de energía
generada (criterio del grupo: se asume que el 0 es un reporte preliminar).
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

Hay un solo proceso de negocio (1 fila = 1 máquina en 1 mes), así que no hace falta una
constelación. No se normaliza a copo de nieve: las jerarquías estrictas (Central→Máquina,
Año→Mes) son chicas y no justifican el join extra, y Provincia→Región **no** es una
jerarquía estricta (BUENOS AIRES pertenece a dos regiones), así que ambas quedan como
dimensiones independientes. El Programa tampoco es un atributo fijo de la central —
cambia en el tiempo en 49 centrales — por eso es dimensión propia referenciada desde
cada registro mensual del hecho.
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
- 22.592 filas esperadas, SUM = 163.315,980622 GWh
""")

    st.subheader("Dos desvíos deliberados respecto de la letra de la consigna")
    st.caption(
        "La consigna pide una PK compuesta por las claves de *todas* las dimensiones "
        "relacionadas y un campo por cada indicador. Este modelo se aparta de ambas "
        "indicaciones a propósito — se explicita acá para que la decisión quede a la vista."
    )
    desvios = pd.DataFrame([
        (
            "PK con 3 FK de 7",
            "PK compuesta por las claves de todas las dimensiones relacionadas",
            "PRIMARY KEY (id_tiempo, id_central, id_maquina); las otras 4 dimensiones entran solo como FK",
            "Una PK de 7 columnas no haría cumplir el grano: aceptaría dos filas de la misma "
            "máquina en el mismo mes con distinto programa (el atributo que varía mes a mes en "
            "49 centrales). La PK elegida es la clave natural del grano (CENTRAL+MAQUINA+MES) y "
            "sí lo hace cumplir.",
        ),
        (
            "Un solo campo para 4 indicadores",
            "Un campo por cada indicador en la tabla de hechos",
            "Se almacena solo la medida energia_generada_gwh (Suma Total al nivel del grano); "
            "los otros 3 se calculan al consultar",
            "3 de los 4 indicadores no se pueden obtener sumando filas del hecho: dos son "
            "cocientes (no aditivos) y el tercero es un conteo de centrales distintas que "
            "depende del primer año con generación. Guardarlos como columna daría resultados "
            "incorrectos al agregar por cualquier dimensión.",
        ),
    ], columns=["Desvío", "Qué dice la consigna", "Qué se hizo", "Por qué"])
    st.dataframe(desvios, use_container_width=True, hide_index=True)

    with st.expander("Pregunta 5 en detalle — ¿cómo se cuentan las \"centrales nuevas\"?"):
        st.markdown("""
El archivo no trae fecha de habilitación, así que el año de alta se aproxima como el
**primer año con generación mayor a cero**. Como el archivo empieza en enero de 2011,
las **39 centrales** que ya figuran en ese primer mes son la base inicial ya existente y
no se cuentan como altas (sin esta exclusión, 2011 mostraría 42 "nuevas" en vez de 5).
Tampoco se cuentan las **2 centrales** que nunca generaron por encima de 0 (DSUD y
HON3FV), que responden a la pregunta 1. En total quedan **240 centrales nuevas**
(281 − 39 − 2).

Se evaluó guardar `anio_alta` como atributo de `dim_central`, pero se decidió no
hacerlo: sería un dato derivado del propio hecho, invertiría el orden natural del ETL
(la dimensión dependería del hecho) y quedaría desactualizado al incorporar meses
nuevos. Se resuelve por consulta:
""")
        st.code("""SELECT a.anio_alta, r.nombre_region, COUNT(DISTINCT a.id_central) AS centrales_nuevas
FROM (SELECT fg.id_central, fg.id_region,
             MIN(t.fecha_mes) AS primer_registro,
             MIN(CASE WHEN fg.energia_generada_gwh > 0 THEN t.anio END) AS anio_alta
      FROM fact_generacion fg
      JOIN dim_tiempo t ON t.id_tiempo = fg.id_tiempo
      GROUP BY fg.id_central, fg.id_region) AS a
JOIN dim_region r ON r.id_region = a.id_region
WHERE a.primer_registro > (SELECT MIN(fecha_mes) FROM dim_tiempo)  -- excluye la base inicial
  AND a.anio_alta IS NOT NULL                                      -- excluye las que nunca generaron
GROUP BY a.anio_alta, r.nombre_region
ORDER BY a.anio_alta, centrales_nuevas DESC;""", language="sql")
        st.caption(
            "La consulta usa dos criterios a propósito: la base inicial se detecta por el "
            "primer registro (aunque valga 0), y el año de alta se toma del primer valor mayor "
            "a 0 — porque 50 centrales aparecen en el archivo con ceros antes de empezar a "
            "generar (puesta en marcha)."
        )

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
**1. Extract:** el CSV se lee con `dtype=str` (todo como texto, sin tocar valores) a la
tabla intermedia `stg_energia_raw`, para tener una copia fiel y poder auditar qué se
transforma después — las 22.784 filas del archivo quedan cargadas tal cual.

**2. Calidad de datos:** sobre esa copia (no sobre el archivo) se chequean vacíos,
valores no numéricos o negativos, rangos de energía, fechas inválidas, meses faltantes,
espacios de más, duplicados de la clave del grano (CENTRAL + MAQUINA + MES), y
consistencia entre columnas (una máquina siempre pertenece a la misma
central/fuente/región/provincia).

**3. Transform:** se aplican las reglas que surgieron de esos chequeos — TRIM en todo
el texto, conversión de tipos, **exclusión de las 187 filas "Demanda MEM"** (no son
generación de una central, quedan fuera del grano, van a `stg_descartes`),
**deduplicación** de las 5 combinaciones repetidas quedándose con el valor más alto,
nombre único para BRC1, y se derivan año/mes/estación de la fecha.

**4. Load:** primero se cargan las 7 dimensiones (generan sus claves subrogadas), y
después, cruzando (`merge`) los datos limpios contra cada dimensión, se arma y carga
`fact_generacion`. Se usa `if_exists="append"` (no `"replace"`) para que MySQL conserve
las PK, FK y CHECK del Paso 3 y controle la integridad al insertar.

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

    with st.expander("Ver los 14 chequeos de calidad de datos (punto 2), con resultado y decisión"):
        calidad = pd.DataFrame([
            (1, "Vacíos o nulos (10 columnas)", "0 celdas", "Sin acción"),
            (2, "Energía no numérica o negativa", "0 filas", "Sin acción"),
            (3, "Rango de energía renovable", "0 a 167,818558 GWh", "Dentro de lo esperado para una máquina en un mes"),
            (4, "Rango de Demanda MEM", "8.537,20 a 13.996,90 GWh", "Dentro de lo esperado para la demanda total mensual del SADI"),
            (5, "Energía igual a 0 (renovables)", "2.262 de 22.597 filas (10,0%)", "Se conservan: dato válido (máquina sin generación ese mes)"),
            (6, "Fechas inválidas / AÑO ≠ año de MES", "0 filas", "Sin acción"),
            (7, "Meses faltantes", "0 (187 meses, 2011-01 a 2026-07)", "Sin acción"),
            (8, "Espacios en \"Demanda MEM\"", "187 filas", "Se corrige con TRIM"),
            (9, "Espacios en CENTRAL DESCRIPCIÓN", "435 filas", "Se corrige con TRIM + espacios múltiples a uno"),
            (10, "Duplicados CENTRAL+MAQUINA+MES", "5 combinaciones (10 filas)", "Se descarta la de menor energía, se conserva la mayor"),
            (11, "Máquinas con más de 1 central/fuente/región/provincia", "0", "Sin acción: confirma la dependencia funcional"),
            (12, "Centrales cuyo programa cambia en el tiempo", "49 centrales", "Sin acción: dato real, por eso el programa es FK del hecho"),
            (13, "Centrales con más de un nombre", "BRC1", "Se unifica (ver nota)"),
            (14, "Filas \"Demanda MEM\"", "187, exactamente 1 por mes", "No se cargan en el modelo; quedan en stg_descartes"),
        ], columns=["#", "Chequeo", "Resultado", "Decisión"])
        st.dataframe(calidad, use_container_width=True, hide_index=True)
        st.caption(
            "BRC1 trae un nombre distinto por máquina: se unen en el orden en que aparecen en "
            "el archivo → \"BIO R. CUARTO 1 / C.BIOELECT.R.CUARTO1 REN2\" (no afecta ningún "
            "total, la energía de ambas máquinas se suma igual bajo BRC1)."
        )

        st.markdown("**Detalle de los 5 duplicados (chequeo 10):**")
        dups = pd.DataFrame([
            ("21429 / 21430", "CASAEO / CASAEO", "2026-02", "8,081923 y 8,081923", "Duplicado exacto: se descarta la línea 21430"),
            ("8967 / 8968", "CHN2EO / CHN2EO", "2021-03", "0,486301 y 6,182240", "Se conserva 6,182240"),
            ("8009 / 8108", "GUA6HI / GUA6HI", "2020-10", "0 y 0,378157", "Se conserva 0,378157"),
            ("8010 / 8110", "GUA7HI / GUA7HI", "2020-10", "0 y 0,280297", "Se conserva 0,280297"),
            ("8011 / 8109", "GUA8HI / GUA8HI", "2020-10", "0 y 0,393016", "Se conserva 0,393016"),
        ], columns=["Línea CSV", "Central / Máquina", "Mes", "Energía (GWh)", "Resultado"])
        st.dataframe(dups, use_container_width=True, hide_index=True)

    st.subheader("6. Política de actualización")
    st.markdown("""
**Contexto:** CAMMESA publica este archivo una vez por mes, y cada publicación trae **el
historial completo** desde 2011, no solo el mes nuevo. Los meses ya publicados pueden
corregirse — lo muestran los duplicados de GUA6HI, GUA7HI, GUA8HI y CHN2EO, donde un
valor preliminar quedó junto a su corrección posterior. El volumen es chico: unas 270
filas nuevas por mes (una por máquina activa) sobre un total de 22.592.

**Frecuencia:** mensual, después de cada publicación de CAMMESA.
""")
    politica = pd.DataFrame([
        ("Tablas intermedias (stg_*)", "Recarga completa en cada corrida", "Son una foto del archivo recibido; no guardan historia"),
        ("dim_tiempo", "Incremental: se agregan solo los meses nuevos", "Un mes publicado no cambia"),
        ("dim_central, dim_maquina", "Incremental: solo códigos nuevos, nunca se borran; si cambia el nombre se actualiza sin cambiar la clave", "Las claves ya usadas por el hecho deben mantenerse estables"),
        ("dim_fuente_energia, dim_region, dim_provincia, dim_programa", "Incremental: solo valores nuevos", "Cambian muy rara vez; un valor nuevo se informa como alerta"),
        ("fact_generacion", "Incremental por ventana móvil: se borran y recargan los últimos 12 meses", "Entran los meses nuevos y se absorben correcciones recientes sin recargar todo el historial"),
        ("Todo el modelo", "Recarga completa 1 vez por año, o si un control detecta un cambio fuera de la ventana", "Corrige cualquier ajuste de CAMMESA sobre meses viejos"),
    ], columns=["Objeto", "Estrategia", "Motivo"])
    st.dataframe(politica, use_container_width=True, hide_index=True)
    st.caption(
        "La ventana de 12 meses es un criterio del grupo: el archivo no informa con cuánto "
        "atraso llegan las correcciones. La recarga completa anual cubre ese riesgo."
    )
    st.markdown("""
**Controles en cada corrida:** repetir la sección de calidad y la de verificación del
notebook — la carga solo se da por buena si todos los controles dan OK.

**Alertas:** aparición de una fuente, región o programa nuevo; una máquina que cambia de
central; un mes faltante; o una diferencia en el total de meses fuera de la ventana
respecto de la carga anterior (indica una corrección vieja y dispara la recarga completa).

**Para esta entrega** se usa la recarga completa (la estrategia de la carga inicial); la
carga incremental descrita arriba es la política a aplicar en producción mes a mes.
""")

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

    st.subheader("Filtros del dashboard")
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        anio_min, anio_max = st.slider(
            "Rango de años (acumulados / por año, según el gráfico)",
            min_value=q.ANIO_MIN_DATOS, max_value=q.ANIO_MAX_DATOS,
            value=(q.ANIO_MIN_DATOS, q.ANIO_MAX_DATOS),
        )
    with col_f2:
        regiones_sel = st.multiselect("Región", regiones_todas, default=regiones_todas)
    with col_f3:
        fuentes_sel = st.multiselect("Fuente de energía", fuentes_todas, default=fuentes_todas)
    st.caption(
        f"{total_filas:,} filas en fact_generacion".replace(",", ".")
        + " · No todos los gráficos usan los tres filtros — cada pestaña aclara cuáles le aplican."
    )

    regiones_arg = regiones_sel if regiones_sel and len(regiones_sel) < len(regiones_todas) else None
    fuentes_arg = fuentes_sel if fuentes_sel and len(fuentes_sel) < len(fuentes_todas) else None

    st.divider()
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
                         color_discrete_map={"Nula": GRIS, "Muy poca": AZUL},
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
            fig_gwh = px.bar(df2, x="anio", y="gwh", labels={"anio": "Año", "gwh": "GWh"}, title="Generación anual",
                              color_discrete_sequence=[AZUL])
            st.plotly_chart(fig_gwh, use_container_width=True)
        with c2:
            colores = df2["cumple_criterio"].map({True: AZUL, False: GRIS_CLARO})
            fig_var = go.Figure(go.Bar(x=df2["anio"], y=df2["variacion_pct"], marker_color=colores))
            fig_var.add_hline(y=umbral, line_dash="dash", annotation_text=f"umbral {umbral}%")
            fig_var.update_layout(title="Variación anual (%) — azul oscuro = cumple el criterio", xaxis_title="Año", yaxis_title="%")
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
