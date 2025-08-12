#!/usr/bin/env python3

import argparse
import os
import dspy
from dspy.evaluate import Evaluate
from typing import List
from src.core.data_loader import create_narrative_examples
from src.core.config import AppConfig
from src.core.instrumentation import setup_instrumentation_from_env


class NarrativeDrafterSignature(dspy.Signature):
    """Draft a concise fraud analysis narrative based on case data."""

    identity_data: str = dspy.InputField(desc="JSON string of identity and KYC information")
    account_data: str = dspy.InputField(desc="JSON string of account information and recent changes")
    transaction_data: str = dspy.InputField(desc="JSON string of chronological transaction list")
    device_network_data: str = dspy.InputField(desc="JSON string of device and network information")
    behavioral_data: str = dspy.InputField(desc="JSON string of behavioral patterns")
    link_graph_data: str = dspy.InputField(desc="JSON string of entity connections and histories")
    model_rule_signals: str = dspy.InputField(desc="JSON string of model scores and triggered rules")
    analyst_paragraph: str = dspy.InputField(desc="Optional text from analyst (can be empty)", default="")

    draft_narrative: str = dspy.OutputField(desc="1-3 paragraph concise, evidence-grounded summary of the case")
    headline: str = dspy.OutputField(desc="One-line summary of the case")


class NarrativeDrafter(dspy.Module):
    def __init__(self):
        super().__init__()
        self.draft = dspy.ChainOfThought(NarrativeDrafterSignature)

    def forward(self, **kwargs):
        result = self.draft(**kwargs)

        return dspy.Prediction(
            draft_narrative=result.draft_narrative.strip(),
            headline=result.headline.strip(),
        )


class NarrativeJudgeSignature(dspy.Signature):
    """Judge the quality of fraud narrative and headline generation."""

    predicted_narrative: str = dspy.InputField(desc="Generated fraud analysis narrative")
    gold_narrative: str = dspy.InputField(desc="Expected fraud analysis narrative")
    predicted_headline: str = dspy.InputField(desc="Generated case headline")
    gold_headline: str = dspy.InputField(desc="Expected case headline")

    narrative_quality: float = dspy.OutputField(
        desc="Score 0.0-1.0 evaluating narrative completeness, accuracy, and clarity"
    )
    headline_quality: float = dspy.OutputField(desc="Score 0.0-1.0 evaluating headline accuracy and conciseness")
    conciseness: float = dspy.OutputField(desc="Score 0.0-1.0 evaluating appropriate length and brevity")


# Global judge instance
_narrative_judge = None


def get_narrative_judge():
    """Get or create the narrative judge instance."""
    global _narrative_judge
    if _narrative_judge is None:
        _narrative_judge = dspy.ChainOfThought(NarrativeJudgeSignature)
    return _narrative_judge


def narrative_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """
    Evaluate narrative quality using LLM-as-a-judge.
    Uses semantic evaluation instead of keyword matching.
    """
    try:
        judge = get_narrative_judge()

        # Call the judge
        judgment = judge(
            predicted_narrative=pred.draft_narrative,
            gold_narrative=example.draft_narrative,
            predicted_headline=pred.headline,
            gold_headline=example.headline,
        )

        # Combine narrative, headline, and conciseness quality
        final_score = judgment.narrative_quality * 0.5 + judgment.headline_quality * 0.3 + judgment.conciseness * 0.2

        # For compilation mode, return boolean
        if trace is not None:
            return final_score >= 0.7

        return final_score

    except Exception as e:
        print(f"▸ Judge evaluation failed: {e}")
        # Fallback to simple metric
        has_content = bool(pred.draft_narrative.strip() and pred.headline.strip())
        return 0.5 if has_content else 0.0


def run_demo(drafter: NarrativeDrafter, examples: List[dspy.Example]):
    """Run demo on a single example."""
    print("\n" + "=" * 70)
    print("NARRATIVE DRAFTER - DEMO MODE")
    print("=" * 70)

    # Use the first example for demo
    example = examples[0]

    print("\n▹ Processing Case A (Account Takeover)...")
    print("-" * 40)

    # Generate prediction
    pred = drafter(**example.inputs())

    print("\n▹ Generated Headline:")
    print(f"   {pred.headline}")

    print("\n- Generated Narrative:")
    # Format narrative for display
    narrative_lines = pred.draft_narrative.split(". ")
    for line in narrative_lines[:5]:  # Show first 5 sentences
        if line:
            print(f"   {line}.")

    print("\n▹ Statistics:")
    print(f"   • Narrative length: {len(pred.draft_narrative.split())} words")
    print(f"   • Headline length: {len(pred.headline.split())} words")

    print("\n✓ Expected Headline:")
    print(f"   {example.headline}")

    # Calculate metric
    score = narrative_metric(example, pred)
    print(f"\n▹ Metric Score: {score:.3f}")


def run_evaluation(drafter: NarrativeDrafter, examples: List[dspy.Example]):
    """Run full evaluation on all examples."""
    print("\n" + "=" * 70)
    print("NARRATIVE DRAFTER - EVALUATION MODE")
    print("=" * 70)

    # Split data
    trainset = examples[:2]
    devset = examples

    print("\n▸ Dataset Statistics:")
    print(f"   • Training examples: {len(trainset)}")
    print(f"   • Evaluation examples: {len(devset)}")

    # Set up evaluator
    evaluator = Evaluate(
        devset=devset,
        metric=narrative_metric,
        num_threads=os.cpu_count() or 1,
        display_progress=True,
    )

    # Run evaluation
    print("\n▸ Running evaluation...")
    results = evaluator(drafter)

    print(f"\n▹ Final Score: {results:.3f}")

    # Detailed metrics
    print("\n- Detailed Analysis:")
    total_score = 0
    for i, example in enumerate(devset):
        pred = drafter(**example.inputs())
        score = narrative_metric(example, pred)
        total_score += score

        case_name = ["Case A (ATO)", "Case B (Synthetic)", "Case C (Legitimate)"][i]
        word_count = len(pred.draft_narrative.split())
        print(f"   • {case_name}: {score:.3f} ({word_count} words)")

    avg_score = total_score / len(devset)
    print(f"\n   Average Score: {avg_score:.3f}")


def main():
    parser = argparse.ArgumentParser(description="DSPy Narrative Drafter for Fraud Analysis")
    parser.add_argument(
        "--mode",
        choices=["demo", "eval"],
        default="demo",
        help="Run mode: demo (single example) or eval (full evaluation)",
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-5-2025-08-07",
        help="Language model to use (default: openai/gpt-5-2025-08-07)",
    )

    args = parser.parse_args()

    # Setup instrumentation (auto-traces all DSPy operations)
    setup_instrumentation_from_env()

    # Create configuration
    config = AppConfig.create(args.model, temperature=1.0)

    # Configure DSPy
    print(f"▸ Configuring DSPy with {config.model.model_name}...")
    lm = dspy.LM(
        config.model.model_name,
        temperature=config.model.temperature,
        cache=config.model.cache,
    )
    dspy.configure(lm=lm)

    # Load data
    print("▸ Loading dataset...")
    examples = create_narrative_examples()

    # Initialize module
    drafter = NarrativeDrafter()

    # Run based on mode
    if args.mode == "demo":
        run_demo(drafter, examples)
    else:
        run_evaluation(drafter, examples)

    print("\n✓ Complete!\n")


if __name__ == "__main__":
    main()
