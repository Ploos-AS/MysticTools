# MysticTools

Linux-first sysop toolkit for Mystic BBS.

MysticTools provides small, script-friendly tools around a Mystic installation without replacing Mystic's own utilities. The current line is intentionally read-only.

## Current capabilities

- Detect a Mystic installation
- Report installation, runtime and operational status
- Detect MIS and Mystic node processes through Linux procfs
- Detect Mystic version from WHATSNEW metadata when available
- Report ownership, permissions and free disk space
- Discover and read candidate Mystic logs safely
- Show detected Mystic sessions with conservative node-number handling
- Optionally enrich nodes from qualified Mystic-side node snapshots
- Read a privacy-safe qualified Mystic user snapshot
- Aggregate user, runtime, FidoNet and door statistics
- Discover listeners owned by MIS/Mystic and report health
- Inspect FidoNet paths, semaphores, queue candidates and MIS POLL state
- Discover Mystic node temp directories and known door dropfiles without reading session contents
- Export structured JSON and optional Prometheus exposition metrics
- Architecture-neutral Linux implementation

## Commands

```text
mystictools status
mystictools check
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
```

Common options:

```text
--root PATH       Explicit Mystic installation root
--json            Emit machine-readable JSON
```

Root detection order: `--root`, `MYSTIC_ROOT`, `/mystic`, `/opt/mystic`, `/srv/mystic`.

### Users and statistics

`users` reads the optional schema-v1 `mystictools-users.json` sidecar. The public schema is deliberately privacy-safe and contains only permanent user ID, handle, security level, calls, uploads, downloads, posts and last-on. It does not expose passwords, e-mail, real name, addresses, phone numbers, IP/host data or notes.

```sh
mystictools users
mystictools --json users
```

`extras/mystic/export_users.mpy` can generate the sidecar from inside Mystic using the documented `getuserid(ID)` API. Because Mystic does not document a global user-count enumeration API, the exporter requires an explicit maximum user ID and scans only that range.

`stats` is an aggregation layer over existing qualified providers. It combines user totals with runtime/MIS/node/listener state, FidoNet signals and door diagnostics. Unavailable source values remain unavailable rather than being reported as false zero totals.

```sh
mystictools stats
mystictools --json stats
```

### Prometheus

Prometheus support is optional. MysticTools remains fully usable with ordinary human-readable or JSON output.

```sh
mystictools metrics
mystictools --json metrics
mystictools metrics --prometheus
```

Public Prometheus metric names use the `mystictools_*` namespace. Current coverage includes runtime/procfs availability, MIS and node processes, network listeners, logs, disk space, health, native node-provider qualification/freshness, privacy-safe user-provider qualification and aggregate user totals, FidoNet signals and door/dropfile diagnostics. Source-dependent values are omitted when their source is unavailable instead of being reported as a false zero.

No user ID or handle is used as a Prometheus label. `--json` and `metrics --prometheus` are mutually exclusive output modes.

### FidoNet diagnostics

`fidonet` is read-only. MysticTools supports explicit FidoNet path configuration through `mystictools-fidonet.ini` or environment variables, with documented Mystic defaults retained as an explicitly unqualified fallback.

Provider precedence is environment override, MysticTools INI, then documented Mystic default. The command reports path provenance/qualification, `echomail.in`, `echomail.out` and `netmail.out` semaphores, outbound busy/control files, packet/TIC queue candidates and detected `MIS POLL` processes. It never removes busy flags or modifies queue contents.

```sh
mystictools fidonet
mystictools --json fidonet
```

### Doors/dropfiles

`doors` discovers documented per-node `tempN` directories and known dropfiles such as `DOOR.SYS`, `CHAIN.TXT`, `DORINFO1.DEF` and `door32.sys`. It reports metadata only and does not expose caller/session contents.

```sh
mystictools doors
mystictools --json doors
```

### Logs

`logs` only reads files already identified by MysticTools log discovery. It does not accept an arbitrary filesystem path.

```sh
mystictools logs
mystictools logs mis --tail 100
mystictools logs --contains error --tail 50
mystictools --json logs mis --contains refused
```

The default tail is 50 matching lines per selected file and the hard maximum is 5000.

### Runtime and nodes

`status`, `who`, `nodes`, `network` and `health` inspect Linux procfs directly and do not require systemd. Mystic can select node numbers internally, so if a running `mystic` process has no explicit `-N#` argument MysticTools reports the node as `?`/`null` instead of guessing.

A qualified schema-v1 `mystictools-nodes.json` sidecar or fresh per-node fragments under `mystictools-nodes.d/` can optionally enrich explicit node IDs with Mystic-side fields. `MYSTICTOOLS_NODE_SNAPSHOT`, `MYSTICTOOLS_NODE_FRAGMENT_DIR` and `MYSTICTOOLS_NODE_MAX_AGE` control the optional provider. MysticTools does not reverse-engineer undocumented Mystic runtime record formats.

### Exit codes

```text
0  OK
1  diagnostics/warnings or invalid bounded input
2  Mystic installation not found
3  required runtime/probe source unavailable
```

MysticTools does not modify Mystic files or configuration.

## Development

Python 3.10+.

```sh
python3 -m mystictools status
python3 -m unittest discover -s tests -v
```

## License

MIT. Copyright (c) 2026 Ploos AS.
