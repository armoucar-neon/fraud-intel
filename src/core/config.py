"""Configuration management for fraud intelligence system."""

import os
from dataclasses import dataclass
from typing import Optional
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv(override=True)


@dataclass
class InstrumentationConfig:
    """Configuration for OpenTelemetry instrumentation."""

    enabled: bool = False
    phoenix_endpoint: Optional[str] = None
    project_name: str = "fraud-intel"

    @classmethod
    def from_env(cls) -> "InstrumentationConfig":
        """Create configuration from environment variables."""
        return cls(
            enabled=os.getenv("ENABLE_INSTRUMENTATION", "false").lower() == "true",
            phoenix_endpoint=os.getenv("PHOENIX_ENDPOINT"),
            project_name=os.getenv("PROJECT_NAME", "fraud-intel"),
        )


@dataclass
class ModelConfig:
    """Configuration for DSPy language model."""

    model_name: str = "openai/gpt-5"
    temperature: float = 1.0
    cache: bool = True

    @classmethod
    def from_args(cls, model: str, temperature: float, cache: Optional[bool] = None) -> "ModelConfig":
        """Create configuration from command line arguments."""

        # Handle special case for GPT-5 temperature
        if "gpt-5" in model.lower() and temperature != 1.0:
            print(f"⚠ Note: {model} only supports temperature=1.0, adjusting from {temperature}")
            temperature = 1.0

        # Use cache from env var if not explicitly provided
        if cache is None:
            cache = os.getenv("DSPY_CACHE", "true").lower() == "true"

        return cls(model_name=model, temperature=temperature, cache=cache)


@dataclass
class AppConfig:
    """Main application configuration."""

    instrumentation: InstrumentationConfig
    model: ModelConfig

    @classmethod
    def create(
        cls,
        model_name: str = "openai/gpt-5",
        temperature: float = 1.0,
        cache: Optional[bool] = None,
    ) -> "AppConfig":
        """Create application configuration."""
        return cls(
            instrumentation=InstrumentationConfig.from_env(),
            model=ModelConfig.from_args(model_name, temperature, cache),
        )
