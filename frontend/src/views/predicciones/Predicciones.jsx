/** Predicciones — diseño glass: generar + resultado con confianza + historial. */
import React, { useEffect, useState } from 'react'
import { CSpinner } from '@coreui/react'
import { getLotes, getPredicciones, crearPrediccion } from '../../api/composta'

const CLASE_CALIDAD = { Alta: 'ok', Media: 'warn', Baja: 'bad' }
const COLOR_BARRA = { Alta: '#A8D5B0', Media: '#E8C574', Baja: '#E5A98F' }

const Predicciones = () => {
  const [lotes, setLotes] = useState([])
  const [idLote, setIdLote] = useState('')
  const [historial, setHistorial] = useState([])
  const [ultima, setUltima] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getLotes()
      .then((ls) => {
        setLotes(ls)
        if (ls.length > 0) setIdLote(String(ls[0].id))
      })
      .catch(() => setError('No se pudieron cargar los lotes'))
  }, [])

  useEffect(() => {
    if (!idLote) return
    setUltima(null)
    getPredicciones(idLote)
      .then(setHistorial)
      .catch(() => setHistorial([]))
  }, [idLote])

  const predecir = async () => {
    setCargando(true)
    setError('')
    try {
      const pred = await crearPrediccion(idLote)
      setUltima(pred)
      setHistorial(await getPredicciones(idLote))
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al generar la predicción')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="cm-grid-2" style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 16, alignItems: 'start' }}>
      <div className="glass-card">
        <div className="cm-card-titulo" style={{ marginBottom: 14 }}>
          Generar predicción
        </div>
        <div className="cm-label">Lote</div>
        <select className="cm-input" style={{ marginBottom: 14 }} value={idLote} onChange={(e) => setIdLote(e.target.value)}>
          {lotes.map((l) => (
            <option key={l.id} value={l.id}>
              Lote L-{String(l.id).padStart(3, '0')} — {l.material_principal} ({l.estado})
            </option>
          ))}
        </select>
        <button className="cm-btn" style={{ width: '100%' }} disabled={!idLote || cargando} onClick={predecir}>
          {cargando ? 'Analizando…' : 'Predecir calidad'}
        </button>

        {error && (
          <div className="cm-pill bad" style={{ marginTop: 14, display: 'block', textAlign: 'center', padding: '8px 12px', fontSize: 12.5 }}>
            {error}
          </div>
        )}

        {ultima && (
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.6)' }}>Calidad estimada</div>
            <div style={{ marginTop: 10 }}>
              <span
                className={`cm-pill ${CLASE_CALIDAD[ultima.resultado]}`}
                style={{ padding: '9px 28px', borderRadius: 12, fontSize: 20, fontWeight: 600 }}
              >
                {ultima.resultado}
              </span>
            </div>
            <div style={{ marginTop: 18, textAlign: 'left' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'rgba(250,249,246,0.6)', marginBottom: 6 }}>
                <span>Confianza</span>
                <span>{Number(ultima.confianza).toFixed(1)}%</span>
              </div>
              <div className="cm-barra">
                <div style={{ width: `${Number(ultima.confianza)}%`, background: COLOR_BARRA[ultima.resultado] }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="glass-card">
        <div className="cm-card-titulo" style={{ marginBottom: 10 }}>
          Historial de predicciones{' '}
          {idLote && (
            <span style={{ fontWeight: 400, color: 'rgba(250,249,246,0.55)', fontSize: 13 }}>
              — lote L-{String(idLote).padStart(3, '0')}
            </span>
          )}
        </div>
        <div className="cm-tabla-head" style={{ gridTemplateColumns: '1fr 130px 180px' }}>
          <span>Fecha</span>
          <span>Resultado</span>
          <span>Confianza</span>
        </div>
        {historial.map((p) => (
          <div className="cm-tabla-fila" key={p.id} style={{ gridTemplateColumns: '1fr 130px 180px' }}>
            <span style={{ color: 'rgba(250,249,246,0.8)' }}>{new Date(p.fecha).toLocaleString('es-MX')}</span>
            <span>
              <span className={`cm-pill ${CLASE_CALIDAD[p.resultado]}`}>{p.resultado}</span>
            </span>
            <span>
              <span className="cm-barra" style={{ display: 'block', height: 6 }}>
                <div style={{ width: `${Number(p.confianza)}%`, background: COLOR_BARRA[p.resultado] }} />
              </span>
              <span style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.55)' }}>{Number(p.confianza).toFixed(1)}%</span>
            </span>
          </div>
        ))}
        {historial.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(250,249,246,0.55)', fontSize: 13.5 }}>
            Este lote aún no tiene predicciones
          </div>
        )}
      </div>
    </div>
  )
}

export default Predicciones
