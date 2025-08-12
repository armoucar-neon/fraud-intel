# Fraud Analysis Demo: Story, Process, UI, and Example Cases

> **Purpose.** This document gives you a realistic story for a fintech fraud‑analysis backend application, explains how it gathers and fuses data into a single analyst UI, and defines exactly what **inputs** the human sees and what **outputs** the human must provide to make the final call. It ends with **three worked example cases** (with sample data) that you can use in a demo.

---

## 1) End‑to‑end story: from signal to decision

1. **Event happens** (onboarding, login, card swipe, bank transfer, card‑not‑present purchase, P2P, dispute, etc.).
2. **Ingestion**: raw events stream into the fraud backend via collectors and partners:

   * **Core ledger & payments processor** (authorizations, settlements, ACH, PIX/instant payments, chargebacks).
   * **KYC/KYB provider(s)** (identity documents, face match score, watchlist hits).
   * **Device & network intelligence** (device fingerprint, emulator/rooted flags, IP reputation, geolocation).
   * **Behavioral biometrics/session** (typing cadence, mouse/touch patterns, session anomalies).
   * **Consortium/negative lists** (shared fraud devices/emails, compromised BINs).
   * **Sanctions/PEP screening** (periodic rescreen results).
   * **Customer support & CRM** (tickets, call outcomes).
   * **Historical outcomes** (prior cases, chargeback results).
3. **Normalization & entity resolution**: we map everything into a unified schema and link entities (person ↔ accounts ↔ cards ↔ devices ↔ emails ↔ addresses ↔ merchants ↔ beneficiaries) using deterministic keys and probabilistic matching.
4. **Feature engineering (stream + batch)**: we compute rolling features and risk signals (e.g., velocity counts, geodistance from last login, device first\_seen\_age, name/SSN mismatch, email domain age, beneficiary novelty, merchant MCC risk).
5. **Models & rules evaluate**: ML models and rules produce **advisory scores and reason codes** (never a final verdict).
6. **Case assembly & triage**: if triggers meet thresholds (e.g., high score + new beneficiary + rapid transfer), we build a **Case Package** and route it to an analyst queue with an SLA.
7. **Human review in the UI**: the analyst inspects fused data, adds notes, and makes the call.
8. **Decision orchestration**: the system executes actions (block/freezes, reversals, customer comms), logs an auditable trail, and **labels data** to continuously improve models.

---

## 2) What the system collects and how it shows it (the UI)

### Panels the analyst sees (system‑assembled **inputs**)

* **Case Header**: case ID, creation time, SLA countdown, risk score band, queue, status (Open/Pending/Closed), and quick actions (Freeze, Reverse, Escalate).
* **Identity & KYC**: legal name, DOB, national ID/SSN, address(es), email(s), phone(s); KYC provider results (document type, MRZ checks, liveness score, face match score, sanctions/PEP hits); change history.
* **Accounts & Instruments**: bank accounts, cards, wallets; limits; current holds/blocks; recent changes (new device, password reset, new payee).
* **Transaction Timeline**: ordered stream of relevant events with filters (type, channel, amount, geolocation, outcome).
* **Device & Network**: device fingerprints (ID, model, OS), risk flags (emulator, rooted), IPs with reputation/ASN, geodistance from last good login, proxy/VPN/Tor indicators.
* **Behavioral & Session**: session duration, typing/tap patterns, failed vs. successful 2FA, password reset patterns, step‑up challenges.
* **Link Graph**: connected entities (shared device/email/phone/beneficiary/merchant), prior case outcomes on neighbors, betweenness/degree metrics.
* **Model & Rule Signals**: top features + SHAP‑style explanations, triggered rules (IDs, descriptions), versioning.
* **Documents & Media**: uploaded ID images, selfies, proof of address, screenshots.
* **History & Chargebacks**: prior disputes, outcomes, reason codes, any SAR/Reg reports filed.
* **Notes & Collaboration**: threaded comments, @mentions, file attachments.

> All personally identifiable data in the demo should be **synthetic** (fake) and clearly labeled as such.

### What the human must provide (explicit **outputs**)

The analyst completes a structured decision form plus optional notes. Required fields:

* **Final Decision** *(required)*: `Confirmed Fraud` | `Not Fraud (Genuine)` | `Inconclusive – Monitor` | `Escalate` | `Request More Info`
* **Fraud Type** *(when Fraud or Suspicious)*: `Account Takeover (ATO)` | `Synthetic Identity` | `Stolen Card / CNP` | `Friendly Fraud/First‑Party` | `Money Mule` | `Merchant Collusion` | `Other`
* **Reason Codes** *(multi‑select)*: e.g., `New device + foreign IP`, `Beneficiary first‑time + high amount`, `Document tampering`, `Shared device with 5+ bad accounts`, `Geovelocity impossible`, etc.
* **Narrative** *(1–3 paragraphs)*: plain‑language summary with evidence (timestamps, entities, screenshots reference).
* **Confidence (0–100%)**
* **Actions to Execute**: `Freeze account` | `Cancel card` | `Reverse/Recall transfer` | `Decline application` | `File regulatory report` | `Notify customer` | `Whitelist` | `Adjust limits`
* **Customer Contact Outcome** (if applicable): `Reached/Not reached`, `Verified identity (KBA/OTP)`, call summary.
* **Labeling Hooks** (automatic after submit): snapshot of all features + decision for training sets; watchlist updates (emails/devices/beneficiaries); rule feedback.

