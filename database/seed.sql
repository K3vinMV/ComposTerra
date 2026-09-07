-- =====================================================================
-- Datos de ejemplo para desarrollo y demostración
--
-- Uso: mysql -u root -p < seed.sql
--
-- Las fechas son RELATIVAS a la fecha de ejecución (CURDATE / NOW), para que
-- el conjunto siga siendo coherente sin importar cuándo se cargue. Si fueran
-- fechas fijas, el avance del ciclo de cada lote se desajustaría con el tiempo
-- y los estados dejarían de tener sentido.
--
-- Los seis lotes cubren todos los estados que el sistema puede mostrar:
--
--   L-001  fase activa, parámetros correctos      -> Óptimo
--   L-002  fase activa, humedad baja              -> Advertencia
--   L-003  fase de maduración, evolución normal   -> Maduración
--   L-004  fase activa, pH ácido                  -> Advertencia
--   L-005  recién registrado, sin lecturas        -> Sin lecturas
--   L-006  ciclo terminado, con historial         -> Finalizado
--
-- Nota: el usuario administrador NO se crea aquí. Se crea con
-- backend/scripts/crear_admin.py, para generar el hash bcrypt correctamente.
-- =====================================================================

USE composta_db;

-- Limpieza previa (permite recargar el seed sin duplicar)
DELETE FROM predicciones;
DELETE FROM registros_sensor;
DELETE FROM lotes;
ALTER TABLE lotes AUTO_INCREMENT = 1;
ALTER TABLE registros_sensor AUTO_INCREMENT = 1;
ALTER TABLE predicciones AUTO_INCREMENT = 1;

-- ---------------------------------------------------------------------
-- Lotes
-- ---------------------------------------------------------------------
INSERT INTO lotes (fecha_inicio, material_principal, peso_kg, duracion_estimada_dias, estado) VALUES
  -- L-001 · 13 % del ciclo · fase termofílica saludable
  (DATE_SUB(CURDATE(), INTERVAL  12 DAY), 'Restos de fruta y verdura', 120.50,  90, 'activo'),
  -- L-002 · 44 % del ciclo · se secó, necesita riego
  (DATE_SUB(CURDATE(), INTERVAL  40 DAY), 'Hojas secas y pasto',        80.00,  90, 'activo'),
  -- L-003 · 83 % del ciclo · madurando correctamente
  (DATE_SUB(CURDATE(), INTERVAL  75 DAY), 'Estiércol y paja',          200.00,  90, 'activo'),
  -- L-004 · 17 % del ciclo · acidificación por exceso de material verde
  (DATE_SUB(CURDATE(), INTERVAL  20 DAY), 'Residuos de cocina',         65.75, 120, 'activo'),
  -- L-005 · registrado hoy, todavía sin instrumentar
  (CURDATE(),                             'Poda de jardín',             45.00,  60, 'activo'),
  -- L-006 · ciclo completo, cerrado
  (DATE_SUB(CURDATE(), INTERVAL 140 DAY), 'Mezcla de estiércol y hoja',180.00, 120, 'finalizado');

-- ---------------------------------------------------------------------
-- Registros de sensor
-- Timestamps dentro de las últimas horas para que caigan en la ventana de
-- 24 h que usa el endpoint de predicción.
-- ---------------------------------------------------------------------

-- L-001 · termofílico: caliente y húmedo, todo en rango
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (1, 53.80, 51.20, 6.95, DATE_SUB(NOW(), INTERVAL 50 MINUTE)),
  (1, 54.60, 50.40, 7.02, DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
  (1, 55.90, 49.80, 7.08, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
  (1, 55.10, 50.10, 6.99, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (1, 56.40, 49.30, 7.11, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
  (1, 55.70, 48.90, 7.05, DATE_SUB(NOW(), INTERVAL  2 MINUTE));

-- L-002 · humedad por debajo del rango en plena fase activa -> alerta
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (2, 57.20, 34.10, 7.15, DATE_SUB(NOW(), INTERVAL 50 MINUTE)),
  (2, 58.60, 33.20, 7.09, DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
  (2, 59.10, 31.80, 7.18, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
  (2, 58.30, 30.90, 7.12, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (2, 59.80, 29.70, 7.21, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
  (2, 58.90, 30.20, 7.16, DATE_SUB(NOW(), INTERVAL  2 MINUTE));

-- L-003 · maduración: frío y seco, comportamiento esperado en esta fase
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (3, 26.40, 27.10, 7.42, DATE_SUB(NOW(), INTERVAL 50 MINUTE)),
  (3, 25.80, 26.40, 7.38, DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
  (3, 25.10, 25.90, 7.45, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
  (3, 24.70, 25.20, 7.40, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (3, 24.30, 24.80, 7.47, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
  (3, 24.90, 25.40, 7.43, DATE_SUB(NOW(), INTERVAL  2 MINUTE));

-- L-004 · pH ácido -> alerta en cualquier fase
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (4, 51.30, 47.80, 5.42, DATE_SUB(NOW(), INTERVAL 50 MINUTE)),
  (4, 52.10, 48.60, 5.28, DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
  (4, 50.80, 49.10, 5.15, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
  (4, 51.60, 48.20, 5.31, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (4, 52.40, 47.50, 5.09, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
  (4, 51.90, 48.00, 5.22, DATE_SUB(NOW(), INTERVAL  2 MINUTE));

-- L-005 · sin registros a propósito (estado "Sin lecturas")

-- L-006 · historial de un ciclo completo, de fase activa a maduración
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (6, 58.20, 58.40, 6.85, DATE_SUB(NOW(), INTERVAL 130 DAY)),
  (6, 61.50, 54.10, 7.12, DATE_SUB(NOW(), INTERVAL 110 DAY)),
  (6, 52.30, 47.60, 7.35, DATE_SUB(NOW(), INTERVAL  80 DAY)),
  (6, 38.70, 38.20, 7.48, DATE_SUB(NOW(), INTERVAL  50 DAY)),
  (6, 28.40, 29.50, 7.52, DATE_SUB(NOW(), INTERVAL  30 DAY)),
  (6, 24.10, 24.30, 7.46, DATE_SUB(NOW(), INTERVAL  22 DAY));

-- ---------------------------------------------------------------------
-- Predicciones históricas del lote cerrado
-- Muestran la evolución del proceso: de deficiente al inicio a óptimo al final.
-- ---------------------------------------------------------------------
INSERT INTO predicciones (id_lote, resultado, confianza, fecha) VALUES
  (6, 'deficiente', 71.40, DATE_SUB(NOW(), INTERVAL 110 DAY)),
  (6, 'aceptable',  64.80, DATE_SUB(NOW(), INTERVAL  80 DAY)),
  (6, 'aceptable',  77.20, DATE_SUB(NOW(), INTERVAL  50 DAY)),
  (6, 'optimo',     92.60, DATE_SUB(NOW(), INTERVAL  22 DAY));
