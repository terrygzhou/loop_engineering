---
name: interview-me
description: >
  Elicit requirements from the user one question at a time until
  reaching 95% spec confidence. Activates when a user says "build me X"
  or provides a vague feature request without enough context to start
  implementation. Ideal for FastAPI backend services, Jinja2 templates,
  and Docker-based deployments.
version: 1.0.0
author: hermes
triggers:
  - "build me"
  - "I want to create"
  - "make a"
  - "develop"
  - "build"
  - "create"
  - "new project"
  - "new feature"
  - "implement"
tools:
  - read_file
  - write_file
  - search_files
  - patch
---

# interview-me

## Purpose

When a user requests a new feature or project with insufficient detail,
this skill drives a structured interview to gather all necessary
requirements **one question at a time** before any code is written.
The goal is 95% spec confidence — meaning you can implement the feature
with minimal follow-up clarification.

## Process

### 1. Assess initial confidence

Read the user's request. Estimate your current confidence level (0–95%)
in understanding what needs to be built. If confidence is already ≥95%,
skip the interview and proceed to implementation.

### 2. Set the interview frame

Tell the user: *"I want to make sure I build exactly what you need. Let
me ask a few questions — I'll ask them one at a time so we can iterate
on each point."*

### 3. Ask questions one at a time

Follow this priority order for FastAPI + Jinja2 + Docker projects:

1. **Core behavior** — What does this feature do? What are the inputs
   and outputs? What are the success and failure paths?
2. **Data model** — What entities are involved? What fields do they
   have? Are there relationships to existing models?
3. **API surface** — What HTTP methods, paths, and parameters? Any
   authentication/authorization requirements?
4. **Validation** — What input validation rules? What error responses?
5. **UI/Template** — Are there Jinja2 templates involved? What data
   do they display? Any styling or component requirements?
6. **Integration** — Does this feature interact with other services,
   databases, or external APIs?
7. **Deployment** — Any Docker or infrastructure implications?
   Environment variables, volumes, or network configuration?
8. **Edge cases** — What are the known edge cases? What should happen
   with invalid input, missing data, or rate limits?
9. **Non-functional** — Performance targets, security requirements,
   logging/monitoring needs?

### 4. Summarize and confirm

After each answer, briefly restate your understanding before moving to
the next question. This catches miscommunications early.

### 5. Close at 95% confidence

When you've reached ≥95% confidence, provide a concise summary of the
full spec and ask for final confirmation:

*"Here's what I understand. Shall I start building?"*

If the user says "yes" or provides corrections, incorporate them and
proceed.

## Pitfalls

- **Don't ask multiple questions in one message.** One question, one
  message. Batched questions overwhelm users and produce incomplete
  answers.
- **Don't skip to coding.** Even if you feel 70% confident, ask the
  remaining questions. The cost of rework far exceeds the cost of
  clarification.
- **Don't assume defaults silently.** If you're going to assume a
  database type, framework version, or design pattern, state it
  explicitly and get confirmation.
- **Don't ignore follow-up corrections.** If the user corrects
  something from an earlier question, update your mental model and
  check if it affects other decisions.
- **Don't interview for the sake of interviewing.** If the user's
  request is already detailed enough, acknowledge that and move on.

## Verification

- The user confirms the spec with a "yes" or equivalent.
- You can list the key API endpoints, data models, and expected
  behaviors without guessing.
- No major architectural decisions are left unresolved.
- The interview took roughly 3–10 questions (adjust based on feature
  complexity).
