import BacktestStats from './components/BacktestStats'
import LiveTicker from './components/LiveTicker'
import SignalCard from './components/SignalCard'
import TrainingStatus from './components/TrainingStatus'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">⬡ XAUUSD AI</div>
        <TrainingStatus />
      </header>

      <main className="main-content">
        <section className="dashboard-section" aria-label="Signal">
          <SignalCard />
        </section>

        <section className="dashboard-section" aria-labelledby="performance-heading">
          <h2 className="section-heading" id="performance-heading">
            Backtest Performance
          </h2>
          <BacktestStats />
        </section>

        <section className="dashboard-section" aria-labelledby="live-feed-heading">
          <h2 className="section-heading" id="live-feed-heading">
            Live Signal Feed
          </h2>
          <LiveTicker />
        </section>
      </main>

      <footer className="footer">
        AI signals are for educational purposes only. Not financial advice.
      </footer>
    </div>
  )
}

export default App
