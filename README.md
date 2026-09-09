# MysticTools

Linux-first sysop toolkit for Mystic BBS.

MysticTools provides small, script-friendly tools around a Mystic installation without replacing Mystic's own utilities. The current line is intentionally read-only.

## Current capabilities

- Detect a Mystic installation
- Report basic installation status
- Detect MIS and Mystic node processes through Linux procfs
- Detect Mystic version from WHATSNEW metadata when available
- Perform safe installation and operational checks
- Report ownership, permissions and free disk space
- Discover and read candidate Mystic logs safely
- Show detected Mystic sessions with conservative node-number handling
- Human-readable and JSON output
- Architecture-neutral Linux implementation

## Commands

```text
mystictools status
mystictools check
mystictools who
mystictools logs
```

Common options:

```text
--root PATH       Explicit Mystic installation root
--json            Emit machine-readable JSON
```

Root detection order: `--root`, `MYSTIC_ROOT`, `/mystic`, `/opt/mystic`, `/srv/mystic`.

### Logs

`logs` only reads files already identified by MysticTools log discovery. It does not accept an arbitrary filesystem path.

Examples:

```sh
mystictools logs
mystictools logs mis --tail 100
mystictools logs --contains error --tail 50
mystictools --json logs mis --contains refused
```

The default tail is 50 matching lines per selected file and the hard maximum is 5000.

### Runtime discovery

`status` and `who` inspect `/proc` directly and do not require systemd. Mystic can select node numbers internally, so if a running `mystic` process has no explicit `-N#` argument MysticTools reports the node as `?`/`null` instead of guessing.

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
