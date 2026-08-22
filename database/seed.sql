-- =====================================================================
-- Datos de ejemplo para desarrollo
-- Uso: mysql -u root -p < seed.sql
-- Nota: el usuario admin se crea con backend/scripts/crear_admin.py
--       (para generar el hash bcrypt correctamente)
-- =====================================================================

USE composta_db;

INSERT INTO lotes (fecha_inicio, material_principal, peso_kg, estado) VALUES
  ('2026-06-01', 'Restos de fruta y verdura', 120.50, 'activo'),
  ('2026-06-10', 'Hojas secas y pasto',        80.00, 'activo'),
  ('2026-05-15', 'Estiércol y paja',          200.00, 'finalizado');

-- Registros de sensor de ejemplo (lote 1: dentro de rango óptimo)
INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph, timestamp) VALUES
  (1, 52.30, 48.10, 6.80, '2026-07-06 10:00:00'),
  (1, 54.10, 50.20, 6.90, '2026-07-06 10:00:05'),
  (1, 55.60, 49.70, 7.00, '2026-07-06 10:00:10'),
  -- lote 2: humedad baja (fuera de rango → alerta)
  (2, 47.00, 35.50, 6.50, '2026-07-06 10:00:00'),
  (2, 46.20, 34.80, 6.40, '2026-07-06 10:00:05'),
  -- lote 3: finalizado
  (3, 58.00, 55.00, 7.20, '2026-06-20 09:00:00');

INSERT INTO predicciones (id_lote, resultado, confianza, fecha) VALUES
  (3, 'optimo', 92.50, '2026-06-25 12:00:00');
