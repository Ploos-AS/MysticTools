# MysticTools

Linux-first sysop toolkit for Mystic BBS.

MysticTools provides small, script-friendly tools around a Mystic installation without replacing Mystic's own utilities. Observability and diagnostics are read-only by default. Backup, restore and rollback are explicit recovery operations with guarded execution boundaries.

## Release surface

MysticTools targets Mystic 1.12 A48+ on Linux while avoiding unnecessary coupling to one alpha build. Python 3.10+ is supported.

Umbrella CLI:

```text
mystictools status
mystictools check
mystictools doctor
mystictools backup DESTINATION
mystictools restore ARCHIVE
mystictools who
mystictools nodes
mystictools users
mystictools stats
mystictools logs
mystictools network
mystictools health
mystictools metrics
mystictools fidonet
mystictools doors
mystictools watch
mystictools exporter
```

Standalone entry points:

```text
mysticstatus   mysticcheck    mysticdoctor
mysticbackup   mysticrestore  mysticrollback
mysticwho      mysticnodes    mysticusers
mysticstats    mysticlog      mysticnet
mystichealth   mysticmetrics  mysticfidonet
mysticdoors    mysticwatch    mysticexporter
```

Common options:

```text
--root PATH       Explicit Mystic installation root
--json            Emit machine-readable JSON where supported
```

Root detection order: `--root`, `MYSTIC_ROOT`, `/mystic`, `/opt/mystic`, `/srv/mystic`.

## What it does

- Detects Mystic installations, MIS and Mystic node processes through Linux procfs.
- Reports installation, runtime, ownership, permissions, disk space and log state.
- Discovers listeners owned by MIS/Mystic and provides health/doctor diagnostics.
- Optionally enriches nodes from qualified Mystic-side snapshots.
- Reads a privacy-safe qualified user snapshot and aggregates BBS statistics.
- Inspects FidoNet paths, semaphores, queue candidates and `MIS POLL` state.
- Discovers node `tempN` directories and known door dropfiles without parsing session contents.
- Provides human, JSON and optional Prometheus output.
- Provides guarded backup, restore and rollback with checksums, staging and recovery state.
- Provides a terminal watch view and an optional HTTP Prometheus exporter.
- Publishes architecture-neutral Python tooling and amd64/arm64 OCI exporter images.

## Safety model

MysticTools does not reverse-engineer or directly modify Mystic `.dat` databases. Diagnostic commands inspect procfs, documented filesystem conventions and explicit sidecar/provider contracts.

`backup` is offline by default. Live or unverifiable runtime state requires explicit opt-in. `restore` defaults to verification/preflight only; filesystem mutation requires `--execute`, and replacing an existing Mystic root additionally requires `--replace-existing`. `mysticrollback` also defaults to preflight and requires `--execute` before activation.

Restore never uses generic tar extraction. Archive members and the manifest are validated, regular-file hashes are verified, payload is staged beside the target, runtime state is rechecked before commit, and replacement preserves rollback data. Restore transaction journals and recovery trees are retained conservatively rather than silently cleaned up.

## Users and statistics

`users` reads the optional schema-v1 `mystictools-users.json` sidecar. The public schema is deliberately privacy-safe and contains only permanent user ID, handle, security level, calls, uploads, downloads, posts and last-on. It does not expose passwords, e-mail, real name, addresses, phone numbers, IP/host data or notes.

`extras/mystic/export_users.mpy` can generate the sidecar from inside Mystic using the documented `getuserid(ID)` API. Because Mystic does not document a global user-count enumeration API, the exporter requires an explicit maximum user ID. MysticTools validates timestamp freshness, explicit scan bounds, duplicate IDs and field types before qualifying the snapshot.

`stats` aggregates only qualified source data. A numeric user total is emitted only when that field is valid for every user record; partial data is reported as unavailable instead of as a misleading partial sum.

## Runtime and node provider

Mystic can select node numbers internally, so a running `mystic` process without explicit `-N#` is reported as unknown rather than guessed.

A qualified schema-v1 `mystictools-nodes.json` sidecar or fresh per-node fragments under `mystictools-nodes.d/` can enrich explicit node IDs. `MYSTICTOOLS_NODE_SNAPSHOT`, `MYSTICTOOLS_NODE_FRAGMENT_DIR` and `MYSTICTOOLS_NODE_MAX_AGE` control the optional provider. Stale or future-dated fragments are not accepted as fresh qualified data.

MysticTools does not reverse-engineer undocumented Mystic runtime record formats.

## FidoNet diagnostics

`fidonet` is read-only. Provider precedence is environment override, `mystictools-fidonet.ini`, then documented Mystic defaults as an explicitly unqualified fallback. Relative environment and INI paths are anchored to the selected Mystic root.

Malformed/unreadable explicit configuration and filesystem scan errors are surfaced instead of silently becoming empty/healthy data. The command never clears busy flags, semaphores or queue contents.

## Doors/dropfiles

`doors` discovers documented per-node `tempN` directories and known dropfiles such as `DOOR.SYS`, `CHAIN.TXT`, `DORINFO1.DEF` and `door32.sys`. It reports metadata only and does not expose caller/session contents. Filesystem scan degradation is explicitly marked unqualified.

## Logs

`logs` only reads files already identified by MysticTools log discovery. It does not accept an arbitrary filesystem path. The default tail is 50 matching lines per selected file and the hard maximum is 5000.

```sh
mystictools logs mis --tail 100
mystictools logs --contains error --tail 50
```

## Prometheus

Prometheus is optional and first-class. Human-readable and JSON output remain supported independently.

```sh
mystictools metrics
mystictools --json metrics
mystictools metrics --prometheus
```

Public metric names use the `mystictools_*` namespace. Source-dependent metrics are omitted when their source is unavailable instead of reporting false zeroes. No user ID or handle is used as a Prometheus label. `--json` and `metrics --prometheus` are mutually exclusive.

The v0.1.0 metric/API freeze is documented in `docs/PROMETHEUS.md`.

## Exporter and deployment

`mysticexporter` / `mystictools exporter` serves `/metrics` and `/healthz`, binding to `127.0.0.1:9108` by default. It is read-only and intentionally has no built-in TLS/auth layer; remote exposure should be deliberate and protected by firewall/reverse proxy.

For OCI deployment, host PID visibility is required for host procfs runtime discovery and the Mystic root is mounted read-only. See `docs/DEPLOYMENT.md`.

## Exit codes

```text
0  OK
1  diagnostics/warnings or invalid bounded input
2  Mystic installation not found
3  required runtime/probe source unavailable
```

## Development and qualification

```sh
python3 -m unittest discover -s tests -v
python3 -m mystictools --help
```

CI covers Python 3.10 and 3.12, OCI build/config validation, wheel/sdist creation, clean-environment installation and smoke tests for every installed console script.

The current release-readiness contract and remaining qualification gates are documented in `docs/RELEASE_CONTRACT.md` and `docs/ROADMAP.md`.

## License

MIT. Copyright (c) 2026 Ploos AS.
