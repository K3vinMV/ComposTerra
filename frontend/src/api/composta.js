/** Funciones de la API del sistema de composta. */
import client from './client'

export const RANGOS = {
  temperatura: { min: 45, max: 65, unidad: '°C', label: 'Temperatura' },
  humedad: { min: 40, max: 60, unidad: '%', label: 'Humedad' },
  ph: { min: 6, max: 8, unidad: '', label: 'pH' },
}

export const UMBRAL_MADURACION = 0.7

/** Avance del ciclo de un lote, de 0 (inicio) a 1 (fin esperado). */
export const progresoLote = (lote) => {
  if (!lote?.fecha_inicio) return 0
  const dias = (Date.now() - new Date(lote.fecha_inicio).getTime()) / 86400000
  const duracion = lote.duracion_estimada_dias || 120
  return Math.min(Math.max(dias / duracion, 0), 1)
}

/** Fase del proceso en la que se encuentra el lote. */
export const fase = (lote) =>
  progresoLote(lote) >= UMBRAL_MADURACION ? 'maduracion' : 'activa'

export const requiereAlerta = (param, valor, lote) => {
  const r = RANGOS[param]
  const fueraPorDebajo = valor < r.min
  const fueraPorArriba = valor > r.max
  if (!fueraPorDebajo && !fueraPorArriba) return false
  if (fase(lote) === 'maduracion' && fueraPorDebajo && param !== 'ph') return false
  return true
}

export const login = async (email, password) => {
  const { data } = await client.post('/auth/login', { email, password })
  return data // { access_token, token_type, usuario }
}

export const getLotes = async () => (await client.get('/lotes')).data

export const crearLote = async (lote) => (await client.post('/lotes', lote)).data

export const cambiarEstado = async (id, estado) =>
  (await client.patch(`/lotes/${id}/estado`, null, { params: { estado } })).data

export const getRegistros = async (idLote, limit = 100) =>
  (await client.get(`/lotes/${idLote}/registros`, { params: { limit } })).data

export const getPredicciones = async (idLote) =>
  (await client.get(`/lotes/${idLote}/predicciones`)).data

export const crearPrediccion = async (idLote) =>
  (await client.post(`/predicciones/${idLote}`)).data

/** Métricas del modelo en producción, generadas durante el entrenamiento. */
export const getInfoModelo = async () => (await client.get('/modelo/info')).data

/** Alertas registradas por el monitor (scripts/monitor_alertas.py). */
export const getAlertas = async (params = {}) =>
  (await client.get('/alertas', { params })).data

/** Texto corto para mostrar una alerta en pantalla. */
export const describirAlerta = (a) => {
  if (a.tipo === 'sin_datos') return `Lote ${a.id_lote} · el sensor dejó de reportar`
  const r = RANGOS[a.tipo]
  const valor = a.valor != null ? `${Number(a.valor).toFixed(a.tipo === 'ph' ? 2 : 1)}${r.unidad ? ' ' + r.unidad : ''}` : ''
  let estado = a.direccion === 'bajo' ? 'baja' : 'alta'
  if (a.tipo === 'ph') estado = a.direccion === 'bajo' ? 'ácido' : 'alcalino'
  return `Lote ${a.id_lote} · ${r.label} ${estado}${valor ? ` (${valor})` : ''}`
}
