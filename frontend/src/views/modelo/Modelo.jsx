/**
 * Vista Modelo
 */
import React, { useEffect, useState } from 'react'
import { CSpinner } from '@coreui/react'
import { getInfoModelo } from '../../api/composta'

const ETIQUETA = { optimo: 'Óptimo', aceptable: 'Aceptable', deficiente: 'Deficiente' }
const NOMBRE_VAR = {
  progreso: 'Avance del ciclo',
  temperatura: 'Temperatura',
  humedad: 'Humedad',
  ph: 'pH',
}

const Paso = ({ n, titulo, children }) => (
  <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
    <div
      style={{
        width: 28,
        height: 28,
        borderRadius: '50%',
        background: 'var(--acento)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 13,
        fontWeight: 600,
        flexShrink: 0,
      }}
    >
      {n}
    </div>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 3 }}>{titulo}</div>
      <div style={{ fontSize: 12.5, color: 'rgba(250,249,246,0.65)', lineHeight: 1.55 }}>
        {children}
      </div>
    </div>
  </div>
)

const Barra = ({ valor, max = 1, color = 'var(--acento)' }) => (
  <span className="cm-barra" style={{ display: 'block', height: 6 }}>
    <div style={{ width: `${(valor / max) * 100}%`, background: color }} />
  </span>
)

