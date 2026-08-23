/** Layout principal: fondo glass + sidebar + main con header. */
import React from 'react'
import { AppContent, AppSidebar, AppHeader } from '../components/index'

const DefaultLayout = () => {
  return (
    <div className="cm-app">
      <div className="cm-bg-foto" />
      <div className="cm-velo" />
      <div className="cm-contenido">
        <AppSidebar />
        <main className="cm-main">
          <AppHeader />
          <AppContent />
        </main>
      </div>
    </div>
  )
}

export default DefaultLayout
