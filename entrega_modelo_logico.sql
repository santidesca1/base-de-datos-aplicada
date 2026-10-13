-- =====================================================================
-- Proyecto Final: Metodología HEFESTO — Paso 3: Modelo Lógico del DW
-- Tema: Generación de energía renovable en el MEM (CAMMESA)
-- Esquema: estrella (1 tabla de hechos y 7 dimensiones)
-- Motor: MySQL 8 (InnoDB, utf8mb4)
-- =====================================================================
--
-- CIFRAS DE CONTROL ESPERADAS TRAS LA CARGA (Paso 4)
-- Reglas aplicadas: excluir filas "Demanda MEM" del hecho de generación,
-- TRIM() en todo texto, y deduplicar CENTRAL+MAQUINA+MES quedándose con
-- el valor más alto de energía.
--
--   dim_tiempo ............  187      fact_generacion ......  22.592
--   dim_central ...........  281
--   dim_maquina ...........  289      SUM(energia_generada_gwh)
--   dim_fuente_energia ....    6        = 163.315,980622 GWh
--   dim_region ............    9
--   dim_provincia .........   21
--   dim_programa ..........    7
--
-- Si SUM(energia_generada_gwh) da 163.324,548846 en lugar de
-- 163.315,980622, se están sumando las filas duplicadas en vez de
-- descartarlas (diferencia de 8,568224 GWh).
-- =====================================================================

SET NAMES utf8mb4;

DROP DATABASE IF EXISTS dw_energia_renovable;
CREATE DATABASE dw_energia_renovable
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE dw_energia_renovable;

-- ---------------------------------------------------------------------
-- DIMENSIONES
-- ---------------------------------------------------------------------

CREATE TABLE dim_tiempo (
  id_tiempo    INT UNSIGNED     NOT NULL AUTO_INCREMENT,
  fecha_mes    DATE             NOT NULL,          -- MES (AAAA-MM-01)
  anio         SMALLINT UNSIGNED NOT NULL,         -- AÑO
  mes          TINYINT UNSIGNED NOT NULL,          -- 1..12, derivado de MES
  nombre_mes   VARCHAR(12)      NOT NULL,          -- Enero..Diciembre
  estacion     VARCHAR(10)      NOT NULL,          -- Verano/Otoño/Invierno/Primavera
  PRIMARY KEY (id_tiempo),
  UNIQUE KEY uk_tiempo_fecha (fecha_mes),
  CONSTRAINT ck_tiempo_mes      CHECK (mes BETWEEN 1 AND 12),
  CONSTRAINT ck_tiempo_estacion CHECK (estacion IN ('Verano','Otoño','Invierno','Primavera'))
) ENGINE = InnoDB;

CREATE TABLE dim_central (
  id_central      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  codigo_central  VARCHAR(10)  NOT NULL,             -- CENTRAL
  nombre_central  VARCHAR(60)  NOT NULL,             -- CENTRAL DESCRIPCIÓN
  PRIMARY KEY (id_central),
  UNIQUE KEY uk_central_codigo (codigo_central)
) ENGINE = InnoDB;

CREATE TABLE dim_maquina (
  id_maquina      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  codigo_maquina  VARCHAR(10)  NOT NULL,             -- MAQUINA
  PRIMARY KEY (id_maquina),
  UNIQUE KEY uk_maquina_codigo (codigo_maquina)
) ENGINE = InnoDB;

CREATE TABLE dim_fuente_energia (
  id_fuente      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre_fuente  VARCHAR(20)      NOT NULL,          -- FUENTE DE ENERGÍA
  PRIMARY KEY (id_fuente),
  UNIQUE KEY uk_fuente_nombre (nombre_fuente)
) ENGINE = InnoDB;

CREATE TABLE dim_region (
  id_region      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre_region  VARCHAR(20)      NOT NULL,          -- REGIÓN
  PRIMARY KEY (id_region),
  UNIQUE KEY uk_region_nombre (nombre_region)
) ENGINE = InnoDB;

CREATE TABLE dim_provincia (
  id_provincia      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre_provincia  VARCHAR(30)      NOT NULL,       -- PROVINCIA
  PRIMARY KEY (id_provincia),
  UNIQUE KEY uk_provincia_nombre (nombre_provincia)
) ENGINE = InnoDB;

CREATE TABLE dim_programa (
  id_programa      TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nombre_programa  VARCHAR(20)      NOT NULL,        -- Nueva Generación
  PRIMARY KEY (id_programa),
  UNIQUE KEY uk_programa_nombre (nombre_programa)
) ENGINE = InnoDB;

-- ---------------------------------------------------------------------
-- HECHOS
-- ---------------------------------------------------------------------

-- Hecho: generación mensual por máquina (sin filas "Demanda MEM", que quedan fuera del grano)
CREATE TABLE fact_generacion (
  id_tiempo             INT UNSIGNED     NOT NULL,
  id_central            INT UNSIGNED     NOT NULL,
  id_maquina            INT UNSIGNED     NOT NULL,
  id_fuente             TINYINT UNSIGNED NOT NULL,
  id_region             TINYINT UNSIGNED NOT NULL,
  id_provincia          TINYINT UNSIGNED NOT NULL,
  id_programa           TINYINT UNSIGNED NOT NULL,
  energia_generada_gwh  DECIMAL(12,6)    NOT NULL,   -- ENERGÍA GENERADA [GWh]
  -- PK = clave natural del grano definido en el Paso 2 (CENTRAL + MAQUINA + MES).
  -- Fuente, región, provincia y programa dependen funcionalmente de ella: van solo como FK.
  PRIMARY KEY (id_tiempo, id_central, id_maquina),
  CONSTRAINT ck_generacion_energia CHECK (energia_generada_gwh >= 0),
  CONSTRAINT fk_gen_tiempo    FOREIGN KEY (id_tiempo)    REFERENCES dim_tiempo (id_tiempo),
  CONSTRAINT fk_gen_central   FOREIGN KEY (id_central)   REFERENCES dim_central (id_central),
  CONSTRAINT fk_gen_maquina   FOREIGN KEY (id_maquina)   REFERENCES dim_maquina (id_maquina),
  CONSTRAINT fk_gen_fuente    FOREIGN KEY (id_fuente)    REFERENCES dim_fuente_energia (id_fuente),
  CONSTRAINT fk_gen_region    FOREIGN KEY (id_region)    REFERENCES dim_region (id_region),
  CONSTRAINT fk_gen_provincia FOREIGN KEY (id_provincia) REFERENCES dim_provincia (id_provincia),
  CONSTRAINT fk_gen_programa  FOREIGN KEY (id_programa)  REFERENCES dim_programa (id_programa)
) ENGINE = InnoDB;
