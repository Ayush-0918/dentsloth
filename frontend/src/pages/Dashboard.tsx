import { API_BASE } from '../api'
import { useState, useEffect } from 'react'
import { useT } from '../hooks/useT'
import { useApp } from '../context/AppContext'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { Banner } from '../components/Banner'
import { Skeleton } from '../components/Skeleton'
import { EmptyState } from '../components/EmptyState'
import { Button } from '../components/Button'
import { DEMO_DASHBOARD } from '../api/demo'
import type { DashboardData } from '../api'
import { Link } from 'react-router-dom'
import './Dashboard.css'

export function Dashboard() {
  const t = useT()
  const { demoMode } = useApp()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [manualMinutes, setManualMinutes] = useState(30)

  useEffect(() => {
    if (demoMode) {
      setTimeout(() => { setData(DEMO_DASHBOARD); setLoading(false) }, 700)
      return
    }
    fetch(`${API_BASE}/dashboard`).then(r => r.json()).then(d => {
      setData(d); setLoading(false)
    }).catch(() => { setData(DEMO_DASHBOARD); setLoading(false) })
  }, [demoMode])

  const listingCount = data?.listings.length ?? 0
  const medianS = data?.lazy_payoff?.measured_median_s ?? 38
  const savedMin = listingCount * (manualMinutes - medianS / 60)

  const fmtTime = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' }) + ' · ' + d.toLocaleDateString('en-IN', { day:'numeric', month:'short' })
  }

  return (
    <main className="dash-page page-wrap" id="main-content">
      <div className="dash-page__header">
        <h1>{t('dash_title')}</h1>
        <Badge label={t('synthetic_badge') || 'Demo data is synthetic'} variant="synthetic" />
        {demoMode && <Badge label={t('demo_mode_badge')} />}
      </div>

      {loading ? (
        <div className="dash-skeleton">
          <Skeleton height="100px" className="mb-4" />
          <Skeleton height="60px" />
          <Skeleton height="60px" />
        </div>
      ) : (
        <div className="dash-grid">
          {/* Morning summary */}
          {data?.sloth_run && (
            <Card className="dash-summary">
              <h2 className="dash-summary__greet">{t('dash_good_morning')} 🌅</h2>
              <p className="dash-summary__text">{data.sloth_run.summary}</p>
              <p className="dash-summary__ts text-muted text-sm">{t('dash_last_run')}: {fmtTime(data.sloth_run.timestamp)}</p>
            </Card>
          )}

          {/* Lazy payoff */}
          <Card className="payoff-card">
            <h2 className="payoff-card__title">{t('dash_lazy_payoff')}</h2>
            {listingCount === 0 ? (
              <EmptyState title={t('dash_payoff_empty')} />
            ) : (
              <>
                <div className="payoff-big">
                  <span className="payoff-big__num">{savedMin.toFixed(1)}</span>
                  <span className="payoff-big__unit">min saved</span>
                </div>
                <details className="payoff-formula">
                  <summary>See formula</summary>
                  <div className="payoff-formula__body">
                    <p className="payoff-formula__eq">{t('dash_payoff_formula')}</p>
                    <div className="payoff-formula__row">
                      <label htmlFor="manual-min">{t('dash_payoff_manual')}</label>
                      <input id="manual-min" type="number" min={1} max={120} value={manualMinutes}
                        onChange={e => setManualMinutes(Number(e.target.value))}
                        className="payoff-formula__input"
                      /> min
                    </div>
                    <div className="payoff-formula__row">
                      <span>{t('dash_payoff_measured')}</span>
                      <span>{medianS}s</span>
                    </div>
                    <p className="payoff-formula__note">{t('dash_payoff_note')}</p>
                  </div>
                </details>
              </>
            )}
          </Card>

          {/* My listings */}
          <section className="dash-section">
            <h2>{t('dash_my_listings')}</h2>
            {(data?.listings ?? []).length === 0 ? (
              <EmptyState title={t('dash_no_listings')} action={<Button as="a" href="/snap">{t('nav_sell')}</Button>} />
            ) : (
              <ul className="dash-list">
                {(data?.listings ?? []).map((l, i) => (
                  <li key={i} className="dash-list__item">
                    <span className="dash-list__name">{l.instrument_type}</span>
                    <Badge label={l.status} variant="condition" />
                    <span className="dash-list__price text-muted">₹{l.suggested_price_inr.toLocaleString('en-IN')}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Matches */}
          <section className="dash-section">
            <h2>{t('dash_matches')}</h2>
            {(data?.matches ?? []).length === 0 ? (
              <p className="text-muted">{t('dash_no_matches')}</p>
            ) : (
              <ul className="dash-list">
                {((data?.matches ?? []) as Array<{buyer:string;instrument:string;score:number}>).map((m, i) => (
                  <li key={i} className="dash-list__item">
                    <span className="dash-list__name">{m.instrument}</span>
                    <span className="text-muted text-sm">{m.buyer}</span>
                    <Badge label={`${Math.round(m.score*100)}%`} variant="condition" />
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Notifications (mock) */}
          <section className="dash-section">
            <div className="dash-section__head">
              <h2>{t('dash_notifications')}</h2>
              <Banner variant="info">{t('dash_notifications_note')}</Banner>
            </div>
            <ul className="dash-events">
              {(data?.events as Array<{type:string;message:string;ts:string}> ?? []).map((ev, i) => (
                <li key={i} className="dash-event">
                  <span className="dash-event__dot" aria-hidden="true" />
                  <div>
                    <p className="dash-event__msg">{ev.message}</p>
                    <p className="dash-event__ts text-muted text-sm">{fmtTime(ev.ts)}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </main>
  )
}
