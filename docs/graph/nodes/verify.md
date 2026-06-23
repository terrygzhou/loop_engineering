# `graph/nodes/verify.py`

## Purpose
The VERIFY node runs comprehensive User Acceptance Testing (UAT) combining API checks, Playwright-based browser tests (desktop + mobile), and browser-tool fallback walkthroughs. Test coverage is derived dynamically from DISCOVER's route discovery and spec analysis — never hardcoded. It also conditionally runs performance optimization, systematic debugging, and code simplification based on guardrail thresholds.

## Public API

### Functions
#### `verify_node(state: dict) -> dict`
- **Parameters**: - `state` (dict): WorkflowState containing project_path, project_context, spec_refined, build_status, and metrics
- **Returns**: dict — updated WorkflowState with uat_results, perf_report, debug_report, simplified_code artifacts, metrics (uat_pass_rate, latency_ms, test_flakiness_rate), phase="VERIFY", next_phase="SHIP"
- **Behavior**: Executes the verification pipeline:
  1. **Load thresholds**: Reads `max_latency_ms`, `max_test_flakiness_rate`, and `max_review_revisions` from guardrails.yaml.
  2. **Dynamic route coverage**: Parses DISCOVER's project_context for API endpoints and page routes. Extracts edge cases from spec keywords.
  3. **UAT workflow**: Invokes `uat-workflow` skill with an 8-phase prompt: Playwright setup, Docker rebuild/health check (skipped if BUILD passed), bulk API sweep, template completeness check, pytest (skipped if BUILD passed), Playwright desktop UAT, Playwright mobile UAT, browser-tool fallback walkthrough, and final PASS/FAIL verdict.
  4. **Parse UAT metrics**: Extracts pass rate, latency, and flakiness from UAT output.
  5. **Conditional optimization**: Runs `performance-optimization` if latency exceeds threshold, `systematic-debugging` if flakiness exceeds threshold, `code-simplification` if review revisions exceed threshold.

#### `_parse_uat_metrics(uat_output: str) -> dict`
- **Parameters**: - `uat_output` (str): text output from the uat-workflow skill
- **Returns**: dict — `{"uat_pass_rate": float, "latency_ms": float, "test_flakiness_rate": float}`
- **Behavior**: Parses the UAT output text using regex to extract pass rate, latency (ms or seconds), and flakiness indicators (retry/retried/intermittent/flaky keywords). Returns conservative defaults (0.5, 0.0, 0.0) if unparseable.

#### `_parse_uat_pass_rate(uat_output: str) -> float`
- **Parameters**: - `uat_output` (str): text output from UAT
- **Returns**: float (0.0–1.0) — parsed pass rate
- **Behavior**: Tries multiple parsing strategies in priority order:
  1. Explicit "pass"/"fail" verdict keywords
  2. "X passed / Y failed" pattern
  3. "pass rate: X.XX" pattern
  4. Percentage notation (e.g., "85%")
  5. [PASS]/[FAIL] marker counts
  6. HTTP 200 vs 4xx/5xx status code counts
  - Defaults to 0.5 (conservative) if all strategies fail.

## Dependencies / Used By
- **Imports**: `os`, `re`, `json`, `tools.loader.build_skill_registry`, `tools.llm.invoke_skill`, `config.guardrails.get_threshold`
- **Used By**: `graph/main.py` (wires `verify_node` into LangGraph)

## Notes / Caveats
- **UAT pass rate gate**: Used by `graph/edges.py` — if below `min_uat_pass` threshold, loops back to BUILD.
- **Dynamic coverage**: Unlike hard-coded test suites, the UAT prompt is built from actual discovered routes, templates, and spec-derived edge cases.
- **Build status awareness**: If `build_status == "pass"`, skips Docker rebuild and pytest (already done in BUILD), saving time.
- **Performance/debug triggers**: Conditional skill invocations only fire when thresholds are breached, avoiding unnecessary overhead.
- **Flakiness heuristic**: Computed as retry count / total checks, with a fallback multiplier if no checks are detected.
- **Conservative defaults**: All metric parsers default to conservative/failing values (0.5 pass rate) when output is unparseable.
- **Playwright mandatory**: Both desktop and mobile UAT passes are marked MANDATORY in the prompt.
- **Screenshot capture**: Desktop screenshots go to `/tmp/uat_desktop_*.png`, mobile to `/tmp/uat_mobile_*.png`.
