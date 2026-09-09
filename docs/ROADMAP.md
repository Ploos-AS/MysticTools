# Roadmap

## M0 — Foundation

- [x] Linux-first Python CLI
- [x] MIT / Ploos AS
- [x] Mystic root auto-detection
- [x] Explicit `--root` and `MYSTIC_ROOT` override
- [x] Read-only `status`, `check`, `who` command surface
- [x] Human-readable and JSON output
- [x] Unit tests for detection/check primitives

## M0.1 — Runtime discovery

- Detect MIS process state without assuming systemd
- Detect Mystic version safely
- Discover a qualified node-status source
- Implement useful `who` output
- Add fixture-driven tests

## M0.2 — Operational checks

- Permissions and ownership diagnostics
- Disk-space checks
- Log-directory discovery
- Stable exit-code contract

## M1 — Sysop observability

- logs and nodes
- network/service status
- monitoring-friendly health output
- metrics/statistics groundwork

## Later

- FidoNet diagnostics
- door/dropfile diagnostics
- backup/restore tooling
- optional Mystic-side Python/menu integration
