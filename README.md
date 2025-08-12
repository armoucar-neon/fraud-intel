# Fraud Intel - DSPy-Powered Fraud Analysis System

A demonstration of using DSPy to build AI-powered fraud analysis capabilities for fintech applications.

## Overview

This project implements three core fraud analysis modules using DSPy:

1. **Hypothesis Generator** - Generates plausible fraud type hypotheses based on case data
2. **Contradiction & Missing-Info Checker** - Identifies data inconsistencies and missing information
3. **Narrative Drafter** - Creates concise, evidence-based case summaries

## Installation

```bash
# Install dependencies
uv sync

# Copy and configure environment variables
cp .env.sample .env
# Edit .env and add your OpenAI API key
```

## Usage

Ensure your OpenAI API key is set in `.env` before running.

Each module can be run independently with `uv run` and supports two modes:

- **demo**: Run on a single example with detailed output
- **eval**: Run full evaluation on all datasets

### Run Demo Mode (default)

```bash
# Hypothesis Generator
uv run python -m src.modules.hypothesis_generator --mode demo

# Contradiction Checker
uv run python -m src.modules.contradiction_checker --mode demo

# Narrative Drafter
uv run python -m src.modules.narrative_drafter --mode demo
```

### Run Evaluation Mode

```bash
# Hypothesis Generator
uv run python -m src.modules.hypothesis_generator --mode eval

# Contradiction Checker
uv run python -m src.modules.contradiction_checker --mode eval

# Narrative Drafter
uv run python -m src.modules.narrative_drafter --mode eval
```

### Additional Options

```bash
# Get help
uv run python -m src.modules.hypothesis_generator --help
```

## Case Studies

### Case A - Account Takeover

- Password reset followed by foreign login
- Rapid transfer to known money mule
- Impossible geovelocity detected

### Case B - Synthetic Identity

- Tampered documents with low biometric scores
- Device linked to multiple failed applications
- Minimal digital footprint

### Case C - Legitimate Travel

- Pre-declared travel matching transaction locations
- Consistent device usage
- Strong authentication success

## Evaluation Metrics

All modules use **LLM-as-a-Judge** evaluation with DSPy ChainOfThought for semantic assessment:

- **Hypothesis Generator**: Hypothesis quality (0.6) + Evidence quality (0.4)
- **Contradiction Checker**: Contradiction accuracy (0.5) + Missing info completeness (0.5)
- **Narrative Drafter**: Narrative quality (0.5) + Headline accuracy (0.3) + Conciseness (0.2)

## Development

### Code Formatting and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting:

```bash
# Check code style and run linter
uv run ruff check

# Format code
uv run ruff format

# Check and fix auto-fixable issues
uv run ruff check --fix
```

## Instrumentation & Observability

This project includes OpenTelemetry instrumentation for monitoring DSPy workflows and LLM calls.

### Setup Phoenix (Optional)

[Phoenix](https://docs.arize.com/phoenix) provides an observability platform for LLM applications. This project includes a Docker Compose setup with Phoenix and PostgreSQL:

```bash
# Start Phoenix and PostgreSQL
docker-compose up -d

# Phoenix UI will be available at http://localhost:6006
# OTLP endpoint will be available at http://localhost:6007
```

### Enable Instrumentation

Configure instrumentation in your `.env` file:

```bash
# Enable instrumentation with Phoenix
ENABLE_INSTRUMENTATION=true
PHOENIX_ENDPOINT=http://localhost:6007
PROJECT_NAME=fraud-intel

# Run modules with instrumentation
uv run python -m src.modules.hypothesis_generator --mode demo
```

### Environment Variables

- `ENABLE_INSTRUMENTATION`: Set to `true` to enable tracing
- `PHOENIX_ENDPOINT`: Phoenix/OTLP endpoint (default: `http://localhost:6007`)
- `PROJECT_NAME`: Project name for trace attribution (default: "fraud-intel")
- `DSPY_CACHE`: Enable/disable DSPy caching (default: true)
- `OPENAI_API_KEY`: Your OpenAI API key
