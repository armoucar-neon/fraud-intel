# AGENTS.md

This file provides guidance to Code Agents when working with code in this repository.

## Development Commands

### Linting and Formatting

```bash
# Check code style and run linter
uv run ruff check

# Format code
uv run ruff format

# Check and fix auto-fixable issues
uv run ruff check --fix
```

### Running Modules

Each DSPy module is standalone and executable with `uv run`:

```bash
# Demo mode (default) - runs single example with detailed output
uv run python -m src.modules.hypothesis_generator --mode demo
uv run python -m src.modules.contradiction_checker --mode demo
uv run python -m src.modules.narrative_drafter --mode demo

# Evaluation mode - runs full evaluation on all datasets
uv run python -m src.modules.hypothesis_generator --mode eval
uv run python -m src.modules.contradiction_checker --mode eval
uv run python -m src.modules.narrative_drafter --mode eval

# Custom model
uv run python -m src.modules.hypothesis_generator --model openai/gpt-4
```

### Docker Services

```bash
# Start PostgreSQL and Phoenix for observability
docker-compose up postgres phoenix

# Phoenix UI available at http://localhost:6006
# PostgreSQL available at localhost:5432
```

### Environment Setup

```bash
# Required
export OPENAI_API_KEY='your-key-here'

# Optional instrumentation
export ENABLE_INSTRUMENTATION=true
export PHOENIX_ENDPOINT=http://localhost:6007
export PROJECT_NAME=fraud-intel
export DSPY_CACHE=true  # Enable/disable DSPy response caching (default: true)
```

## Code Style Guidelines

### Logging Conventions

Use ASCII/Unicode symbols instead of emojis for status indicators:

- Success: `✓` or `◎` (not ✅)
- Error: `✗` or `▪` (not ❌)
- Warning: `▸` or `⚠` (not ⚠️)
- Info: `-` or `▹` (not ℹ️)
- Progress: `▸` (not 🔄)
- Time/Date: `⏱` (not 📅)

## Architecture Overview

### DSPy Implementation Pattern

This codebase follows DSPy best practices with three fraud analysis modules:

1. **Signature Definition**: Each module defines structured input/output with `dspy.Signature`
2. **Module Implementation**: Uses `dspy.ChainOfThought` for enhanced reasoning
3. **Dataset Format**: All data converted to `dspy.Example` objects with proper input marking
4. **Evaluation**: Uses `dspy.evaluate.Evaluate` with custom metrics supporting both evaluation mode (float scores) and compilation mode (bool)

### Core Components

**src/core/config.py**: Centralized configuration management

- `ModelConfig`: LLM settings with environment variable support
- `InstrumentationConfig`: OpenTelemetry configuration
- `AppConfig`: Main app configuration factory

**src/core/data_loader.py**: Dataset loading and `dspy.Example` conversion

- Loads JSON case data from `datasets/cases/`
- Loads ground truth labels from `datasets/labels/`
- Creates proper `dspy.Example` objects with `.with_inputs()` marking

**src/core/instrumentation.py**: OpenTelemetry setup

- Auto-instruments DSPy operations (no custom spans needed)
- Supports Phoenix and generic OTLP endpoints
- Environment-driven configuration

### Fraud Analysis Modules

Each module in `src/modules/` (`hypothesis_generator.py`, `contradiction_checker.py`, `narrative_drafter.py`) follows identical structure:

- DSPy Signature with typed input/output fields
- ChainOfThought module implementation
- Custom evaluation metrics
- Standalone CLI with argparse (demo/eval modes)
- Auto-instrumentation integration

### Dataset Structure

```text
datasets/
├── cases/           # Input data (JSON files per case)
│   ├── case_a/     # Account Takeover
│   ├── case_b/     # Synthetic Identity
│   └── case_c/     # Legitimate Travel
├── labels/         # Ground truth labels (JSON)
└── analyst_notes/  # Optional analyst inputs (TXT)
```

### Key Implementation Details

- **GPT-5 Temperature**: Auto-adjusted to 1.0 (required by model)
- **Caching**: Controlled globally via `DSPY_CACHE` environment variable
- **Instrumentation**: DSPy auto-instruments all operations, no custom spans needed
- **Database**: PostgreSQL backend for Phoenix (SQLite fallback in docker-compose)
- **Evaluation**: Custom metrics follow DSPy pattern: `(example, pred, trace) -> float|bool`

### Important Data Mappings

When loading case data, ensure correct key mapping:

- `accounts_data` → `account_data` (singular)
- `transactions_data` → `transaction_data` (singular)

This is a proof-of-concept implementing three fraud analysis capabilities with proper DSPy evaluation and OpenTelemetry observability.
