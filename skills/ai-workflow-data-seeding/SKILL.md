---
name: ai-workflow-data-seeding
description: Database seeding for AI-driven development workflows (DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT)
---

# Data Seeding for AI-Driven Development Workflows

## Trigger

Any task involving database seeding in an AI loop engineering context. Also applies to migrating seed data between projects with different database schemas or ORM versions.

## What This Skill Covers

1. **Seed script creation** for SQLAlchemy 2.0 async models
2. **Workflow integration** of seeding as a distinct phase in AI-driven development loops
3. **Data migration** between different project structures while preserving business logic
4. **Idempotent seeding** patterns that work across workflow iterations

## Key Patterns

### SQLAlchemy 2.0 Async Seeding

```python
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

async def seed_table(session: AsyncSession, table_cls, data: list[dict]):
    for row in data:
        stmt = insert(table_cls).values(**row)
        await session.execute(stmt)
    await session.commit()
```

### Idempotent Seeding

- Use `INSERT OR IGNORE` for SQLite: `db.dialect.supports_multivalues_insert = True`
- For UUID PKs: generate deterministic UUIDs based on content hash
- For INTEGER PKs: use sequence or explicit IDs with `ON CONFLICT DO NOTHING`

### Mixed Primary Key Types

- **INTEGER PKs**: `user`, `vehicle`, `dealership`, `order`, `test_drive_booking`
- **UUID PKs**: `customer`, `membership`, `hire`, `trade_in`, `service_record`, `review`, `notification`, `delivery`, `reward`, `maintenance_alert`, `support_ticket`, `faq`, `vehicle_image`, `vehicle_config`
- **FK relationships**: User (INT) → Customer (UUID) → other UUID-based tables

### Workflow Integration

Insert seeding as a phase between BUILD and VERIFY:

```
DEFINE → PLAN → BUILD → SEED_DATA → VERIFY → SHIP → REFLECT
```

The SEED_DATA node:
1. Generates/imports seed data
2. Executes against target database
3. Returns success/failure with row counts
4. Feeds into VERIFY for UAT against populated data

## Pitfalls

- **PG_UUID on SQLite**: SQLAlchemy's `PG_UUID(as_uuid=True)` creates `VARCHAR(36)` in SQLite - seed must provide string UUIDs, not Python UUID objects
- **Timezone handling**: `dt.replace(tzinfo=None)` required for SQLite naive datetime compatibility
- **Relationship cascade order**: Seed parent tables first (User → Customer → others), respect FK constraints
- **Static assets**: Vehicle images must be copied to `app/static/vehicles/` before seeding references them
- **Workflow state**: Seed node must update workflow state with actual row counts for VERIFY to validate

## Verification

After seeding, VERIFY should confirm:
- Expected row counts per table
- FK constraints satisfied (no orphaned records)
- API endpoints return populated data (not empty lists)
- Frontend renders seeded data correctly