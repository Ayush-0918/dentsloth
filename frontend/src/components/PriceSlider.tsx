import './PriceSlider.css'
interface Props {
  low: number; suggested: number; high: number
  onSuggestedChange?: (v: number) => void
}
export function PriceSlider({ low, suggested, high, onSuggestedChange }: Props) {
  const pct = (v: number) => ((v - low) / (high - low)) * 100
  return (
    <div className="price-slider">
      <div className="price-slider__labels">
        <span>₹{low.toLocaleString('en-IN')}</span>
        <span className="price-slider__suggested">₹{suggested.toLocaleString('en-IN')}</span>
        <span>₹{high.toLocaleString('en-IN')}</span>
      </div>
      <div className="price-slider__track" role="presentation">
        <div className="price-slider__fill" style={{ width: `${pct(suggested)}%` }} />
        <input
          type="range" min={low} max={high} step={50}
          value={suggested}
          onChange={e => onSuggestedChange?.(Number(e.target.value))}
          className="price-slider__input"
          aria-label={`Suggested price ₹${suggested.toLocaleString('en-IN')}`}
          aria-valuemin={low} aria-valuemax={high} aria-valuenow={suggested}
        />
      </div>
      <p className="price-slider__hint">Drag to adjust suggested price</p>
    </div>
  )
}
