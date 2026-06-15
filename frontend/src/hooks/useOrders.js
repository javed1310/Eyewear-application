import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'
import toast from 'react-hot-toast'
import { useWebSocket } from './useWebSocket'

export function useOrders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/v1/orders/')
      setOrders(response.data)
      setError(null)
    } catch (err) {
      setError(err)
      toast.error('Failed to fetch orders')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchOrders()
  }, [fetchOrders])

  const handleWebSocketMessage = useCallback((msg) => {
    if (msg.action === 'created' || msg.action === 'status_changed') {
      // For now, easiest way to stay perfectly in sync is refetching. 
      // In a production app with thousands of orders, we'd do targeted state updates.
      fetchOrders()
      toast(`Order ${msg.order_id} ${msg.action.replace('_', ' ')}`, {
        icon: '🔄',
        style: { background: '#1e293b', color: '#38bdf8' }
      })
    }
  }, [fetchOrders])

  const { isConnected } = useWebSocket(handleWebSocketMessage)

  const createOrder = async (orderData) => {
    try {
      const response = await api.post('/api/v1/orders/', orderData)
      setOrders((prev) => [...prev, response.data])
      toast.success('Order created successfully')
      return response.data
    } catch (err) {
      toast.error('Failed to create order')
      throw err
    }
  }

  const transitionOrder = async (orderId, targetStage, actor = 'User', delayReason = null) => {
    try {
      const payload = { to_stage: targetStage, actor, delay_reason: delayReason }
      await api.post(`/api/v1/orders/${orderId}/transition`, payload)
      
      // Update local state
      setOrders((prev) =>
        prev.map((order) =>
          order.id === orderId ? { ...order, status: targetStage } : order
        )
      )
      toast.success(`Order moved to ${targetStage.replace(/_/g, ' ')}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to transition order')
      throw err
    }
  }
  
  const checkInventory = async (orderId) => {
      try {
          const response = await api.post(`/api/v1/inventory/check-order/${orderId}`)
          toast.success(response.data.message)
          // Refetch to get updated status and SLA
          fetchOrders()
          return response.data
      } catch (err) {
          toast.error(err.response?.data?.detail || 'Inventory check failed')
          throw err
      }
  }

  return {
    orders,
    loading,
    error,
    refresh: fetchOrders,
    createOrder,
    transitionOrder,
    checkInventory,
    isWsConnected: isConnected
  }
}
