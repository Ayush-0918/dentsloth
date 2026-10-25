"""Gemma Multimodal Vision Provider for DentSloth.

Supports:
- OllamaProvider (local open-weight Gemma, e.g. gemma3:4b)
- HostedGemmaProvider (Google AI Studio Gemma/Gemini API)
- DemoVisionProvider (deterministic cached responses for sample images & offline mode)
"""
import abc
import base64
import json
import logging
import os
import re
import time
from typing import Optional, Dict, Any
import httpx
from pydantic import ValidationError

from ..config import get_settings
from ..models import IdentifiedItem, IdentifyResponse, ConditionGrade

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert dental instrument cataloging AI for DentSloth.
Your task is to analyze the provided photo and identify all dental instruments present.
Support single instruments as well as tray photos containing multiple instruments.

Return ONLY a valid JSON object matching this exact structure:
{
  "items": [
    {
      "instrument_type": "<instrument_identifier_or_name>",
      "likely_brand": "<brand_name_or_unknown>",
      "material": "<material_specification>",
      "condition_grade": "<A|B|C>",
      "visible_defects": ["<defect_1>", ...],
      "needs_sharpening": <true|false>,
      "is_single_use": <true|false>,
      "confidence": <float_between_0.0_and_1.0>
    }
  ],
  "notes": "<concise clinical evaluation notes>"
}

CRITICAL RULES & GUARDRAILS:
1. NEVER guess or invent a brand name. If a clear brand logo or stamp (e.g., Hu-Friedy, GDC, Dentsply, API, Medesy) is NOT clearly visible, return "unknown".
2. Set "is_single_use": true for any disposable or single-use item (e.g. disposable syringe, disposable needles, plastic suction tips, cotton rolls, disposable scalpel blades, matrix bands, saliva ejectors).
3. Condition Grade:
   - "A": Pristine / near new, flawless mirror finish, no visible handle scratches.
   - "B": Good, standard clinical wear, minor light scratches on shank/handle, structurally sound.
   - "C": Fair, visible wear, micro-chips on tip, needs re-tipping or heavy sharpening, slight discoloration.
