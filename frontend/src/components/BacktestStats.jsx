import { useEffect, useState } from 'react'

const API_URL = 'http://localhost:8000/backtest-stats'

const metrics = [
  {
    key: 'total_return',
    label: 'Total Return',
    suffix: '%',
    color: 'var(--color-buy)',
    format: (value) => Number(value ?? 0).toFixed(2),
  },
  {
    key: 'win_rate',
    label: 'Win Rate',
    suffix: '%',
    color: 'var(--color-buy)',
    format: (value) => Number(value ?? 0).toFixed(2),
  },
  {
    key: 'max_drawdown',
    label: 'Max Drawdown',
    suffix: '%',
    color: 'var(--color-sell)',
    format: (value) => Number(value ?? 0).toFixed(2),
  },
  {
    key: 'sharpe_ratio',
    label: 'Sharpe Ratio',
    suffix: '',
    color: 'var(--color-accent)',
    format: (value) => Number(value ?? 0).toFixed(2),
  },
  {
    key: 'total_trades',
    label: 'Total Trades',
    suffix: '',
    color: '#ffffff',
    format: (value) => String(Math.round(Number(value ?? 0))),
  },
]

function BacktestStats() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function fetchStats() {
      try {
        const response = await fetch(API_URL)
        const data = await response.json()

        if (!response.ok || data.error) {
          throw new Error(data.error || 'Unable to load backtest stats')
        }

        if (isMounted) {
          setStats(data)
          setError('')
        }
      } catch (fetchError) {
        if (isMounted) {
          setError(fetchError.message)
        }
      }
    }

    fetchStats()

    return () => {
      isMounted = false
    }
  }, [])

  if (error) {
    return <div className="card error-state">Backtest stats error: {error}</div>
  }

  return (
    <div className="stats-grid">
      {metrics.map((metric) => (
        <article
          className="card metric-card"
          key={metric.key}
          style={{ '--metric-color': metric.color }}
        >
          <p className="metric-label">{metric.label}</p>
          <p className="metric-value">
            {stats ? metric.format(stats[metric.key]) : '--'}
            {metric.suffix}
          </p>
        </article>
      ))}
    </div>
  )
}

export default BacktestStats
