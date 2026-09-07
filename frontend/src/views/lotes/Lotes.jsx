/** Lotes — tabla glass con últimas lecturas por lote, alta y finalizar. */
import React, { useEffect, useState } from 'react'
import { CSpinner } from '@coreui/react'
import {
  getLotes,
  getRegistros,
  crearLote,
  cambiarEstado,
  requiereAlerta,
  fase,
} from '../../api/composta'

const hoy = () => new Date().toISOString().slice(0, 10)
const COLS = '64px 110px minmax(120px,1fr) 84px 76px 84px 56px 110px 96px'


const Lotes = () => {
  const [filas, setFilas] = useState(null)
  const [error, setError] = useState('')
  const [modal, setModal] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [form, setForm] = useState({
    fecha_inicio: hoy(),
    material_principal: '',
    peso_kg: '',
    duracion_estimada_dias: 120,
  })

  const cargar = async () => {
    try {
      const lotes = await getLotes()
      const lecturas = await Promise.all(
        lotes.map((l) => getRegistros(l.id, 1).then((r) => r[0] || null).catch(() => null)),
      )
      setFilas(
        lotes.map((l, i) => {
          const u = lecturas[i]
          // El estado considera la fase: durante la maduración, enfriarse y
          // secarse es lo esperado y no cuenta como advertencia.
          const params = u
            ? ['temperatura', 'humedad', 'ph'].some((p) => requiereAlerta(p, Number(u[p]), l))
              ? 'Advertencia'
              : fase(l) === 'maduracion'
                ? 'Maduración'
                : 'Óptimo'
            : null
          return { ...l, ultima: u, param: params }
        }),
      )
    } catch {
      setError('No se pudieron cargar los lotes. ¿Está corriendo la API?')
    }
  }

  useEffect(() => {
    cargar()
    const t = setInterval(cargar, 5000) // refresco en vivo, igual que el Dashboard
    return () => clearInterval(t)
  }, [])

  const guardar = async (e) => {
    e.preventDefault()
    setGuardando(true)
    setError('')
    try {
      await crearLote({
        ...form,
        peso_kg: parseFloat(form.peso_kg),
        duracion_estimada_dias: parseInt(form.duracion_estimada_dias, 10),
      })
      setModal(false)
      setForm({
        fecha_inicio: hoy(),
        material_principal: '',
        peso_kg: '',
        duracion_estimada_dias: 120,
      })
      await cargar()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear el lote')
    } finally {
      setGuardando(false)
    }
  }

  const finalizar = async (id) => {
    await cambiarEstado(id, 'finalizado')
    await cargar()
  }

  return (
    <>
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <span className="cm-card-titulo">Historial de lotes</span>
          <button className="cm-btn" style={{ padding: '9px 18px', fontSize: 13 }} onClick={() => setModal(true)}>
            Nuevo lote
          </button>
        </div>

        {error && (
          <div className="cm-pill bad" style={{ marginBottom: 12, display: 'inline-block' }}>
            {error}
          </div>
        )}

        {filas === null ? (
          <div style={{ textAlign: 'center', padding: '30px 0' }}>
            <CSpinner color="light" />
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <div style={{ minWidth: 730 }}>
              <div className="cm-tabla-head" style={{ gridTemplateColumns: COLS }}>
                <span>Lote</span>
                <span>Fecha inicio</span>
                <span>Material principal</span>
                <span>Peso (kg)</span>
                <span>Temp.</span>
                <span>Humedad</span>
                <span>pH</span>
                <span>Estado</span>
                <span />
              </div>
              {filas.map((l) => (
                <div className="cm-tabla-fila" key={l.id} style={{ gridTemplateColumns: COLS }}>
                  <span style={{ fontWeight: 500 }}>L-{String(l.id).padStart(3, '0')}</span>
                  <span style={{ color: 'rgba(250,249,246,0.75)' }}>{l.fecha_inicio}</span>
                  <span style={{ color: 'rgba(250,249,246,0.85)' }}>{l.material_principal}</span>
                  <span>{Number(l.peso_kg).toFixed(1)}</span>
                  <span>{l.ultima ? `${Number(l.ultima.temperatura).toFixed(1)} °C` : '—'}</span>
                  <span>{l.ultima ? `${Number(l.ultima.humedad).toFixed(0)} %` : '—'}</span>
                  <span>{l.ultima ? Number(l.ultima.ph).toFixed(1) : '—'}</span>
                  <span>
                    {l.estado === 'finalizado' ? (
                      <span className="cm-pill neutro">Finalizado</span>
                    ) : l.param ? (
                      <span
                        className={`cm-pill ${
                          l.param === 'Óptimo' ? 'ok' : l.param === 'Maduración' ? 'info' : 'warn'
                        }`}
                      >
                        {l.param}
                      </span>
                    ) : (
                      <span className="cm-pill info">Sin lecturas</span>
                    )}
                  </span>
                  <span style={{ textAlign: 'right' }}>
                    {l.estado === 'activo' && (
                      <button className="cm-btn-ghost" style={{ padding: '5px 12px', fontSize: 12 }} onClick={() => finalizar(l.id)}>
                        Finalizar
                      </button>
                    )}
                  </span>
                </div>
              ))}
              {filas.length === 0 && (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'rgba(250,249,246,0.55)', fontSize: 13.5 }}>
                  Sin lotes registrados
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {modal && (
        <div className="cm-modal-overlay" onClick={() => setModal(false)}>
          <form className="cm-modal" onClick={(e) => e.stopPropagation()} onSubmit={guardar}>
            <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 18 }}>Nuevo lote de composta</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <div className="cm-label">Fecha de inicio</div>
                <input
                  className="cm-input"
                  type="date"
                  value={form.fecha_inicio}
                  onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })}
                  required
                />
              </div>
              <div>
                <div className="cm-label">Material principal</div>
                <input
                  className="cm-input"
                  placeholder="Ej. Restos de fruta y verdura"
                  value={form.material_principal}
                  onChange={(e) => setForm({ ...form, material_principal: e.target.value })}
                  maxLength={100}
                  required
                />
              </div>
              <div>
                <div className="cm-label">Peso (kg)</div>
                <input
                  className="cm-input"
                  type="number"
                  min="0.1"
                  step="0.1"
                  placeholder="0.0"
                  value={form.peso_kg}
                  onChange={(e) => setForm({ ...form, peso_kg: e.target.value })}
                  required
                />
              </div>
              <div>
                <div className="cm-label">Duración estimada del ciclo (días)</div>
                <input
                  className="cm-input"
                  type="number"
                  min="1"
                  max="365"
                  value={form.duracion_estimada_dias}
                  onChange={(e) => setForm({ ...form, duracion_estimada_dias: e.target.value })}
                  required
                />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 22 }}>
              <button type="button" className="cm-btn-ghost" onClick={() => setModal(false)}>
                Cancelar
              </button>
              <button type="submit" className="cm-btn" style={{ padding: '9px 18px', fontSize: 13 }} disabled={guardando}>
                {guardando ? <CSpinner size="sm" /> : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )
}

export default Lotes
