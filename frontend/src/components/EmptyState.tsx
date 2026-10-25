import { type ReactNode } from 'react'
import './EmptyState.css'
interface Props { title: string; body?: string; action?: ReactNode }
export function EmptyState({ title, body, action }: Props) {
  return (
    <div className="empty-state" role="status">
      <div className="empty-state__icon" aria-hidden="true">🦥</div>
      <h3 className="empty-state__title">{title}</h3>
      {body && <p className="empty-state__body">{body}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  )
}
