import { useEffect } from 'react'
import './Toast.css'
interface Props { message: string; type?: 'ok' | 'error' | 'info'; onClose: () => void }
export function Toast({ message, type = 'info', onClose }: Props) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div className={`toast toast--${type}`} role="alert" aria-live="assertive">
      <span>{message}</span>
      <button className="toast__close" onClick={onClose} aria-label="Close notification">×</button>
    </div>
  )
}
