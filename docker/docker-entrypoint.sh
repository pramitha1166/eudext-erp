#!/bin/bash
set -e

SITE_NAME="${SITE_NAME:-eudext.local}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
BENCH_DIR=/home/frappe/frappe-bench

# --- MariaDB ---------------------------------------------------------
if [ ! -d /var/lib/mysql/mysql ]; then
	sudo mariadb-install-db --user=mysql --datadir=/var/lib/mysql >/dev/null
fi
sudo chown -R mysql:mysql /var/lib/mysql /var/run/mysqld
sudo -u mysql mysqld_safe --datadir=/var/lib/mysql &

until mysqladmin ping --silent 2>/dev/null; do
	echo "Waiting for MariaDB..."
	sleep 2
done

# Only meaningful on a fresh datadir; harmless (and ignored) once the
# root password is already set on subsequent starts of a persisted volume.
mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('${DB_ROOT_PASSWORD}'); FLUSH PRIVILEGES;" 2>/dev/null || true

# --- Redis: one server, two logical DBs (cache vs queue) --------------
redis-server --daemonize yes --port 6379

until redis-cli -p 6379 ping >/dev/null 2>&1; do
	echo "Waiting for Redis..."
	sleep 1
done

cd "$BENCH_DIR"
bench set-config -g db_host 127.0.0.1
bench set-config -g redis_cache "redis://127.0.0.1:6379/0"
bench set-config -g redis_queue "redis://127.0.0.1:6379/1"
bench set-config -g redis_socketio "redis://127.0.0.1:6379/1"

# --- Site: create once, reuse thereafter (persist sites/ in a volume) -
if [ ! -d "sites/${SITE_NAME}" ]; then
	echo "Creating site ${SITE_NAME}..."
	bench new-site "${SITE_NAME}" \
		--mariadb-root-password "${DB_ROOT_PASSWORD}" \
		--admin-password "${ADMIN_PASSWORD}" \
		--no-mariadb-socket
	bench --site "${SITE_NAME}" install-app erpnext hrms eudext_lk
fi

bench use "${SITE_NAME}"

exec "$@"
