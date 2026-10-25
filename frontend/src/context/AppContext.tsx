import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from 'react'
import { type Lang, setLang as setI18nLang, getLang } from '../i18n'
import { api, type HealthResponse } from '../api'

export type ServerStatus = 'checking' | 'healthy' | 'waking' | 'offline'

interface AppCtx {
  lang: Lang
  setLang: (l: Lang) => void
  theme: 'light' | 'dark'
  toggleTheme: () => void
  demoMode: boolean
  serverStatus: ServerStatus
  serverInfo: HealthResponse | null
  wakingElapsed: number
  retryHealth: () => void
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
  const [serverStatus, setServerStatus] = useState<ServerStatus>('checking')
  const [serverInfo, setServerInfo] = useState<HealthResponse | null>(null)
  const [wakingElapsed, setWakingElapsed] = useState(0)

  const retryTimerRef = useRef<any>(null)
  const elapsedTimerRef = useRef<any>(null)
  const startAttemptRef = useRef<number>(Date.now())

  const checkHealth = useCallback(async () => {
    const start = Date.now()
    startAttemptRef.current = start

    // If it takes more than 4 seconds, mark as waking
    const slowTimer = setTimeout(() => {
      setServerStatus(prev => (prev === 'healthy' ? 'healthy' : 'waking'))
    }, 4000)

    try {
      const data = await api.health()
      clearTimeout(slowTimer)
      setServerInfo(data)
      setServerStatus('healthy')
      if (typeof data.demo_mode === 'boolean') {
        setDemoMode(data.demo_mode)
      }
      setWakingElapsed(0)
    } catch {
      clearTimeout(slowTimer)
      const elapsed = Math.round((Date.now() - start) / 1000)
      if (Date.now() - startAttemptRef.current > 90000) {
        setServerStatus('offline')
      } else {
        setServerStatus('waking')
        // Schedule next retry in 5s
        retryTimerRef.current = setTimeout(checkHealth, 5000)
      }
    }
  }, [])

  useEffect(() => {
    checkHealth()
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current)
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current)
    }
  }, [checkHealth])

  useEffect(() => {
    if (serverStatus === 'waking') {
      elapsedTimerRef.current = setInterval(() => {
        setWakingElapsed(s => s + 1)
      }, 1000)
    } else {
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current)
      setWakingElapsed(0)
    }
    return () => {
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current)
    }
  }, [serverStatus])

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
    <Ctx.Provider value={{
      lang,
      setLang,
      theme,
      toggleTheme,
      demoMode,
      serverStatus,
      serverInfo,
      wakingElapsed,
      retryHealth: checkHealth
    }}>
      {children}
    </Ctx.Provider>
  )
}

export function useApp() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useApp must be inside AppProvider')
  return ctx
}
