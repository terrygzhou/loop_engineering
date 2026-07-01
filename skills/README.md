# Skills

Self-contained skills for the loop_factory workflow. Each directory contains a `SKILL.md` with YAML frontmatter and markdown body.

## Skills by Phase

| Phase | Skills |
|-------|--------|
| DEFINE | interview-me, speckit-specify, api-and-interface-design |
| PLAN | writing-plans, speckit-tasks, speckit-analyze, doubt-driven-development, speckit-checklist |
| BUILD | incremental-implementation, fastapi-jinja2-feature-build, test-driven-development, security-and-hardening, requesting-code-review |
| SEED_DATA | ai-workflow-data-seeding |
| VERIFY | uat-workflow, performance-optimization, systematic-debugging, code-simplification |
| SHIP | observability-and-instrumentation, shipping-and-launch, docker-compose-deployment, git-workflow |

## Usage

Point the workflow to this directory for self-contained operation:

```bash
export SKILLS_DIR="$(pwd)/skills"
python main.py run --spec path/to/spec --project path/to/project
```

Or set the default in `config/guardrails.yaml`:
```yaml
skills:
  dir: ./skills
```
