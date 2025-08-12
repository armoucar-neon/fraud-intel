#!/usr/bin/env python3

import argparse
import os
import dspy
from dspy.evaluate import Evaluate
from typing import List
from src.core.data_loader import create_hypothesis_examples
from src.core.config import AppConfig
from src.core.instrumentation import setup_instrumentation_from_env


class HypothesisGeneratorSignature(dspy.Signature):
    """Generate fraud hypotheses based on case data."""

    identity_data: str = dspy.InputField(desc="JSON string of identity and KYC information")
    account_data: str = dspy.InputField(desc="JSON string of account information and recent changes")
    transaction_data: str = dspy.InputField(desc="JSON string of chronological transaction list")
    device_network_data: str = dspy.InputField(desc="JSON string of device and network information")
    behavioral_data: str = dspy.InputField(desc="JSON string of behavioral patterns")
    link_graph_data: str = dspy.InputField(desc="JSON string of entity connections and histories")
    model_rule_signals: str = dspy.InputField(desc="JSON string of model scores and triggered rules")

    hypotheses: list[str] = dspy.OutputField(desc="Plausible fraud types or explanations")
    supporting_evidence: list[str] = dspy.OutputField(desc="Key evidence snippets")
    confidence_scores: list[float] = dspy.OutputField(desc="Confidence scores (0-1) for each hypothesis")


class HypothesisGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(HypothesisGeneratorSignature)

    def forward(self, **kwargs):
        result = self.generate(**kwargs)

        return dspy.Prediction(
            hypotheses=result.hypotheses,
            supporting_evidence=result.supporting_evidence,
            confidence_scores=result.confidence_scores,
        )


class HypothesisJudgeSignature(dspy.Signature):
    """Judge the quality of fraud hypothesis generation compared to gold standard."""

    predicted_hypotheses: list[str] = dspy.InputField(desc="Generated fraud hypotheses")
    gold_hypotheses: list[str] = dspy.InputField(desc="Expected fraud hypotheses")
    predicted_evidence: list[str] = dspy.InputField(desc="Generated supporting evidence")
    gold_evidence: list[str] = dspy.InputField(desc="Expected supporting evidence")

    hypothesis_quality: float = dspy.OutputField(
        desc="Score 0.0-1.0 evaluating how well predicted hypotheses match expected fraud types semantically"
    )
    evidence_quality: float = dspy.OutputField(
        desc="Score 0.0-1.0 evaluating coverage and relevance of supporting evidence"
    )


# Global judge instance
_hypothesis_judge = None


def get_hypothesis_judge():
    """Get or create the hypothesis judge instance."""
    global _hypothesis_judge
    if _hypothesis_judge is None:
        _hypothesis_judge = dspy.ChainOfThought(HypothesisJudgeSignature)
    return _hypothesis_judge


def hypothesis_metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
    """
    Evaluate hypothesis generation quality using LLM-as-a-judge.
    Uses semantic evaluation instead of string matching.
    """
    try:
        judge = get_hypothesis_judge()

        # Call the judge with list outputs
        judgment = judge(
            predicted_hypotheses=pred.hypotheses,
            gold_hypotheses=example.hypotheses,
            predicted_evidence=pred.supporting_evidence,
            gold_evidence=example.supporting_evidence,
        )

        # Combine hypothesis and evidence quality
        final_score = judgment.hypothesis_quality * 0.6 + judgment.evidence_quality * 0.4

        # For compilation mode, return boolean
        if trace is not None:
            return final_score >= 0.7

        return final_score

    except Exception as e:
        print(f"▸ Judge evaluation failed: {e}")
        # Fallback to simple metric
        pred_has_content = bool(
            pred.hypotheses
            and len(pred.hypotheses) > 0
            and pred.supporting_evidence
            and len(pred.supporting_evidence) > 0
        )
        return 0.5 if pred_has_content else 0.0


def run_demo(generator: HypothesisGenerator, examples: List[dspy.Example]):
    """Run demo on a single example."""
    print("\n" + "=" * 70)
    print("HYPOTHESIS GENERATOR - DEMO MODE")
    print("=" * 70)

    # Use the first example for demo
    example = examples[0]

    print("\n▹ Processing Case A (Account Takeover)...")
    print("-" * 40)

    # Generate prediction (DSPy instrumentation auto-traces this)
    pred = generator(**example.inputs())

    # Display results
    hypotheses = pred.hypotheses
    evidence = pred.supporting_evidence
    scores = pred.confidence_scores

    print("\n- Generated Hypotheses:")
    for i, (hyp, score) in enumerate(zip(hypotheses[:3], scores[:3]), 1):
        print(f"   {i}. {hyp} (confidence: {score:.2f})")

    print("\n- Supporting Evidence (sample):")
    for i, ev in enumerate(evidence[:3], 1):
        print(f"   • {ev[:80]}...")

    print("\n✓ Expected Output:")
    for i, hyp in enumerate(example.hypotheses[:3], 1):
        print(f"   {i}. {hyp}")

    # Calculate metric
    score = hypothesis_metric(example, pred)
    print(f"\n▹ Metric Score: {score:.3f}")


def run_evaluation(generator: HypothesisGenerator, examples: List[dspy.Example]):
    """Run full evaluation on all examples."""
    print("\n" + "=" * 70)
    print("HYPOTHESIS GENERATOR - EVALUATION MODE")
    print("=" * 70)

    # Split data (in practice, you'd have separate train/dev/test sets)
    trainset = examples[:2]
    devset = examples

    print("\n▸ Dataset Statistics:")
    print(f"   • Training examples: {len(trainset)}")
    print(f"   • Evaluation examples: {len(devset)}")

    # Set up evaluator
    evaluator = Evaluate(
        devset=devset,
        metric=hypothesis_metric,
        num_threads=os.cpu_count() or 1,
        display_progress=True,
    )

    # Run evaluation (DSPy instrumentation auto-traces this)
    print("\n▸ Running evaluation...")
    results = evaluator(generator)

    print(f"\n▹ Final Score: {results:.3f}")

    # Detailed metrics
    print("\n- Detailed Analysis:")
    total_score = 0
    for i, example in enumerate(devset):
        pred = generator(**example.inputs())
        score = hypothesis_metric(example, pred)
        total_score += score

        case_name = ["Case A (ATO)", "Case B (Synthetic)", "Case C (Legitimate)"][i]
        print(f"   • {case_name}: {score:.3f}")

    avg_score = total_score / len(devset)
    print(f"\n   Average Score: {avg_score:.3f}")


def main():
    parser = argparse.ArgumentParser(description="DSPy Hypothesis Generator for Fraud Analysis")
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
    examples = create_hypothesis_examples()

    # Initialize module
    generator = HypothesisGenerator()

    # Run based on mode
    if args.mode == "demo":
        run_demo(generator, examples)
    else:
        run_evaluation(generator, examples)

    print("\n✓ Complete!\n")


if __name__ == "__main__":
    main()
