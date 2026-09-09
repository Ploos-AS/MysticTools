# MysticTools exporter deployment

M4.3 packages the read-only HTTP exporter for practical Linux and OCI deployment. The exporter exposes only `GET /metrics` and `GET /healthz`; mutating HTTP methods remain disabled by the exporter itself.

## systemd

The example unit lives at `deploy/systemd/mystictools-exporter.service` and assumes:

- Mystic root: `/opt/mystic`
- Mystic service user/group: `mystic:mystic`
- exporter binary: `/usr/local/bin/mysticexporter`
- listener: `127.0.0.1:9108`

Install and enable it with the normal systemd workflow after adapting paths/user for the actual Mystic installation. The example applies `NoNewPrivileges`, strict filesystem protection, kernel/control-group protections, namespace restrictions, `UMask=0077`, and a read-only Mystic root.

Keep the exporter bound to loopback when Prometheus runs on the same host. If remote scraping is required, explicitly change the bind address and protect access with host firewalling or a trusted reverse proxy/network boundary.

## Prometheus

`deploy/prometheus/prometheus.yml` contains a minimal scrape job for `127.0.0.1:9108` with a 15-second interval.

## OCI / Docker Compose

Build locally:

```sh
docker build -t mystictools-exporter:local .
```

Run the supplied Compose definition:

```sh
MYSTIC_ROOT=/opt/mystic docker compose -f compose.exporter.yaml up -d --build
```

The Compose deployment deliberately uses:

- read-only container root filesystem
- read-only Mystic bind mount
- all Linux capabilities dropped
- `no-new-privileges`
- host port published only on `127.0.0.1:9108`
- Linux host PID namespace (`pid: host`)

The host PID namespace is required because MysticTools runtime discovery reads Linux procfs to identify MIS and Mystic node processes. Without host PID visibility, filesystem metrics still work but runtime/process metrics describe the container rather than the Mystic host and are therefore incomplete.

The image itself runs as a non-root user. That user must have read permission on the mounted Mystic tree. If the host installation is not world/group-readable, run the container with a suitable numeric UID/GID or grant a narrowly scoped read permission; do not make the Mystic installation broadly writable for the exporter.

## Security boundary

The exporter is observability-only. M4.3 does not expose backup, restore, rollback, cleanup, shell execution, Mystic configuration changes, or any HTTP write API. TLS and authentication are intentionally left to a reverse proxy or trusted monitoring network rather than being implemented in the exporter.