The system enforces completeness (e.g., you can’t resolve as Fraud without choosing a Fraud Type) and journals **who did what when** for audit.

---

## 3) Process: step‑by‑step with responsibilities

1. **Intake & Deduplication**

   * *System*: Create/merge case based on entity keys and time windows.
2. **Initial Triage**

   * *System*: Apply routing (risk band, geography, product) and SLA.
   * *Analyst*: Acknowledge case; add initial note if obvious.
3. **Evidence Gathering in UI**

   * *System*: Surfaces the most informative panels first (e.g., Link Graph when neighbors are hot).
   * *Analyst*: Review timeline, devices, documents; request info if needed.
4. **Decision & Actions**

   * *Analyst*: Fill decision form and submit.
   * *System*: Execute actions atomically (freeze/reverse/notify), update ledgers/blocks, emit webhooks.
5. **Post‑Decision Learning**

   * *System*: Write the decision + features to the labeling store, update heuristics, and close case.

---

## 4) Three demo cases (synthetic data)

Each case below lists **what the UI shows** (system inputs) and the **expected analyst outputs**.

### Case A — Account Takeover with rapid outbound transfer

**Trigger**: New device + foreign IP + password reset + high‑value PIX/ACH to a new beneficiary within 30 minutes.

**UI shows (inputs)**

* **Identity & KYC**: João Pereira, DOB 1991‑05‑12, national ID 123.456.789‑00; KYC verified (doc + selfie match 0.92), no sanctions hits.
* **Accounts**: Current account • ACCT‑884231; card • \*\*\*\* 6621.
* **Recent changes**: Password reset at **2025‑08‑10 18:03 BRT**; new device registered at **18:05**; new beneficiary added at **18:18**.
* **Login events**:

  * **18:02** from IP 185.199.110.34 (ASN: Hosting provider), geolocated to Frankfurt, DE; device: Windows 10, Chrome 126, fingerprint `dfp_e3b…`; 2FA: **SMS OTP bypassed via fallback email** after two failures.
  * Last known good login: **2025‑08‑08 10:21 BRT** from São Paulo, BR, iPhone 14, device fingerprint `dfp_7aa…`.
* **Transaction timeline**:

  * **18:26** PIX/instant transfer **R\$ 18,900.00** to **BEN‑70211 (Carlos M.)**; beneficiary first‑time; memo "consulting".
  * **18:29** Secondary transfer **R\$ 3,500.00** to same beneficiary (queued).
* **Device & network**: New device first\_seen\_age = 0 days; IP risk: high; VPN/proxy suspected; geovelocity São Paulo→Frankfurt in 1 min (impossible).
* **Link graph**: Beneficiary account **BEN‑70211** is linked to **3 prior fraud cases** in the last 7 days (shared destination).
* **Model & rules**: Risk score 0.94; rules: `R‑119 (new device + high amount)`, `R‑204 (impossible geovelocity)`, `R‑331 (shared mule)`.
* **Customer support**: No travel note; email auto‑reply bounce on file.

**Expected analyst outputs**

* **Final Decision**: Confirmed Fraud.
* **Fraud Type**: Account Takeover (ATO) → Money Mule destination.
* **Reason Codes**: New device + foreign IP; Impossible geovelocity; 2FA bypass; First‑time beneficiary; Shared mule account.
* **Narrative**: *Compromised account used from Frankfurt on hosting ASN minutes after password reset; rapid high‑value PIX to beneficiary BEN‑70211 with known fraud linkages; evidence across device/IP/timeline supports ATO.*
* **Confidence**: 95%.
* **Actions**: Freeze account; cancel queued transfer (R\$ 3,500); initiate recall on R\$ 18,900; block beneficiary; require step‑up re‑verification for customer; notify customer via out‑of‑band; file internal mule report.
* **Customer Contact Outcome**: Not reached (email bounces; phone unanswered).

---

### Case B — Synthetic identity application (document tampering + cross‑device sharing)

**Trigger**: New account application with high document risk + device seen across many identities + thin history.

**UI shows (inputs)**

