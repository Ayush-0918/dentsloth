import './Skeleton.css'
interface Props { width?: string; height?: string; className?: string; lines?: number }
export function Skeleton({ width = '100%', height = '1em', className = '', lines = 1 }: Props) {
  if (lines > 1) return (
    <div className={`skeleton-block ${className}`}>
      {Array.from({length: lines}).map((_, i) => (
        <span key={i} className="skeleton" style={{ width: i === lines - 1 ? '70%' : '100%', height, display: 'block', marginBottom: 6 }} />
      ))}
    </div>
  )
  return <span className={`skeleton ${className}`} style={{ width, height, display: 'block' }} aria-hidden="true" />
}
