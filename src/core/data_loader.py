import json
import dspy
from pathlib import Path
from typing import List, Dict, Any


def load_case_data(case_name: str) -> Dict[str, str]:
    """Load all JSON files for a case and return as string dict."""
    base_path = Path(f"datasets/cases/{case_name}")
    data = {}

    files = [
        "identity.json",
        "accounts.json",
        "transactions.json",
        "device_network.json",
        "behavioral.json",
        "link_graph.json",
        "model_rules.json",
    ]

    for file in files:
        file_path = base_path / file
        if file_path.exists():
            with open(file_path, "r") as f:
                key = file.replace(".json", "_data")
                # Map to signature field names
                if key == "model_rules_data":
                    key = "model_rule_signals"
                elif key == "accounts_data":
                    key = "account_data"  # singular
                elif key == "transactions_data":
                    key = "transaction_data"  # singular
                data[key] = f.read()

    return data


def load_labels(case_name: str) -> Dict[str, Any]:
    """Load ground truth labels for a case."""
    labels_path = Path(f"datasets/labels/{case_name}_labels.json")
    with open(labels_path, "r") as f:
        return json.load(f)


def load_analyst_note(case_name: str) -> str:
    """Load optional analyst paragraph for a case."""
    note_path = Path(f"datasets/analyst_notes/{case_name}_note.txt")
    if note_path.exists():
        with open(note_path, "r") as f:
            return f.read().strip()
    return ""


def create_hypothesis_examples() -> List[dspy.Example]:
    """Create DSPy Examples for hypothesis generation task."""
    examples = []
    cases = ["case_a", "case_b", "case_c"]

    for case in cases:
        case_data = load_case_data(case)
        labels = load_labels(case)

        # Create Example with inputs and expected outputs
        example = dspy.Example(
            **case_data,
            hypotheses=labels["hypotheses"],
            supporting_evidence=labels["supporting_evidence"],
            confidence_scores=labels["confidence_scores"],
        ).with_inputs(
            "identity_data",
            "account_data",
            "transaction_data",
            "device_network_data",
            "behavioral_data",
            "link_graph_data",
            "model_rule_signals",
        )

        examples.append(example)

    return examples


def create_contradiction_examples() -> List[dspy.Example]:
    """Create DSPy Examples for contradiction checking task."""
    examples = []
    cases = ["case_a", "case_b", "case_c"]

    for case in cases:
        case_data = load_case_data(case)
        labels = load_labels(case)

        example = dspy.Example(
            **case_data,
            contradictions=labels.get("contradictions", []),
            missing_info_requests=labels.get("missing_info_requests", []),
        ).with_inputs(
            "identity_data",
            "account_data",
            "transaction_data",
            "device_network_data",
            "behavioral_data",
            "link_graph_data",
            "model_rule_signals",
        )

        examples.append(example)

    return examples


def create_narrative_examples() -> List[dspy.Example]:
    """Create DSPy Examples for narrative drafting task."""
    examples = []
    cases = ["case_a", "case_b", "case_c"]

    for case in cases:
        case_data = load_case_data(case)
        labels = load_labels(case)
        analyst_note = load_analyst_note(case)

        example = dspy.Example(
            **case_data,
            analyst_paragraph=analyst_note,
            draft_narrative=labels["draft_narrative"],
            headline=labels["headline"],
        ).with_inputs(
            "identity_data",
            "account_data",
            "transaction_data",
            "device_network_data",
            "behavioral_data",
            "link_graph_data",
            "model_rule_signals",
            "analyst_paragraph",
        )

        examples.append(example)

    return examples
