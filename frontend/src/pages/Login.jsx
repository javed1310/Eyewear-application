/**
 * OptiFlow — Login Page
 * Lightweight role-based authentication (Mock for demo purposes).
 */

import { LogIn, Shield, User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

function Login() {
  const navigate = useNavigate()

  const handleLogin = (role) => {
    // In a real app, this would hit /api/v1/auth/login and get a JWT
    localStorage.setItem('optiflow_role', role)
    localStorage.setItem('optiflow_token', 'mock_token_for_demo')
    toast.success(`Logged in as ${role.toUpperCase()}`)
    
    // Redirect to Dashboard
    navigate('/')
    // Force a small reload to update sidebar state if needed, or rely on React state
    window.location.reload()
  }

  const roles = [
    { id: 'ops', label: 'Operations & Intake', desc: 'Create orders and manage customer facing tasks.' },
    { id: 'lab', label: 'Lab Technician', desc: 'Process orders through production stages.' },
    { id: 'qc', label: 'Quality Control', desc: 'Validate lens specs against Rx.' },
    { id: 'admin', label: 'Administrator', desc: 'Full system access and analytics.' },
  ]

  return (
    <div className="min-h-[80vh] flex items-center justify-center animate-fade-in p-4">
      <div className="glass-card p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl gradient-primary mx-auto flex items-center justify-center mb-4 shadow-lg shadow-primary-600/20">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-surface-100">Welcome to OptiFlow</h2>
          <p className="text-sm text-surface-500 mt-1">Select a role to continue</p>
        </div>

        <div className="space-y-3">
          {roles.map((role) => (
            <button
              key={role.id}
              onClick={() => handleLogin(role.id)}
              className="w-full text-left p-4 rounded-xl border border-surface-700 bg-surface-800/50 hover:bg-surface-700/50 hover:border-primary-500/50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-surface-900 rounded-lg group-hover:bg-primary-500/20 group-hover:text-primary-400 transition-colors">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-surface-200 group-hover:text-white transition-colors">{role.label}</h3>
                  <p className="text-xs text-surface-500">{role.desc}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Login
