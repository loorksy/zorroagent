# Zorro VPS deploy (isolated)

This stack is **self-contained**. It must never share compose project names, host ports, nginx vhosts, or data directories with other apps on the same machine.

## Isolation contract

| Resource | Zorro uses | Must not touch |
|---|---|---|
| Directory | `/opt/zorroagent` | `/opt/aichart`, `/opt/leovee`, `/opt/wakeed-platform`, `/var/www/*` |
| Compose project | `-p zorroagent` | any other `docker compose` project |
| Containers | `zorroagent-postgres`, `zorroagent-redis`, `zorroagent-api`, `zorroagent-worker`, `zorroagent-web` | `chart-host`, `omniroute`, and anything else |
| Network | `zorroagent_net` | `leovee_gates`, `bridge` |
| Host ports | **8088** (public nginx) and **127.0.0.1:18088** (docker web, localhost only) | 80/443 (existing sites), 5432/6379 (host postgres/redis), 3010/3020/3780/8787/8791, docker 8788/20128 |
| Nginx | **new file** `/etc/nginx/sites-available/zorroagent.conf` | existing `aichart` / `erp` / `leovee` / `wakeed` vhosts |
| Secrets | `/opt/zorroagent/.env` | any other project's `.env` |

Postgres and Redis for Zorro stay on the **internal docker network**. Host 5432 and 6379 are left alone.

## Inventory before bind

On the target host:

```bash
ss -tlnp
docker ps --format '{{.Names}} {{.Ports}}'
ls /etc/nginx/sites-enabled
ls /opt
```

Suggested public port **8088** is in the 8080–8099 window. If it is taken, pick the next free port in that range and update `deploy/nginx.host.conf` plus this file.

## Files

- `deploy/docker-compose.vps.yml` — production compose (unique names, no DB/Redis publish)
- `deploy/nginx.host.conf` — host nginx site template (copy, do not merge)
- `frontend/Dockerfile.prod` + `frontend/nginx.conf` — SPA + `/api` `/health` `/healthz` `/ws` proxy
- `/opt/zorroagent/.env` — generated on the VPS; **never commit**

## Bring up (only this stack)

Always pass `--project-directory` so build contexts and `.env` resolve from `/opt/zorroagent` (not from `deploy/`).

```bash
cd /opt/zorroagent
# .env must already exist on the server (not in git)
docker compose -p zorroagent --project-directory /opt/zorroagent \
  -f /opt/zorroagent/deploy/docker-compose.vps.yml up -d --build
```

Enable the **new** nginx site (do not edit other vhosts):

```bash
cp deploy/nginx.host.conf /etc/nginx/sites-available/zorroagent.conf
ln -sfn /etc/nginx/sites-available/zorroagent.conf /etc/nginx/sites-enabled/zorroagent.conf
nginx -t && systemctl reload nginx
```

Optional TLS for the new names only (does not modify other certificates):

```bash
certbot --nginx -d zorro.lork.cloud -d zorroagent.lork.cloud
```

## URLs (this host)

Deployed 2026-08-27 on `srv1150752` (`72.60.83.140`), directory `/opt/zorroagent`.

**Ports were free before bind** (`ss -tlnp` showed nothing on 8080–8099 or 18088). Occupied ports left alone: 80/443 (nginx), 22, 3010, 3020, 3780, 8787, 8791, localhost 5432/6379/3000/8788/20128.

| Bind | Role |
|---|---|
| `0.0.0.0:8088` | **new** host nginx site `zorroagent.conf` only |
| `127.0.0.1:18088` | docker `zorroagent-web` (not public) |
| docker internal 5432 / 6379 | Zorro postgres/redis — **not published** |

- UI (TLS, new cert `zorro.lork.cloud` only): https://zorro.lork.cloud/ and https://zorroagent.lork.cloud/
- UI (dedicated unused port): http://72.60.83.140:8088/
- Health: `/healthz` and `/health` on those origins
- Bootstrap operator file on the VPS (mode 600, not in git): `/opt/zorroagent/.operator-bootstrap`

Trading keys are entered in **Settings → Providers** after first login. Bootstrap `.env` only needs database, redis, and encryption/JWT secrets.

First login creates the single operator (email + password you submit).

## Stop / start **only** Zorro

```bash
cd /opt/zorroagent
COMPOSE="docker compose -p zorroagent --project-directory /opt/zorroagent -f /opt/zorroagent/deploy/docker-compose.vps.yml"
$COMPOSE down     # stop Zorro only
$COMPOSE up -d    # start Zorro only
```

Do **not** run `docker compose down` without `-p zorroagent`. Do **not** `docker system prune`, volume prune, or stop other containers.

To remove the nginx site later (leave other sites):

```bash
rm -f /etc/nginx/sites-enabled/zorroagent.conf
nginx -t && systemctl reload nginx
```

## Health checks

```bash
docker ps --filter name=zorroagent
curl -sS http://127.0.0.1:18088/healthz
curl -sS http://127.0.0.1:8088/healthz
curl -sS -H 'Host: zorro.lork.cloud' http://127.0.0.1/healthz
curl -sS https://zorro.lork.cloud/healthz
```
