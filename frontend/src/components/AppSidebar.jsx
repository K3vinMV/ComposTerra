/** Sidebar glass del diseño Composta Monitor. */
import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { IconoHoja, IconoDashboard, IconoLotes, IconoPredicciones, IconoSalir } from './icons'

const NAV = [
  { to: '/dashboard', nombre: 'Dashboard', Icono: IconoDashboard },
  { to: '/lotes', nombre: 'Lotes', Icono: IconoLotes },
  { to: '/predicciones', nombre: 'Predicciones', Icono: IconoPredicciones },
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
        <div className="cm-logo">
          <IconoHoja size={19} color="#FAF9F6" />
        </div>
        <div>
          Composta
          <br />
          Monitor
        </div>
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
