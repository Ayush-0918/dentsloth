import { useApp } from '../context/AppContext'
import { SlothMascot } from './SlothMascot'
import './ServerStatusBanner.css'

export function ServerStatusBanner() {
  const { serverStatus, wakingElapsed, retryHealth } = useApp()

  if (serverStatus === 'healthy' || serverStatus === 'checking') {
    return null
  }

  if (serverStatus === 'waking') {
    return (
      <aside className="server-banner server-banner--waking" role="status" aria-live="polite">
        <div className="server-banner__inner">
          <SlothMascot state="thinking" size={26} />
          <div className="server-banner__text">
            <strong>Waking the sloth...</strong>
            <span>Free cloud server sleeps when idle. Connecting (~{Math.max(4, wakingElapsed)}s)...</span>
          </div>
          <div className="server-banner__spinner" aria-hidden="true" />
        </div>
      </aside>
    )
  }

  if (serverStatus === 'offline') {
    return (
      <aside className="server-banner server-banner--offline" role="alert">
        <div className="server-banner__inner">
          <span className="server-banner__icon">⚠️</span>
          <div className="server-banner__text">
            <strong>Demo API Offline</strong>
            <span>Cloud instance is unreachable right now.</span>
          </div>
          <button type="button" onClick={retryHealth} className="server-banner__retry-btn">
            Retry Connection
          </button>
        </div>
      </aside>
    )
  }

  return null
}
