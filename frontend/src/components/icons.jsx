/** Iconos SVG del diseño Composta Monitor (trazos del archivo .dc.html). */
import React from 'react'

const Icono = ({ d, size = 18, color = 'currentColor', ...props }) => (
  <svg viewBox="0 0 24 24" width={size} height={size} {...props}>
    <path
      d={d}
      style={{ fill: 'none', stroke: color, strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round' }}
    />
  </svg>
)

export const IconoHoja = (p) => (
  <Icono d="M12 3 C7 8 6 13 12 21 C18 13 17 8 12 3 Z M12 20 C12 15 12 12 12 9" {...p} />
)
export const IconoDashboard = (p) => <Icono d="M3 11 L12 4 L21 11 M5 9.5 V20 H19 V9.5" {...p} />
export const IconoLotes = (p) => <Icono d="M4 5 H20 M4 10 H20 M4 15 H20 M4 20 H12" {...p} />
export const IconoPredicciones = (p) => <Icono d="M4 17 L10 11 L14 14 L20 7 M15 7 H20 V12" {...p} />
export const IconoSalir = (p) => <Icono d="M10 4 H19 V20 H10 M14 12 H3 M6 9 L3 12 L6 15" {...p} />
export const IconoCalendario = (p) => <Icono d="M5 6 H19 V20 H5 Z M5 10 H19 M9 3 V7 M15 3 V7" {...p} />
export const IconoReloj = (p) => <Icono d="M12 4 a8 8 0 1 0 0.01 0 M12 8 V12 L15 14" {...p} />
export const IconoAlerta = (p) => <Icono d="M12 4.5 L21.5 19.5 H2.5 Z M12 10 V14.5 M12 17 L12 17.01" {...p} />
export const IconoOk = (p) => <Icono d="M12 3.5 a8.5 8.5 0 1 0 0.01 0 M8 12.5 L10.8 15.2 L16 9.5" {...p} />
