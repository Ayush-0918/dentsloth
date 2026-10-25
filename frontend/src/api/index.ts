const BASE = import.meta.env.VITE_API_URL || '/api'

async function req<T>(method: string, path: string, body?: unknown, isForm = false): Promise<T> {
  const opts: RequestInit = { method }
  if (body) {
    if (isForm) {
      opts.body = body as FormData
    } else {
      opts.headers = { 'Content-Type': 'application/json' }
      opts.body = JSON.stringify(body)
    }
  }
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => req<{ status: string; demo_mode: boolean; db: string; llm_provider: string }>('GET', '/health'.replace('/api', '').replace('//','/')),
  identify: (file: File) => {
    const fd = new FormData(); fd.append('file', file)
    return req<IdentifyResponse>('POST', '/identify', fd, true)
  },
  price: (payload: PriceRequest) => req<PriceResponse>('POST', '/price', payload),
  createListing: (payload: unknown) => req<{ id: string; draft: unknown }>('POST', '/listings/auto', payload, false),
  publishListing: (id: string) => req<{ id: string; status: string }>('POST', `/listings/${id}/publish`),
  getListings: (params?: Record<string,string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return req<{ listings: Listing[] }>('GET', `/listings${qs}`)
  },
  getListing: (id: string) => req<Listing>('GET', `/listings/${id}`),
  createWishlist: (payload: unknown) => req<{ id: string }>('POST', '/wishlist', payload),
  buildKit: (payload: { request: string; budget: number }) => req<KitResult>('POST', '/kit', payload),
  getDashboard: () => req<DashboardData>('GET', '/dashboard'),
}

// ── Type stubs (will be expanded as backend phases complete) ──────────────────
export interface IdentifyResponse {
  items: IdentifiedItem[]
  notes?: string
  demo?: boolean
}
export interface IdentifiedItem {
  instrument_type: string
  likely_brand: string
  material: string
  condition_grade: 'A' | 'B' | 'C'
  visible_defects: string[]
  needs_sharpening: boolean
  is_single_use: boolean
  confidence: number
  price?: PriceResponse
  description_en?: string
  description_hi?: string
  price_explanation?: string
  id?: string
}
export interface PriceRequest { instrument_type: string; brand: string; condition_grade: string; age_years: number; original_price_inr?: number; sterilization_cycles_est?: number }
export interface PriceResponse { suggested_price_inr: number; price_low: number; price_high: number; explanation: string }
export interface Listing {
  _id?: string
  instrument_type: string
  brand: string
  condition_grade: string
  age_years: number
  original_price_inr?: number
  suggested_price_inr: number
  price_low: number
  price_high: number
  description_en: string
  description_hi: string
  image_url?: string
  clinic_name: string
  city: string
  status: string
  price_explanation: string
  created_at?: string
}
export interface KitResult {
  selected_listings: KitItem[]
  total_price: number
  total_new_price_est: number
  gaps: string[]
}
export interface KitItem {
  listing_id: string
  instrument_type: string
  price: number
  condition_grade: string
  clinic_name: string
  city?: string
  description_en?: string
  image_url?: string
}
export interface DashboardData {
  sloth_run?: { summary: string; timestamp: string }
  listings: Listing[]
  matches: unknown[]
  wishlist: unknown[]
  events: unknown[]
  lazy_payoff?: { measured_median_s: number; listing_count: number }
}
