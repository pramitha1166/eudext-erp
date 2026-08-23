# Self-contained image: MariaDB + Redis + Frappe bench (frappe, erpnext,
# hrms, eudext_lk) all in one container. Meant for a quick local demo of
# eudext_lk, not as a production topology (a real deployment should split
# db/redis/backend/queue/websocket into separate containers -- see
# frappe_docker: https://github.com/frappe/frappe_docker, using the
# apps.json at the repo root).

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
	PATH="/home/frappe/.local/bin:/home/frappe/frappe-bench/env/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
		git curl wget sudo cron gnupg2 ca-certificates \
		python3.11 python3.11-venv python3-pip \
		mariadb-server mariadb-client \
		redis-server \
		wkhtmltopdf \
		build-essential libmysqlclient-dev pkg-config \
	&& curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
	&& apt-get install -y --no-install-recommends nodejs \
	&& npm install -g yarn \
	&& rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash frappe \
	&& echo "frappe ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/frappe \
	&& chmod 0440 /etc/sudoers.d/frappe \
	&& mkdir -p /var/lib/mysql /var/run/mysqld \
	&& chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

COPY docker/50-frappe-charset.cnf /etc/mysql/mariadb.conf.d/50-frappe-charset.cnf

USER frappe
WORKDIR /home/frappe

RUN pip install --user --no-cache-dir frappe-bench

# --- Build the bench with frappe, erpnext, hrms, and eudext_lk ----------
ARG FRAPPE_BRANCH=version-15
ARG EUDEXT_LK_REPO=https://github.com/pramitha1166/eudext-erp
ARG EUDEXT_LK_BRANCH=claude/eudext-lk-frappe-scaffold-0ku9yk

RUN bench init frappe-bench \
		--frappe-branch ${FRAPPE_BRANCH} \
		--python python3.11 \
		--no-backups \
	&& cd frappe-bench \
	&& bench get-app erpnext --branch ${FRAPPE_BRANCH} \
	&& bench get-app hrms --branch ${FRAPPE_BRANCH} \
	&& bench get-app eudext_lk ${EUDEXT_LK_REPO} --branch ${EUDEXT_LK_BRANCH}

WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe docker/docker-entrypoint.sh /home/frappe/docker-entrypoint.sh
USER root
RUN chmod +x /home/frappe/docker-entrypoint.sh
USER frappe

EXPOSE 8000

ENTRYPOINT ["/home/frappe/docker-entrypoint.sh"]
CMD ["bench", "start"]