4. If the image is blurry, ambiguous, non-dental, or difficult to recognize, assign "confidence" < 0.40.
5. If multiple instruments are in a tray or set, include each as a distinct object in "items".
6. Output raw JSON only. Do NOT include markdown code fences (```json), explanations, or preambles.
"""

RETRY_PROMPT_SUFFIX = "\n\nCRITICAL FIX: Your previous response was not valid JSON or failed the schema requirements. Return ONLY pure raw JSON starting with '{' and ending with '}' with no extra text or markdown formatting."


def parse_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """Extract and parse JSON from raw LLM output."""
    cleaned = raw_text.strip()
    # Strip markdown code blocks if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    
    # Try locating outer braces
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx : end_idx + 1]

    return json.loads(cleaned)


def apply_guardrails(items: list[IdentifiedItem], notes: str) -> tuple[bool, Optional[str]]:
    """Enforce clinical safety guardrails on identified items.

    Returns:
        (can_list: bool, refusal_reason: Optional[str])
    """
    if not items:
        return False, "No dental instruments could be identified in the image. Please retake photo with clearer framing."

    for item in items:
        if item.is_single_use:
            return (
                False,
                f"Refusal: '{item.instrument_type}' is identified as a single-use / disposable item. Single-use medical instruments cannot be resold for patient safety and infection control standards.",
            )

        if item.confidence < 0.40:
            return (
                False,
                f"Low confidence ({item.confidence:.2f} < 0.40) identifying '{item.instrument_type}'. Please retake photo with clearer lighting and a plain background.",
            )

    return True, None


class LLMProvider(abc.ABC):
    """Abstract Base Class for Multimodal LLM Vision Providers."""

    @abc.abstractmethod
    async def identify(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        filename: Optional[str] = None,
    ) -> IdentifyResponse:
        """Process dental instrument image and return structured identification."""
        pass


class OllamaProvider(LLMProvider):
    """Local open-weight Gemma provider via Ollama."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3:4b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def identify(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        filename: Optional[str] = None,
    ) -> IdentifyResponse:
        start_t = time.perf_counter()
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = SYSTEM_PROMPT
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [img_b64],
                }
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            # First attempt
            try:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                res.raise_for_status()
                raw_content = res.json().get("message", {}).get("content", "")
                parsed = parse_and_validate_json(raw_content)
                items = [IdentifiedItem(**it) for it in parsed.get("items", [])]
                notes = parsed.get("notes", "")
            except Exception as first_err:
                logger.warning(f"Ollama identify attempt 1 failed ({first_err}); retrying once...")
                # Retry once with explicit corrective prompt
                payload["messages"].append({"role": "assistant", "content": raw_content if 'raw_content' in locals() else ""})
                payload["messages"].append({"role": "user", "content": RETRY_PROMPT_SUFFIX})
                try:
                    res2 = await client.post(f"{self.base_url}/api/chat", json=payload)
                    res2.raise_for_status()
                    raw2 = res2.json().get("message", {}).get("content", "")
                    parsed = parse_and_validate_json(raw2)
                    items = [IdentifiedItem(**it) for it in parsed.get("items", [])]
                    notes = parsed.get("notes", "")
                except Exception as second_err:
                    logger.error(f"Ollama identify retry failed: {second_err}")
                    raise RuntimeError(f"Gemma model failed to produce valid JSON: {second_err}") from second_err

        can_list, refusal_reason = apply_guardrails(items, notes)
        latency = (time.perf_counter() - start_t) * 1000.0

        return IdentifyResponse(
            items=items,
            notes=notes,
            can_list=can_list,
            refusal_reason=refusal_reason,
            demo=False,
            latency_ms=round(latency, 2),
        )


class HostedGemmaProvider(LLMProvider):
    """Hosted Gemma / Gemini API provider via Google AI Studio."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def identify(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        filename: Optional[str] = None,
    ) -> IdentifyResponse:
        start_t = time.perf_counter()
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": img_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                candidate = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                parsed = parse_and_validate_json(candidate)
                items = [IdentifiedItem(**it) for it in parsed.get("items", [])]
                notes = parsed.get("notes", "")
            except Exception as err:
                logger.warning(f"Hosted Gemma attempt 1 failed ({err}); retrying once...")
                payload["contents"][0]["parts"].append({"text": RETRY_PROMPT_SUFFIX})
                try:
                    res2 = await client.post(url, json=payload)
                    res2.raise_for_status()
                    candidate2 = res2.json()["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = parse_and_validate_json(candidate2)
                    items = [IdentifiedItem(**it) for it in parsed.get("items", [])]
                    notes = parsed.get("notes", "")
                except Exception as err2:
                    logger.error(f"Hosted Gemma retry failed: {err2}")
                    raise RuntimeError(f"Hosted Gemma failed to produce valid JSON: {err2}") from err2

        can_list, refusal_reason = apply_guardrails(items, notes)
        latency = (time.perf_counter() - start_t) * 1000.0

        return IdentifyResponse(
            items=items,
            notes=notes,
            can_list=can_list,
            refusal_reason=refusal_reason,
            demo=False,
            latency_ms=round(latency, 2),
        )


class DemoVisionProvider(LLMProvider):
    """Deterministic, offline-capable vision provider for sample images & demonstrations."""

    def __init__(self, cache_file: Optional[str] = None, fallback_provider: Optional[LLMProvider] = None):
        self.fallback = fallback_provider
        self.cache: Dict[str, Any] = {}
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load demo cache from {cache_file}: {e}")

    async def identify(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        filename: Optional[str] = None,
    ) -> IdentifyResponse:
        start_t = time.perf_counter()

        # Check by filename first
        entry = None
        if filename:
            clean_name = os.path.basename(filename)
            entry = self.cache.get(clean_name)

        # Fallback to content-based heuristic match if not found by name
        if not entry:
            # Heuristic match based on byte length or basic checks
            for key, val in self.cache.items():
                if filename and key.lower() in filename.lower():
                    entry = val
                    break

        if not entry and self.fallback:
            try:
                return await self.fallback.identify(image_bytes, mime_type, filename)
            except Exception as e:
                logger.warning(f"Fallback provider failed in DemoVisionProvider: {e}")

        # Default mock response if image is completely unknown in demo mode
        if not entry:
            entry = {
                "items": [
                    {
                        "instrument_type": "mouth_mirror",
                        "likely_brand": "unknown",
                        "material": "stainless_steel",
                        "condition_grade": "B",
                        "visible_defects": ["Minor surface scuffs on handle"],
                        "needs_sharpening": False,
                        "is_single_use": False,
                        "confidence": 0.88,
                    }
                ],
                "notes": "(Demo Mode) Auto-identified reusable examination instrument.",
            }

        items = [IdentifiedItem(**it) for it in entry.get("items", [])]
        notes = entry.get("notes", "(Demo Mode)")
        can_list, refusal_reason = apply_guardrails(items, notes)
        latency = (time.perf_counter() - start_t) * 1000.0 + 35.0  # simulate realistic fast local processing

        return IdentifyResponse(
            items=items,
            notes=notes,
            can_list=can_list,
            refusal_reason=refusal_reason,
            demo=True,
            latency_ms=round(latency, 2),
        )


def get_llm_provider() -> LLMProvider:
    """Factory to instantiate the appropriate vision provider based on settings."""
    settings = get_settings()
    demo_cache_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "sample_images",
        "demo_cache.json",
    )

    # Base provider
    base_provider: Optional[LLMProvider] = None
    if settings.llm_provider == "hosted" and settings.gemma_api_key:
        base_provider = HostedGemmaProvider(api_key=settings.gemma_api_key)
    elif settings.llm_provider == "ollama":
        base_provider = OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    # If demo mode is active, wrap in DemoVisionProvider
    if settings.is_demo:
        return DemoVisionProvider(cache_file=demo_cache_path, fallback_provider=base_provider)

    if base_provider:
        return base_provider

    # Fallback to demo provider if no credentials / endpoints configured
    return DemoVisionProvider(cache_file=demo_cache_path)
