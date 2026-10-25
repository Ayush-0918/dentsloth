import './Stepper.css'
export interface Step { label: string; status: 'waiting' | 'active' | 'done'; elapsed?: number }
interface Props { steps: Step[] }
export function Stepper({ steps }: Props) {
  return (
    <ol className="stepper" aria-label="Processing steps">
      {steps.map((s, i) => (
        <li key={i} className={`stepper__step stepper__step--${s.status}`}>
          <span className="stepper__dot" aria-hidden="true">
            {s.status === 'done' ? '✓' : i + 1}
          </span>
          <span className="stepper__label">{s.label}</span>
          {s.status === 'done' && s.elapsed !== undefined && (
            <span className="stepper__time">{(s.elapsed / 1000).toFixed(1)}s</span>
          )}
          {s.status === 'active' && <span className="stepper__pulse" aria-hidden="true" />}
        </li>
      ))}
    </ol>
  )
}
