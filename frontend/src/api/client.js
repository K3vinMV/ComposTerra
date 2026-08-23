/**
 * Cliente Axios central.
 * - Agrega el JWT a cada petición
 * - Si el token expira (401), limpia sesión y manda a /login
 * - En AWS solo cambia VITE_API_URL al dominio de API Gateway
 */
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const esLogin = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !esLogin) {
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      window.location.hash = '#/login'
    }
    return Promise.reject(error)
  },
)

export default client
