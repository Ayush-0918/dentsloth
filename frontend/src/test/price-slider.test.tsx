import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { PriceSlider } from '../components/PriceSlider'

describe('PriceSlider', () => {
  it('renders low, suggested, high labels', () => {
    render(<PriceSlider low={300} suggested={500} high={700} />)
    expect(screen.getByText(/₹300/)).toBeInTheDocument()
    expect(screen.getByText(/₹700/)).toBeInTheDocument()
    expect(screen.getByText(/₹500/)).toBeInTheDocument()
  })

  it('calls onSuggestedChange when slider moves', () => {
    const onChange = vi.fn()
    render(<PriceSlider low={300} suggested={500} high={700} onSuggestedChange={onChange} />)
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '600' } })
    expect(onChange).toHaveBeenCalledWith(600)
  })

  it('slider min/max enforce low <= suggested <= high in aria', () => {
    render(<PriceSlider low={300} suggested={500} high={700} />)
    const slider = screen.getByRole('slider')
    expect(Number(slider.getAttribute('aria-valuemin'))).toBeLessThanOrEqual(500)
    expect(Number(slider.getAttribute('aria-valuemax'))).toBeGreaterThanOrEqual(500)
  })
})
