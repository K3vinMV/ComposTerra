-- =====================================================================
-- Sistema de Monitoreo y Predicción de Calidad de Composta
-- Schema MySQL 8 — compatible local y AWS RDS sin cambios
-- Uso: mysql -u root -p < schema.sql
-- =====================================================================

CREATE DATABASE IF NOT EXISTS composta_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE composta_db;

-- ---------------------------------------------------------------------
-- usuarios
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  nombre        VARCHAR(100)    NOT NULL,
  email         VARCHAR(150)    NOT NULL,
  password_hash VARCHAR(255)    NOT NULL,
  rol           ENUM('admin', 'operador') NOT NULL DEFAULT 'operador',
  PRIMARY KEY (id),
  UNIQUE KEY uq_usuarios_email (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- lotes
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lotes (
  id                 INT UNSIGNED   NOT NULL AUTO_INCREMENT,
  fecha_inicio       DATE           NOT NULL,
  material_principal VARCHAR(100)   NOT NULL,
  peso_kg            DECIMAL(8,2)   NOT NULL,
  estado             ENUM('activo', 'finalizado') NOT NULL DEFAULT 'activo',
  PRIMARY KEY (id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- registros_sensor
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registros_sensor (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_lote     INT UNSIGNED    NOT NULL,
  temperatura DECIMAL(5,2)    NOT NULL,  -- °C  (óptimo 45-65)
  humedad     DECIMAL(5,2)    NOT NULL,  -- %   (óptimo 40-60)
  ph          DECIMAL(4,2)    NOT NULL,  --     (óptimo 6-8)
  timestamp   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_registros_lote_ts (id_lote, timestamp),
  CONSTRAINT fk_registros_lote
    FOREIGN KEY (id_lote) REFERENCES lotes (id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- predicciones
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicciones (
  id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  id_lote   INT UNSIGNED  NOT NULL,
  resultado ENUM('optimo', 'aceptable', 'deficiente') NOT NULL,
  confianza DECIMAL(5,2)  NOT NULL,       -- porcentaje 0-100
  fecha     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_predicciones_lote (id_lote),
  CONSTRAINT fk_predicciones_lote
    FOREIGN KEY (id_lote) REFERENCES lotes (id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
