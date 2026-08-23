/** Funciones de la API del sistema de composta. */
import client from './client'

// Rangos óptimos (para alertas y colores)
export const RANGOS = {
  temperatura: { min: 45, max: 65, unidad: '°C', label: 'Temperatura' },
  humedad: { min: 40, max: 60, unidad: '%', label: 'Humedad' },
  ph: { min: 6, max: 8, unidad: '', label: 'pH' },
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
