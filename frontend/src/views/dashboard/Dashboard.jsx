/**
 * Dashboard glass — diseño Composta Monitor con datos reales:
 * KPIs (lotes activos + 3 métricas en vivo), gráfica histórica,
 * anillo de estado y alertas. Poll cada 5 s.
 */
import React, { useCallback, useEffect, useState } from 'react'
import { CSpinner } from '@coreui/react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  getLotes,
  getRegistros,
  RANGOS,
  requiereAlerta,
  fase,
  progresoLote,
} from '../../api/composta'
import { IconoHoja, IconoAlerta, IconoOk } from '../../components/icons'

const COLORES = { temperatura: '#E5A98F', humedad: '#A9C6E2', ph: '#A8D5B0' }
const INTERVALO_MS = 5000

const fueraDeRango = (p, v) => v < RANGOS[p].min || v > RANGOS[p].max

const Dashboard = () => {
  const [lotes, setLotes] = useState([])
  const [idLote, setIdLote] = useState('')
  const [historico, setHistorico] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    getLotes()
      .then((ls) => {
        setLotes(ls)
        const activo = ls.find((l) => l.estado === 'activo') || ls[0]
        if (activo) setIdLote(String(activo.id))
      })
      .catch(() => setError('No se pudieron cargar los lotes. ¿Está corriendo la API?'))
  }, [])

  const refrescar = useCallback(async () => {
    if (!idLote) return
    try {
      const regs = await getRegistros(idLote, 100)
      setHistorico(
        regs
          .slice()
          .reverse()
          .map((x) => ({
            hora: new Date(x.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            }),
            temperatura: Number(x.temperatura),
            humedad: Number(x.humedad),
            ph: Number(x.ph),
          })),
      )
      setError('')
    } catch {
      setError('Error al consultar registros del sensor')
    }
  }, [idLote])

  useEffect(() => {
    refrescar()
    const t = setInterval(refrescar, INTERVALO_MS)
    return () => clearInterval(t)
  }, [refrescar])

  const ultimo = historico.length > 0 ? historico[historico.length - 1] : null
  const loteSel = lotes.find((l) => String(l.id) === idLote)
  const enMaduracion = loteSel && fase(loteSel) === 'maduracion'
  const alertas = ultimo
    ? Object.keys(RANGOS).filter((p) => requiereAlerta(p, ultimo[p], loteSel))
    : []
  const lotesActivos = lotes.filter((l) => l.estado === 'activo').length
  const enRango = ultimo ? 3 - alertas.length : 0
  const circunferencia = 2 * Math.PI * 62
  const anillo = ultimo ? (enRango / 3) * circunferencia : 0
  const colorAnillo = !ultimo ? 'rgba(255,255,255,0.25)' : alertas.length === 0 ? 'var(--acento)' : alertas.length < 3 ? '#E8C574' : '#E5A98F'

  const kpi = (param) => {
    const r = RANGOS[param]
    const v = ultimo ? ultimo[param] : null
    const alerta = v !== null && requiereAlerta(param, v, loteSel)
    // Fuera del rango activo pero sin alerta = descenso normal de la maduración
    const normalizando = v !== null && !alerta && fueraDeRango(param, v)

    let etiqueta = 'Óptimo'
    let clase = 'ok'
    if (v === null) {
      etiqueta = 'Sin datos'
      clase = 'neutro'
    } else if (alerta) {
      etiqueta = 'Fuera de rango'
      clase = 'bad'
    } else if (normalizando) {
      etiqueta = 'Maduración'
      clase = 'info'
    }

    return (
      <div className="glass-card" key={param} style={{ padding: '18px 20px' }}>
        <div className="cm-kpi-label">{r.label} actual</div>
        <div className="cm-kpi-valor">
          {v === null ? '—' : v.toFixed(1)}
          {v !== null && r.unidad && <span className="cm-kpi-unidad">{r.unidad}</span>}
        </div>
        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className={`cm-pill ${clase}`}>{etiqueta}</span>
          <span style={{ fontSize: 11, color: 'rgba(250,249,246,0.5)' }}>
            {r.min}–{r.max}
            {r.unidad}
          </span>
        </div>
      </div>
    )
  }

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 300 }}>
          <select className="cm-input" value={idLote} onChange={(e) => setIdLote(e.target.value)}>
            {lotes.map((l) => (
              <option key={l.id} value={l.id}>
                Lote {l.id} — {l.material_principal} ({l.estado})
              </option>
            ))}
          </select>
        </div>
        {error && <span className="cm-pill bad">{error}</span>}
      </div>

      <div className="cm-kpi-grid">
        <div className="glass-card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="cm-kpi-label">Lotes activos</div>
              <div className="cm-kpi-valor">{lotesActivos}</div>
            </div>
            <div className="cm-kpi-icono">
              <IconoHoja size={19} color="#A8D5B0" />
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#A8D5B0', marginTop: 8 }}>de {lotes.length} en total</div>
        </div>
        {Object.keys(RANGOS).map(kpi)}
      </div>

      <div className="cm-grid-2" style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 300px', gap: 16, marginTop: 16 }}>
        <div className="glass-card" style={{ minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 16 }}>
            <div className="cm-dot-vivo" />
            <span className="cm-card-titulo">Histórico del lote {idLote}</span>
            <span style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)' }}>
              · últimas {historico.length} lecturas, cada 5 s
            </span>
          </div>
          <div style={{ height: 260 }}>
            {historico.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'rgba(250,249,246,0.6)', paddingTop: 70 }}>
                <CSpinner color="light" size="sm" style={{ display: 'block', margin: '0 auto 10px' }} />
                Esperando lecturas del sensor…
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historico}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                  <XAxis dataKey="hora" minTickGap={40} tick={{ fill: 'rgba(250,249,246,0.5)', fontSize: 11 }} stroke="rgba(255,255,255,0.15)" />
                  <YAxis yAxisId="izq" tick={{ fill: 'rgba(250,249,246,0.5)', fontSize: 11 }} stroke="rgba(255,255,255,0.15)" />
                  <YAxis yAxisId="der" orientation="right" domain={[0, 14]} tick={{ fill: 'rgba(250,249,246,0.5)', fontSize: 11 }} stroke="rgba(255,255,255,0.15)" />
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(28,40,30,0.95)',
                      border: '1px solid rgba(255,255,255,0.16)',
                      borderRadius: 10,
                      color: '#FAF9F6',
                      fontSize: 12.5,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: 'rgba(250,249,246,0.7)' }} />
                  <Line yAxisId="izq" type="monotone" dataKey="temperatura" name="Temperatura (°C)" stroke={COLORES.temperatura} dot={false} strokeWidth={2} />
                  <Line yAxisId="izq" type="monotone" dataKey="humedad" name="Humedad (%)" stroke={COLORES.humedad} dot={false} strokeWidth={2} />
                  <Line yAxisId="der" type="monotone" dataKey="ph" name="pH" stroke={COLORES.ph} dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <span className="cm-card-titulo" style={{ alignSelf: 'flex-start' }}>
            Estado actual
          </span>
          <div style={{ position: 'relative', width: 150, height: 150, marginTop: 18 }}>
            <svg viewBox="0 0 150 150" width="150" height="150">
              <circle cx="75" cy="75" r="62" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="10" />
              <circle
                cx="75"
                cy="75"
                r="62"
                transform="rotate(-90 75 75)"
                fill="none"
                stroke={colorAnillo}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={`${anillo} ${circunferencia + 1}`}
              />
            </svg>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 19, fontWeight: 600 }}>
              {!ultimo ? 'Sin datos' : alertas.length === 0 ? 'Óptimo' : 'Alerta'}
            </div>
          </div>
          <div style={{ fontSize: 12.5, color: 'rgba(250,249,246,0.6)', textAlign: 'center', marginTop: 16, lineHeight: 1.5 }}>
            {!ultimo
              ? 'Este lote aún no tiene lecturas'
              : alertas.length === 0
                ? enMaduracion
                  ? 'Proceso en maduración, sin incidencias'
                  : 'Todo dentro de los parámetros ideales'
                : `${enRango} de 3 parámetros requieren atención`}
          </div>
          {loteSel && (
            <>
              <div style={{ marginTop: 12 }}>
                <span className={`cm-pill ${enMaduracion ? 'info' : 'ok'}`}>
                  {enMaduracion ? 'Fase de maduración' : 'Fase activa'}
                </span>
              </div>
              <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.45)', marginTop: 10, textAlign: 'center' }}>
                {Math.round(progresoLote(loteSel) * 100)}% del ciclo ·{' '}
                {loteSel.duracion_estimada_dias} días estimados
                <br />
                {loteSel.material_principal} · {Number(loteSel.peso_kg).toFixed(1)} kg
              </div>
            </>
          )}
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: 16 }}>
        <div className="cm-card-titulo" style={{ marginBottom: 6 }}>
          Alertas del lote {idLote}
        </div>
        {alertas.length === 0 ? (
          <div className="cm-alerta">
            <IconoOk size={18} color="#8FCB9B" />
            <span style={{ flex: 1 }}>
              {!ultimo
                ? 'Sin lecturas del sensor todavía'
                : enMaduracion
                  ? 'El lote está en maduración: el enfriamiento y el secado son esperados en esta fase'
                  : 'Sin alertas: todos los parámetros están en su rango óptimo'}
            </span>
            {ultimo && <span className="cm-pill ok">Éxito</span>}
          </div>
        ) : (
          alertas.map((p) => (
            <div className="cm-alerta" key={p}>
              <IconoAlerta size={18} color="#E0B24E" />
              <span style={{ flex: 1 }}>
                {RANGOS[p].label} fuera del rango óptimo ({RANGOS[p].min}–{RANGOS[p].max}
                {RANGOS[p].unidad}): actualmente{' '}
                <strong>
                  {ultimo[p].toFixed(1)}
                  {RANGOS[p].unidad}
                </strong>
              </span>
              <span className="cm-pill warn">Advertencia</span>
            </div>
          ))
        )}
      </div>
    </>
  )
}

export default Dashboard
