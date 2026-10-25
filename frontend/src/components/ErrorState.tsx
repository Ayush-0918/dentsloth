import { Button } from './Button'
import './ErrorState.css'
interface Props { message: string; onRetry?: () => void; hint?: string }
export function ErrorState({ message, onRetry, hint }: Props) {
  return (
    <div className="error-state" role="alert">
      <p className="error-state__msg">{message}</p>
      {hint && <p className="error-state__hint">{hint}</p>}
      {onRetry && <Button variant="ghost" size="sm" onClick={onRetry}>Try again</Button>}
    </div>
  )
}
