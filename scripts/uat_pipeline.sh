#!/usr/bin/env bash
# UAT Pipeline — automated workflow execution, bug tracking, and fix dispatch
# Run via cron every 2 hours: 0 */2 * * *
set -euo pipefail

LOG_DIR="${LOG_DIR:-logs}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$LOG_DIR/uat_pipeline_${TIMESTAMP}.log"
PROJECT="${PROJECT:-My_test_CRM}"
PROJECT_DIR="${PROJECT_DIR:-./mvp_output}"
WEBAPP_URL="http://localhost:8011"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "========================================"
log "UAT Pipeline started — $TIMESTAMP"
log "========================================"

# ── 1. Health Check ──────────────────────────────────────────────────
log "→ Health check: frontend-ui container"
if ! docker ps --format '{{.Names}}' | grep -q frontend-ui; then
  log "ERROR: frontend-ui not running — skipping run"
  exit 1
fi

STATUS=$(curl -sf "$WEBAPP_URL/api/status" 2>/dev/null || echo "unreachable")
if [ -z "$STATUS" ]; then
  log "ERROR: /api/status unreachable — skipping run"
  exit 1
fi

CURRENT_PHASE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('phase','unknown'))" 2>/dev/null)
CURRENT_STATUS=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
log "Current state: status=$CURRENT_STATUS phase=$CURRENT_PHASE"

# ── 2. Start Workflow if Idle ────────────────────────────────────────
if [ "$CURRENT_STATUS" = "idle" ] || [ "$CURRENT_STATUS" = "complete" ]; then
  log "→ Workflow idle — starting new workflow"

  # Start workflow via POST /api/start
  START_RESPONSE=$(curl -sf -X POST "$WEBAPP_URL/api/start" \
    -H "Content-Type: application/json" \
    -d "$(cat <<EOF
{
  "project_name": "$PROJECT",
  "description": "App for managing contacts/customers — contact details, emails, and meeting appointments synced with Google Calendar",
  "features": [
    "Create, update contacts",
    "Receive emails and associate with contacts",
    "Make appointments with groups of contacts"
  ],
  "entities": {
    "Contact": ["Contact_ID", "first_name", "last_name", "email", "mobile", "address", "sex", "date_of_birth", "interests"],
    "Email": ["sent_by", "contact_ID", "receive_date", "headline", "content"],
    "Appointment": ["eventID", "event_name", "date", "time", "venue", "online_link"]
  },
  "apis": [
    "CRUD APIs for contacts",
    "CRUD APIs for emails per customer",
    "CRUD APIs for appointment booking to Google Calendar"
  ]
}
EOF
)" 2>/dev/null || echo "failed")

  log "Start response: $START_RESPONSE"
  log "Waiting 10s for workflow to initialize..."
  sleep 10
fi

# ── 3. Monitor Execution ─────────────────────────────────────────────
log "→ Monitoring workflow execution..."
MAX_WAIT=1200   # 20 minutes max (covers full workflow cycle)
ELAPSED=0
POLL_INTERVAL=15
PHASE_LOG="$LOG_DIR/phase_log_${TIMESTAMP}.json"

while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS=$(curl -sf "$WEBAPP_URL/api/status" 2>/dev/null || echo '{"status":"unknown"}')
  STATUS_VAL=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
  PHASE_VAL=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('phase','—'))" 2>/dev/null)
  CYCLE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cycle',0))" 2>/dev/null)

  log "  status=$STATUS_VAL phase=$PHASE_VAL cycle=$CYCLE (elapsed: ${ELAPSED}s)"

  if [ "$STATUS_VAL" = "complete" ]; then
    log "✓ Workflow completed successfully"
    break
  fi

  if [ "$STATUS_VAL" = "error" ] || [ "$STATUS_VAL" = "failed" ]; then
    log "✗ Workflow failed with status: $STATUS_VAL"
    break
  fi

  # Check for stuck phase (>300s in same phase)
  PHASE_STARTED=$(echo "$STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
phases=d.get('phases',{})
for k,v in phases.items():
  if v.get('status')=='running':
    print(v.get('startedAt',''))
" 2>/dev/null)

  if [ -n "$PHASE_STARTED" ]; then
    PHASE_EPOCH=$(date -d "$PHASE_STARTED" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    if [ $((NOW_EPOCH - PHASE_EPOCH)) -gt 300 ]; then
      log "⚠ Phase $PHASE_VAL stuck for >300s — flagging"
    fi
  fi

  sleep $POLL_INTERVAL
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

# Save final status
echo "$STATUS" > "$PHASE_LOG"

# ── 4. Extract Container Logs ────────────────────────────────────────
log "→ Capturing container logs..."
CONTAINER_LOG="$LOG_DIR/container_${TIMESTAMP}.log"
docker logs frontend-ui --tail 500 --since 30m > "$CONTAINER_LOG" 2>&1

# ── 5. Generate Backlog ──────────────────────────────────────────────
log "→ Generating backlog..."
BACKLOG="$PROJECT_DIR/build/backlog.md"
mkdir -p "$PROJECT_DIR/build"

# Extract errors and warnings from logs
ERROR_COUNT=$(grep -ci 'error\|exception\|traceback' "$CONTAINER_LOG" 2>/dev/null || echo 0)
WARN_COUNT=$(grep -ci 'warning\|warn' "$CONTAINER_LOG" 2>/dev/null || echo 0)
PHASE_COUNT=$(echo "$STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
phases=d.get('phases',{})
completed=sum(1 for v in phases.values() if v.get('status')=='complete')
print(completed)
" 2>/dev/null || echo 0)

cat > "$BACKLOG" <<BACKLOG_EOF
# Backlog — $PROJECT ($TIMESTAMP)

## Workflow Status
- Final status: $STATUS_VAL
- Phases completed: $PHASE_COUNT
- Errors in logs: $ERROR_COUNT
- Warnings in logs: $WARN_COUNT

## Issues Found
BACKLOG_EOF

# Parse specific errors from logs
grep -i 'error\|exception\|failed\|crash' "$CONTAINER_LOG" 2>/dev/null | \
  tail -20 | while read -r line; do
    echo "- $line" >> "$BACKLOG"
done

cat >> "$BACKLOG" <<BACKLOG_EOF

## Fix Status
| # | Status | Agent | Notes |
|---|--------|-------|-------|

## Observations
- Pipeline run: $TIMESTAMP
- Log file: $CONTAINER_LOG
- Phase log: $PHASE_LOG
BACKLOG_EOF

log "→ Backlog written to $BACKLOG"

# ── 6. Summary ───────────────────────────────────────────────────────
log "========================================"
log "UAT Pipeline completed — $TIMESTAMP"
log "  Status: $STATUS_VAL"
log "  Phases completed: $PHASE_COUNT"
log "  Errors: $ERROR_COUNT | Warnings: $WARN_COUNT"
log "  Backlog: $BACKLOG"
log "  Logs: $CONTAINER_LOG"
log "========================================"
