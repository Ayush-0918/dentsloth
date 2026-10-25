import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { type Lang, setLang as setI18nLang, getLang } from '../i18n'
import { API_BASE } from '../api'

interface AppCtx {
  lang: Lang
  setLang: (l: Lang) => void
  theme: 'light' | 'dark'
  toggleTheme: () => void
  demoMode: boolean
}

const Ctx = createContext<AppCtx | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getLang())
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('dentsloth-theme')
    if (stored === 'light' || stored === 'dark') return stored
    return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  const [demoMode, setDemoMode] = useState<boolean>(import.meta.env.VITE_DEMO_MODE === 'true')

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(d => {
        if (typeof d.demo_mode === 'boolean') {
          setDemoMode(d.demo_mode)
        }
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('dentsloth-theme', theme)
  }, [theme])

  const setLang = useCallback((l: Lang) => {
    setI18nLang(l)
    setLangState(l)
    document.documentElement.lang = l
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme(t => t === 'dark' ? 'light' : 'dark')
  }, [])

  return (
    <Ctx.Provider value={{ lang, setLang, theme, toggleTheme, demoMode }}>
      {children}
    </Ctx.Provider>
  )
}

export function useApp() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useApp must be inside AppProvider')
  return ctx
}
