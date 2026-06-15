/**
 * OptiFlow — Main Application Component
 * Defines routes and the global layout shell.
 */

import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  Package,
  ClipboardList,
  Bell,
  LogIn,
  Activity,
  Eye,
} from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import Inventory from './pages/Inventory'
import Login from './pages/Login'
import { AlertPanel } from './components/AlertPanel'
import { healthCheck } from './api/client'

const ALL_NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['ops', 'lab', 'qc', 'admin'] },
  { path: '/analytics', label: 'Analytics', icon: Activity, roles: ['admin'] },
  { path: '/inventory', label: 'Inventory', icon: Package, roles: ['ops', 'admin'] },
]

function Sidebar({ role }) {
  const location = useLocation()
  
  const navItems = ALL_NAV_ITEMS.filter(item => item.roles.includes(role))

  const handleLogout = () => {
    localStorage.removeItem('optiflow_role')
    localStorage.removeItem('optiflow_token')
    window.location.href = '/login'
  }

  return (
    <aside className="fixed left-0 top-0 h-full w-64 gradient-header border-r border-surface-700/50 flex flex-col z-50">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-surface-700/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg gradient-primary flex items-center justify-center shadow-lg shadow-primary-600/20">
            <Eye className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gradient">OptiFlow</h1>
            <p className="text-[10px] text-surface-500 uppercase tracking-widest">Eyewear OMS</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path
          return (
            <NavLink
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                ${isActive
                  ? 'bg-primary-600/20 text-primary-400 border border-primary-500/20'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/60'
                }`}
            >
              <Icon className={`w-4.5 h-4.5 ${isActive ? 'text-primary-400' : ''}`} />
              {label}
            </NavLink>
          )
        })}
      </nav>

      {/* Alert Panel */}
      <div className="px-3 pb-1">
        <AlertPanel />
      </div>

      <div className="px-3 py-2 border-t border-surface-700/50">
        <button 
          onClick={handleLogout}
          className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-surface-400 hover:text-risk-breached hover:bg-risk-breached/10 transition-all"
        >
          <LogIn className="w-4.5 h-4.5 rotate-180" />
          Logout ({role})
        </button>
      </div>

      {/* System Health Indicator */}
      <SystemHealth />
    </aside>
  )
}

function SystemHealth() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await healthCheck()
        setHealth(res.data)
      } catch {
        setHealth({ status: 'offline', db: 'unknown', redis: 'unknown' })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30s
    return () => clearInterval(interval)
  }, [])

  const statusColor = {
    healthy: 'bg-risk-ontrack',
    degraded: 'bg-risk-atrisk',
    offline: 'bg-risk-breached',
  }

  return (
    <div className="px-4 py-3 border-t border-surface-700/50">
      <div className="flex items-center gap-2 text-xs text-surface-500">
        <div className={`w-2 h-2 rounded-full ${statusColor[health?.status] || 'bg-surface-600'} ${health?.status === 'healthy' ? '' : 'animate-pulse'}`} />
        <span>System: {health?.status || 'checking...'}</span>
      </div>
      {health && (
        <div className="flex gap-3 mt-1 text-[10px] text-surface-600">
          <span>DB: {health.db}</span>
          <span>Redis: {health.redis}</span>
        </div>
      )}
    </div>
  )
}

function App() {
  const role = localStorage.getItem('optiflow_role')

  if (!role) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    )
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar role={role} />
      <main className="flex-1 ml-64 p-6 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={['admin'].includes(role) ? <Analytics /> : <Dashboard />} />
          <Route path="/inventory" element={['ops', 'admin'].includes(role) ? <Inventory /> : <Dashboard />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
