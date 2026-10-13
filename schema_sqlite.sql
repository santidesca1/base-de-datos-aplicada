-- =====================================================================
-- Proyecto Final: Metodología HEFESTO — Paso 3: Modelo Lógico del DW
-- Tema: Generación de energía renovable en el MEM (CAMMESA)
-- Esquema: estrella (1 tabla de hechos y 7 dimensiones)
-- Versión SQLite del mismo modelo de entrega_modelo_logico.sql (MySQL),
-- traducida para poder embeber la base como un único archivo portátil
-- (sin depender de un servidor MySQL corriendo en la nube).
-- =====================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE dim_tiempo (
  id_tiempo    INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha_mes    TEXT NOT NULL UNIQUE,              -- MES (AAAA-MM-01)
  anio         INTEGER NOT NULL,                  -- AÑO
  mes          INTEGER NOT NULL,                  -- 1..12, derivado de MES
  nombre_mes   TEXT NOT NULL,                      -- Enero..Diciembre
  estacion     TEXT NOT NULL,                      -- Verano/Otoño/Invierno/Primavera
  CHECK (mes BETWEEN 1 AND 12),
  CHECK (estacion IN ('Verano','Otoño','Invierno','Primavera'))
);

CREATE TABLE dim_central (
  id_central      INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo_central  TEXT NOT NULL UNIQUE,            -- CENTRAL
  nombre_central  TEXT NOT NULL                    -- CENTRAL DESCRIPCIÓN
);

CREATE TABLE dim_maquina (
  id_maquina      INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo_maquina  TEXT NOT NULL UNIQUE             -- MAQUINA
);

CREATE TABLE dim_fuente_energia (
  id_fuente      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_fuente  TEXT NOT NULL UNIQUE              -- FUENTE DE ENERGÍA
);

CREATE TABLE dim_region (
  id_region      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_region  TEXT NOT NULL UNIQUE              -- REGIÓN
);

CREATE TABLE dim_provincia (
  id_provincia      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_provincia  TEXT NOT NULL UNIQUE           -- PROVINCIA
);

CREATE TABLE dim_programa (
  id_programa      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre_programa  TEXT NOT NULL UNIQUE            -- Nueva Generación
);

-- Hecho: generación mensual por máquina (sin filas "Demanda MEM", fuera del grano)
CREATE TABLE fact_generacion (
  id_tiempo             INTEGER NOT NULL,
  id_central            INTEGER NOT NULL,
  id_maquina            INTEGER NOT NULL,
  id_fuente             INTEGER NOT NULL,
  id_region             INTEGER NOT NULL,
  id_provincia          INTEGER NOT NULL,
  id_programa           INTEGER NOT NULL,
  energia_generada_gwh  REAL    NOT NULL,          -- ENERGÍA GENERADA [GWh]
  PRIMARY KEY (id_tiempo, id_central, id_maquina),
  CHECK (energia_generada_gwh >= 0),
  FOREIGN KEY (id_tiempo)    REFERENCES dim_tiempo (id_tiempo),
  FOREIGN KEY (id_central)   REFERENCES dim_central (id_central),
  FOREIGN KEY (id_maquina)   REFERENCES dim_maquina (id_maquina),
  FOREIGN KEY (id_fuente)    REFERENCES dim_fuente_energia (id_fuente),
  FOREIGN KEY (id_region)    REFERENCES dim_region (id_region),
  FOREIGN KEY (id_provincia) REFERENCES dim_provincia (id_provincia),
  FOREIGN KEY (id_programa)  REFERENCES dim_programa (id_programa)
);
