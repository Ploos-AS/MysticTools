# M4.1 — MysticWatch

`mysticwatch` is a read-only terminal dashboard built entirely from existing MysticTools providers and snapshots.

## Commands

Run continuously with the default two-second refresh:

```text
mysticwatch --root /srv/mystic
```

The same command is available through the umbrella CLI:

```text
mystictools --root /srv/mystic watch
```

Useful bounded forms:

```text
mysticwatch --once
mysticwatch --count 5 --interval 1
mysticwatch --json
mysticwatch --no-clear
```

The minimum refresh interval is 0.5 seconds. `--json` implies one snapshot and exits.

## Display contract

The terminal view correlates:

- runtime/procfs availability
- MIS state and detected Mystic node process count
- qualified node-sidecar user/action fields when available
- listener count
- FidoNet poll, busy, outbound and inbound signals
- door temp/dropfile counts
- recovery-state qualification and preserved rollback/failed trees
- aggregate health and Prometheus schema version

The human view deliberately does not print raw process argv, credentials, addresses, dropfile contents or unqualified user/session data.

## Qualification boundary

M4.1 introduces no new Mystic file parser or runtime-data assumption. It is a presentation/refresh layer over existing MysticTools providers. Unknown or unavailable source state remains unknown rather than being coerced into healthy/zero values. The command is read-only and does not start, stop, repair, clean up, back up, restore or roll back the BBS.
