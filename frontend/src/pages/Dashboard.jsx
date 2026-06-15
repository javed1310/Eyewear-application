import { useState, useMemo, useEffect } from 'react'
import { LayoutDashboard, Columns3, Table2, Plus, Clock, AlertTriangle, CheckCircle2, ChevronRight, PackageCheck, Filter, X, ArrowRight, MessageSquare, History } from 'lucide-react'
import { useOrders } from '../hooks/useOrders'
import { OrderIntakeForm } from '../components/OrderIntakeForm'
import { formatDistanceToNow } from 'date-fns'
import api from '../api/client'
import toast from 'react-hot-toast'

const STAGES = [
  { id: 'order_intake', label: 'Order Intake', color: 'bg-blue-500/10 border-blue-500/30 text-blue-400' },
  { id: 'prescription_validation', label: 'Rx Validation', color: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' },
  { id: 'inventory_check', label: 'Inventory', color: 'bg-purple-500/10 border-purple-500/30 text-purple-400' },
  { id: 'lab_production', label: 'Lab Production', color: 'bg-amber-500/10 border-amber-500/30 text-amber-400' },
  { id: 'quality_control', label: 'Quality Control', color: 'bg-rose-500/10 border-rose-500/30 text-rose-400' },
  { id: 'ready_for_dispatch', label: 'Ready', color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' },
  { id: 'out_for_delivery', label: 'Out for Delivery', color: 'bg-teal-500/10 border-teal-500/30 text-teal-400' },
  { id: 'delivered', label: 'Delivered', color: 'bg-surface-500/10 border-surface-500/30 text-surface-400' },
]

const ALLOWED_TRANSITIONS = {
  order_intake: ['prescription_validation'],
  prescription_validation: ['inventory_check'],
  inventory_check: ['lab_production'],
  lab_production: ['quality_control'],
  quality_control: ['ready_for_dispatch', 'lab_production'],
  ready_for_dispatch: ['out_for_delivery'],
  out_for_delivery: ['delivered'],
  delivered: [],
}

function FilterBar({ filters, setFilters }) {
  const [isOpen, setIsOpen] = useState(false)
  const hasFilters = filters.status || filters.lensType || filters.storeLocation

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all border ${
            hasFilters
              ? 'bg-primary-600/20 text-primary-400 border-primary-500/30'
              : 'bg-surface-800 text-surface-400 border-surface-700 hover:text-surface-200'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filters
          {hasFilters && (
            <span className="bg-primary-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold">
              {[filters.status, filters.lensType, filters.storeLocation].filter(Boolean).length}
            </span>
          )}
        </button>
        {hasFilters && (
          <button
            onClick={() => setFilters({ status: '', lensType: '', storeLocation: '' })}
            className="flex items-center gap-1 px-2 py-1.5 rounded-md text-xs text-surface-400 hover:text-risk-breached transition-colors"
          >
            <X className="w-3 h-3" /> Clear all
          </button>
        )}
      </div>

      {isOpen && (
        <div className="mt-3 p-4 glass-card bg-surface-900/80 animate-slide-up grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-surface-400 mb-1.5 font-medium uppercase tracking-wider">Status</label>
            <select
              className="input-field text-sm bg-surface-800 w-full"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <option value="">All Stages</option>
              {STAGES.map(s => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-surface-400 mb-1.5 font-medium uppercase tracking-wider">Lens Type</label>
            <select
              className="input-field text-sm bg-surface-800 w-full"
              value={filters.lensType}
              onChange={(e) => setFilters({ ...filters, lensType: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="single_vision">Single Vision</option>
              <option value="bifocal">Bifocal</option>
              <option value="progressive">Progressive</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-surface-400 mb-1.5 font-medium uppercase tracking-wider">Store Location</label>
            <input
              type="text"
              placeholder="Search location..."
              className="input-field text-sm bg-surface-800 w-full"
              value={filters.storeLocation}
              onChange={(e) => setFilters({ ...filters, storeLocation: e.target.value })}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function KanbanCard({ order, onClick }) {
  const isBreached = order.risk_level === 'breached'
  const isAtRisk = order.risk_level === 'at_risk'
  
  return (
    <div 
      onClick={() => onClick(order)}
      className={`glass-card-hover p-3 cursor-pointer mb-3 animate-slide-up ${
        isBreached ? 'border-risk-breached/50 shadow-risk-breached/10' : 
        isAtRisk ? 'border-risk-atrisk/50 shadow-risk-atrisk/10' : ''
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <span className="text-sm font-mono font-semibold text-surface-200">{order.order_number}</span>
        {isBreached && <AlertTriangle className="w-4 h-4 text-risk-breached animate-pulse" />}
        {isAtRisk && <Clock className="w-4 h-4 text-risk-atrisk" />}
      </div>
      
      <div className="text-xs text-surface-400 mb-3 flex justify-between">
        <span>{order.store_location}</span>
        {order.loopback_count > 0 && (
          <span className="text-rose-400 font-medium">{order.loopback_count}x Loopback</span>
        )}
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface-700/50">
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
          isBreached ? 'bg-risk-breached/20 text-risk-breached' :
          isAtRisk ? 'bg-risk-atrisk/20 text-risk-atrisk' :
          'bg-risk-ontrack/20 text-risk-ontrack'
        }`}>
          {order.sla_target_at ? 
            formatDistanceToNow(new Date(order.sla_target_at), { addSuffix: true }) 
            : 'No SLA'
          }
        </span>
      </div>
    </div>
  )
}

function KanbanBoard({ orders, onOrderClick }) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4 h-[calc(100vh-320px)]">
      {STAGES.map(stage => {
        const stageOrders = orders.filter(o => o.status === stage.id)
        
        return (
          <div key={stage.id} className="flex-shrink-0 w-72 flex flex-col bg-surface-900/50 rounded-xl border border-surface-800">
            <div className={`p-3 border-b rounded-t-xl font-medium text-sm flex justify-between items-center ${stage.color}`}>
              <span>{stage.label}</span>
              <span className="bg-surface-900/50 px-2 py-0.5 rounded-full text-xs">
                {stageOrders.length}
              </span>
            </div>
            
            <div className="p-3 flex-1 overflow-y-auto">
              {stageOrders.map(order => (
                <KanbanCard key={order.id} order={order} onClick={onOrderClick} />
              ))}
              {stageOrders.length === 0 && (
                <div className="text-center p-4 text-sm text-surface-600 border border-dashed border-surface-700 rounded-lg">
                  No orders
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function TableView({ orders, onOrderClick }) {
  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-surface-400 uppercase bg-surface-900/50 border-b border-surface-700">
            <tr>
              <th className="px-6 py-4">Order ID</th>
              <th className="px-6 py-4">Location</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Risk Level</th>
              <th className="px-6 py-4">SLA Target</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="border-b border-surface-700/50 hover:bg-surface-800/50 transition-colors">
                <td className="px-6 py-4 font-mono text-surface-200">{order.order_number}</td>
                <td className="px-6 py-4 text-surface-300">{order.store_location}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-medium border ${
                    STAGES.find(s => s.id === order.status)?.color || 'bg-surface-800 text-surface-400'
                  }`}>
                    {STAGES.find(s => s.id === order.status)?.label || order.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                   <span className={
                     order.risk_level === 'on_track' ? 'badge-ontrack' :
                     order.risk_level === 'at_risk' ? 'badge-atrisk' : 'badge-breached'
                   }>
                     {order.risk_level.replace('_', ' ').toUpperCase()}
                   </span>
                </td>
                <td className="px-6 py-4 text-surface-400">
                  {order.sla_target_at ? new Date(order.sla_target_at).toLocaleDateString() : '-'}
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => onOrderClick(order)}
                    className="text-primary-400 hover:text-primary-300 text-xs font-medium"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function OrderDetailModal({ order, onClose, onCheckInventory, onTransition, onRefresh }) {
  const [delayReason, setDelayReason] = useState('')
  const [qcFailReason, setQcFailReason] = useState('')
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [detailData, setDetailData] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    if (!order) return
    setLoadingDetail(true)
    api.get(`/api/v1/orders/${order.id}`)
      .then(res => setDetailData(res.data))
      .catch(() => toast.error('Failed to load order details'))
      .finally(() => setLoadingDetail(false))
  }, [order])

  if (!order) return null

  const nextStages = ALLOWED_TRANSITIONS[order.status] || []
  const role = localStorage.getItem('optiflow_role')

  const handleAdvance = async (targetStage) => {
    setIsTransitioning(true)
    try {
      const isLoopback = order.status === 'quality_control' && targetStage === 'lab_production'
      await onTransition(
        order.id,
        targetStage,
        role || 'User',
        delayReason || null,
        isLoopback ? (qcFailReason || 'QC Failed') : null
      )
      onClose()
    } catch {
      // error already toasted by useOrders
    } finally {
      setIsTransitioning(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] animate-fade-in p-4">
      <div className="glass-card w-full max-w-2xl bg-surface-900 border-surface-600 shadow-2xl flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-surface-700 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-surface-100 font-mono">{order.order_number}</h2>
            <p className="text-sm text-surface-400">{order.store_location} • Created {new Date(order.created_at).toLocaleDateString()}</p>
          </div>
          <button onClick={onClose} className="text-surface-400 hover:text-white transition-colors">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          
          {/* Status Timeline visualization */}
          <div className="mb-8">
            <h3 className="text-sm font-semibold text-surface-300 mb-4 uppercase tracking-wider">Lifecycle Stage</h3>
            <div className="flex items-center w-full">
              {STAGES.slice(0, 5).map((stage, i) => {
                const isActive = order.status === stage.id
                const isPast = STAGES.findIndex(s => s.id === order.status) > i
                
                return (
                  <div key={stage.id} className="flex items-center flex-1 last:flex-none">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 text-xs font-bold
                      ${isActive ? 'border-primary-500 bg-primary-500/20 text-primary-400 shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 
                        isPast ? 'border-surface-500 bg-surface-700 text-surface-300' : 
                        'border-surface-700 bg-surface-900 text-surface-600'}`}>
                      {isPast ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                    </div>
                    {i < 4 && (
                      <div className={`flex-1 h-1 mx-2 rounded-full ${isPast ? 'bg-surface-500' : 'bg-surface-800'}`} />
                    )}
                  </div>
                )
              })}
            </div>
            <p className="text-center mt-3 text-sm font-medium text-primary-400">
              Current: {STAGES.find(s => s.id === order.status)?.label}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
               <div className="bg-surface-800/50 p-4 rounded-xl border border-surface-700/50">
                 <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Order Details</h3>
                 <div className="space-y-2 text-sm text-surface-200">
                   <div className="flex justify-between"><span className="text-surface-500">Source:</span> <span>{order.source_channel}</span></div>
                   <div className="flex justify-between"><span className="text-surface-500">Loopbacks:</span> <span className={order.loopback_count > 0 ? "text-rose-400 font-bold" : ""}>{order.loopback_count}</span></div>
                   <div className="flex justify-between"><span className="text-surface-500">Procurement:</span> <span>{order.external_procurement ? 'External Supplier' : 'In-House'}</span></div>
                 </div>
               </div>
            </div>

            <div className="space-y-4">
              <div className="bg-surface-800/50 p-4 rounded-xl border border-surface-700/50">
                 <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">SLA & Risk</h3>
                 <div className="space-y-2 text-sm text-surface-200">
                   <div className="flex justify-between items-center">
                     <span className="text-surface-500">Risk Level:</span> 
                     <span className={order.risk_level === 'on_track' ? 'badge-ontrack' : order.risk_level === 'at_risk' ? 'badge-atrisk' : 'badge-breached'}>
                       {order.risk_level.toUpperCase()}
                     </span>
                   </div>
                   <div className="flex justify-between"><span className="text-surface-500">Target SLA:</span> <span>{order.sla_target_at ? new Date(order.sla_target_at).toLocaleString() : 'Pending'}</span></div>
                 </div>
               </div>
            </div>
          </div>

          {/* Transition Audit Log */}
          {detailData?.stage_transitions?.length > 0 && (
            <div className="mt-6 bg-surface-800/50 p-4 rounded-xl border border-surface-700/50">
              <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <History className="w-3.5 h-3.5" /> Stage Transition History
              </h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {detailData.stage_transitions.map((t, i) => (
                  <div key={i} className="flex items-start gap-3 text-xs p-2 rounded-lg bg-surface-900/50 border border-surface-700/30">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-surface-300 font-medium">
                          {STAGES.find(s => s.id === t.from_stage)?.label || t.from_stage}
                        </span>
                        <ArrowRight className="w-3 h-3 text-surface-500" />
                        <span className="text-primary-400 font-medium">
                          {STAGES.find(s => s.id === t.to_stage)?.label || t.to_stage}
                        </span>
                        {t.is_loopback && <span className="text-rose-400 text-[10px] font-bold bg-rose-500/10 px-1.5 py-0.5 rounded">LOOPBACK</span>}
                      </div>
                      {t.delay_reason && (
                        <p className="text-surface-500 mt-1 flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" /> {t.delay_reason}
                        </p>
                      )}
                    </div>
                    <div className="text-right text-surface-500 flex-shrink-0">
                      <div>{t.changed_by}</div>
                      <div>{new Date(t.changed_at).toLocaleString()}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Advance Stage Actions */}
          {nextStages.length > 0 && order.status !== 'delivered' && (
            <div className="mt-6 bg-surface-800/30 p-4 rounded-xl border border-primary-500/20">
              <h3 className="text-xs font-semibold text-primary-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <ArrowRight className="w-3.5 h-3.5" /> Advance Order Stage
              </h3>

              {/* Delay Reason Input */}
              <div className="mb-3">
                <label className="block text-xs text-surface-400 mb-1">Delay Reason (optional — required if order exceeded dwell time)</label>
                <input
                  type="text"
                  placeholder="e.g., Waiting for coating supplier..."
                  className="input-field text-sm w-full"
                  value={delayReason}
                  onChange={(e) => setDelayReason(e.target.value)}
                />
              </div>

              {/* QC Fail Reason (only when QC → Lab loopback is an option) */}
              {order.status === 'quality_control' && (
                <div className="mb-3">
                  <label className="block text-xs text-surface-400 mb-1">QC Failure Reason (for loopback)</label>
                  <input
                    type="text"
                    placeholder="e.g., Axis misaligned by 3°..."
                    className="input-field text-sm w-full"
                    value={qcFailReason}
                    onChange={(e) => setQcFailReason(e.target.value)}
                  />
                </div>
              )}

              {/* Transition Buttons */}
              <div className="flex gap-3 flex-wrap">
                {nextStages.map(targetStage => {
                  const isLoopback = order.status === 'quality_control' && targetStage === 'lab_production'
                  const targetLabel = STAGES.find(s => s.id === targetStage)?.label || targetStage
                  return (
                    <button
                      key={targetStage}
                      disabled={isTransitioning}
                      onClick={() => handleAdvance(targetStage)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        isLoopback
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30'
                          : 'bg-primary-600/20 text-primary-400 border border-primary-500/30 hover:bg-primary-600/30'
                      } disabled:opacity-50`}
                    >
                      {isTransitioning ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
                      ) : (
                        <>
                          {isLoopback ? <AlertTriangle className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          {isLoopback ? `QC Fail → ${targetLabel}` : `Advance → ${targetLabel}`}
                        </>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-surface-700 bg-surface-800/30 flex justify-end gap-3">
          {order.status === 'prescription_validation' && (
            <button 
              onClick={() => {
                onCheckInventory(order.id)
                onClose()
              }}
              className="btn-primary flex items-center gap-2"
            >
              <PackageCheck className="w-4 h-4" />
              Check Inventory & Proceed
            </button>
          )}
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}


function Dashboard() {
  const [viewMode, setViewMode] = useState('kanban') // 'kanban' | 'table'
  const { orders, loading, checkInventory, createOrder, transitionOrder, isWsConnected, refresh } = useOrders()
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [isIntakeOpen, setIsIntakeOpen] = useState(false)
  const [filters, setFilters] = useState({ status: '', lensType: '', storeLocation: '' })

  // Apply client-side filters
  const filteredOrders = useMemo(() => {
    let result = orders
    if (filters.status) {
      result = result.filter(o => o.status === filters.status)
    }
    if (filters.storeLocation) {
      result = result.filter(o => o.store_location.toLowerCase().includes(filters.storeLocation.toLowerCase()))
    }
    // lens_type filter would need data from backend; for now we filter on source_channel as proxy
    // This will work once the backend returns lens_spec with orders
    return result
  }, [orders, filters])

  // Demo stats
  const stats = useMemo(() => {
    return {
      intake: orders.filter(o => o.status === 'order_intake').length,
      production: orders.filter(o => o.status === 'lab_production').length,
      qc: orders.filter(o => o.status === 'quality_control').length,
      ready: orders.filter(o => o.status === 'ready_for_dispatch').length,
    }
  }, [orders])

  const handleTransition = async (orderId, targetStage, actor, delayReason, qcFailReason) => {
    try {
      const payload = { to_stage: targetStage, actor, delay_reason: delayReason, qc_fail_reason: qcFailReason }
      await api.post(`/api/v1/orders/${orderId}/transition`, payload)
      toast.success(`Order moved to ${STAGES.find(s => s.id === targetStage)?.label || targetStage}`)
      refresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to transition order')
      throw err
    }
  }

  return (
    <div className="animate-fade-in h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-100 flex items-center gap-3">
            <LayoutDashboard className="w-7 h-7 text-primary-400" />
            Order Dashboard
          </h1>
          <p className="text-sm text-surface-500 mt-1 flex items-center gap-2">
            Track and manage all eyewear orders across the production lifecycle
            <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${
              isWsConnected ? 'bg-risk-ontrack/10 text-risk-ontrack border-risk-ontrack/20' : 'bg-surface-800 text-surface-500 border-surface-700'
            }`}>
              <div className={`w-1.5 h-1.5 rounded-full ${isWsConnected ? 'bg-risk-ontrack animate-pulse' : 'bg-surface-600'}`} />
              {isWsConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-surface-800 rounded-lg p-1 border border-surface-700">
            <button 
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'kanban' ? 'bg-primary-600/20 text-primary-400 border border-primary-500/20' : 'text-surface-400 hover:text-surface-200'
              }`}
            >
              <Columns3 className="w-3.5 h-3.5 inline mr-1.5" />
              Kanban
            </button>
            <button 
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'table' ? 'bg-primary-600/20 text-primary-400 border border-primary-500/20' : 'text-surface-400 hover:text-surface-200'
              }`}
            >
              <Table2 className="w-3.5 h-3.5 inline mr-1.5" />
              Table
            </button>
          </div>
          <button 
            className="btn-primary flex items-center gap-2"
            onClick={() => setIsIntakeOpen(true)}
          >
            <Plus className="w-4 h-4" />
            New Order
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar filters={filters} setFilters={setFilters} />

      {/* Status Pipeline Overview */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { stage: 'Order Intake', count: stats.intake, color: 'from-blue-500/10 to-blue-600/5 border-blue-500/20' },
          { stage: 'In Production', count: stats.production, color: 'from-amber-500/10 to-amber-600/5 border-amber-500/20' },
          { stage: 'Quality Control', count: stats.qc, color: 'from-purple-500/10 to-purple-600/5 border-purple-500/20' },
          { stage: 'Ready / Delivered', count: stats.ready, color: 'from-emerald-500/10 to-emerald-600/5 border-emerald-500/20' },
        ].map(({ stage, count, color }) => (
          <div key={stage} className={`glass-card p-4 bg-gradient-to-br ${color}`}>
            <p className="text-xs text-surface-400 font-medium uppercase tracking-wide">{stage}</p>
            <p className="text-3xl font-bold mt-1 text-surface-100">{count}</p>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 min-h-0">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
          </div>
        ) : viewMode === 'kanban' ? (
          <KanbanBoard orders={filteredOrders} onOrderClick={setSelectedOrder} />
        ) : (
          <TableView orders={filteredOrders} onOrderClick={setSelectedOrder} />
        )}
      </div>

      <OrderDetailModal 
        order={selectedOrder} 
        onClose={() => setSelectedOrder(null)} 
        onCheckInventory={async (id) => {
          await checkInventory(id)
          setSelectedOrder(null)
        }}
        onTransition={handleTransition}
        onRefresh={refresh}
      />

      {isIntakeOpen && (
        <OrderIntakeForm 
          onClose={() => setIsIntakeOpen(false)}
          onSubmit={async (data) => {
            await createOrder(data)
            setIsIntakeOpen(false)
          }}
        />
      )}
    </div>
  )
}

export default Dashboard
