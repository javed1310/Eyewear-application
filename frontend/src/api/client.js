/**
 * OptiFlow — API Client
 * Axios-based wrapper for backend communication.
 */

import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request Interceptor: Attach auth token ──
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('optiflow_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response Interceptor: Handle errors globally ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    if (error.response?.status === 401) {
      localStorage.removeItem('optiflow_token')
      // Will redirect to login in Phase 7
    } else if (error.response?.status >= 500) {
      toast.error(`Server error: ${message}`)
    }

    return Promise.reject(error)
  }
)

export default api

// ── Convenience methods ──
export const healthCheck = () => api.get('/health')
