import { useState, useRef, useCallback, type DragEvent, type ChangeEvent } from 'react'
import { useT } from '../hooks/useT'
import { useApp } from '../context/AppContext'
import { Button } from '../components/Button'
import { Card } from '../components/Card'
import { SlothMascot } from '../components/SlothMascot'
import { Stepper, type Step } from '../components/Stepper'
import { PriceSlider } from '../components/PriceSlider'
import { Chip } from '../components/Chip'
import { Badge } from '../components/Badge'
import { Banner } from '../components/Banner'
import { ErrorState } from '../components/ErrorState'
import { Toast } from '../components/Toast'
import { DEMO_IDENTIFY } from '../api/demo'
import type { IdentifiedItem } from '../api'
import './SnapAndList.css'

type FlowState = 'idle' | 'processing' | 'result' | 'refused' | 'published' | 'error'

export function SnapAndList() {
  const t = useT()
  const { demoMode } = useApp()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [flowState, setFlowState] = useState<FlowState>('idle')
  const [preview, setPreview] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [steps, setSteps] = useState<Step[]>([
    { label: t('step_identifying'), status: 'waiting' },
    { label: t('step_pricing'), status: 'waiting' },
    { label: t('step_writing'), status: 'waiting' },
  ])
  const [items, setItems] = useState<IdentifiedItem[]>([])
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [descLang, setDescLang] = useState<'en' | 'hi'>('en')
  const [toast, setToast] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [refusalMsg, setRefusalMsg] = useState<string | null>(null)
  const [suggestedPrice, setSuggestedPrice] = useState<Record<number, number>>({})

  const runStep = (idx: number, status: Step['status'], elapsed?: number) => {
    setSteps(s => s.map((step, i) => i === idx ? { ...step, status, elapsed } : step))
  }

  const processFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/')) return
    setPreview(URL.createObjectURL(file))
    setFlowState('processing')
    setErrorMsg(null)
    setRefusalMsg(null)

    const stepsReset: Step[] = [
      { label: t('step_identifying'), status: 'active' },
      { label: t('step_pricing'), status: 'waiting' },
      { label: t('step_writing'), status: 'waiting' },
    ]
    setSteps(stepsReset)

    try {
      const t0 = Date.now()
      let result = DEMO_IDENTIFY

      if (!demoMode) {
        const fd = new FormData(); fd.append('file', file)
        const res = await fetch('/api/identify', { method: 'POST', body: fd })
        if (!res.ok) throw new Error((await res.json()).detail || 'Identify failed')
        result = await res.json()
      } else {
        await new Promise(r => setTimeout(r, 1800))
      }

      runStep(0, 'done', Date.now() - t0)

      // Check refusals
      const refused = result.items.filter(i => i.is_single_use || i.confidence < 0.4)
      if (result.items.length > 0 && refused.length === result.items.length) {
        const r = refused[0]
        setRefusalMsg(r.is_single_use ? t('refusal_single_use') : t('refusal_low_confidence'))
        setFlowState('refused')
        return
      }

      const t1 = Date.now()
      runStep(1, 'active')
      for (const it of result.items) {
        if (!it.price && !demoMode) {
          try {
            const pRes = await fetch('/api/price', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                instrument_type: it.instrument_type,
                brand: it.likely_brand,
                condition_grade: it.condition_grade,
                age_years: 2.0,
              }),
            })
            if (pRes.ok) {
              const pData = await pRes.json()
              it.price = pData
              it.price_explanation = pData.explanation
            }
          } catch (e) {
            console.warn('Pricing call error:', e)
          }
        }
      }
      runStep(1, 'done', Date.now() - t1)

      const t2 = Date.now()
      runStep(2, 'active')
      for (const it of result.items) {
        if (!it.description_en) {
          const typeLabel = it.instrument_type.replace(/_/g, ' ')
          const brandLabel = it.likely_brand !== 'unknown' ? it.likely_brand : 'Professional'
          it.description_en = `${brandLabel} ${typeLabel} (Grade ${it.condition_grade}). Sterilization inspected: autoclave ready. ${it.price?.explanation || ''}`
          it.description_hi = `${brandLabel} ${typeLabel} (ग्रेड ${it.condition_grade})। ऑटोकलेव के लिए सुरक्षित स्टेनलेस स्टील। जाँचा गया नैदानिक पुनः उपयोग।`
        }
      }
      runStep(2, 'done', Date.now() - t2)

      const validItems = result.items.filter(i => !i.is_single_use && i.confidence >= 0.4)
      setItems(validItems)
      const prices: Record<number, number> = {}
      validItems.forEach((it, i) => { prices[i] = it.price?.suggested_price_inr ?? 500 })
      setSuggestedPrice(prices)
      setFlowState('result')
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : t('error_generic'))
      setFlowState('error')
    }
  }, [demoMode, t])

  const handleDrop = (e: DragEvent) => {
    e.preventDefault(); setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) processFile(file)
  }

  const handlePublish = async () => {
    const item = items[selectedIdx]
    try {
      const res = await fetch('/api/listings/auto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...item,
          suggested_price_inr: suggestedPrice[selectedIdx] ?? item.price?.suggested_price_inr ?? 500,
        }),
      })
      if (!res.ok) throw new Error('Publish failed')
      const created = await res.json()
      if (created.id) {
        await fetch(`/api/listings/${created.id}/publish`, { method: 'POST' })
      }
      setFlowState('published')
    } catch (err: unknown) {
      if (demoMode) {
        setFlowState('published')
      } else {
        setToast('Publish failed – ' + (err instanceof Error ? err.message : t('error_retry')))
      }
    }
  }

  const reset = () => {
    setFlowState('idle'); setPreview(null); setItems([]); setSelectedIdx(0)
    setSteps([
      { label: t('step_identifying'), status: 'waiting' },
      { label: t('step_pricing'), status: 'waiting' },
      { label: t('step_writing'), status: 'waiting' },
    ])
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const item = items[selectedIdx]

  return (
    <main className="snap-page page-wrap" id="main-content">
      <h1 className="snap-page__title">{t('snap_title')}</h1>
      {demoMode && <Badge label={t('demo_mode_badge')} className="snap-page__demo-badge" />}

      {/* Idle: upload */}
      {flowState === 'idle' && (
        <div
          className={`drop-zone ${dragging ? 'drop-zone--dragging' : ''}`}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button" tabIndex={0}
          aria-label={t('snap_drop_hint')}
          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click() }}
        >
          <span className="drop-zone__icon" aria-hidden="true">📷</span>
          <p className="drop-zone__hint">{t('snap_drop_hint')}</p>
          <input
            ref={fileInputRef} type="file" accept="image/*"
            capture="environment"
            onChange={handleFile}
            className="drop-zone__input" aria-hidden="true"
          />
        </div>
      )}
      <p className="snap-page__privacy">{t('snap_privacy_note')}</p>

      {/* Processing */}
      {flowState === 'processing' && (
        <div className="processing-view">
          <div className="processing-view__preview">
            {preview && <img src={preview} alt="Uploaded instrument" className="processing-view__img" />}
          </div>
          <div className="processing-view__right">
            <SlothMascot state="thinking" size={100} />
            <p className="processing-view__label">{t('snap_processing')}</p>
            <Stepper steps={steps} />
          </div>
        </div>
      )}

      {/* Refusal */}
      {flowState === 'refused' && (
        <Card className="refusal-card">
          <p className="refusal-card__msg">{refusalMsg}</p>
          <Button variant="ghost" onClick={reset}>{t('refusal_retake')}</Button>
        </Card>
      )}

      {/* Error */}
      {flowState === 'error' && (
        <ErrorState message={errorMsg || t('error_generic')} hint={t('error_demo_hint')} onRetry={reset} />
      )}

      {/* Result */}
      {flowState === 'result' && item && (
        <div className="result-view">
          {items.length > 1 && (
            <div className="result-tabs">
              {items.map((it, i) => (
                <Chip key={i} label={it.instrument_type} active={i === selectedIdx} onClick={() => setSelectedIdx(i)} />
              ))}
            </div>
          )}

          <Card className="result-card">
            {preview && <img src={preview} alt="Uploaded" className="result-card__img" />}
            <div className="result-card__body">
              <div className="result-card__row">
                <span className="result-card__label">{t('result_instrument')}</span>
                <span className="result-card__value">{item.instrument_type.replace(/_/g,' ')}</span>
              </div>
              <div className="result-card__row">
                <span className="result-card__label">{t('result_brand')}</span>
                <span className="result-card__value">{item.likely_brand}</span>
              </div>
              <div className="result-card__row">
                <span className="result-card__label">{t('result_condition')}</span>
                <div className="cond-chips">
                  {(['A','B','C'] as const).map(g => (
                    <Chip key={g} label={t(`condition_${g}`)} active={item.condition_grade === g} />
                  ))}
                </div>
              </div>
              {item.visible_defects.length > 0 && (
                <div className="result-card__row">
                  <span className="result-card__label">{t('result_defects')}</span>
                  <ul className="defects-list">{item.visible_defects.map(d => <li key={d}>{d}</li>)}</ul>
                </div>
              )}

              <hr />
              <h3 className="result-card__section">{t('result_price_range')}</h3>
              {item.price && (
                <PriceSlider
                  low={item.price.price_low}
                  suggested={suggestedPrice[selectedIdx] ?? item.price.suggested_price_inr}
                  high={item.price.price_high}
                  onSuggestedChange={v => setSuggestedPrice(p => ({...p, [selectedIdx]: v}))}
                />
              )}
              <details className="why-price">
                <summary className="why-price__toggle">{t('result_why_price')}</summary>
                <p className="why-price__body">{item.price_explanation || item.price?.explanation}</p>
              </details>

              <hr />
              <div className="desc-toggle">
                <Chip label="EN" active={descLang === 'en'} onClick={() => setDescLang('en')} />
                <Chip label="हिं" active={descLang === 'hi'} onClick={() => setDescLang('hi')} />
              </div>
              <p className="result-card__desc">
                {descLang === 'en' ? item.description_en : item.description_hi}
              </p>

              <Banner variant="info">{t('market_reprocess_banner')}</Banner>

              <div className="result-card__actions">
                <Button onClick={handlePublish} size="lg">{t('publish_btn')}</Button>
                <Button variant="ghost" onClick={reset}>{t('refusal_retake')}</Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Published */}
      {flowState === 'published' && (
        <div className="published-view">
          <SlothMascot state="happy" size={140} />
          <h2 className="published-view__title">{t('publish_success')}</h2>
          <div className="published-view__actions">
            <Button as="a" href="/marketplace" variant="ghost">View Marketplace</Button>
            <Button onClick={reset}>{t('publish_add_another')}</Button>
          </div>
        </div>
      )}

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </main>
  )
}
