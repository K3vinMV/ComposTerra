import React, { useEffect, useRef, useState } from 'react'
import { describirAlerta, getAlertas } from '../api/composta'
import { IconoAlerta, IconoCampana } from './icons'

const INTERVALO_MS = 10000
const DURACION_TOAST_MS = 8000

const hace = (iso) => {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'hace un momento'
  if (min < 60) return `hace ${min} min`
  const h = Math.round(min / 60)
  return h < 24 ? `hace ${h} h` : `hace ${Math.round(h / 24)} d`
}

const AlertasMonitor = () => {
  const [abiertas, setAbiertas] = useState([])
  const [toasts, setToasts] = useState([])
  const [panel, setPanel] = useState(false)
  const ultimoId = useRef(null)

  useEffect(() => {
    let activo = true
    const consultar = async () => {
      try {
        const lista = await getAlertas({ limit: 50 })
        if (!activo) return
        setAbiertas(lista.filter((a) => !a.cerrada_en))

        const maxId = lista.reduce((m, a) => Math.max(m, a.id), 0)
        if (ultimoId.current !== null) {
          const nuevas = lista.filter((a) => a.id > ultimoId.current && !a.cerrada_en)
          if (nuevas.length) setToasts((t) => [...t, ...nuevas])
          nuevas.forEach((a) =>
            setTimeout(() => setToasts((t) => t.filter((x) => x.id !== a.id)), DURACION_TOAST_MS),
          )
        }
        ultimoId.current = Math.max(ultimoId.current ?? 0, maxId)
      } catch {
        // Sin conexión momentánea: se reintenta en el siguiente ciclo.
      }
    }
    consultar()
    const t = setInterval(consultar, INTERVALO_MS)
    return () => {
      activo = false
      clearInterval(t)
    }
  }, [])

  return (
    <>
      <div className="cm-alertas">
        <button
          type="button"
          className={`cm-chip-fecha cm-campana ${abiertas.length ? 'activa' : ''}`}
          onClick={() => setPanel((v) => !v)}
          aria-label="Alertas activas"
        >
          <IconoCampana size={16} />
          {abiertas.length > 0 && <span className="cm-campana-num">{abiertas.length}</span>}
        </button>

        {panel && (
          <div className="cm-alertas-panel">
            <div className="cm-alertas-titulo">Alertas activas</div>
            {abiertas.length === 0 ? (
              <div className="cm-alertas-vacio">Todos los lotes en rango</div>
            ) : (
              abiertas.map((a) => (
                <div key={a.id} className="cm-alertas-item">
                  <IconoAlerta size={15} />
                  <div>
                    <div>{describirAlerta(a)}</div>
                    <div className="cm-alertas-hora">{hace(a.abierta_en)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <div className="cm-toasts">
        {toasts.map((a) => (
          <div
            key={a.id}
            className="cm-toast"
            onClick={() => setToasts((t) => t.filter((x) => x.id !== a.id))}
          >
            <IconoAlerta size={18} />
            <div>
              <div className="cm-toast-titulo">Nueva alerta</div>
              <div>{describirAlerta(a)}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

export default AlertasMonitor
