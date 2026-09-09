# MysticTools

Linux-first sysop toolkit for Mystic BBS.

MysticTools provides small, script-friendly tools around a Mystic installation without replacing Mystic's own utilities. The current M0.x line is intentionally read-only.

## Current capabilities

- Detect a Mystic installation
- Report basic installation status
- Detect MIS and Mystic node processes through Linux procfs
- Detect Mystic version from WHATSNEW metadata when available
- Check permissions and report uid/gid ownership without changing it
- Check available disk space
- Discover Mystic log directories and candidate log files
- Show detected Mystic sessions with conservative node-number handling
- Human-readable and JSON output
- Stable monitoring-friendly exit codes
- Architecture-neutral Linux implementation

## Commands

```text
mystictools status
mystictools check
mystictools who
```

Common options:

```text
--root PATH       Explicit Mystic installation root
--json            Emit machine-readable JSON
```

Root detection order: `--root`, `MYSTIC_ROOT`, `/mystic`, `/opt/mystic`, `/srv/mystic`.

### Runtime discovery

`status` and `who` inspect `/proc` directly and do not require systemd. Mystic can select node numbers internally, so if a running `mystic` process has no explicit `-N#` argument MysticTools reports the node as `?`/`null` instead of guessing.

### Operational diagnostics

`check` combines installation checks with read-only permission/ownership, disk-space and log-discovery diagnostics. Mixed ownership is reported conservatively; MysticTools does not assume a required Linux user or group.

Exit codes:

```text
0  success / healthy
1  diagnostic warnings
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
