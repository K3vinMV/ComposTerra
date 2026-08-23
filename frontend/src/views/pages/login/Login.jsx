/** Login glass — diseño Composta Monitor. */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CSpinner } from '@coreui/react'
import { login } from '../../../api/composta'
import { IconoHoja } from '../../../components/icons'

const Login = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  const entrar = async (e) => {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await login(email, password)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('usuario', JSON.stringify(data.usuario))
      navigate('/dashboard')
    } catch (err) {
      setError(
        err.response?.status === 401
          ? 'Correo o contraseña incorrectos'
          : 'No se pudo conectar con el servidor',
      )
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="cm-app">
      <div className="cm-bg-foto" />
      <div className="cm-velo" />
      <div
        className="cm-contenido"
        style={{ alignItems: 'center', justifyContent: 'center', zIndex: 3 }}
      >
        <form
          onSubmit={entrar}
          className="glass-card"
          style={{
            width: 380,
            maxWidth: 'calc(100vw - 32px)',
            padding: '40px 36px',
            borderRadius: 20,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            background: 'rgba(22,32,24,0.55)',
            boxShadow: '0 16px 48px rgba(0,0,0,0.35)',
          }}
        >
          <div className="cm-logo" style={{ width: 56, height: 56, marginBottom: 14 }}>
            <IconoHoja size={26} color="#FAF9F6" />
          </div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>Composta Monitor</div>
          <div style={{ fontSize: 13, color: 'rgba(250,249,246,0.6)', marginTop: 4, marginBottom: 26 }}>
            Sistema de monitoreo de composta
          </div>

          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
            {error && (
              <div className="cm-pill bad" style={{ textAlign: 'center', padding: '8px 12px', fontSize: 12.5 }}>
                {error}
              </div>
            )}
            <div>
              <div className="cm-label">Correo</div>
              <input
                className="cm-input"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <div className="cm-label">Contraseña</div>
              <input
                className="cm-input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button className="cm-btn" type="submit" disabled={cargando} style={{ marginTop: 6, padding: 12 }}>
              {cargando ? <CSpinner size="sm" /> : 'Iniciar sesión'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
