/**
 * OptiFlow — Inventory Page
 * Displays lens inventory with stock levels and restock recommendations.
 */

import { useState, useEffect } from 'react'
import { Package, AlertTriangle, TrendingDown, CheckCircle2, RefreshCw } from 'lucide-react'
import api from '../api/client'
import toast from 'react-hot-toast'

function Inventory() {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchInventory = async () => {
    try {
      setLoading(true)
      const res = await api.get('/api/v1/inventory/')
      setInventory(res.data)
    } catch (err) {
      toast.error('Failed to load inventory data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInventory()
  }, [])

  const lowStockItems = inventory.filter(item => item.quantity < item.minimum_threshold)
  const healthyItems = inventory.length - lowStockItems.length

  return (
    <div className="animate-fade-in h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-100 flex items-center gap-3">
            <Package className="w-7 h-7 text-accent-400" />
            Lens Inventory
          </h1>
          <p className="text-sm text-surface-500 mt-1">
            Real-time stock levels, SLA matching limits, and AI restock recommendations.
          </p>
        </div>
        <button onClick={fetchInventory} className="btn-secondary flex items-center gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="glass-card p-5 border-t-2 border-t-accent-500 col-span-2">
           <h3 className="text-sm font-semibold text-surface-300 mb-4 flex items-center gap-2">
             <TrendingDown className="w-4 h-4 text-accent-400" /> Smart Restock Insights
           </h3>
           {lowStockItems.length > 0 ? (
             <ul className="space-y-3">
               {lowStockItems.slice(0, 3).map(item => (
                 <li key={item.id} className="flex justify-between items-center p-3 bg-risk-atrisk/10 border border-risk-atrisk/20 rounded-lg">
                   <div>
                     <p className="text-sm font-medium text-surface-200">
                       {item.lens_type.replace('_', ' ').toUpperCase()} • Index {item.lens_index}
                     </p>
                     <p className="text-xs text-risk-atrisk">Only {item.quantity} left (Min: {item.minimum_threshold})</p>
                   </div>
                   <button className="text-xs bg-risk-atrisk/20 text-risk-atrisk px-3 py-1.5 rounded hover:bg-risk-atrisk/30 transition-colors font-medium">
                     Order 50 Units
                   </button>
                 </li>
               ))}
             </ul>
           ) : (
             <div className="h-full flex items-center justify-center text-sm text-surface-500 pb-8">
               <CheckCircle2 className="w-5 h-5 text-risk-ontrack mr-2" /> All inventory levels are optimal.
             </div>
           )}
        </div>
        
        <div className="glass-card p-5 flex flex-col justify-center items-center text-center">
           <div className="w-16 h-16 rounded-full border-4 border-risk-ontrack flex items-center justify-center mb-3 text-risk-ontrack font-bold text-xl">
             {inventory.length > 0 ? Math.round((healthyItems / inventory.length) * 100) : 0}%
           </div>
           <h3 className="text-surface-200 font-medium">Stock Health</h3>
           <p className="text-xs text-surface-500 mt-1">Based on reorder limits</p>
        </div>
      </div>

      <div className="glass-card flex-1 overflow-hidden flex flex-col">
        <div className="overflow-y-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-surface-400 uppercase bg-surface-900/50 sticky top-0 border-b border-surface-700 backdrop-blur-md">
              <tr>
                <th className="px-6 py-4">SKU / Type</th>
                <th className="px-6 py-4">Index</th>
                <th className="px-6 py-4">SLA (Hrs)</th>
                <th className="px-6 py-4 text-right">In Stock</th>
                <th className="px-6 py-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="5" className="text-center py-8 text-surface-500">Loading...</td></tr>
              ) : inventory.map((item) => (
                <tr key={item.id} className="border-b border-surface-700/50 hover:bg-surface-800/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-surface-200">{item.lens_type.replace('_', ' ').toUpperCase()}</td>
                  <td className="px-6 py-4 text-surface-300">{item.lens_index}</td>
                  <td className="px-6 py-4 text-surface-400">{item.promised_sla_hours}</td>
                  <td className="px-6 py-4 text-right font-mono">{item.quantity}</td>
                  <td className="px-6 py-4 text-center">
                    {item.quantity < item.minimum_threshold ? (
                      <span className="badge-atrisk">Low Stock</span>
                    ) : (
                      <span className="badge-ontrack">Healthy</span>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && inventory.length === 0 && (
                <tr><td colSpan="5" className="text-center py-8 text-surface-500">No inventory found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Inventory
