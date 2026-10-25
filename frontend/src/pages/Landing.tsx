import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useT } from '../hooks/useT'
import { useReveal } from '../hooks/useReveal'
import { SlothMascot } from '../components/SlothMascot'
import { Banner } from '../components/Banner'
import { Badge } from '../components/Badge'
import './Landing.css'

function AnimatedHeadline({ text }: { text: string }) {
  const ref = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const words = text.split(' ')
    el.innerHTML = words.map((w, i) =>
      `<span class="word" style="animation-delay:${i * 90}ms">${w}</span>`
    ).join(' ')
  }, [text])
  return <h1 ref={ref} className="hero__headline" aria-label={text} />
}

export function Landing() {
  const t = useT()
  const howRef = useReveal()
  const whyRef = useReveal()

  return (
    <main className="landing" id="main-content">
      {/* Hero */}
      <section className="hero page-wrap">
        <div className="hero__content">
          <AnimatedHeadline text={t('hero_headline')} />
          <p className="hero__sub">{t('hero_sub')}</p>
          <div className="hero__ctas">
            <Link to="/snap" className="btn btn--primary btn--lg hero__cta">{t('hero_cta_sell')}</Link>
            <Link to="/marketplace" className="btn btn--ghost btn--lg hero__cta">Browse Catalog</Link>
          </div>
          <Banner variant="synthetic">{t('synthetic_notice')}</Banner>

          {/* Product Preview Card */}
          <div className="product-preview" aria-label="Product preview example">
            <div className="product-preview__header">
              <span className="product-preview__badge">EXAMPLE RESULT</span>
              <span className="product-preview__meta">Processed in 4.8 s</span>
            </div>
            <div className="product-preview__content">
              <img
                src="/samples/sample_curette.jpg"
                alt="Example instrument scan"
                className="product-preview__img"
              />
              <div className="product-preview__details">
                <div className="product-preview__title-row">
                  <h4 className="product-preview__name">Hu-Friedy Gracey 13/14 Curette</h4>
                  <Badge label="Grade A" variant="condition" />
                </div>
                <div className="product-preview__price-row">
                  <span className="product-preview__price">₹850</span>
                  <span className="product-preview__range">Suggested range: ₹780 – ₹950</span>
                </div>
                <p className="product-preview__snippet">
                  "Hu-Friedy Gracey 13/14 (ग्रेड A)। ऑटोकलेव के लिए सुरक्षित स्टेनलेस स्टील।"
                </p>
                <div className="product-preview__tags">
                  <span className="preview-tag">✓ EXIF Scrubbed</span>
                  <span className="preview-tag">✓ TabPFN Valued</span>
                  <span className="preview-tag">✓ EN + हिं Ready</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="hero__mascot">
          <SlothMascot state="resting" size={170} />
        </div>
      </section>

      <hr />

      {/* How it works */}
      <section className="how page-wrap reveal" ref={howRef as React.RefObject<HTMLElement>}>
        <h2 className="how__title">{t('how_title')}</h2>
        <ol className="how__steps">
          <li className="how__step">
            <div className="how__icon-wrap">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
                <circle cx="18" cy="9" r="1.5" fill="var(--accent)" stroke="var(--accent)"/>
              </svg>
            </div>
            <h3 className="how__step-title">{t('how_step1_title')}</h3>
            <p className="how__step-body">{t('how_step1_body')}</p>
          </li>

          <li className="how__step">
            <div className="how__icon-wrap">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                <circle cx="12" cy="12" r="3"/>
                <circle cx="15" cy="9" r="1.5" fill="var(--accent)" stroke="var(--accent)"/>
              </svg>
            </div>
            <h3 className="how__step-title">{t('how_step2_title')}</h3>
            <p className="how__step-body">{t('how_step2_body')}</p>
          </li>

          <li className="how__step">
            <div className="how__icon-wrap">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                <circle cx="21" cy="7" r="1.5" fill="var(--accent)" stroke="var(--accent)"/>
              </svg>
            </div>
            <h3 className="how__step-title">{t('how_step3_title')}</h3>
            <p className="how__step-body">{t('how_step3_body')}</p>
          </li>
        </ol>
      </section>

      <hr />

      {/* Why open models */}
      <section className="why-open page-wrap reveal" ref={whyRef as React.RefObject<HTMLElement>}>
        <h2 className="why-open__title">{t('why_open_title')}</h2>
        <ul className="why-open__list">
          {(['why_open_1','why_open_2','why_open_3'] as const).map(k => (
            <li key={k} className="why-open__item">
              <span className="why-open__dot" aria-hidden="true" />
              {t(k)}
            </li>
          ))}
        </ul>
      </section>

      <footer className="landing-footer">
        <p>{t('footer_open')}</p>
      </footer>
    </main>
  )
}
