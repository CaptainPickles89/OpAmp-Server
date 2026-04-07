# OpAMP Server Operations Runbook

Operational procedures for deploying, monitoring, and troubleshooting the OpAMP Server in production.

## Table of Contents

1. [Deployment](#deployment)
2. [Health Checks](#health-checks)
3. [Monitoring](#monitoring)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)
6. [Recovery Procedures](#recovery-procedures)

## Deployment

### Prerequisites

- Docker Engine 20.10+ with Compose support
- 1GB+ available disk space for data volume
- Network access for collectors on port 8080 (HTTP)
- For rootless containers: use port 8080 (not 80)

### Quick Start

```bash
# Clone repository and navigate
git clone <repository>
cd opamp-server

# Start stack
docker compose up -d --build

# Verify all services healthy
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f ui
docker compose logs -f collector
```

### Environment Configuration

Create a `.env` file in the repository root to override defaults:

```bash
# .env — Backend configuration
OPAMP_HOST=0.0.0.0
OPAMP_PORT=8000
OPAMP_DB_PATH=/app/data/registry.db
OPAMP_LOG_LEVEL=INFO
OPAMP_RATE_LIMIT=100/minute
OPAMP_COLLECTOR_TTL_HOURS=24
OPAMP_PURGE_INTERVAL_HOURS=1
```

The `docker compose` command automatically loads `.env` variables into the containers.

### Customizing the Stack

**Change UI port:**
```yaml
# compose.yaml
ui:
  ports:
    - "80:80"  # Change 8080 to 80 if using privileged Docker
```

**Use a different database path:**
```bash
OPAMP_DB_PATH=/mnt/persistent-storage/registry.db docker compose up
```

**Run example collector separately:**
```bash
# Start only api and ui
docker compose up -d api ui

# Start collector after connecting to different server
docker run -e OPAMP_SERVER=http://other-server:8000 ...
```

### Data Persistence

SQLite data is stored in a named Docker volume:

```bash
# List volumes
docker volume ls | grep opamp

# Inspect volume location
docker volume inspect opamp-data

# Backup data
docker run --rm -v opamp-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/registry-$(date +%s).tar.gz -C /data .

# Restore from backup
docker volume rm opamp-data
docker volume create opamp-data
docker run --rm -v opamp-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/registry-*.tar.gz -C /data
```

## Health Checks

<!-- AUTO-GENERATED: Health check procedures from compose.yaml -->

### API Service Health

The API service exposes a health check endpoint:

```bash
# Check API directly
curl http://localhost:8000/api/v1/collectors

# Expected response (200 OK):
{
  "data": [
    {
      "instance_uid": "...",
      "last_seen": 1234567890,
      "health_status": "healthy",
      "capabilities": 0,
      "resource_attributes": {}
    }
  ],
  "error": null
}
```

**Docker Compose health check:**
The API service includes a built-in health check:
- Test: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/collectors')"`
- Interval: 5 seconds
- Timeout: 3 seconds
- Retries: 5
- Start period: 10 seconds

View health status:
```bash
docker compose ps  # Shows STATUS (healthy/unhealthy/starting)
```

### UI Service Health

```bash
# Check UI is serving (should return 200 with HTML)
curl -I http://localhost:8080

# Check API proxy works
curl http://localhost:8080/api/v1/collectors
```

### Collector Connection

Collectors connect via the OpAMP endpoint at `/v1/opamp`:

```bash
# Check collector logs for connection attempts
docker compose logs -f collector

# Expected logs:
# collector_1  | time=... level=info msg="connected to server" address=...
```

If no collectors appear in the UI after 10 seconds, check:
1. Collector logs: `docker compose logs collector`
2. API logs: `docker compose logs api`
3. Network connectivity: `docker compose network ls`

<!-- END AUTO-GENERATED -->

## Monitoring

### Metrics & Logs

**API Logs:**
```bash
docker compose logs -f api

# Filter for errors
docker compose logs api 2>&1 | grep ERROR

# Filter for specific collector
docker compose logs api 2>&1 | grep "collector-id"
```

**Structured Logging:**
The backend uses `structlog` for JSON-formatted logs (in production). Set `OPAMP_LOG_LEVEL` for verbosity:
- `DEBUG` — Protocol details, every request
- `INFO` — Key events (collector connections, config pushes)
- `WARNING` — Recoverable issues
- `ERROR` — Failures

**Database State:**
```bash
# Check database size
docker run --rm -v opamp-data:/data alpine du -sh /data

# Query collector count
docker exec <api-container> sqlite3 /app/data/registry.db \
  "SELECT COUNT(*) as total_collectors FROM agents;"

# Check oldest/newest collectors
docker exec <api-container> sqlite3 /app/data/registry.db \
  "SELECT instance_uid, first_seen, last_seen FROM agents ORDER BY first_seen LIMIT 5;"
```

### Key Metrics to Watch

| Metric | Normal | Action |
|--------|--------|--------|
| API response time | <100ms | Investigate slow DB queries |
| Database size | <100MB (default retention) | Purge if >1GB |
| Collectors connected | Varies | Check health checks if 0 |
| Failed config pushes | 0% | Check collector logs |
| API error rate (4xx/5xx) | <1% | Review logs for spikes |

### Alerting (Optional)

To set up alerting with your monitoring stack:

**Prometheus scrape example:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: opamp-api
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'  # (not implemented yet; custom endpoint needed)
```

For now, monitor via:
- Docker health status: `docker compose ps`
- Log aggregation: pipe `docker compose logs` to your SIEM
- Custom polling: `curl /api/v1/collectors` in a monitoring script

## Troubleshooting

### Collector Not Appearing in UI

**Symptoms:**
- UI shows 0 collectors
- Collector service is running

**Diagnosis:**
```bash
# 1. Check collector logs
docker compose logs collector | tail -20

# 2. Check if API is reachable from collector network
docker compose exec collector \
  curl -v http://api:8000/api/v1/collectors

# 3. Check API logs for connection errors
docker compose logs api | grep collector
```

**Solutions:**
- **DNS resolution fails**: Ensure `api` service is healthy: `docker compose ps api`
- **Connection refused**: API not listening on port 8000; check `OPAMP_PORT` env var
- **Server rejects message**: Check collector config in `collector/config.compose.yaml` — ensure correct OpAMP endpoint path `/v1/opamp`

### API Service Won't Start

**Symptoms:**
- `docker compose up` exits with error
- `docker compose ps` shows API status `Exited(1)`

**Diagnosis:**
```bash
# View full error
docker compose logs api

# Common errors:
# "Address already in use" — port 8000 in use by another process
# "Permission denied" — database path not writable
# "No module named" — missing Python dependency
```

**Solutions:**
- **Port conflict**: Stop other services or change `OPAMP_PORT`
  ```bash
  lsof -i :8000  # Find what's using port 8000
  ```
- **Database permission**: Ensure data volume is writable
  ```bash
  docker run --rm -v opamp-data:/data alpine ls -la /data
  ```
- **Rebuild**: Force rebuild to refresh dependencies
  ```bash
  docker compose down
  docker compose build --no-cache api
  docker compose up -d api
  ```

### Config Push Fails

**Symptoms:**
- UI shows push status "Failed" with auto-rollback
- Collector doesn't apply new config

**Diagnosis:**
```bash
# Check collector logs for why it rejected config
docker compose logs collector | grep -i "config\|error"

# Check API logs for push state
docker compose logs api | grep "config_push"

# Check what config is stored in database
docker exec <api-container> sqlite3 /app/data/registry.db \
  "SELECT config_json FROM effective_configs \
   WHERE agent_id = 'your-collector-id' \
   ORDER BY recorded_at DESC LIMIT 1;"
```

**Solutions:**
- **Invalid YAML syntax**: Ensure config editor shows valid YAML (CodeMirror should highlight errors)
- **Collector doesn't support config**: Some OTel receivers don't support hot-reload; check collector capabilities
- **Config too large**: Check `OPAMP_MAX_BODY_SIZE` (default 1MB)
  ```bash
  # Increase if needed
  OPAMP_MAX_BODY_SIZE=5242880 docker compose up api
  ```

### Database Corruption or Disk Full

**Symptoms:**
- API returns 500 errors sporadically
- `docker compose logs api` shows "disk I/O error" or "database disk image malformed"

**Diagnosis:**
```bash
# Check disk space
docker volume inspect opamp-data  # Note mount point
df -h /path/to/volume

# Check database integrity
docker exec <api-container> sqlite3 /app/data/registry.db "PRAGMA integrity_check;"
```

**Recovery:**
```bash
# If disk full: purge old data or expand volume storage

# If corrupted: backup existing data, rebuild database
docker compose down
docker volume create opamp-data-new
# (Manually migrate data if needed from backup)
docker volume rm opamp-data
docker volume rename opamp-data-new opamp-data
docker compose up -d

# If backup exists: restore from backup (see Data Persistence section)
```

### High Memory or CPU Usage

**Symptoms:**
- `docker compose stats` shows API using >500MB memory
- Server becomes slow/unresponsive

**Diagnosis:**
```bash
# Monitor resource usage
docker compose stats api

# Check what's in memory
docker exec <api-container> python -m tracemalloc

# Database size growing unbounded?
docker exec <api-container> sqlite3 /app/data/registry.db \
  "SELECT COUNT(*) FROM health_snapshots;"
```

**Solutions:**
- **Too many health snapshots**: Reduce `OPAMP_HEALTH_SNAPSHOT_RETENTION` (default 1000 per collector)
  ```bash
  OPAMP_HEALTH_SNAPSHOT_RETENTION=100 docker compose up
  ```
- **Old collector data**: Run TTL purge more frequently or reduce `OPAMP_COLLECTOR_TTL_HOURS`
  ```bash
  OPAMP_PURGE_INTERVAL_HOURS=1 docker compose up  # Purge hourly instead of default
  ```
- **Database not vacuumed**: Force cleanup
  ```bash
  docker exec <api-container> sqlite3 /app/data/registry.db "VACUUM;"
  ```

## Maintenance

### Regular Tasks

#### Daily
- Monitor logs for errors: `docker compose logs --tail 100 api`
- Spot-check API response time: `curl -w "@curl-format.txt" http://localhost:8000/api/v1/collectors`

#### Weekly
- Database size: `docker run --rm -v opamp-data:/data alpine du -sh /data`
- Collector count and stale collectors: See Database State queries above
- Verify backups (if using): Check backup file timestamps

#### Monthly
- Review and clean old data if TTL-based purge isn't enabled
- Test disaster recovery: Restore from backup to verify integrity
- Update Docker images: `docker compose pull && docker compose up -d --build`

### Database Maintenance

**Vacuum database (optimize storage):**
```bash
docker exec <api-container> sqlite3 /app/data/registry.db "VACUUM;"
```

**Analyze tables (optimize queries):**
```bash
docker exec <api-container> sqlite3 /app/data/registry.db "ANALYZE;"
```

**Export data for analysis:**
```bash
docker exec <api-container> sqlite3 /app/data/registry.db \
  ".mode csv" \
  ".output collectors.csv" \
  "SELECT * FROM agents;"
```

### Collector TTL & Auto-Purge

The server automatically removes collectors that haven't reported in > `OPAMP_COLLECTOR_TTL_HOURS` (default 24 hours).

The cleanup runs every `OPAMP_PURGE_INTERVAL_HOURS` (default 1 hour).

**Check TTL settings:**
```bash
docker compose exec api python -c \
  "from opamp_server.config import settings; \
   print(f'TTL: {settings.collector_ttl_hours}h, Purge interval: {settings.purge_interval_hours}h')"
```

**Disable auto-purge (NOT recommended):**
```bash
# Set TTL very high so purge never triggers
OPAMP_COLLECTOR_TTL_HOURS=87600 docker compose up  # ~10 years
```

## Recovery Procedures

### Graceful Shutdown

```bash
docker compose stop  # Stops all services (30s grace period)
# OR
docker compose down  # Stops and removes containers (preserves volumes)
```

### Restart Without Data Loss

```bash
docker compose restart api

# Or full stack restart
docker compose down
docker compose up -d
```

### Restore from Backup

See "Data Persistence" section under Deployment.

### Rebuild from Scratch

```bash
# WARNING: This deletes all collector history and configs!

docker compose down -v                    # Remove all volumes
docker compose up -d --build              # Rebuild and start fresh
```

### Emergency Contact / Escalation

For production incidents:
1. Check this runbook's troubleshooting section
2. Collect logs: `docker compose logs > logs.txt`
3. Capture database state: `docker exec <container> sqlite3 /app/data/registry.db ".schema"`
4. Contact the OpAMP Server team with logs and configuration

---

**Last Updated:** 2026-04-07

**Related Documentation:**
- [CONTRIBUTING.md](CONTRIBUTING.md) — Development setup and contributing guide
- [README.md](../README.md) — Quick start and usage overview
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/03-compose-file/) — Detailed compose configuration options
