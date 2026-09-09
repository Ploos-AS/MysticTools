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

### M2.5 — Prometheus contract and cross-tool coverage

- [x] Normalize public metric names under `mystictools_*`
- [x] Replace ambiguous `mystictools_up` with explicit source-availability metrics
- [x] Omit source-dependent values when their probe is unavailable rather than emitting false zeroes
- [x] Add native node-provider qualification metrics
- [x] Add FidoNet queue, busy, inbound and MIS POLL metrics
- [x] Add door/temp/dropfile metrics
- [x] Keep Prometheus optional alongside human-readable and JSON output
- [x] Reject simultaneous JSON and Prometheus output
- [x] Add CLI regression tests for node and metrics contracts

### M2.5 observability policy

Prometheus support is an optional first-class output layer. New MysticTools commands should expose useful low-cardinality metrics where meaningful, while remaining fully usable without Prometheus. Public metric names use the `mystictools_*` namespace and should be treated as an API once v0.1.0 is released.

### M2.6 — Mystic-side node snapshot exporter

- [x] Add Python 3 `export_node.mpy` helper for execution inside Mystic
- [x] Use documented Mystic MCI values for node, handle, server, invisibility and availability
- [x] Write one atomic schema-v1 fragment per node to avoid cross-node write races
- [x] Add `mystictools-nodes.d` fragment aggregation to the native provider
- [x] Optional `MYSTICTOOLS_NODE_FRAGMENT_DIR` override
- [x] Preserve full `mystictools-nodes.json` sidecar as higher-precedence provider
- [x] Add fragment aggregation and invalid-schema tests

### M2.6 qualification boundary

Mystic Python documents `mci2str()` and the MCI values used by the exporter, but it does not document a global node-enumeration API. The exporter therefore publishes only the current session's node record. The optional `action` field is supplied explicitly to the exporter rather than inferred from undocumented Mystic state.

### M2.7 — Fragment freshness and active-node correlation

- [x] Require `generated_at` on per-node fragments
- [x] Reject stale fragments from native enrichment
- [x] Default freshness window to 300 seconds
- [x] Optional `MYSTICTOOLS_NODE_MAX_AGE` override
- [x] Correlate native records with explicit procfs node IDs when available
- [x] Mark unmatched native records inactive only when all active process nodes are known
- [x] Preserve unresolved status when Mystic auto-selects node IDs
- [x] Add freshness and correlation tests
- [x] Add low-cardinality Prometheus metrics for fragment count/fresh/stale/max-age

### M2.7 qualification boundary

Procfs remains the authority for process liveness. A fresh fragment is accepted as qualified native session metadata, but freshness alone does not prove that the corresponding Mystic process is still alive. When procfs exposes explicit node IDs, MysticTools can positively correlate those records. If one or more running Mystic processes have auto-selected/unknown node IDs, unmatched fresh fragments are reported as unresolved rather than guessed active or inactive. M2.7 is intentionally read-only and never deletes stale fragments.

### M2.8 — Users provider

- [x] Add privacy-safe schema-v1 `mystictools-users.json` provider
- [x] Add `users` CLI command with human and JSON output
- [x] Add Mystic Python `export_users.mpy` helper using documented `getuserid(ID)`
- [x] Require an explicit maximum user ID instead of guessing undocumented enumeration bounds
- [x] Exclude passwords, e-mail, real name, addresses, phone numbers, IP/host data and notes
- [x] Add user-provider qualification and count metrics
- [x] Add provider and CLI regression tests

### M2.8 qualification boundary

Mystic documents `getuserid(ID)` for permanent user IDs but does not document a global user-count/enumeration API. The exporter therefore scans only an explicitly configured `1..max_user_id` range. The public sidecar schema intentionally contains a restricted statistics-safe subset of user fields.

### M2.9 — Aggregated BBS statistics

- [x] Add `stats` command with human and JSON output
- [x] Aggregate qualified user count, calls, uploads, downloads and posts
- [x] Combine runtime/MIS/node/listener state with FidoNet and door diagnostics
- [x] Preserve per-source availability/qualification in the statistics model
- [x] Never coerce unavailable sources into false zero totals
- [x] Add Prometheus totals for calls, uploads, downloads and posts
- [x] Add statistics model and CLI regression tests

### M2.9 qualification boundary

`stats` is an aggregation layer, not a new parser. User totals are emitted only from a qualified users provider; runtime and listener values retain their procfs availability semantics; FidoNet and door values come from their existing conservative providers. No user identity is used as a Prometheus label.

### M2.10 — Doctor diagnostics

- [x] Add `doctor` command with human and JSON output
- [x] Correlate runtime/MIS, network, operational checks, node provider, users provider, FidoNet and doors
- [x] Use explicit `ok`, `warning`, `critical` and `unavailable` finding states
- [x] Preserve source uncertainty instead of converting missing providers into healthy values
- [x] Warn on stale node fragments, unqualified providers/configuration, busy FidoNet state and unreadable dropfiles
- [x] Add low-cardinality Prometheus doctor status/count metrics
- [x] Add doctor model tests

### M2.10 qualification boundary

`doctor` is a read-only correlation and diagnosis layer over already-qualified MysticTools probes and providers. It does not parse new Mystic formats, repair files, clear semaphores/busy state, delete stale fragments, or alter configuration. Findings are recommendations/status only; mutating repair operations remain outside this milestone.

### Later M2 areas

- optional explicit stale-fragment cleanup command/design
- backup/restore design and consistency model
- optional HTTP Prometheus exporter/service packaging
- optional Mystic-side Python/menu integration
