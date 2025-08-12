#!/usr/bin/env python3

import argparse
import os
import dspy
from dspy.evaluate import Evaluate
from typing import List
from src.core.data_loader import create_contradiction_examples
from src.core.config import AppConfig
from src.core.instrumentation import setup_instrumentation_from_env


class ContradictionCheckSignature(dspy.Signature):
    """Check for contradictions and identify missing information in fraud case data."""

    identity_data: str = dspy.InputField(desc="JSON string of identity and KYC information")
    account_data: str = dspy.InputField(desc="JSON string of account information and recent changes")
    transaction_data: str = dspy.InputField(desc="JSON string of chronological transaction list")
    device_network_data: str = dspy.InputField(desc="JSON string of device and network information")
    behavioral_data: str = dspy.InputField(desc="JSON string of behavioral patterns")
    link_graph_data: str = dspy.InputField(desc="JSON string of entity connections and histories")
    model_rule_signals: str = dspy.InputField(desc="JSON string of model scores and triggered rules")

    contradictions: list[str] = dspy.OutputField(desc="Detected inconsistencies in the case data")
    missing_info_requests: list[str] = dspy.OutputField(desc="Specific follow-up questions or data requests needed")


class ContradictionChecker(dspy.Module):
    def __init__(self):
        super().__init__()
        self.check = dspy.ChainOfThought(ContradictionCheckSignature)

    def forward(self, **kwargs):
        result = self.check(**kwargs)

        return dspy.Prediction(
            contradictions=result.contradictions,
            missing_info_requests=result.missing_info_requests,
        )


class ContradictionJudgeSignature(dspy.Signature):
    """Judge the quality of contradiction detection and missing information identification."""

    predicted_contradictions: list[str] = dspy.InputField(desc="Detected contradictions")
    gold_contradictions: list[str] = dspy.InputField(desc="Expected contradictions")
    predicted_missing_info: list[str] = dspy.InputField(desc="Missing information requests")
    gold_missing_info: list[str] = dspy.InputField(desc="Expected missing information requests")

    contradiction_quality: float = dspy.OutputField(
        desc="Score 0.0-1.0 evaluating accuracy of contradiction detection (precision/recall)"
    )
    missing_info_quality: float = dspy.OutputField(
        desc="Score 0.0-1.0 evaluating completeness of missing information identification"
    )


# Global judge instance
_contradiction_judge = None


def get_contradiction_judge():
    """Get or create the contradiction judge instance."""
    global _contradiction_judge
    if _contradiction_judge is None:
        _contradiction_judge = dspy.ChainOfThought(ContradictionJudgeSignature)
    return _contradiction_judge


def contradiction_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """
    Evaluate contradiction detection and missing info identification using LLM-as-a-judge.
    Uses semantic evaluation instead of string matching.
    """
    try:
        judge = get_contradiction_judge()

        # Call the judge
        judgment = judge(
            predicted_contradictions=pred.contradictions,
            gold_contradictions=example.contradictions,
            predicted_missing_info=pred.missing_info_requests,
            gold_missing_info=example.missing_info_requests,
        )

        # Combine contradiction and missing info quality
        final_score = judgment.contradiction_quality * 0.5 + judgment.missing_info_quality * 0.5

        # For compilation mode, return boolean
        if trace is not None:
            return final_score >= 0.7

        return final_score

    except Exception as e:
        print(f"▸ Judge evaluation failed: {e}")
        # Fallback to simple metric
        has_output = bool(
            (pred.contradictions and len(pred.contradictions) > 0)
            or (pred.missing_info_requests and len(pred.missing_info_requests) > 0)
        )
        return 0.5 if has_output else 0.0


def run_demo(checker: ContradictionChecker, examples: List[dspy.Example]):
    """Run demo on a single example."""
    print("\n" + "=" * 70)
    print("CONTRADICTION & MISSING INFO CHECKER - DEMO MODE")
    print("=" * 70)

    # Use the first example for demo
    example = examples[0]

    print("\n▹ Processing Case A (Account Takeover)...")
    print("-" * 40)

    # Generate prediction (DSPy instrumentation auto-traces this)
    pred = checker(**example.inputs())

    # Display results
    contradictions = pred.contradictions or []
    missing_info = pred.missing_info_requests or []

    print("\n▸ Contradictions Found:")
    if contradictions:
        for i, cont in enumerate(contradictions, 1):
            print(f"   {i}. {cont}")
    else:
        print("   None detected")

    print("\n▹ Missing Information Requests:")
    if missing_info:
        for i, req in enumerate(missing_info[:3], 1):
            print(f"   {i}. {req}")
    else:
        print("   None identified")

    print("\n✓ Expected Output:")
    if example.missing_info_requests:
        print("   Missing Info Requests:")
        for i, req in enumerate(example.missing_info_requests, 1):
            print(f"     {i}. {req}")

    # Calculate metric
    score = contradiction_metric(example, pred)
    print(f"\n▹ Metric Score: {score:.3f}")


def run_evaluation(checker: ContradictionChecker, examples: List[dspy.Example]):
    """Run full evaluation on all examples."""
    print("\n" + "=" * 70)
    print("CONTRADICTION & MISSING INFO CHECKER - EVALUATION MODE")
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
        metric=contradiction_metric,
        num_threads=os.cpu_count() or 1,
        display_progress=True,
    )

    # Run evaluation (DSPy instrumentation auto-traces this)
    print("\n▸ Running evaluation...")
    results = evaluator(checker)

    print(f"\n▹ Final Score: {results:.3f}")

    # Detailed metrics
    print("\n- Detailed Analysis:")
    total_score = 0
    for i, example in enumerate(devset):
        pred = checker(**example.inputs())
        score = contradiction_metric(example, pred)
        total_score += score

        case_name = ["Case A (ATO)", "Case B (Synthetic)", "Case C (Legitimate)"][i]
        print(f"   • {case_name}: {score:.3f}")

    avg_score = total_score / len(devset)
    print(f"\n   Average Score: {avg_score:.3f}")


def main():
    parser = argparse.ArgumentParser(description="DSPy Contradiction Checker for Fraud Analysis")
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
        max_tokens=16000,
    )
    dspy.configure(lm=lm)

    # Load data
    print("▸ Loading dataset...")
    examples = create_contradiction_examples()

    # Initialize module
    checker = ContradictionChecker()

    # Run based on mode
    if args.mode == "demo":
        run_demo(checker, examples)
    else:
        run_evaluation(checker, examples)

    print("\n✓ Complete!\n")


if __name__ == "__main__":
    main()
