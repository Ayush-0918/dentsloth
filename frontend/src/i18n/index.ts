import { en } from './en'
import { hi } from './hi'

export type Lang = 'en' | 'hi'
export type TranslationKey = keyof typeof en

const translations = { en, hi }

let currentLang: Lang = (localStorage.getItem('dentsloth-lang') as Lang) || 'en'

export function setLang(lang: Lang) {
  currentLang = lang
  localStorage.setItem('dentsloth-lang', lang)
  document.documentElement.lang = lang
}

export function getLang(): Lang { return currentLang }

export function t(key: TranslationKey): string {
  const dict = translations[currentLang] as Record<string, string>
  return dict[key] ?? (translations.en as Record<string, string>)[key] ?? key
}