* **Application**: Name "Maria Luiza Alves"; DOB 2002‑11‑03; SSN/CPF submitted; address: Rua das Flores 123, Curitiba.
* **KYC results**: Document front/back uploaded; **liveness 0.48 (low)**; **face match 0.56**; MRZ checksum fail; detected **edge artifacts** on ID photo; email domain age 12 days; phone registered 8 days ago.
* **Device & network**: Android 9 device `and_4c1…`; rooted: **true**; seen on **11 prior failed/blocked applications**; IP: mobile CGNAT; time on page 42 seconds (low).
* **Behavioral**: Typing cadence inconsistent; pasted full name + ID; copy/paste for selfie step; abandoned when asked for proof of address.
* **Link graph**: Device connects to 7 other identities with overlapping addresses; two were later chargebacks.
* **Funding attempts (pre‑KYC sandbox)**: two micro‑deposits from the same external bank; reversed next day.
* **Model & rules**: Application risk 0.91; `R‑510 (rooted device)`, `R‑612 (document tamper)`, `R‑433 (device multi‑identity)`.

**Expected analyst outputs**

* **Final Decision**: Confirmed Fraud.
* **Fraud Type**: Synthetic Identity.
* **Reason Codes**: Document tampering; Low liveness/face match; Rooted device; Shared device across 10+ identities; Thin/young contact points.
* **Narrative**: *Application exhibits synthetic patterns: tampered document with failed MRZ, low biometric confidence, and a rooted device previously tied to multiple blocked identities; minimal digital history. High likelihood of bust‑out/fraud account creation.*
* **Confidence**: 90%.
* **Actions**: Decline application; blacklist device fingerprint and emails/phones; add address/email to internal watchlist; notify KYC vendor with sample; no regulatory filing required.
* **Customer Contact Outcome**: Not applicable (no active customer).

---

### Case C — Legitimate customer traveling (false positive avoided)

**Trigger**: Card‑not‑present purchase burst in another country + new IP → model high but explainable by travel.

**UI shows (inputs)**

* **Identity**: Ana Souza, long‑tenured customer since 2021.
* **Travel note**: Customer set travel plan **2025‑08‑05 → 2025‑08‑15** for Portugal & Spain via app.
* **Login & device**: Same iPhone 13 `ios_d1a…`; IPs from Lisbon hotel ASN; device not jailbroken.
* **Transaction timeline (last 24h)**:

  * 09:20 — EUR 85.40 online museum tickets (PT) — 3DS successful.
  * 09:34 — EUR 312.00 airline baggage fees (ES) — AVS partial match; 3DS frictionless.
  * 10:02 — EUR 1,120.00 boutique hotel hold (PT) — within limits.
* **Behavioral**: Normal session duration; successful 2FA; geolocation matches device GPS consent.
* **Model & rules**: Score 0.78 due to country change + spend burst; rule `R‑210 (country jump)` fired.
* **Customer support**: No open tickets; positive history; zero chargebacks in 3 years.

**Expected analyst outputs**

* **Final Decision**: Not Fraud (Genuine).
* **Fraud Type**: N/A.
* **Reason Codes**: Travel note matches location; device consistent; 3DS success; long clean history.
* **Narrative**: *Spending aligns with declared travel window and consistent device; strong authentication on CNP transactions; no indicators of takeover or mule behavior.*
* **Confidence**: 88%.
* **Actions**: Whitelist customer for EU merchants during travel window; raise temporary CNP limit by 10%; notify customer by in‑app message confirming approvals.
* **Customer Contact Outcome**: Not contacted (sufficient evidence).

---

## 5) What to demo live (script cheat‑sheet)

1. Open **Case A** → highlight password reset → new device → link graph mule → show one‑click "Freeze + Recall" action.
2. Open **Case B** → zoom on Document panel (tamper markers) → open Device panel to show prior identities → Decline + blacklist.
3. Open **Case C** → point out Travel note + device continuity → choose "Not Fraud" → add reason codes → enable temporary whitelist.

---

## 6) Implementation notes (for engineers)

* **Pipelines**: event collectors (REST + streaming), schema registry, PII tokenization, dead‑letter queues.
* **Entity resolution**: fuzzy match with thresholds, deterministic joins on hashed identifiers.
* **Feature store**: stream (real‑time counts) + batch (daily aggregates), feature versioning.
* **Decisioning**: rules engine + ML service; signals are advisory; human makes the call.
* **Case service**: idempotent case builder, queue router, SLA manager.
* **UI**: case view with pluggable panels; JSON Case Package → typed view models.
* **Audit & compliance**: immutable journal; reason codes & narratives mandatory; export for regulators; redaction for screenshots.
* **Feedback loop**: labels to training data; drift tracking; rule performance dashboards.

---

### Appendix: Example structured decision output (what the backend records)

```json
{
  "case_id": "CASE-2025-0810-00042",
  "final_decision": "Confirmed Fraud",
  "fraud_type": "Account Takeover",
  "reason_codes": ["New device + foreign IP", "Impossible geovelocity", "Shared mule beneficiary"],
  "confidence": 0.95,
  "narrative": "Compromised account used from Frankfurt minutes after password reset; high-value PIX to known mule...",
  "actions": ["freeze_account", "recall_transfer", "block_beneficiary", "notify_customer"],
  "customer_contact": {"status": "not_reached"},
  "labels": {"entities": ["acct:ACCT-884231", "beneficiary:BEN-70211", "device:dfp_e3b"], "ts": "2025-08-10T18:35:00-03:00"}
}
```
