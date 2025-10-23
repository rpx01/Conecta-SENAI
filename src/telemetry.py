import os

try:  # pragma: no cover - dependência opcional
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    _TELEMETRY_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - fallback
    trace = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    OTLPSpanExporter = None
    FlaskInstrumentor = None
    _TELEMETRY_AVAILABLE = False


def instrument(app):
    if not _TELEMETRY_AVAILABLE:  # pragma: no cover - sem dependências
        return

    FlaskInstrumentor().instrument_app(app)
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
    attrs_str = os.getenv('OTEL_RESOURCE_ATTRIBUTES')
    attributes = {}
    if attrs_str:
        for item in attrs_str.split(','):
            if '=' in item:
                k, v = item.split('=', 1)
                attributes[k.strip()] = v.strip()
    resource = Resource.create(attributes)
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
