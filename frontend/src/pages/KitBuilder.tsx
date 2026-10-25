import { useState } from 'react'
import { useT } from '../hooks/useT'
import { useApp } from '../context/AppContext'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { Banner } from '../components/Banner'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { Toast } from '../components/Toast'
import { DEMO_KIT } from '../api/demo'
import type { KitResult } from '../api'
import './KitBuilder.css'

export function KitBuilder() {
  const t = useT()
  const { demoMode } = useApp()
  const [request, setRequest] = useState('')
  const [budget, setBudget] = useState(60000)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<KitResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const examples = [t('kit_example_1'), t('kit_example_2'), t('kit_example_3')]

  const build = async () => {
    if (!request.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      if (demoMode) {
        await new Promise(r => setTimeout(r, 1500))
        setResult(DEMO_KIT)
      } else {
        const res = await fetch('/api/kit', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ request, budget }),
        })
        if (!res.ok) throw new Error((await res.json()).detail || 'Kit build failed')
        setResult(await res.json())
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : t('error_generic'))
    } finally { setLoading(false) }
  }

  const copyKit = () => {
    if (!result) return
    const txt = [
      'DentSloth Starter Kit',
      ...result.selected_listings.map(i => `• ${i.instrument_type}: ₹${i.price.toLocaleString('en-IN')} (${i.condition_grade}) – ${i.clinic_name}`),
      `Total: ₹${result.total_price.toLocaleString('en-IN')}`,
      result.gaps.length ? `Still needed: ${result.gaps.join(', ')}` : '',
    ].filter(Boolean).join('\n')
    navigator.clipboard.writeText(txt)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
    setToast('Kit summary copied!')
  }

  const savings = result ? result.total_new_price_est - result.total_price : 0
  const budgetPct = result ? Math.min(100, (result.total_price / budget) * 100) : 0

  return (
    <main className="kit-page page-wrap" id="main-content">
      <div className="kit-page__header">
        <h1>{t('kit_title')}</h1>
        {demoMode && <Badge label={t('demo_mode_badge')} />}
      </div>

      {/* Input */}
      <Card className="kit-input-card">
        <label className="kit-input-card__label" htmlFor="kit-request">
          {t('kit_placeholder')}
        </label>
        <textarea
          id="kit-request"
          className="kit-input-card__textarea"
          value={request}
          onChange={e => setRequest(e.target.value)}
          placeholder={t('kit_placeholder')}
          rows={3}
        />
        <div className="kit-examples">
          {examples.map(ex => (
            <button key={ex} className="kit-example" onClick={() => setRequest(ex)}>{ex}</button>
          ))}
        </div>
        <div className="kit-budget-row">
          <label htmlFor="kit-budget" className="kit-budget-row__label">{t('kit_budget_label')}</label>
          <input
            id="kit-budget" type="number" min={1000} step={1000}
            value={budget} onChange={e => setBudget(Number(e.target.value))}
            className="kit-budget-row__input"
          />
        </div>
        <Button onClick={build} loading={loading} size="lg">{t('kit_build_btn')}</Button>
      </Card>

      {error && <ErrorState message={error} onRetry={build} />}

      {/* Result */}
      {result && (
        <div className="kit-result">
          {result.selected_listings.length === 0 ? (
            <EmptyState title={t('kit_empty')} />
          ) : (
            <>
              {/* Budget bar */}
              <div className="budget-bar">
                <div className="budget-bar__track">
                  <div className="budget-bar__fill" style={{ width: `${budgetPct}%` }} />
                </div>
                <p className="budget-bar__label">
                  ₹{result.total_price.toLocaleString('en-IN')} / ₹{budget.toLocaleString('en-IN')} budget
                </p>
              </div>

              {/* Savings */}
              <Card className="savings-card">
                <div className="savings-card__row">
                  <span>{t('kit_total')}</span>
                  <span className="savings-card__total">₹{result.total_price.toLocaleString('en-IN')}</span>
                </div>
                <div className="savings-card__row text-muted text-sm">
                  <span>{t('kit_vs_new')}</span>
                  <span>₹{result.total_new_price_est.toLocaleString('en-IN')}</span>
                </div>
                {savings > 0 && (
                  <div className="savings-card__row savings-card__savings">
                    <span>{t('kit_savings')}</span>
                    <span>₹{savings.toLocaleString('en-IN')} <small>{t('kit_savings_note')}</small></span>
                  </div>
                )}
              </Card>

              {/* Kit items */}
              <ul className="kit-list">
                {result.selected_listings.map((item, i) => (
                  <li key={i} className="kit-item">
                    <div className="kit-item__info">
                      <span className="kit-item__name">{item.instrument_type}</span>
                      <span className="kit-item__meta text-muted text-sm">{item.condition_grade} · {item.clinic_name}</span>
                    </div>
                    <span className="kit-item__price">₹{item.price.toLocaleString('en-IN')}</span>
                  </li>
                ))}
              </ul>

              {/* Gaps */}
              {result.gaps.length > 0 && (
                <div className="kit-gaps">
                  <h3 className="kit-gaps__title">{t('kit_gaps_title')}</h3>
                  <ul className="kit-gaps__list">
                    {result.gaps.map(g => <li key={g} className="text-muted">• {g}</li>)}
                  </ul>
                </div>
              )}

              <Banner variant="info">{t('market_reprocess_banner')}</Banner>
              <Banner variant="synthetic">{t('synthetic_notice')}</Banner>

              <div className="kit-actions">
                <Button variant="ghost" onClick={copyKit}>{copied ? '✓ Copied!' : t('kit_copy')}</Button>
                <Button onClick={() => setToast('Wishlist saved (mock)')}>
                  {t('kit_save')}
                </Button>
              </div>
            </>
          )}
        </div>
      )}

      {toast && <Toast message={toast} type="ok" onClose={() => setToast(null)} />}
    </main>
  )
}
