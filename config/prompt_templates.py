"""
Prompt templates for the DEFINE phase.
These templates can be updated by the REFLECT node between cycles.
Each template supports ToT (Tree of Thought) + CoT (Chain of Thought) reasoning.
"""
# Interview template
interview_me = """Analyze the feature description at {spec_path} and conduct a structured interview.

## REASONING PHASE (Tree of Thought)
Generate 3 candidate interview angles, evaluate each, and select the best:

- **Angle A** — User-centric: Who are the actors? What jobs-to-be-done drive this feature?
- **Angle B** — System-centric: What existing components, data stores, or APIs are involved?
- **Angle C** — Risk-centric: What could go wrong (performance, security, edge cases, failures)?

For each angle, assign a score (1-5) based on how much unknown information it would reveal given the context. Then state which angle you're pursuing first and why.

## EXECUTION PHASE (Chain of Thought)
Follow this sequential process:

**Step 1 — Persona**: Ask one question to identify the primary user role, their goals, and frustrations. Wait for the answer.
**Step 2 — Workflow**: Walk through the happy path step by step, asking one clarification question per step. Wait after each.
**Step 3 — Acceptance**: Propose 3 Given/When/Then acceptance criteria and ask the user to confirm or modify.
**Step 4 — Risk**: Probe for edge cases, error handling, performance concerns, and security implications. One question at a time.
**Step 5 — Metrics**: Ask how success will be measured (latency, throughput, error rate, adoption).

Rules: Ask ONE question at a time. Wait for the answer. Follow up only on that answer.
Flag assumptions when the user is uncertain. Never invent requirements."""

# Spec generation template
speckit_specify = """Produce a complete, actionable specification for the feature at {spec_path}.

## REASONING PHASE (Tree of Thought)
Generate 3 candidate scope interpretations, evaluate each, and select the best:

- **Interpretation A** — Minimal: Core value only, bare minimum to ship
- **Interpretation B** — Standard: Core value plus the obvious follow-on use cases
- **Interpretation C** — Extended: Full vision including edge cases and future-proofing

For each interpretation, assess completeness, risk of scope creep, and alignment with available context. Then state which interpretation you're using and why.

## EXECUTION PHASE (Chain of Thought)
Follow this sequential process, justifying each section:

**Step 1 — Summary**: Write a one-paragraph overview of what, who, and why.
**Step 2 — User Stories**: Write numbered stories (US-1, US-2, ...) in "As a [persona], I want [goal] so that [benefit]" format. Each story must have ≥2 Given/When/Then acceptance criteria.
**Step 3 — Edge Cases**: For each user story, identify what happens when input is missing, invalid, slow, or auth fails. Cross-reference to the story ID (e.g., "Edge case for US-3").
**Step 4 — Non-Functional**: Specify performance targets, security requirements, and data retention rules.
**Step 5 — Dependencies**: List external services, data sources, or other features required.
**Step 6 — Out of Scope**: Explicitly state what this does NOT cover.
**Step 7 — Open Items**: List unresolved questions needing stakeholder input.

Ground all content in the provided context. Do not add features not implied."""

# API/interface design template
api_and_interface_design = """Design all interfaces required by this feature.

## REASONING PHASE (Tree of Thought)
Generate 3 candidate architecture approaches, evaluate each, and select the best:

- **Approach A** — Monolithic: Single service with a simple database
- **Approach B** — Modular: Separated domains sharing a database
- **Approach C** — Distributed: Microservices with event-driven communication

For each approach, assess complexity, team capacity fit, and feature alignment. Then state which approach you're using and why.

## EXECUTION PHASE (Chain of Thought)
Follow this sequential process:

**Step 1 — REST API** (if applicable): Define HTTP method, path, query params, and request/response JSON schemas with real field names. Specify auth requirements per endpoint.
**Step 2 — CLI** (if applicable): Define command, flags, args, exit codes, and output format.
**Step 3 — Database** (if applicable): Define tables/collections, column types, indexes, and foreign keys.
**Step 4 — Event Bus** (if applicable): Define event names, payload schemas, consumers, and retry semantics.
**Step 5 — Error Responses**: Specify status codes and error payload structure.
**Step 6 — Contract Guarantees**: Define idempotency rules, versioning strategy, and backward-compatibility obligations.
**Step 7 — Module Ownership**: Map each interface to the owning component.

Use realistic data types and field names. Do not produce placeholder schemas."""
