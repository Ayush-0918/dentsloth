import { Link, useLocation } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { useT } from '../hooks/useT'
import { Badge } from './Badge'
import './Nav.css'

export function Nav() {
  const { lang, setLang, theme, toggleTheme, demoMode } = useApp()
  const t = useT()
  const loc = useLocation()

  const links = [
    { to: '/snap', labelKey: 'nav_sell' as const, icon: '📷' },
    { to: '/marketplace', labelKey: 'nav_browse' as const, icon: '🔍' },
    { to: '/kit', labelKey: 'nav_kit' as const, icon: '🧰' },
    { to: '/dashboard', labelKey: 'nav_morning' as const, icon: '🌅' },
  ]

  return (
    <>
      <header className="nav" role="banner">
        <div className="page-wrap nav__inner">
          <Link to="/" className="nav__logo" aria-label={t('nav_logo_alt')}>
            <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
              <circle cx="16" cy="16" r="14" fill="var(--ink)"/>
              <circle cx="16" cy="14" r="6" fill="var(--bg)" opacity=".9"/>
              <circle cx="16" cy="18" r="9" fill="var(--ink)"/>
              <circle cx="13" cy="13" r="1.5" fill="var(--ink)"/>
              <circle cx="19" cy="13" r="1.5" fill="var(--ink)"/>
              <circle cx="22" cy="20" r="2" fill="var(--accent)"/>
            </svg>
            <span className="nav__wordmark">DentSloth</span>
          </Link>

          <nav className="nav__links" aria-label="Main navigation">
            {links.map(l => (
              <Link key={l.to} to={l.to}
                className={`nav__link ${loc.pathname === l.to ? 'nav__link--active' : ''}`}
              >{t(l.labelKey)}</Link>
            ))}
          </nav>

          <div className="nav__controls">
            {demoMode && <Badge label={t('demo_mode_badge')} variant="demo" />}
            <button
              className="nav__btn"
              onClick={() => setLang(lang === 'en' ? 'hi' : 'en')}
              aria-label={`Switch to ${lang === 'en' ? 'Hindi' : 'English'}`}
            >{t('nav_lang_toggle')}</button>
            <button
              className="nav__btn"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            >{theme === 'dark' ? '☀️' : '🌙'}</button>
          </div>
        </div>
      </header>

      {/* Mobile bottom tabs */}
      <nav className="bottom-tabs" aria-label="Mobile navigation">
        {links.map(l => (
          <Link key={l.to} to={l.to}
            className={`bottom-tab ${loc.pathname.startsWith(l.to) ? 'bottom-tab--active' : ''}`}
          >
            <span className="bottom-tab__icon" aria-hidden="true">{l.icon}</span>
            <span className="bottom-tab__label">{t(l.labelKey)}</span>
          </Link>
        ))}
      </nav>
    </>
  )
}
