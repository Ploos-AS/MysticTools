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

- [x] Dedicated `nodes` command
- [x] PID and explicit/unknown node number
- [x] Process start time and runtime from procfs when available
- [x] Process arguments and executable path
- [x] Conservative enrichment only; no guessed usernames or remote addresses
- [x] Human-readable and JSON output
- [x] Node model tests

### M1.3 — Network/service status

- [x] Discover TCP/TCP6 listeners through procfs
- [x] Map socket inodes to detected MIS/Mystic PIDs
- [x] `network` command with human-readable and JSON output
- [x] `health` command with monitoring-friendly status/checks
- [x] Preserve stable exit-code contract
- [x] Network fixture tests

### M1.4 — Metrics groundwork

- [x] Versioned structured metrics snapshot
- [x] Runtime, listener, log, disk and health metrics
- [x] `metrics` CLI command
- [x] JSON output via global `--json`
- [x] Prometheus exposition via `metrics --prometheus`
- [x] Omit unavailable numeric metrics instead of inventing values
- [x] Metrics model and renderer tests

## M2 — Deeper Mystic-aware diagnostics

### M2.1 — FidoNet filesystem diagnostics

- [x] Dedicated `fidonet` command
- [x] Detect default EchoMail inbound/outbound/semaphore paths conservatively
- [x] Detect `echomail.in`, `echomail.out` and `netmail.out` semaphores
- [x] Detect outbound busy/control files without mutating them
- [x] Count inbound packet/TIC and outbound queue candidates
- [x] Human-readable and JSON output
- [x] Explicitly mark default-path discovery as unqualified configuration
- [x] Fixture tests

### M2.2 — Qualified FidoNet configuration/provider

- [x] Provider abstraction with explicit per-path provenance
- [x] Optional `mystictools-fidonet.ini` configuration
- [x] Environment overrides with highest precedence
- [x] Preserve Mystic documented defaults as explicit unqualified fallback
- [x] Mark configuration globally qualified only when all required paths are explicit
- [x] Detect active `MIS POLL` processes through procfs
- [x] Correlate qualified paths, poll state, semaphores and queue signals in `fidonet`
- [x] Provider and poll-context tests

### M2.2 qualification boundary

Mystic's System Paths are configurable, but MysticTools does not reverse-engineer undocumented/proprietary configuration storage. A path is considered qualified only when it is supplied explicitly to MysticTools through its INI provider or environment. Defaults remain visible but are labelled unqualified.

### M2.3 — Doors/dropfiles

- [x] Dedicated `doors` command
- [x] Discover per-node `tempN` directories
- [x] Detect DOOR.SYS, CHAIN.TXT, DORINFO1.DEF and door32.sys
- [x] Report format, size, timestamp and readability without parsing session contents
- [x] Preserve case-sensitive Mystic dropfile conventions
- [x] Human-readable and JSON output
- [x] Fixture tests

### M2.3 qualification boundary

Mystic documents that door drop files are created in each node's `tempN` directory. MysticTools treats that filesystem convention and the documented dropfile names as qualified, but M2.3 intentionally does not parse dropfile contents because those files can contain user/session details.

### M2.4 — Native node-data provider

- [x] Define versioned `mystictools-nodes.json` sidecar contract
- [x] Optional `MYSTICTOOLS_NODE_SNAPSHOT` path override
- [x] Validate schema before treating native data as qualified
- [x] Merge qualified native node records with procfs process records by explicit node number
- [x] Preserve unmatched native records without inventing PIDs
- [x] Expose user/action/server/invisible/message-availability only from qualified provider data
- [x] Provider and merge tests

### M2.4 qualification boundary

Mystic documents Who's Online, node action status and NodeSpy, but no stable external node-status file/API is documented for third-party readers. MysticTools therefore does not reverse-engineer Mystic runtime records. The sidecar contract is qualified only when a Mystic-side exporter explicitly produces schema version 1 data. Procfs remains the independent baseline.

### Later M2 areas

- Mystic-side node snapshot exporter (Python/MPL) qualification
- backup/restore design and consistency model
- optional exporter/service packaging
- optional Mystic-side Python/menu integration
