import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor


def instrument(app):
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
