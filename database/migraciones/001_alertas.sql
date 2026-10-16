USE composta_db;

CREATE TABLE IF NOT EXISTS alertas (
  id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_lote           INT UNSIGNED    NOT NULL,
  -- Variable que se salió de rango, o 'sin_datos' si el sensor dejó de reportar
  tipo              ENUM('temperatura', 'humedad', 'ph', 'sin_datos') NOT NULL,
  direccion         ENUM('bajo', 'alto') NULL,       -- NULL en 'sin_datos'
  valor             DECIMAL(6,2)    NULL,            -- promedio de las últimas lecturas
  abierta_en        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  cerrada_en        DATETIME        NULL,            -- NULL mientras siga activa
  notificada        TINYINT(1)      NOT NULL DEFAULT 0,  -- aviso de apertura enviado
  notificada_cierre TINYINT(1)      NOT NULL DEFAULT 0,  -- aviso de recuperación enviado
  PRIMARY KEY (id),
  KEY idx_alertas_lote_abiertas (id_lote, cerrada_en),
  CONSTRAINT fk_alertas_lote
    FOREIGN KEY (id_lote) REFERENCES lotes (id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
