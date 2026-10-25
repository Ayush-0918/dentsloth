import type { IdentifyResponse, KitResult, DashboardData } from './index'

export const DEMO_IDENTIFY: IdentifyResponse = {
  demo: true,
  items: [
    {
      instrument_type: 'gracey_curette',
      likely_brand: 'Hu-Friedy',
      material: 'Stainless steel',
      condition_grade: 'B',
      visible_defects: ['Minor handle wear'],
      needs_sharpening: false,
      is_single_use: false,
      confidence: 0.91,
      price: { suggested_price_inr: 650, price_low: 580, price_high: 750, explanation: 'Condition B, 2 yrs, premium brand – based on 31 synthetic comparable sales.' },
      description_en: 'Hu-Friedy Gracey 13/14 curette in good condition. Tip intact, minor handle wear. Sold individually.',
      description_hi: 'Hu-Friedy Gracey 13/14 क्यूरेट अच्छी स्थिति में। टिप सही, हैंडल पर हल्की घिसाव। अकेले बेचा जा रहा है।',
      price_explanation: 'Condition B, ~2 yrs, premium brand. Based on 31 synthetic comparable sales. Capped at 85% of new price.',
    }
  ],
  notes: '(Demo Mode) Pre-recorded response for sample image.',
}

export const DEMO_KIT: KitResult = {
  selected_listings: [
    { listing_id: 'demo-1', instrument_type: 'Mouth Mirror', price: 280, condition_grade: 'B', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune' },
    { listing_id: 'demo-2', instrument_type: 'Dental Probe', price: 220, condition_grade: 'A', clinic_name: 'Lakeview Polyclinic (Demo)', city: 'Mumbai' },
    { listing_id: 'demo-3', instrument_type: 'Sickle Scaler', price: 400, condition_grade: 'B', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune' },
    { listing_id: 'demo-4', instrument_type: 'Gracey Curette', price: 650, condition_grade: 'B', clinic_name: 'Lakeview Polyclinic (Demo)', city: 'Mumbai' },
    { listing_id: 'demo-5', instrument_type: 'Upper Anterior Forceps', price: 400, condition_grade: 'B', clinic_name: 'Sunrise Dental Care (Demo)', city: 'Pune' },
    { listing_id: 'demo-6', instrument_type: 'Straight Elevator', price: 350, condition_grade: 'B', clinic_name: 'Metro Implant Centre (Demo)', city: 'Delhi' },
  ],
  total_price: 2300,
  total_new_price_est: 6200,
  gaps: ['Lower molar forceps', 'College tweezers'],
}

export const DEMO_DASHBOARD: DashboardData = {
  sloth_run: {
    summary: '3 new listings matched with 2 wishlists overnight. Best match: Gracey curette (Pune → Mumbai buyer, 94% similarity). No budgets exceeded.',
    timestamp: new Date(Date.now() - 7 * 3600000).toISOString(),
  },
  listings: [
    { instrument_type: 'Sickle Scaler', brand: 'Hu-Friedy', condition_grade: 'B', age_years: 3, suggested_price_inr: 400, price_low: 350, price_high: 480, description_en: '', description_hi: '', clinic_name: 'My Clinic', city: 'Pune', status: 'published', price_explanation: '' },
  ],
  matches: [
    { buyer: 'Dr. Priya S.', instrument: 'Gracey Curette', score: 0.94 },
  ],
  wishlist: [{ wanted: 'Basic exam set', budget: 5000 }],
  events: [
    { type: 'match', message: 'Gracey Curette matched with Dr. Priya S. (94% similarity)', ts: new Date(Date.now() - 7*3600000).toISOString() },
    { type: 'notification', message: 'Morning summary sent to 1 buyer', ts: new Date(Date.now() - 6*3600000).toISOString() },
  ],
  lazy_payoff: { measured_median_s: 38, listing_count: 1 },
}
