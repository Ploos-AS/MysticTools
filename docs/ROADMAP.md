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

- [x] Permissions and ownership diagnostics
- [x] Disk-space checks
- [x] Log-directory discovery
- [x] Stable exit-code contract

## M1 — Sysop observability

### M1.1 — Logs

- [x] `logs` command over discovered log files
- [x] Filename/stem selector
- [x] Bounded tail output
- [x] Case-insensitive substring filtering
- [x] Human-readable and JSON output
- [x] Read-only file access and fixture tests

### M1.2 — Nodes

- richer node/session presentation
- conservative enrichment from qualified sources

### M1.3 — Network/service status

- listener/service discovery
- monitoring-friendly health output

### M1.4 — Metrics groundwork

- structured statistics and exporter-friendly data model

## Later

- FidoNet diagnostics
- door/dropfile diagnostics
- backup/restore tooling
- optional Mystic-side Python/menu integration
