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

- [x] Detect MIS process state without assuming systemd (Linux procfs)
- [x] Detect Mystic version safely from WHATSNEW metadata when available
- [x] Discover Mystic node processes without parsing proprietary data files
- [x] Implement useful `who` output with explicit unknown-node semantics
- [x] Add fixture-driven runtime tests

### M0.1 qualification boundary

Mystic may select a node number internally when `-N#` is not present. MysticTools reports such node IDs as unknown rather than guessing. A richer Mystic-native node-status source can be added later after its format/interface is qualified.

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
