import { useApp } from '../context/AppContext'
import { t, type TranslationKey } from '../i18n'

export function useT() {
  const { lang } = useApp() // re-render when lang changes
  void lang
  return t
}
