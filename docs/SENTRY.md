# DentSloth — Sentry Agent Tracing & AI Observability

> **AI Agent Tracing Guide for Hacktoberfest 2026**  
> DentSloth uses the official `sentry-sdk` (v2.x) to record distributed transactions and granular child spans across every stage of the "lazy seller" loop and overnight buyer-matching agent.

---

## 1. Architecture & Privacy Guarantees

* **Zero PII Exposure (`send_default_pii=False`):** No camera images, EXIF metadata, patient records, or unscrubbed textual identifiers are ever sent to Sentry. Only sanitized operational tags and metric attributes are attached.
* **Safe Fallback:** If `SENTRY_DSN` is empty or unset, all tracing wrappers operate as zero-overhead no-ops without error.
* **Sampling Rate:** `traces_sample_rate=1.0` during hackathon benchmarking to record every interaction end-to-end.

---

## 2. Spans & Transaction Hierarchy

### Transaction 1: `lazy_listing` (`op="ai.agent"`)
Triggered automatically on every listing creation via `POST /api/listings/auto` or `/api/debug/trace-test`.

| Span Name | Operation (`op`) | Description & Captured Attributes |
|---|---|---|
| `image_sanitize` | `ai.sanitize` | EXIF/GPS stripping, byte validation, aspect ratio verification (`exif_stripped: true`, `latency_ms`). |
| `gemma_identify` | `ai.inference` | Gemma 3 4B vision model inference (`provider`, `model_name`, `confidence`, `can_list`, `token_counts`, `cost: "0 for local; hosted per Google AI Studio free tier/quota"`). |
| `tabpfn_price` | `ai.pricing` | TabPFN Tabular Transformer regression (`mode`, `instrument_type`, `condition_grade`, `suggested_price_inr`, `price_range`, `sanity_applied`). |
| `gemma_listing_text` | `ai.synthesis` | Bilingual listing generation in Hindi & English (`languages: ["en", "hi"]`, `instrument`). |
| `db_write` | `db.insert` | Database persistence to MongoDB Atlas or SQLite fallback (`storage_backend`, `collection: "listings"`). |

### Transaction 2: `overnight_sloth_run` (`op="ai.agent"`)
Triggered when `scripts/sloth_run.py` runs (nightly cron or on-demand). Traces wishlist retrieval, vector similarity matching, and match notifications.

---

## 3. How to Generate Real Traces & Screenshots

1. **Enable Tracing in `.env` or Render Dashboard:**
   ```bash
   SENTRY_DSN="https://your_public_key@oXXXXXX.ingest.sentry.io/XXXXXX"
   ENABLE_DEBUG="true"
   ```
2. **Trigger a Sample Agent Trace:**
   ```bash
   curl http://localhost:8000/api/debug/trace-test
   # or on deployed service:
   curl https://dentsloth-api.onrender.com/api/debug/trace-test
   ```
3. **Trigger a Real Photo Listing:**
   Upload any dental instrument photo via the Snap & List flow in the web interface or CLI.

---

## 4. Screenshot Checklist for Hackathon Judges

* [ ] **Trace Waterfall View:** Sentry Performance -> Transactions -> click `lazy_listing`. Shows the hierarchical waterfall containing `image_sanitize` -> `gemma_identify` -> `tabpfn_price` -> `gemma_listing_text` -> `db_write`.
* [ ] **Step Latencies & Span Details:** Click into `gemma_identify` or `tabpfn_price` span to show attributes (`confidence`, `model_name`, `provider`, `suggested_price_inr`).
* [ ] **Edge-Case / Error Trace:** Photographing a single-use needle or low-confidence blur triggers clinical safety refusal, captured as a refusal span (`can_list: false`, `refusal_reason`).
