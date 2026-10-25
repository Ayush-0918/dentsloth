import { type ReactNode } from 'react'
import './Card.css'

interface Props {
  children: ReactNode
  className?: string
  onClick?: () => void
  as?: keyof JSX.IntrinsicElements
}

export function Card({ children, className = '', onClick, as: Tag = 'div' }: Props) {
  return (
    <Tag
      className={`card ${onClick ? 'card--clickable' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e: React.KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') onClick() } : undefined}
    >
      {children}
    </Tag>
  )
}
