# Running eudext_lk on Docker

Two ways to do this, depending on what you're after.

## Quick demo: single self-contained container

`docker/Dockerfile` builds one image with MariaDB, Redis, and a Frappe
bench (frappe + erpnext + hrms + eudext_lk) all inside it. Good for trying
the app out locally; not a production topology (see the next section for
that).

```bash
docker compose up -d --build
```

First boot creates the site (`eudext.local` by default) and installs
erpnext, hrms, and eudext_lk -- this takes a few minutes the first time.
MariaDB data and the site live in named volumes (`mariadb-data`,
`bench-sites`), so a second `docker compose up` reuses them instead of
recreating the site.

Then either add a hosts entry:

```bash
echo "127.0.0.1 eudext.local" | sudo tee -a /etc/hosts
```

and open `http://eudext.local:8000`, or just open `http://localhost:8000`
directly (Frappe's default multi-tenant routing needs the Host header to
match a site name, so `localhost` only works if you've set
`eudext.local` as the sole/default site, which `bench use` -- run for you
by the entrypoint -- takes care of).

Log in as `Administrator` / `admin` (override via the `ADMIN_PASSWORD`
environment variable in `docker-compose.yml` before first boot).

Override the site name, DB root password, or admin password by editing the
`environment:` block in `docker-compose.yml` before the first `up`.

To reset everything and start over:

```bash
docker compose down -v
```

## Production-style: frappe_docker (separate db/redis/backend/queue/frontend)

For anything beyond a local demo, use the official
[frappe_docker](https://github.com/frappe/frappe_docker) multi-container
setup with the `apps.json` at the root of this repo:

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

export APPS_JSON_BASE64=$(base64 -w 0 /path/to/eudext-erp/apps.json)

docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=eudext-erp:latest \
  --file=images/layered/Containerfile .
```

Then follow frappe_docker's own `compose.yaml` / `pwd.yml` instructions to
bring up `db`, `redis-cache`, `redis-queue`, `backend`, `websocket`,
`queue-short`, `queue-long`, `scheduler`, and `frontend` as separate
services pointed at `eudext-erp:latest`, and create the site with:

```bash
docker compose exec backend bench new-site eudext.local \
  --mariadb-root-password <password> --admin-password admin --no-mariadb-socket
docker compose exec backend bench --site eudext.local install-app erpnext hrms eudext_lk
```

frappe_docker's compose files change from time to time -- follow its own
`docs/` for the current service names/env vars rather than this file, this
section is just the `apps.json` wiring specific to this app.

## Running the tests inside a container

```bash
docker compose exec eudext-erp bench --site eudext.local set-config allow_tests true
docker compose exec eudext-erp bench --site eudext.local run-tests --app eudext_lk
```
