export const API_BASE = import.meta.env.VITE_API_URL || '/api'

export class ApiError extends Error {
  status: number
  isRefusal: boolean
  code?: string

  constructor(status: number, message: string, isRefusal = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.isRefusal = isRefusal
  }
}

async function req<T>(method: string, path: string, body?: unknown, isForm = false, timeoutMs = 45000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  const opts: RequestInit = { method, signal: controller.signal }
  if (body) {
    if (isForm) {
      opts.body = body as FormData
    } else {
      opts.headers = { 'Content-Type': 'application/json' }
      opts.body = JSON.stringify(body)
    }
  }

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, opts)
  } catch (err: any) {
    clearTimeout(timer)
    if (err.name === 'AbortError') {
      throw new ApiError(408, 'Request timed out after 45s. Free server may be waking up—please try again.')
    }
    throw new ApiError(0, 'Network connection failed. The free cloud server may be waking up (sleeping while idle).')
  } finally {
    clearTimeout(timer)
  }

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = errData.detail || `HTTP ${res.status}`

    if (res.status === 413) {
      throw new ApiError(413, 'Photo exceeds 10MB upload limit. Please upload a compressed or smaller image.')
    }
    if (res.status === 415) {
      throw new ApiError(415, 'Unsupported file format. Please upload JPEG, PNG, or WebP.')
    }
    if (res.status === 422 || res.status === 400) {
      const lower = detail.toLowerCase()
      const isRefusal = lower.includes('refusal') || lower.includes('single-use') || lower.includes('confidence') || lower.includes('cannot be approved')
      throw new ApiError(res.status, detail, isRefusal)
    }
    if (res.status === 429) {
      throw new ApiError(429, 'Rate limit reached. Please wait a few seconds before retrying.')
    }
    if (res.status === 503) {
      throw new ApiError(503, 'AI model service is currently unavailable. Please try again.')
    }
    throw new ApiError(res.status, detail)
  }
  return res.json()
}

export interface HealthResponse {
  status: string
  demo_mode: boolean
  storage_backend?: string
  matching_mode?: string
  db: string
  llm_provider: string
}

export const api = {
  health: () => req<HealthResponse>('GET', '/health', undefined, false, 8000),
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

// ── Types ────────────────────────────────────────────────────────────────────
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
export interface PriceResponse { suggested_price_inr: number; price_low: number; price_high: number; explanation: string; original_price_inr?: number }
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
