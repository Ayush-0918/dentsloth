import { API_BASE } from '../api'
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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

const CONDITIONS = ['A', 'B', 'C']
const DEMO_LISTINGS: Listing[] = [
  { instrument_type: 'Sickle Scaler', brand: 'Hu-Friedy', condition_grade: 'B', age_years: 3, suggested_price_inr: 400, price_low: 350, price_high: 480, description_en: 'H6/H7 sickle scaler in good condition.', description_hi: 'H6/H7 सिकल स्केलर अच्छी स्थिति में।', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune', status: 'published', price_explanation: 'Condition B, 3 yrs, premium.', _id: 'd1' },
  { instrument_type: 'Gracey Curette', brand: 'Hu-Friedy', condition_grade: 'A', age_years: 1, suggested_price_inr: 850, price_low: 780, price_high: 950, description_en: 'Gracey 13/14 curette barely used.', description_hi: 'Gracey 13/14 क्यूरेट, बहुत कम इस्तेमाल।', clinic_name: 'Lakeview Polyclinic (Demo)', city: 'Mumbai', status: 'published', price_explanation: 'Condition A, 1 yr, premium.', _id: 'd2' },
  { instrument_type: 'Extraction Forceps', brand: 'GDC', condition_grade: 'B', age_years: 4, suggested_price_inr: 450, price_low: 400, price_high: 550, description_en: 'Upper anterior forceps. Clean joints.', description_hi: 'ऊपरी पूर्व दाँत संदंश, जोड़ साफ हैं।', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune', status: 'published', price_explanation: 'Condition B, 4 yrs, mid-tier.', _id: 'd3' },
  { instrument_type: 'Straight Elevator', brand: 'API', condition_grade: 'A', age_years: 1.5, suggested_price_inr: 400, price_low: 350, price_high: 450, description_en: 'Straight elevator #34, blade prime condition.', description_hi: 'सीधा एलिवेटर #34, ब्लेड बेहतरीन स्थिति।', clinic_name: 'Metro Implant Centre (Demo)', city: 'Delhi', status: 'published', price_explanation: 'Condition A, 1.5 yrs, economy-plus.', _id: 'd4' },
  { instrument_type: 'Mathieu Needle Holder', brand: 'Kohler', condition_grade: 'A', age_years: 1.2, suggested_price_inr: 1700, price_low: 1500, price_high: 1900, description_en: 'German stainless steel with tungsten carbide inserts.', description_hi: 'मैथ्यू नीडल होल्डर, टीसी इंसर्ट के साथ जर्मन स्टील।', clinic_name: 'Metro Implant Centre (Demo)', city: 'Delhi', status: 'published', price_explanation: 'Condition A, 1.2 yrs, premium.', _id: 'd5' },
  { instrument_type: 'Periodontal Probe', brand: 'Hu-Friedy', condition_grade: 'B', age_years: 2.5, suggested_price_inr: 350, price_low: 300, price_high: 420, description_en: 'UNC-15 probe, mm markings clear.', description_hi: 'UNC-15 प्रोब, मिलीमीटर अंकन स्पष्ट है।', clinic_name: 'Apex Ortho Associates (Demo)', city: 'Bengaluru', status: 'published', price_explanation: 'Condition B, 2.5 yrs, markings intact.', _id: 'd6' },
]

export function Marketplace() {
  const t = useT()
  const { demoMode } = useApp()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [cond, setCond] = useState<string[]>(() => {
    const param = searchParams.get('cond')
    return param ? param.split(',').filter(Boolean) : []
  })
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [descLang, setDescLang] = useState<'en'|'hi'>('en')
  const [detail, setDetail] = useState<Listing | null>(null)
  const [interestSent, setInterestSent] = useState<Record<string,boolean>>({})
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false)

  // Sync filters to URL query params
  useEffect(() => {
    if (cond.length > 0) {
      setSearchParams({ cond: cond.join(',') }, { replace: true })
    } else {
      setSearchParams({}, { replace: true })
    }
  }, [cond, setSearchParams])

  useEffect(() => {
    if (demoMode) {
      setTimeout(() => { setListings(DEMO_LISTINGS); setLoading(false) }, 500)
      return
    }
    fetch(`${API_BASE}/listings`)
      .then(r => r.json())
      .then(d => {
        setListings(d.listings && d.listings.length > 0 ? d.listings : DEMO_LISTINGS)
        setLoading(false)
      })
      .catch(() => {
        setListings(DEMO_LISTINGS)
        setLoading(false)
      })
  }, [demoMode])

  const filtered = cond.length ? listings.filter(l => cond.includes(l.condition_grade)) : listings

  return (
    <main className="market-page page-wrap" id="main-content">
      <div className="market-page__header">
        <div>
          <h1>{t('market_title')}</h1>
          <p className="market-page__subtitle">Reprocessable clinical instruments from verified local practices</p>
        </div>
        <Badge label="Demo data is synthetic" variant="synthetic" />
      </div>

      {/* Mobile Filter Toggle */}
      <div className="market-mobile-bar">
        <button
          type="button"
          className="market-filter-btn"
          onClick={() => setMobileFilterOpen(o => !o)}
          aria-expanded={mobileFilterOpen}
        >
          ⚙️ Filter by Condition {cond.length > 0 ? `(${cond.length})` : ''}
        </button>
      </div>

      {/* Filters bar / bottom sheet */}
      <div className={`market-filters ${mobileFilterOpen ? 'market-filters--open' : ''}`} role="search" aria-label="Filter listings">
        <span className="market-filters__label">{t('market_filter_condition')}:</span>
        <div className="market-filters__chips">
          {CONDITIONS.map(c => (
            <Chip key={c} label={`Grade ${c} (${c === 'A' ? 'Like-New' : c === 'B' ? 'Good' : 'Fair'})`}
              active={cond.includes(c)}
              onClick={() => setCond(p => p.includes(c) ? p.filter(x=>x!==c) : [...p,c])}
            />
          ))}
        </div>
        {cond.length > 0 && (
          <button className="market-filters__clear" onClick={() => setCond([])}>
            Reset filters
          </button>
        )}
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
        <EmptyState
          title={t('market_empty')}
          action={
            <Button variant="ghost" onClick={() => { setCond([]); navigate('/kit') }}>
              Build a Starter Kit
            </Button>
          }
        />
      ) : (
        <div className="listing-grid">
          {filtered.map(l => (
            <Card key={l._id} className="listing-card" onClick={() => setDetail(l)}>
              <div className="listing-card__img-wrap">
                {l.image_url
                  ? <img src={l.image_url} alt={l.instrument_type} className="listing-card__img" loading="lazy" />
                  : <div className="listing-card__no-img" aria-hidden="true">🔬</div>
                }
                <span className="listing-card__grade-badge">Grade {l.condition_grade}</span>
              </div>
              <div className="listing-card__body">
                <h3 className="listing-card__name">{l.instrument_type.replace(/_/g, ' ')}</h3>
                <p className="listing-card__brand text-muted text-sm">{l.brand} · {l.city || 'Pune'}</p>
                <div className="listing-card__footer">
                  <span className="listing-card__price">₹{l.suggested_price_inr.toLocaleString('en-IN')}</span>
                  <span className="listing-card__clinic text-muted">{l.clinic_name}</span>
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
            <div className="detail-drawer__img-wrap">
              {detail.image_url
                ? <img src={detail.image_url} alt={detail.instrument_type} className="detail-drawer__img" />
                : <div className="detail-drawer__no-img" aria-hidden="true">🔬</div>
              }
            </div>
            <h2 className="detail-drawer__title">{detail.instrument_type.replace(/_/g, ' ')}</h2>
            <p className="detail-drawer__meta text-muted">{detail.brand} · {detail.city || 'Pune'} · {detail.clinic_name}</p>
            <Badge label={`Grade ${detail.condition_grade} (${detail.condition_grade === 'A' ? 'Like-new' : detail.condition_grade === 'B' ? 'Good' : 'Fair'})`} variant="condition" />
            <div className="detail-drawer__price">
              <span className="detail-drawer__price-main">₹{detail.suggested_price_inr.toLocaleString('en-IN')}</span>
              <span className="text-muted text-sm"> (₹{detail.price_low.toLocaleString('en-IN')} – ₹{detail.price_high.toLocaleString('en-IN')})</span>
            </div>
            <details className="why-price">
              <summary className="why-price__toggle">{t('result_why_price')}</summary>
              <p className="why-price__body">{detail.price_explanation}</p>
            </details>
            <div className="desc-toggle mt-4">
              <Chip label="English" active={descLang==='en'} onClick={()=>setDescLang('en')} />
              <Chip label="हिन्दी" active={descLang==='hi'} onClick={()=>setDescLang('hi')} />
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
