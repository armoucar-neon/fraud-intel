# Engineering Prompt — Fraud Analyst Assistant PoC (DSPy)

**Goal:** Build a **single Python script** PoC using DSPy that implements three core capabilities for fraud analysis support:

1. **Hypothesis Generator**
2. **Contradiction & Missing-Info Check**
3. **Narrative Drafter** (takes structured case data + optional analyst paragraph)

---

## Requirements

### Signatures

**1. Hypothesis Generator**

* **Inputs**:

  * `identity_data` (JSON): name, DOB, ID numbers, KYC results, sanctions/PEP flags.
  * `account_data` (JSON): accounts, cards, wallets, limits, status, recent changes.
  * `transaction_data` (JSON): chronological list of transactions with type, amount, location, channel, authentication results.
  * `device_network_data` (JSON): device fingerprints, OS, browser, IPs, geolocation, risk flags.
  * `behavioral_data` (JSON): session patterns, typing/mouse behavior, 2FA attempts.
  * `link_graph_data` (JSON): connected entities and their case histories.
  * `model_rule_signals` (JSON): model scores, rule IDs/descriptions.
* **Outputs**:

  * `hypotheses` (list of strings): plausible fraud types or explanations.
  * `supporting_evidence` (list of strings): key evidence snippets from inputs.
  * `confidence_scores` (list of floats 0–1): model-estimated confidence for each hypothesis.

**2. Contradiction & Missing-Info Check**

* **Inputs**:

  * All the above input datasets.
* **Outputs**:

  * `contradictions` (list of strings): detected inconsistencies in the evidence.
  * `missing_info_requests` (list of strings): specific follow-up questions or data requests to clarify.

**3. Narrative Drafter**

* **Inputs**:

  * All the above input datasets.
  * `analyst_paragraph` (string): optional text from the analyst.
* **Outputs**:

  * `draft_narrative` (string): 1–3 paragraph concise, evidence-grounded summary.
  * `headline` (string): one-line summary of the case.

---

## Dataset Organization

Use the demo cases in the previous documentation as the starting dataset.

* Folder structure:

  * `datasets/cases/` → subfolders for each case containing separate `.json` files for each input type (e.g., `identity.json`, `accounts.json`, `transactions.json`, etc.).
  * `datasets/analyst_notes/` → optional `.txt` files with `analyst_paragraph` examples.
  * `datasets/labels/` → ground truth `.json` files for hypotheses, contradictions, and narratives.
* Maintain naming consistency across folders (e.g., `case_a/identity.json`, `case_a_labels.json`).

---

## Evaluation & Metrics (for the three signatures only)

All modules use **LLM-as-a-Judge** evaluation with DSPy ChainOfThought for semantic assessment:

**Hypothesis Generator**

* **Primary Metric**: Weighted combination of hypothesis quality (0.6) + evidence quality (0.4)
* **Implementation**: DSPy ChainOfThought judge evaluates semantic similarity between predicted and gold hypotheses/evidence
* **Output**: Single score 0.0-1.0 (≥0.7 for compilation mode)

**Contradiction & Missing-Info Check**

* **Primary Metric**: Weighted combination of contradiction accuracy (0.5) + missing info completeness (0.5)  
* **Implementation**: DSPy ChainOfThought judge evaluates precision/recall of contradictions and completeness of missing information requests
* **Output**: Single score 0.0-1.0 (≥0.7 for compilation mode)

**Narrative Drafter**

* **Primary Metric**: Weighted combination of narrative quality (0.5) + headline accuracy (0.3) + conciseness (0.2)
* **Implementation**: DSPy ChainOfThought judge evaluates narrative completeness, accuracy, clarity, and appropriate length
* **Output**: Single score 0.0-1.0 (≥0.7 for compilation mode)

---

## What You Will Deliver

* **Three Python scripts** (one per signature) using DSPy:

  * Define each signature (`@dspy.signature` or equivalent) with the separated inputs above.
  * Implement as DSPy modules (e.g., `Predict`, `ChainOfThought`).
  * Load datasets, run predictions, compute metrics.
* Scripts should run locally with example data from `datasets/`.
* This is a PoC — minimal structure, but code must run end-to-end with provided demo data.
