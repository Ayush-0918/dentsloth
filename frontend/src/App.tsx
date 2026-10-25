import { Routes, Route } from 'react-router-dom'
import { Nav } from './components/Nav'
import { ServerStatusBanner } from './components/ServerStatusBanner'
import { Landing } from './pages/Landing'
import { SnapAndList } from './pages/SnapAndList'
import { Marketplace } from './pages/Marketplace'
import { KitBuilder } from './pages/KitBuilder'
import { Dashboard } from './pages/Dashboard'
import './App.css'

export function App() {
  return (
    <div className="app-root">
      {/* Editorial column lines (desktop) */}
      <div className="col-lines" aria-hidden="true">
        <span /><span /><span /><span />
      </div>

      <a href="#main-content" className="skip-link">Skip to main content</a>

      <ServerStatusBanner />
      <Nav />

      <div className="app-content">
        <Routes>
          <Route path="/"           element={<Landing />} />
          <Route path="/snap"       element={<SnapAndList />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/kit"        element={<KitBuilder />} />
          <Route path="/dashboard"  element={<Dashboard />} />
        </Routes>
      </div>
    </div>
  )
}
