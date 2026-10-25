import { type ButtonHTMLAttributes, type AnchorHTMLAttributes } from 'react'
import './Button.css'

type Variant = 'primary' | 'accent' | 'ghost' | 'danger'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  as?: 'button'
  href?: undefined
}

type AnchorProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  as: 'a'
  href: string
}

type Props = (ButtonProps | AnchorProps) & {
  variant?: Variant
  loading?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ variant = 'primary', loading, size = 'md', children, className = '', ...rest }: Props) {
  const cls = `btn btn--${variant} btn--${size} ${loading ? 'btn--loading' : ''} ${className}`
  if (rest.as === 'a') {
    const { as: _, ...anchorRest } = rest
    return (
      <a className={cls} {...anchorRest}>
        {children}
      </a>
    )
  }
  const { as: _, disabled, ...buttonRest } = rest as ButtonProps
  return (
    <button
      className={cls}
      disabled={disabled || loading}
      {...buttonRest}
    >
      {loading && <span className="btn-spinner" aria-hidden="true" />}
      {children}
    </button>
  )
}
