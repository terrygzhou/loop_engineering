# Loop Factory — Agent Instructions

## Skill Loading

Before any coding task, load and follow:
```
skill_view(name='coding-principles')
```

When things break, load:
```
skill_view(name='systematic-debugging')
```

When tasks span 3+ files, load:
```
skill_view(name='subagent-driven-development')
```

## Project Layout

```
loop_factory/
├── main.py              # CLI entry (Option B)
├── app/                # Web UI (FastAPI, :8011)
├── skills/              # Project-local skills (29 SKILL.md)
├── docker-compose.yml  # Stack (API + DB)
└── mvp_output/          # Deploy target
```

## Key Constraints

- Docker compose: `docker compose up -d --build api` (no bind mounts)
- DB: `loop_eng` on PostgreSQL container
- CLI auto-approves; Web UI is HIL (Human-in-the-Loop)
- Artifacts land in `~/workspace/projects/`
