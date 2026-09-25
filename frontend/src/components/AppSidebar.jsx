/** Sidebar glass del diseño ComposTerra. */
import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  IconoDashboard,
  IconoLotes,
  IconoPredicciones,
  IconoModelo,
  IconoSalir,
} from './icons'

const NAV = [
  { to: '/dashboard', nombre: 'Dashboard', Icono: IconoDashboard },
  { to: '/lotes', nombre: 'Lotes', Icono: IconoLotes },
  { to: '/predicciones', nombre: 'Predicciones', Icono: IconoPredicciones },
  { to: '/modelo', nombre: 'Modelo', Icono: IconoModelo },
]

const AppSidebar = () => {
  const navigate = useNavigate()
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
  const iniciales = (usuario.nombre || 'U')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  const cerrarSesion = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
    navigate('/login')
  }

  return (
    <aside className="cm-sidebar">
      <div className="cm-brand">
        <img src="/logo.png" alt="" style={{ width: 42, height: 'auto', flexShrink: 0 }} />
        <div>ComposTerra</div>
      </div>

      <nav className="cm-nav">
        {NAV.map(({ to, nombre, Icono }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `cm-nav-item${isActive ? ' activo' : ''}`}>
            <Icono size={18} />
            <span>{nombre}</span>
          </NavLink>
        ))}
      </nav>

      <div style={{ flex: 1 }} />

      <div className="cm-usuario">
        <div className="cm-avatar">{iniciales}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 500, lineHeight: 1.2 }}>{usuario.nombre || 'Usuario'}</div>
          <div style={{ fontSize: 11, color: 'rgba(250,249,246,0.55)' }}>{usuario.rol || ''}</div>
        </div>
        <button className="cm-logout" title="Cerrar sesión" onClick={cerrarSesion}>
          <IconoSalir size={15} />
        </button>
      </div>
    </aside>
  )
}

export default React.memo(AppSidebar)
