# M4.2 HTTP Prometheus exporter

MysticTools includes a dependency-free, read-only HTTP exporter for the existing Prometheus metrics contract.

## Commands

Standalone:

```sh
mysticexporter --root /srv/mystic
```

Umbrella CLI:

```sh
mystictools --root /srv/mystic exporter
```

Defaults:

- bind: `127.0.0.1`
- port: `9108`

Use `--bind` and `--port` to override them. Loopback is the default so installing MysticTools does not make observability data remotely reachable by accident.

## Endpoints

### `/metrics`

Returns the current MysticTools Prometheus exposition generated from `metrics_snapshot()`. The exporter introduces no second metrics model.

### `/healthz`

Returns a small JSON service probe containing:

- `ok`
- selected Mystic root
- current aggregated MysticTools health state
- metrics schema version

A probe exception returns HTTP 503. Exception messages are not returned to clients.

Unknown paths return HTTP 404. Mutating HTTP methods such as POST, PUT, PATCH and DELETE return HTTP 405. The exporter has no administrative, backup, restore, rollback or cleanup endpoint.

## Security boundary

M4.2 is intentionally a transport wrapper around existing read-only snapshots. It does not add authentication or TLS. For remote access, bind deliberately and place the exporter behind an appropriate firewall or reverse proxy. Do not expose it directly to the public Internet by default.

HTTP responses use `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`. Access logging is disabled by default to avoid per-scrape noise.

## Qualification boundary

The exporter reuses the same qualified/unqualified source semantics as the CLI and Prometheus renderer. It does not parse additional Mystic formats and does not convert missing source values into false zeroes. HTTP availability means that the exporter can produce a snapshot; `/healthz` also reports the current MysticTools health state, but a non-`ok` BBS health value does not by itself make the exporter process unavailable.

## Next deployment layer

Systemd hardening, container packaging and reverse-proxy examples belong in a later deployment milestone. They should preserve the loopback-first/default-deny exposure model established here.