const Modelo = () => {
  const [info, setInfo] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getInfoModelo()
      .then(setInfo)
      .catch((err) =>
        setError(
          err.response?.data?.detail || 'No se pudo cargar la información del modelo',
        ),
      )
  }, [])

  if (error) {
    return (
      <div className="glass-card">
        <span className="cm-pill bad">{error}</span>
      </div>
    )
  }

  if (!info) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: 40 }}>
        <CSpinner color="light" />
      </div>
    )
  }

  const { dataset, particion, hiperparametros, desempeno } = info
  const mc = info.matriz_confusion
  const impOrdenada = Object.entries(info.importancia_variables).sort((a, b) => b[1] - a[1])
  const maxImp = Math.max(...impOrdenada.map(([, v]) => v))

  return (
    <>
      {/* ---------- Resumen ---------- */}
      <div className="cm-kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="glass-card" style={{ padding: '18px 20px' }}>
          <div className="cm-kpi-label">Exactitud</div>
          <div className="cm-kpi-valor">
            {(desempeno.accuracy * 100).toFixed(1)}
            <span className="cm-kpi-unidad">%</span>
          </div>
          <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.5)', marginTop: 6 }}>
            conjunto de prueba
          </div>
        </div>
        <div className="glass-card" style={{ padding: '18px 20px' }}>
          <div className="cm-kpi-label">Validación cruzada</div>
          <div className="cm-kpi-valor">
            {(desempeno.accuracy_validado * 100).toFixed(1)}
            <span className="cm-kpi-unidad">%</span>
          </div>
          <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.5)', marginTop: 6 }}>
            media de {desempeno.particiones_validacion} particiones
          </div>
        </div>
        <div className="glass-card" style={{ padding: '18px 20px' }}>
          <div className="cm-kpi-label">F1 macro</div>
          <div className="cm-kpi-valor">{desempeno.f1_macro.toFixed(3)}</div>
          <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.5)', marginTop: 6 }}>
            promedio entre clases
          </div>
        </div>
        <div className="glass-card" style={{ padding: '18px 20px' }}>
          <div className="cm-kpi-label">Muestras</div>
          <div className="cm-kpi-valor">{dataset.muestras}</div>
          <div style={{ fontSize: 11.5, color: 'rgba(250,249,246,0.5)', marginTop: 6 }}>
            en {dataset.lotes} lotes experimentales
          </div>
        </div>
      </div>

      {/* ---------- Flujo ---------- */}
      <div className="glass-card" style={{ marginTop: 16 }}>
        <div className="cm-card-titulo" style={{ marginBottom: 18 }}>
          Flujo del clasificador
        </div>
        <div style={{ display: 'grid', gap: 14 }}>
          <Paso n="1" titulo="Datos">
            {dataset.muestras} muestras · {dataset.lotes} ciclos de compostaje ·{' '}
            {dataset.fuente}
          </Paso>
          <Paso n="2" titulo="Etiquetas">
            Índice de madurez de laboratorio · óptimo desde{' '}
            {dataset.cortes_score.optimo} · aceptable desde{' '}
            {dataset.cortes_score.aceptable}
          </Paso>
          <Paso n="3" titulo="Variables">
            {Object.keys(info.importancia_variables)
              .map((v) => NOMBRE_VAR[v] || v)
              .join(' · ')}{' '}
            · avance normalizado de 0 a 1
          </Paso>
          <Paso n="4" titulo="Entrenamiento">
            {hiperparametros.n_estimators} árboles · profundidad{' '}
            {hiperparametros.max_depth} · pesos balanceados
          </Paso>
          <Paso n="5" titulo="Validación">
            Partición por lote · {particion.muestras_entrenamiento} muestras (
            {particion.lotes_entrenamiento} lotes) para entrenar ·{' '}
            {particion.muestras_prueba} ({particion.lotes_prueba} lotes) para probar
          </Paso>
          <Paso n="6" titulo="Predicción">
            Los {hiperparametros.n_estimators} árboles votan · gana la clase con
            más votos
          </Paso>
        </div>
      </div>

      {/* ---------- Cómo funciona el algoritmo ---------- */}
      <div className="glass-card" style={{ marginTop: 16 }}>
        <div className="cm-card-titulo">Cómo decide el modelo</div>
        <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)', margin: '4px 0 18px' }}>
          Random Forest — {hiperparametros.n_estimators} árboles votando
        </div>

        <div
          style={{
            fontSize: 13.5,
            color: 'rgba(250,249,246,0.8)',
            lineHeight: 1.6,
            maxWidth: 680,
          }}
        >
          Cada árbol vota por su cuenta. Gana el más votado, y 
            el porcentaje de votos que obtuvo es la confianza.
        </div>

        <div
          className="cm-grid-2"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            marginTop: 20,
          }}
        >
          <div
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 12,
              padding: '14px 16px',
            }}
          >
            <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}>
              Por qué un bosque y no un árbol
            </div>
            <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.65)', lineHeight: 1.55 }}>
              {(info.comparacion_algoritmos['Árbol de decisión (prof. 3)'] * 100).toFixed(1)}%
              con un árbol · {' '}
              {(info.comparacion_algoritmos['Random Forest (modelo final)'] * 100).toFixed(1)}%
              con el bosque
            </div>
          </div>

          <div
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 12,
              padding: '14px 16px',
            }}
          >
            <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 6 }}>
              Configuración
            </div>
            <div style={{ fontSize: 12, fontFamily: 'ui-monospace, monospace' }}>
              {Object.entries(hiperparametros).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'rgba(250,249,246,0.6)' }}>{k}</span>
                  <span>{String(v)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ---------- Comparaciones ---------- */}
      <div
        className="cm-grid-2"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
          marginTop: 16,
          alignItems: 'start',
        }}
      >
        <div className="glass-card">
          <div className="cm-card-titulo">¿Por qué Random Forest?</div>
          <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)', margin: '4px 0 14px' }}>
            
          </div>
          {Object.entries(info.comparacion_algoritmos).map(([nombre, v]) => {
            const esFinal = nombre.startsWith('Random')
            return (
              <div key={nombre} style={{ marginBottom: 12 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 12.5,
                    marginBottom: 5,
                    fontWeight: esFinal ? 600 : 400,
                    color: esFinal ? 'var(--crema)' : 'rgba(250,249,246,0.75)',
                  }}
                >
                  <span>{nombre}</span>
                  <span>{(v * 100).toFixed(1)}%</span>
                </div>
                <Barra
                  valor={v}
                  color={esFinal ? 'var(--acento)' : 'rgba(250,249,246,0.3)'}
                />
              </div>
            )
          })}
        </div>

        <div className="glass-card">
          <div className="cm-card-titulo">Aporte de cada variable</div>
          <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)', margin: '4px 0 14px' }}>
            
          </div>
          {impOrdenada.map(([v, imp]) => (
            <div key={v} style={{ marginBottom: 12 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 12.5,
                  marginBottom: 5,
                }}
              >
                <span>{NOMBRE_VAR[v] || v}</span>
                <span>{(imp * 100).toFixed(1)}%</span>
              </div>
              <Barra valor={imp} max={maxImp} />
            </div>
          ))}
        </div>
      </div>

      {/* ---------- Matriz de confusión y desglose ---------- */}
      <div
        className="cm-grid-2"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
          marginTop: 16,
          alignItems: 'start',
        }}
      >
        <div className="glass-card">
          <div className="cm-card-titulo">Matriz de confusión</div>
          <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)', margin: '4px 0 14px' }}>
            Filas: estado real · Columnas: predicho
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th />
                  {mc.clases.map((c) => (
                    <th
                      key={c}
                      style={{
                        padding: '6px 4px',
                        color: 'rgba(250,249,246,0.55)',
                        fontWeight: 500,
                        fontSize: 11.5,
                      }}
                    >
                      {ETIQUETA[c]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {mc.valores.map((fila, i) => (
                  <tr key={mc.clases[i]}>
                    <td
                      style={{
                        padding: '8px 6px',
                        color: 'rgba(250,249,246,0.75)',
                        fontSize: 11.5,
                      }}
                    >
                      {ETIQUETA[mc.clases[i]]}
                    </td>
                    {fila.map((v, j) => (
                      <td
                        key={j}
                        style={{
                          padding: '8px 4px',
                          textAlign: 'center',
                          fontWeight: i === j ? 600 : 400,
                          borderRadius: 6,
                          background:
                            i === j ? 'rgba(127,183,143,0.18)' : 'rgba(255,255,255,0.03)',
                          color: i === j ? '#A8D5B0' : 'rgba(250,249,246,0.6)',
                        }}
                      >
                        {v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div
            style={{
              fontSize: 11.5,
              color: 'rgba(250,249,246,0.5)',
              marginTop: 14,
              lineHeight: 1.5,
            }}
          >
            
          </div>
        </div>

        <div className="glass-card">
          <div className="cm-card-titulo">Desempeño por clase</div>
          <div style={{ fontSize: 12, color: 'rgba(250,249,246,0.55)', margin: '4px 0 14px' }}>
            Precisión, exhaustividad y F1
          </div>
          <div className="cm-tabla-head" style={{ gridTemplateColumns: '1.3fr 1fr 1fr 1fr' }}>
            <span>Clase</span>
            <span>Precisión</span>
            <span>Recall</span>
            <span>F1</span>
          </div>
          {Object.entries(info.por_clase).map(([c, m]) => (
            <div
              className="cm-tabla-fila"
              key={c}
              style={{ gridTemplateColumns: '1.3fr 1fr 1fr 1fr' }}
            >
              <span>{ETIQUETA[c]}</span>
              <span>{m.precision.toFixed(2)}</span>
              <span>{m.recall.toFixed(2)}</span>
              <span>{m.f1.toFixed(2)}</span>
            </div>
          ))}
          <div
            style={{
              fontSize: 11.5,
              color: 'rgba(250,249,246,0.5)',
              marginTop: 16,
              lineHeight: 1.5,
            }}
          >
            {Object.entries(dataset.distribucion)
              .map(([c, n]) => `${ETIQUETA[c]} ${n}`)
              .join(' · ')}
            <br />
            Entrenado {new Date(info.entrenado_en).toLocaleString('es-MX')}
          </div>
        </div>
      </div>
    </>
  )
}

export default Modelo
