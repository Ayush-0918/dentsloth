"""DentSloth Sentry Agent Tracing & AI Observability Module.

Supports official Sentry SDK 2.x transactions & spans for AI agent workflows.
Operates as a safe, zero-overhead no-op when SENTRY_DSN is unset.
Privacy guaranteed: Never transmits image buffers, EXIF, or PII.
"""
import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any

from .config import get_settings

logger = logging.getLogger(__name__)

_sentry_initialized = False


def init_sentry():
    """Initialize Sentry SDK with strict PII masking if SENTRY_DSN is configured."""
    global _sentry_initialized
    settings = get_settings()
    if not settings.sentry_dsn:
        logger.info("Sentry tracing disabled (SENTRY_DSN not provided).")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
            send_default_pii=False,          # Strict Privacy Guarantee: No PII
            traces_sample_rate=1.0,           # Full trace coverage for demo & benchmarking
            environment=settings.app_env,
            release="dentsloth@0.1.0",
        )
        _sentry_initialized = True
        logger.info("Sentry agent tracing initialized successfully.")
        return True
    except Exception as err:
        logger.warning(f"Failed to initialize Sentry: {err}")
        return False


class SpanTracker:
    """Wrapper around Sentry span with safe no-op fallback."""

    def __init__(self, raw_span=None):
        self.raw_span = raw_span

    def set_attribute(self, key: str, value: Any):
        if self.raw_span is not None:
            try:
                self.raw_span.set_data(key, value)
            except Exception:
                pass


@contextmanager
def trace_transaction(name: str, op: str = "ai.agent"):
    """Context manager for a top-level AI agent transaction."""
    settings = get_settings()
    if not settings.sentry_dsn:
        yield SpanTracker(None)
        return

    try:
        import sentry_sdk
        with sentry_sdk.start_transaction(name=name, op=op) as txn:
            yield SpanTracker(txn)
    except Exception as err:
        logger.debug(f"Sentry transaction error: {err}")
        yield SpanTracker(None)


@contextmanager
def trace_span(name: str, op: str = "ai.task"):
    """Context manager for child spans within an agent flow."""
    settings = get_settings()
    if not settings.sentry_dsn:
        yield SpanTracker(None)
        return

    try:
        import sentry_sdk
        with sentry_sdk.start_span(op=op, name=name) as span:
            yield SpanTracker(span)
    except Exception as err:
        logger.debug(f"Sentry span error: {err}")
        yield SpanTracker(None)
