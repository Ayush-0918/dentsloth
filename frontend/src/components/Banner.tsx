import './Banner.css'
interface Props { children: React.ReactNode; variant?: 'info' | 'warn' | 'synthetic' }
export function Banner({ children, variant = 'info' }: Props) {
  return <div className={`banner banner--${variant}`} role="note">{children}</div>
}
