# M2.8 — Users provider qualification

MysticTools exposes a read-only, privacy-safe user snapshot through `mystictools users`.

## Qualified interface

The Linux-side provider reads schema-v1 `mystictools-users.json`, optionally overridden with `MYSTICTOOLS_USER_SNAPSHOT`.

The public snapshot intentionally permits only:

- permanent user ID
- handle
- security level
- call count
- upload count
- download count
- post count
- last-on timestamp/value

Fields such as password data, e-mail address, real name, street address, phone numbers, IP address, hostname and free-form notes are not part of the MysticTools users contract.

## Mystic-side exporter

`extras/mystic/export_users.mpy` uses Mystic's documented `getuserid(ID)` Python function. It requires an explicit `max_user_id` argument and probes IDs from 1 through that bound.

This upper bound is deliberately explicit because Mystic documents lookup by permanent user ID but does not document a global user-count/enumeration function suitable for a complete third-party export. Missing IDs are skipped.

The exporter writes atomically to `mystictools-users.json` and never modifies Mystic's user database.

## Prometheus

Only low-cardinality aggregate metrics are exported:

- `mystictools_users_provider_available`
- `mystictools_users_provider_qualified`
- `mystictools_users_count`

Individual handles, user IDs or security levels are never Prometheus labels.
