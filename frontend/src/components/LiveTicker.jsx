import { useEffect, useRef, useState } from 'react'

const WS_URL = 'ws://localhost:8000/ws/live'

function formatPrice(price) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price ?? 0)
}

function createTickerLine(signal) {
  const now = new Date()
  const time = now.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const action = signal.action || 'HOLD'
  const paddedAction = action.padEnd(5, ' ')
  const confidence = Math.round((signal.confidence ?? 0) * 100)

  return {
    id: `${Date.now()}-${Math.random()}`,
    action,
    text: `[${time}]  ${paddedAction} @ ${formatPrice(signal.price)}   confidence: ${confidence}%`,
  }
}

function LiveTicker() {
  const [connectionState, setConnectionState] = useState('Connecting...')
  const [lines, setLines] = useState([])
  const terminalRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const websocketRef = useRef(null)
  const hasConnectedOnceRef = useRef(false)

  useEffect(() => {
    let shouldReconnect = true

    function connect() {
      setConnectionState(hasConnectedOnceRef.current ? 'Reconnecting...' : 'Connecting...')

      const socket = new WebSocket(WS_URL)
      websocketRef.current = socket

      socket.onopen = () => {
        hasConnectedOnceRef.current = true
        setConnectionState('Connected')
      }

      socket.onmessage = (event) => {
        const signal = JSON.parse(event.data)

        if (signal.error) {
          setLines((currentLines) =>
            [...currentLines, {
              id: `${Date.now()}-error`,
              action: 'HOLD',
              text: `[${new Date().toLocaleTimeString('en-US', { hour12: false })}]  ERROR ${signal.error}`,
            }].slice(-20),
          )
          return
        }

        setLines((currentLines) => [...currentLines, createTickerLine(signal)].slice(-20))
      }

      socket.onclose = () => {
        if (!shouldReconnect) {
          return
        }

        setConnectionState('Reconnecting...')
        reconnectTimerRef.current = window.setTimeout(connect, 3000)
      }

      socket.onerror = () => {
        socket.close()
      }
    }

    connect()

    return () => {
      shouldReconnect = false
      window.clearTimeout(reconnectTimerRef.current)
      websocketRef.current?.close()
    }
  }, [])

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [lines])

  return (
    <section className="card ticker-card">
      <div className="ticker-header">
        <span className="section-heading" style={{ margin: 0 }}>
          Stream
        </span>
        <span className={`ticker-state ${connectionState === 'Connected' ? 'connected' : ''}`}>
          {connectionState}
        </span>
      </div>

      <div className="terminal" ref={terminalRef}>
        {lines.length === 0 ? (
          <div className="terminal-empty">{connectionState}</div>
        ) : (
          lines.map((line) => (
            <div className={`terminal-line ${line.action.toLowerCase()}`} key={line.id}>
              {line.text}
            </div>
          ))
        )}
      </div>
    </section>
  )
}

export default LiveTicker
