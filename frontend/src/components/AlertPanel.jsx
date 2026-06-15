import { useState, useEffect } from 'react'
import { Bell, X, AlertTriangle, ShieldAlert, CheckCircle, Clock } from 'lucide-react'
import api from '../api/client'

export function AlertPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const res = await api.get('/api/v1/alerts/?limit=30')
      setAlerts(res.data)
    } catch {
      // silently fail
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 30000)
    return () => clearInterval(interval)
  }, [])

  const breachedCount = alerts.filter(a => a.risk_level === 'breached').length
  const atRiskCount = alerts.filter(a => a.risk_level === 'at_risk').length
  const totalBadge = breachedCount + atRiskCount

  return (
    <>
      {/* Bell Button */}
      <button
        onClick={() => { setIsOpen(true); fetchAlerts() }}
        className="relative flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-surface-400 hover:text-surface-200 hover:bg-surface-800/60 transition-all w-full"
      >
        <Bell className="w-4.5 h-4.5" />
        Alerts
        {totalBadge > 0 && (
          <span className="absolute right-3 bg-risk-breached text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold min-w-[18px] text-center animate-pulse">
            {totalBadge}
          </span>
        )}
      </button>

      {/* Slide-out Panel */}
      {isOpen && (
        <div className="fixed inset-0 z-[200]" onClick={() => setIsOpen(false)}>
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            className="absolute right-0 top-0 h-full w-96 bg-surface-900 border-l border-surface-700 shadow-2xl animate-slide-in-right flex flex-col"
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-5 border-b border-surface-700 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-surface-100 flex items-center gap-2">
                  <Bell className="w-5 h-5 text-primary-400" />
                  Alert Center
                </h2>
                <p className="text-xs text-surface-500 mt-0.5">
                  {breachedCount} breached • {atRiskCount} at risk
                </p>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-surface-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Alert List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loading && alerts.length === 0 && (
                <div className="text-center py-10">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto" />
                </div>
              )}

              {!loading && alerts.length === 0 && (
                <div className="text-center py-10">
                  <CheckCircle className="w-10 h-10 text-risk-ontrack mx-auto mb-3 opacity-50" />
                  <p className="text-sm text-surface-500">No alerts — all systems healthy</p>
                </div>
              )}

              {alerts.map(alert => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-xl border transition-all ${
                    alert.risk_level === 'breached'
                      ? 'bg-risk-breached/5 border-risk-breached/20'
                      : alert.risk_level === 'at_risk'
                      ? 'bg-risk-atrisk/5 border-risk-atrisk/20'
                      : 'bg-surface-800/50 border-surface-700/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 p-1.5 rounded-lg ${
                      alert.risk_level === 'breached' ? 'bg-risk-breached/20 text-risk-breached' :
                      alert.risk_level === 'at_risk' ? 'bg-risk-atrisk/20 text-risk-atrisk' :
                      'bg-risk-ontrack/20 text-risk-ontrack'
                    }`}>
                      {alert.risk_level === 'breached' ? <AlertTriangle className="w-4 h-4" /> :
                       alert.risk_level === 'at_risk' ? <ShieldAlert className="w-4 h-4" /> :
                       <CheckCircle className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium text-surface-200">
                          {alert.order_number || `Order #${alert.order_id}`}
                        </p>
                        <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                          alert.risk_level === 'breached' ? 'bg-risk-breached/20 text-risk-breached' :
                          alert.risk_level === 'at_risk' ? 'bg-risk-atrisk/20 text-risk-atrisk' :
                          'bg-risk-ontrack/20 text-risk-ontrack'
                        }`}>
                          {alert.risk_level.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-surface-500 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(alert.sent_at).toLocaleString()}
                      </p>
                      <p className="text-xs text-surface-400 mt-0.5">
                        via {alert.channel} • {alert.delivery_status}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
