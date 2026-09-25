/** Predicciones — diseño glass: generar + resultado con confianza + historial. */
import React, { useEffect, useState } from 'react'
import { CSpinner } from '@coreui/react'
import { getLotes, getPredicciones, crearPrediccion } from '../../api/composta'

// La API devuelve los valores en minúscula (ENUM de la BD); aquí se traducen a
// la etiqueta visible, su estilo de badge y el color de la barra de confianza.
const ETIQUETA = { optimo: 'Óptimo', aceptable: 'Aceptable', deficiente: 'Deficiente' }
const CLASE_CALIDAD = { optimo: 'ok', aceptable: 'warn', deficiente: 'bad' }
const COLOR_BARRA = { optimo: '#A8D5B0', aceptable: '#E8C574', deficiente: '#E5A98F' }

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
                {ETIQUETA[ultima.resultado] || ultima.resultado}
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

            {/* De dónde sale esa confianza: la votación del ensamble */}
            {ultima.votos && (
              <div style={{ marginTop: 22, textAlign: 'left' }}>
                <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 3 }}>
                  Votación del ensamble
                </div>
                <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.55)', marginBottom: 10 }}>
                  Cómo votaron los {ultima.votos.total_arboles} árboles
                </div>
                {Object.entries(ultima.votos.por_clase)
                  .sort((a, b) => b[1].arboles - a[1].arboles)
                  .map(([clase, v]) => (
                    <div key={clase} style={{ marginBottom: 9 }}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          fontSize: 11.5,
                          marginBottom: 4,
                          color:
                            clase === ultima.resultado
                              ? 'var(--crema)'
                              : 'rgba(250,249,246,0.6)',
                        }}
                      >
                        <span>{ETIQUETA[clase] || clase}</span>
                        <span>
                          {v.arboles} de {ultima.votos.total_arboles}
                        </span>
                      </div>
                      <span className="cm-barra" style={{ display: 'block', height: 5 }}>
                        <div
                          style={{
                            width: `${v.proporcion}%`,
                            background:
                              clase === ultima.resultado
                                ? COLOR_BARRA[clase]
                                : 'rgba(250,249,246,0.25)',
                          }}
                        />
                      </span>
                    </div>
                  ))}
              </div>
            )}

            {/* Entradas exactas que recibió el modelo */}
            {ultima.entradas && (
              <div
                style={{
                  marginTop: 18,
                  paddingTop: 14,
                  borderTop: '1px solid rgba(255,255,255,0.1)',
                  textAlign: 'left',
                  fontSize: 11.5,
                  color: 'rgba(250,249,246,0.55)',
                  lineHeight: 1.6,
                }}
              >
                <div style={{ fontWeight: 600, color: 'rgba(250,249,246,0.8)', marginBottom: 5 }}>
                  Entradas del modelo
                </div>
                Avance del ciclo {(ultima.entradas.progreso * 100).toFixed(0)}% (día{' '}
                {ultima.entradas.dias_transcurridos} de{' '}
                {ultima.entradas.duracion_estimada_dias})
                <br />
                {ultima.entradas.temperatura} °C · {ultima.entradas.humedad} % ·
                pH {ultima.entradas.ph}
                <br />
                <span style={{ color: 'rgba(250,249,246,0.4)' }}>
                  Promedio de las lecturas de las últimas 24 h
                </span>
              </div>
            )}
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
              <span className={`cm-pill ${CLASE_CALIDAD[p.resultado]}`}>
                {ETIQUETA[p.resultado] || p.resultado}
              </span>
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
