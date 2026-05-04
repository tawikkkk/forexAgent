import { useEffect, useMemo, useState } from 'react'

const API_URL = 'http://localhost:8000/signals'

const actionColors = {
  BUY: 'var(--color-buy)',
  SELL: 'var(--color-sell)',
  HOLD: 'var(--color-hold)',
}

function formatPrice(price) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price ?? 0)
}

function SignalSkeleton() {
  return (
    <div className="skeleton-stack" aria-label="Loading latest signal">
      <div className="skeleton action" />
      <div className="skeleton price-line" />
      <div className="skeleton bar" />
    </div>
  )
}

function SignalCard() {
  const [signal, setSignal] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function fetchSignal() {
      try {
        const response = await fetch(API_URL)
        const data = await response.json()

        if (!response.ok || data.error) {
          throw new Error(data.error || 'Unable to load signal')
        }

        if (isMounted) {
          setSignal(data)
          setError('')
        }
      } catch (fetchError) {
        if (isMounted) {
          setError(fetchError.message)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    fetchSignal()
    const intervalId = window.setInterval(fetchSignal, 10000)

    return () => {
      isMounted = false
      window.clearInterval(intervalId)
    }
  }, [])

  const action = signal?.action || 'HOLD'
  const actionClass = action.toLowerCase()
  const confidencePercent = Math.round((signal?.confidence ?? 0) * 100)
  const actionColor = useMemo(() => actionColors[action] || actionColors.HOLD, [action])

  return (
    <section className={`card signal-card ${actionClass}`}>
      {isLoading ? (
        <SignalSkeleton />
      ) : error ? (
        <div className="error-state">Signal error: {error}</div>
      ) : (
        <div className="signal-content">
          <h1 className={`action-label ${actionClass}`}>{action}</h1>
          <div className="price">{formatPrice(signal.price)}</div>

          <div className="confidence-row">
            <span>Confidence</span>
            <span>{confidencePercent}%</span>
          </div>
          <div className="confidence-track" aria-label={`Confidence ${confidencePercent}%`}>
            <div
              className="confidence-fill"
              style={{
                width: `${confidencePercent}%`,
                background: actionColor,
              }}
            />
          </div>

          <div className="signal-meta">
            <span>{signal.timestamp}</span>
            <span className={`mode-badge ${signal.mode === 'live' ? 'live' : 'demo'}`}>
              {signal.mode === 'live' ? '● LIVE' : '● DEMO'}
            </span>
          </div>
        </div>
      )}
    </section>
  )
}

export default SignalCard
