import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useT } from '../hooks/useT'
import { useApp } from '../context/AppContext'
import { Card } from '../components/Card'
import { Chip } from '../components/Chip'
import { Badge } from '../components/Badge'
import { Banner } from '../components/Banner'
import { Skeleton } from '../components/Skeleton'
import { EmptyState } from '../components/EmptyState'
import { Button } from '../components/Button'
import type { Listing } from '../api'
import './Marketplace.css'

const CONDITIONS = ['A','B','C']
const DEMO_LISTINGS: Listing[] = [
  { instrument_type: 'Sickle Scaler', brand: 'Hu-Friedy', condition_grade: 'B', age_years: 3, suggested_price_inr: 400, price_low: 350, price_high: 480, description_en: 'H6/H7 sickle scaler in good condition.', description_hi: 'H6/H7 सिकल स्केलर अच्छी स्थिति में।', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune', status: 'published', price_explanation: 'Condition B, 3 yrs, premium.', _id: 'd1' },
  { instrument_type: 'Gracey Curette', brand: 'Hu-Friedy', condition_grade: 'A', age_years: 1, suggested_price_inr: 850, price_low: 780, price_high: 950, description_en: 'Gracey 13/14 curette barely used.', description_hi: 'Gracey 13/14 क्यूरेट, बहुत कम इस्तेमाल।', clinic_name: 'Lakeview Polyclinic (Demo)', city: 'Mumbai', status: 'published', price_explanation: 'Condition A, 1 yr, premium.', _id: 'd2' },
  { instrument_type: 'High-Speed Handpiece', brand: 'NSK', condition_grade: 'B', age_years: 4, suggested_price_inr: 7000, price_low: 6000, price_high: 8500, description_en: 'NSK high-speed turbine. Serviced 6 months ago.', description_hi: 'NSK हाई-स्पीड टर्बाइन। 6 माह पूर्व सर्विस की गई।', clinic_name: 'Metro Implant Centre (Demo)', city: 'Delhi', status: 'published', price_explanation: 'Condition B, 4 yrs, premium brand.', _id: 'd3' },
  { instrument_type: 'Ultrasonic Scaler Unit', brand: 'Dentsply', condition_grade: 'B', age_years: 3.5, suggested_price_inr: 8500, price_low: 7500, price_high: 10000, description_en: 'Cavitron Select with 3 tips, all modes working.', description_hi: 'Cavitron Select 3 टिप्स के साथ।', clinic_name: 'Bright Smiles Clinic (Demo)', city: 'Bangalore', status: 'published', price_explanation: 'Condition B, 3.5 yrs, mid-tier.', _id: 'd4' },
  { instrument_type: 'Periodontal Probe', brand: 'Hu-Friedy', condition_grade: 'A', age_years: 0.5, suggested_price_inr: 550, price_low: 500, price_high: 620, description_en: 'Williams probe, as-new condition.', description_hi: 'Williams प्रोब, नई जैसी।', clinic_name: 'Ridgeview Orthodontics (Demo)', city: 'Chennai', status: 'published', price_explanation: 'Condition A, 0.5 yr, premium.', _id: 'd5' },
  { instrument_type: 'Shade Guide', brand: 'Vita', condition_grade: 'B', age_years: 4, suggested_price_inr: 2200, price_low: 1900, price_high: 2600, description_en: 'Vita Classic 16-shade guide, all tabs present.', description_hi: 'Vita Classic 16-शेड गाइड।', clinic_name: 'Metro Implant Centre (Demo)', city: 'Delhi', status: 'published', price_explanation: 'Condition B, 4 yrs, shade staining.', _id: 'd6' },
]

export function Marketplace() {
  const t = useT()
  const { demoMode } = useApp()
  const navigate = useNavigate()
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [cond, setCond] = useState<string[]>([])
  const [descLang, setDescLang] = useState<'en'|'hi'>('en')
  const [detail, setDetail] = useState<Listing | null>(null)
  const [interestSent, setInterestSent] = useState<Record<string,boolean>>({})

  useEffect(() => {
    setLoading(true)
    if (demoMode) {
      setTimeout(() => { setListings(DEMO_LISTINGS); setLoading(false) }, 600)
      return
    }
    fetch('/api/listings').then(r => r.json()).then(d => {
      setListings(d.listings ?? []); setLoading(false)
    }).catch(() => { setListings(DEMO_LISTINGS); setLoading(false) })
  }, [demoMode])

  const filtered = cond.length ? listings.filter(l => cond.includes(l.condition_grade)) : listings

  return (
    <main className="market-page page-wrap" id="main-content">
      <div className="market-page__header">
        <h1>{t('market_title')}</h1>
        <Badge label={t('synthetic_badge')} variant="synthetic" />
      </div>

      {/* Filters */}
      <div className="market-filters" role="search" aria-label="Filter listings">
        <span className="market-filters__label">{t('market_filter_condition')}:</span>
        {CONDITIONS.map(c => (
          <Chip key={c} label={t(`condition_${c as 'A'|'B'|'C'}`)}
            active={cond.includes(c)}
            onClick={() => setCond(p => p.includes(c) ? p.filter(x=>x!==c) : [...p,c])}
          />
        ))}
        {cond.length > 0 && <button className="market-filters__clear" onClick={() => setCond([])}>Clear</button>}
      </div>

      {/* Listing grid */}
      {loading ? (
        <div className="listing-grid">
          {Array.from({length:6}).map((_,i) => (
            <div key={i} className="listing-card-skeleton">
              <Skeleton height="160px" />
              <Skeleton height="1.2em" className="mt-2" />
              <Skeleton width="60%" height="1em" className="mt-2" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState title={t('market_empty')} action={
          <Button variant="ghost" onClick={() => navigate('/kit')}>{t('market_empty_action')}</Button>
        } />
      ) : (
        <div className="listing-grid">
          {filtered.map(l => (
            <Card key={l._id} className="listing-card" onClick={() => setDetail(l)}>
              <div className="listing-card__img-wrap">
                {l.image_url
                  ? <img src={l.image_url} alt={l.instrument_type} className="listing-card__img" loading="lazy" />
                  : <div className="listing-card__no-img" aria-hidden="true">🔧</div>
                }
              </div>
              <div className="listing-card__body">
                <h3 className="listing-card__name">{l.instrument_type}</h3>
                <p className="listing-card__brand text-muted text-sm">{l.brand} · {l.city}</p>
                <div className="listing-card__footer">
                  <span className="listing-card__price">₹{l.suggested_price_inr.toLocaleString('en-IN')}</span>
                  <Badge label={`${l.condition_grade}`} variant="condition" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detail drawer */}
      {detail && (
        <div className="detail-overlay" role="dialog" aria-modal="true" aria-label={detail.instrument_type}>
          <div className="detail-drawer">
            <button className="detail-drawer__close" onClick={() => setDetail(null)} aria-label={t('close')}>✕</button>
            {detail.image_url
              ? <img src={detail.image_url} alt={detail.instrument_type} className="detail-drawer__img" />
              : <div className="detail-drawer__no-img" aria-hidden="true">🔧</div>
            }
            <h2 className="detail-drawer__title">{detail.instrument_type}</h2>
            <p className="detail-drawer__meta text-muted">{detail.brand} · {detail.city} · {detail.clinic_name}</p>
            <Badge label={t(`condition_${detail.condition_grade as 'A'|'B'|'C'}`)} variant="condition" />
            <div className="detail-drawer__price">
              <span className="detail-drawer__price-main">₹{detail.suggested_price_inr.toLocaleString('en-IN')}</span>
              <span className="text-muted text-sm"> (₹{detail.price_low.toLocaleString('en-IN')}–₹{detail.price_high.toLocaleString('en-IN')})</span>
            </div>
            <details className="why-price">
              <summary className="why-price__toggle">{t('result_why_price')}</summary>
              <p className="why-price__body">{detail.price_explanation}</p>
            </details>
            <div className="desc-toggle mt-4">
              <Chip label="EN" active={descLang==='en'} onClick={()=>setDescLang('en')} />
              <Chip label="हिं" active={descLang==='hi'} onClick={()=>setDescLang('hi')} />
            </div>
            <p className="detail-drawer__desc">{descLang==='en' ? detail.description_en : detail.description_hi}</p>
            <Banner variant="warn">{t('market_reprocess_banner')}</Banner>
            <Button
              className="mt-4 w-full"
              onClick={() => { setInterestSent(p=>({...p,[detail._id!]:true})) }}
              disabled={!!interestSent[detail._id!]}
            >{interestSent[detail._id!] ? t('market_interest_sent') : t('market_contact')}</Button>
          </div>
        </div>
      )}
    </main>
  )
}
