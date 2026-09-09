# MysticTools

Linux-first sysop toolkit for Mystic BBS.

MysticTools provides small, script-friendly tools around a Mystic installation without replacing Mystic's own utilities. M0 is intentionally read-only.

## M0

- Detect a Mystic installation
- Report basic installation status
- Perform safe installation checks
- Establish an online-node command surface
- Human-readable and JSON output
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

M0 does not modify Mystic files or configuration.

## Development

Python 3.10+.

```sh
python3 -m mystictools status
python3 -m unittest discover -s tests -v
```

## License

MIT. Copyright (c) 2026 Ploos AS.
