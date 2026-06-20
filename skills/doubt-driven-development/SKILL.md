# doubt-driven-development

```yaml
name: doubt-driven-development
description: >
  Structured critical review of architectural decisions through the
  CLAIM → DOUBT → RECONCILE cycle. Before committing to any design
  decision, spawn a mental "devil's advocate" subagent to challenge
  assumptions. Prevents blind spots and groupthink in software
  architecture. Optimized for FastAPI + Jinja2 + Docker projects.
version: 1.0.0
author: hermes
triggers:
  - "architectural decision"
  - "design decision"
  - "should we"
  - "architecture review"
  - "doubt driven"
  - "critical review"
  - "challenge this"
  - "second opinion"
  - "design review"
tools:
  - read_file
  - write_file
  - search_files
  - patch
```

## Purpose

Every significant architectural decision should pass through a structured
challenge process: state the claim, subject it to doubt from a fresh
perspective, then reconcile into a stronger decision. This prevents
the most common cause of rework — decisions that looked good on paper
but fail under real-world conditions.

## Process

### 1. CLAIM — State the proposed decision

Articulate the decision clearly and concisely:

```
CLAIM: We should use SQLAlchemy ORM for database access in the FastAPI
service instead of raw SQL or asyncpg directly.

REASONING: It provides type safety, migrations via Alembic, and
integrates cleanly with Pydantic models for request/response validation.
```

The claim must include:
- What you propose
- Why you propose it (the positive case)
- The alternatives considered

### 2. DOUBT — Challenge from a fresh perspective

Adopt the role of a skeptical reviewer who has **no investment** in the
proposed decision. Ask hard questions:

**Attack categories for the doubt phase:**

| Category | Questions to ask |
|---|---|
| **Complexity** | Does this add more complexity than it solves? What's the cognitive load? |
| **Performance** | Does this introduce N+1 queries, serialization overhead, or memory pressure? |
| **Flexibility** | Does this lock us into a technology? What if we need raw SQL later? |
| **Security** | Does this introduce injection risks, data leaks, or privilege escalation? |
| **Operational** | Does this complicate Docker deployments, monitoring, or debugging? |
| **Alternative** | Is there a simpler approach that covers 90% of use cases? |
| **Team** | Does the team have experience with this? What's the learning curve? |
| **Edge cases** | What happens with large datasets, concurrent access, or partial failures? |

Example doubt:

```
DOUBT: SQLAlchemy ORM adds a significant abstraction layer. For a
FastAPI service that primarily does CRUD operations with well-defined
schemas, raw asyncpg or SQLAlchemy Core might be simpler, faster, and
easier to debug. The ORM's lazy loading can cause N+1 query problems
in list endpoints, and the abstraction can make it harder to reason
about actual SQL queries during performance tuning.
```

### 3. RECONCILE — Resolve and commit

Synthesize the claim and doubt into a final decision:

```
RECONCILE: We'll use SQLAlchemy Core (not ORM) with Alembic migrations.
This gives us type safety and migration management without the
overhead and hidden complexity of the ORM. For the 20% of cases where
we need complex joins, we'll write explicit SQL. We'll add a
repository layer to abstract the database backend.

MITIGATION: We'll add query logging in development to catch N+1 issues
early, and define a strict interface for the repository layer.
```

The reconciliation must include:
- The final decision
- Any modifications to the original claim
- Specific mitigations for the doubts raised
- Explicit acceptance of any remaining risks

## Application to FastAPI + Jinja2 + Docker

Common decision points that benefit from doubt-driven development:

- **Database choice** — PostgreSQL vs. SQLite vs. no database
- **Authentication** — JWT vs. session-based vs. OAuth
- **Template strategy** — Jinja2 vs. returning JSON for a frontend
- **Docker structure** — Single image vs. multi-stage build vs. compose
- **Caching layer** — In-memory dict vs. Redis vs. no caching
- **Task queue** — Background tasks vs. Celery vs. simple cron
- **Configuration** — Environment variables vs. config files vs. both

## Pitfalls

- **Don't doubt for doubt's sake.** The doubt phase must be constructive
  — every challenge should propose a counter-argument or alternative,
  not just say "this is bad."
- **Don't get stuck in analysis paralysis.** Limit the cycle to
  1–2 iterations. If you can't resolve a doubt after two rounds,
  accept the risk and move forward with a note.
- **Don't skip small decisions.** The process is lightweight enough for
  any decision — the key is discipline, not formality.
- **Don't let doubt become dogma.** The doubt phase is a challenge, not
  a veto. The reconciler makes the final call.
- **Don't pretend all alternatives are equal.** Acknowledge trade-offs
  honestly rather than creating false equivalences.

## Verification

- The claim was stated clearly with reasoning.
- At least 3 distinct doubt categories were addressed.
- The reconciliation includes specific mitigations.
- Remaining risks are documented and accepted.
- The decision can be reversed later without catastrophic cost.
