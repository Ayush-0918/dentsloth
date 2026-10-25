import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useT } from '../hooks/useT'
import { useReveal } from '../hooks/useReveal'
import { SlothMascot } from '../components/SlothMascot'
import { Banner } from '../components/Banner'
import './Landing.css'

function AnimatedHeadline({ text }: { text: string }) {
  const ref = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    const el = ref.current; if (!el) return
    const words = text.split(' ')
    el.innerHTML = words.map((w, i) =>
      `<span class="word" style="animation-delay:${i * 80}ms">${w}</span>`
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
            <Link to="/kit"  className="btn btn--ghost  btn--lg hero__cta">{t('hero_cta_buy')}</Link>
          </div>
          <Banner variant="synthetic">{t('synthetic_notice')}</Banner>
        </div>
        <div className="hero__mascot">
          <SlothMascot state="resting" size={160} />
        </div>
      </section>

      <hr />

      {/* How it works */}
      <section className="how page-wrap reveal" ref={howRef as React.RefObject<HTMLElement>}>
        <h2 className="how__title">{t('how_title')}</h2>
        <ol className="how__steps">
          {([
            ['how_step1_title','how_step1_body','📷'],
            ['how_step2_title','how_step2_body','🦥'],
            ['how_step3_title','how_step3_body','🌅'],
          ] as const).map(([tk, bk, icon]) => (
            <li key={tk} className="how__step">
              <span className="how__icon" aria-hidden="true">{icon}</span>
              <h3 className="how__step-title">{t(tk)}</h3>
              <p className="how__step-body">{t(bk)}</p>
            </li>
          ))}
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
