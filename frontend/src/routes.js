/** Rutas protegidas del sistema. */
import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))
const Lotes = React.lazy(() => import('./views/lotes/Lotes'))
const Predicciones = React.lazy(() => import('./views/predicciones/Predicciones'))
const Modelo = React.lazy(() => import('./views/modelo/Modelo'))

export const routes = [
  { path: '/', exact: true, name: 'Inicio' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },
  { path: '/lotes', name: 'Lotes', element: Lotes },
  { path: '/predicciones', name: 'Predicciones', element: Predicciones },
  { path: '/modelo', name: 'Modelo', element: Modelo },
]

export default routes
