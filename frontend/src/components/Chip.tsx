import './Chip.css'
interface Props { label: string; active?: boolean; onClick?: () => void }
export function Chip({ label, active, onClick }: Props) {
  return (
    <button
      className={`chip ${active ? 'chip--active' : ''}`}
      onClick={onClick}
      type="button"
      aria-pressed={active}
    >{label}</button>
  )
}
