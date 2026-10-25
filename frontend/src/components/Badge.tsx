import './Badge.css'
interface Props { label: string; variant?: 'demo' | 'synthetic' | 'condition' | 'warn'; className?: string }
export function Badge({ label, variant = 'demo', className = '' }: Props) {
  return <span className={`badge badge--${variant} ${className}`}>{label}</span>
}
