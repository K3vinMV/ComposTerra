/** Funciones de la API del sistema de composta. */
import client from './client'

// Rangos óptimos de la FASE ACTIVA del compostaje (para alertas y colores).
// Ojo: estos rangos aplican mientras la pila está trabajando. Al final del
// ciclo la composta se enfría y se seca de forma natural, así que salir del
// rango en esa etapa no es una falla — ver `fase()` más abajo.
export const RANGOS = {
  temperatura: { min: 45, max: 65, unidad: '°C', label: 'Temperatura' },
  humedad: { min: 40, max: 60, unidad: '%', label: 'Humedad' },
  ph: { min: 6, max: 8, unidad: '', label: 'pH' },
}

// A partir de este avance del ciclo se considera que el lote entró en
// maduración y se dejan de emitir alertas por enfriamiento y secado.
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

/**
 * Determina si un valor debe generar alerta, considerando la fase.
 * Durante la maduración, que la temperatura o la humedad bajen del rango es el
 * comportamiento esperado y no se alerta. El pH sí se vigila siempre: un pH
 * fuera de rango indica un problema en cualquier etapa.
 */
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
