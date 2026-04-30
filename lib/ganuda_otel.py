"""Ganuda OpenTelemetry helper — emit traces + metrics from federation Python services.

Non-blocking, graceful-degrading. If the collector is unreachable, calls no-op
silently (never raises). Aligned with openclaw semantic conventions but using
our `ganuda.*` namespace prefix.

Use:
    from lib.ganuda_otel import get_tracer, get_meter, redact_sensitive, sacred_attrs_safe
    tracer = get_tracer()
    meter = get_meter()
    counter = meter.create_counter("ganuda.council.specialist.vote")

    with tracer.start_as_current_span("ganuda.council.vote") as span:
        span.set_attribute("question", redact_sensitive(question)[:500])
        ...
        counter.add(1, attributes={"specialist_id": sid, "vote_value": vote})

Council amendments (813dbb85866e45e2 + 84beb73ee61cf993):
- Crawdad: redact_sensitive() applies credential patterns at emit time; sacred_attrs_safe()
  drops sacred_pattern markers before span/metric export
- Eagle Eye: BatchSpanProcessor + async metric reader; OTel NEVER blocks caller;
  collector-down → spans drop silently
- Gecko: cgroup isolation enforced collector-side (MemoryMax=2G, CPUQuota=25%)
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict

logger = logging.getLogger("ganuda.otel")

_OTLP_ENDPOINT = os.environ.get("GANUDA_OTEL_ENDPOINT", "http://localhost:4318")
_SERVICE_NAME = os.environ.get("GANUDA_OTEL_SERVICE_NAME", "ganuda-federation")
try:
    _INSTANCE = os.uname().nodename
except Exception:
    _INSTANCE = "unknown"
_INSTANCE = os.environ.get("GANUDA_OTEL_INSTANCE", _INSTANCE)

# ---------------------------------------------------------------------------
# Redaction (Crawdad amendment, emit-time)
# ---------------------------------------------------------------------------

_CRED_PATTERNS = [
    re.compile(r'(password|token|api[_-]?key|secret)=\S+', re.I),
    re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}'),
    re.compile(r'ghp_[A-Za-z0-9]{36}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'sk-[A-Za-z0-9-]{20,}'),
    re.compile(r'-----BEGIN .*(PRIVATE KEY|CERTIFICATE)'),
]


def redact_sensitive(text: str) -> str:
    """Replace known credential patterns with <REDACTED>. Safe for span attributes."""
    if not isinstance(text, str):
        return text
    for p in _CRED_PATTERNS:
        text = p.sub('<REDACTED>', text)
    return text


_SACRED_KEYS = ("sacred_pattern", "ganuda.memory.sacred_pattern")


def is_sacred(attrs: Dict[str, Any]) -> bool:
    if not attrs:
        return False
    for k in _SACRED_KEYS:
        v = attrs.get(k)
        if v in (True, "true", "True", "TRUE"):
            return True
    return False


def sacred_attrs_safe(attrs: Dict[str, Any]) -> Dict[str, Any]:
    """Return attrs copy with sacred-pattern markers removed + credential-strings redacted.

    Defense-in-depth: a span bearing sacred-pattern=true should not be exported.
    Callers should use is_sacred() to skip span creation entirely when possible.
    This helper handles the case where a span is already opened.
    """
    if not attrs:
        return {}
    clean = {}
    for k, v in attrs.items():
        if k in _SACRED_KEYS:
            continue
        clean[k] = redact_sensitive(v) if isinstance(v, str) else v
    return clean


# ---------------------------------------------------------------------------
# OTel bootstrap (graceful degradation)
# ---------------------------------------------------------------------------

_tracer = None
_meter = None
_initialized = False


def _init() -> None:
    global _tracer, _meter, _initialized
    if _initialized:
        return
    _initialized = True

    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

        resource = Resource.create({
            "service.name": _SERVICE_NAME,
            "service.namespace": "ganuda",
            "service.instance.id": _INSTANCE,
            "deployment.environment": "ganuda-federation",
        })

        trace_exporter = OTLPSpanExporter(endpoint=f"{_OTLP_ENDPOINT}/v1/traces")
        span_processor = BatchSpanProcessor(
            trace_exporter,
            max_queue_size=2048,
            schedule_delay_millis=5000,
            export_timeout_millis=3000,
            max_export_batch_size=512,
        )
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(span_processor)
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("ganuda")

        metric_exporter = OTLPMetricExporter(endpoint=f"{_OTLP_ENDPOINT}/v1/metrics")
        reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=10000,
            export_timeout_millis=3000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter("ganuda")

        logger.info("ganuda_otel initialized endpoint=%s service=%s", _OTLP_ENDPOINT, _SERVICE_NAME)
    except Exception as e:
        logger.warning("ganuda_otel init failed (using no-op): %s", e)
        _tracer = _NoopTracer()
        _meter = _NoopMeter()


# ---------------------------------------------------------------------------
# No-op fallbacks (used when collector unreachable or SDK missing)
# ---------------------------------------------------------------------------

class _NoopSpan:
    def set_attribute(self, *a, **kw): pass
    def set_attributes(self, *a, **kw): pass
    def set_status(self, *a, **kw): pass
    def record_exception(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False


class _NoopTracer:
    def start_as_current_span(self, *a, **kw): return _NoopSpan()
    def start_span(self, *a, **kw): return _NoopSpan()


class _NoopCounter:
    def add(self, *a, **kw): pass


class _NoopHistogram:
    def record(self, *a, **kw): pass


class _NoopMeter:
    def create_counter(self, *a, **kw): return _NoopCounter()
    def create_histogram(self, *a, **kw): return _NoopHistogram()
    def create_up_down_counter(self, *a, **kw): return _NoopCounter()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_tracer():
    if not _initialized:
        _init()
    return _tracer


def get_meter():
    if not _initialized:
        _init()
    return _meter
