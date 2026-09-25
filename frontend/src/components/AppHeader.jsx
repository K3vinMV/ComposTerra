/** Header del diseño: título por vista + chip de fecha/hora en vivo. */
import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { IconoCalendario, IconoReloj } from './icons'

const TITULOS = {
  '/dashboard': ['Resumen general del sistema'],
  '/lotes': ['Lotes', 'Historial y gestión de lotes de composta'],
  '/predicciones': ['Predicciones', 'Estado del proceso estimado con Random Forest'],
  '/modelo': ['Modelo', ''],
}

const AppHeader = () => {
  const { pathname } = useLocation()
  const [ahora, setAhora] = useState(new Date())
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')

  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 30000)
    return () => clearInterval(t)
  }, [])

  const config = TITULOS[pathname]
  const titulo = pathname === '/dashboard' || !config ? `Hola, ${usuario.nombre || 'Usuario'}` : config[0]
  const subtitulo = pathname === '/dashboard' || !config ? 'Resumen general del sistema' : config[1]

  const fecha = ahora.toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' })
  const hora = ahora.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="cm-header">
      <div>
        <div className="cm-titulo">{titulo}</div>
        <div className="cm-subtitulo">{subtitulo}</div>
      </div>
      <div className="cm-chip-fecha">
        <IconoCalendario size={15} />
        <span>{fecha}</span>
        <span style={{ color: 'rgba(250,249,246,0.35)' }}>·</span>
        <IconoReloj size={15} />
        <span>{hora}</span>
      </div>
    </div>
  )
}

export default AppHeader
