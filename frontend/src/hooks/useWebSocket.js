import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'

export function useWebSocket(onMessage) {
  const [isConnected, setIsConnected] = useState(false)
  const ws = useRef(null)
  
  useEffect(() => {
    // In production (served by FastAPI), use the same host. In development, use localhost.
    const host = import.meta.env.PROD ? window.location.host : 'localhost:8000'
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${host}/ws/stream`
    
    const connect = () => {
      ws.current = new WebSocket(wsUrl)
      
      ws.current.onopen = () => {
        setIsConnected(true)
      }
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (onMessage) onMessage(data)
        } catch (err) {
          console.error("Failed to parse websocket message", err)
        }
      }
      
      ws.current.onclose = () => {
        setIsConnected(false)
        // Auto-reconnect after 3 seconds
        setTimeout(connect, 3000)
      }
      
      ws.current.onerror = (error) => {
        console.error("WebSocket error:", error)
        ws.current.close()
      }
    }
    
    connect()
    
    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [onMessage])
  
  return { isConnected }
}
