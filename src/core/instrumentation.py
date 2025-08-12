"""OpenTelemetry instrumentation for fraud intelligence system."""

from typing import Optional
from .config import InstrumentationConfig
from openinference.instrumentation.dspy import DSPyInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from openinference.semconv.resource import ResourceAttributes
from opentelemetry.sdk.resources import Resource


def configure_dspy_instrumentation(
    phoenix_endpoint: Optional[str] = None, project_name: str = "fraud-intel"
) -> None:
    """
    Configure OpenTelemetry instrumentation for DSPy fraud analysis.

    Args:
        phoenix_endpoint: Phoenix/OTLP endpoint URL (e.g., "http://localhost:6006/v1/traces")
        project_name: Project name for trace attribution
    """
    # Create tracer provider
    resource = Resource(attributes={ResourceAttributes.PROJECT_NAME: project_name})
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Configure OTLP exporter if endpoint provided
    if phoenix_endpoint:
        print(f"▸ Configuring instrumentation to send traces to: {phoenix_endpoint}")

        # Add OTLP span processor
        otlp_exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
    else:
        print("▸ Instrumentation configured for local collection only")

    # Instrument DSPy - this automatically creates spans for DSPy operations
    DSPyInstrumentor().instrument(tracer_provider=tracer_provider, skip_dep_check=True)
    print("✓ DSPy instrumentation enabled")

    # Instrument LiteLLM for LLM call tracking
    LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider, skip_dep_check=True)
    print("✓ LiteLLM instrumentation enabled")


def setup_instrumentation_from_env() -> bool:
    """
    Setup instrumentation using centralized configuration.

    Returns:
        True if instrumentation is enabled, False otherwise
    """
    config = InstrumentationConfig.from_env()

    if not config.enabled:
        return False

    configure_dspy_instrumentation(config.phoenix_endpoint, config.project_name)
    return True
