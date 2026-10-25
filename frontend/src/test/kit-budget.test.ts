import { describe, it, expect } from 'vitest'
import { DEMO_KIT } from '../api/demo'

describe('Kit budget constraint (UI invariant)', () => {
  it('demo kit total does not exceed 60000', () => {
    expect(DEMO_KIT.total_price).toBeLessThanOrEqual(60000)
  })
  it('every item price >= 0', () => {
    DEMO_KIT.selected_listings.forEach(i => expect(i.price).toBeGreaterThanOrEqual(0))
  })
  it('total_new_price_est >= total_price (savings >= 0)', () => {
    expect(DEMO_KIT.total_new_price_est).toBeGreaterThanOrEqual(DEMO_KIT.total_price)
  })
})
