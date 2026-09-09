# M6.0 — Real Mystic runtime qualification

M6.0 is the release-gating qualification phase for MysticTools v0.1.0. It is intentionally not a feature milestone.

Target runtime:

- Mystic BBS 1.12 A48 on Linux
- real MIS and Mystic node processes
- real Mystic filesystem paths
- MysticTools from the release-candidate commit

## Safety boundary

The first qualification pass is read-only. Do not run backup/restore/rollback qualification against the production Mystic root. Recovery qualification uses a disposable copy and is a separate step.

## 1. Baseline installation

From the MysticTools checkout:

```sh
python3 -m unittest discover -s tests -v
python3 -m mystictools --version
python3 -m mystictools --root /path/to/mystic status
```

Record the MysticTools commit and Mystic version in the qualification report.

## 2. Mystic-side node exporter

Install or make `extras/mystic/export_node.mpy` available to Mystic and invoke it from a real logged-in node. The exporter must create a fresh schema-v1 fragment under `mystictools-nodes.d/` (or the configured `MYSTICTOOLS_NODE_FRAGMENT_DIR`).

Qualification checks:

- exactly one node record per fragment
- `generated_at` is current, not stale or future-dated
- the node number matches the real Mystic session
- handle/action/server values are plausible for the current session
- no password, address, e-mail, host/IP or other sensitive fields are emitted
- `mystictools --json nodes` reports the provider as qualified

## 3. Mystic-side users exporter

Invoke `extras/mystic/export_users.mpy` inside Mystic with an explicit maximum permanent user ID that covers the known user database.

Qualification checks:

- schema version 1
- explicit `max_user_id_scanned`
- fresh `generated_at`
- no duplicate permanent IDs
- only the documented privacy-safe allowlist is present
- no passwords, e-mail, real name, addresses, phone numbers, IP/host data or notes are emitted
- `mystictools --json users` reports `qualified=true`, `fresh=true`, and `complete_scan=true`
- aggregate `mystictools stats` values agree with the exported records

Do not commit a real users snapshot to the repository.

## 4. FidoNet qualification

Configure all required FidoNet paths explicitly using `mystictools-fidonet.ini` or `MYSTICTOOLS_FIDONET_*` environment variables.

Verify against the live installation:

- inbound path
- unsecured inbound path
- primary outbound path
- semaphore path
- `echomail.in`, `echomail.out`, and `netmail.out` observations when present
- outbound busy/control candidates
- inbound packet/TIC candidates
- active `MIS POLL` detection when a poll is intentionally running
- `qualified_config=true`
- `qualified_scan=true`

No semaphore, busy file, packet, or queue entry may be modified by MysticTools during this phase.

## 5. Doors qualification

With at least one real Mystic node/session and, where practical, a door invocation:

- verify real `tempN` discovery
- verify known dropfile discovery (`DOOR.SYS`, `CHAIN.TXT`, `DORINFO1.DEF`, `door32.sys`) when produced
- confirm `qualified=true` and no scan errors
- confirm MysticTools reports metadata only and does not expose dropfile contents

## 6. Automated read-only evidence collection

After the node/users exporters have been exercised, run:

```sh
python3 scripts/qualify_m6.py \
  --root /path/to/mystic \
  --require-node-provider \
  --require-users-provider \
  --output m6-runtime-qualification.json
```

The harness executes the read-only command surface through the real JSON CLI and records exit codes, parsed payloads, provider qualification, FidoNet/doors scan qualification, and doctor state.

The generated JSON may contain operational details from the installation. Review/redact it before sharing or committing. Do not commit real user records, process secrets, private addresses, or other sensitive installation data.

## 7. Disposable recovery qualification

Recovery qualification must use a disposable copy of the Mystic tree while MIS and Mystic are verifiably stopped.

Required sequence:

1. create an offline backup with `mysticbackup`
2. verify the archive with `mysticrestore` without `--execute`
3. restore to a disposable missing target
4. verify the restored payload and manifest hashes
5. create a controlled change in the disposable target
6. execute guarded replacement restore with `--replace-existing`
7. confirm the previous tree is preserved as a rollback tree
8. run `mysticrollback --list`
9. preflight the selected rollback
10. execute rollback
11. confirm the pre-restore tree is active again and the replaced tree is preserved as `failed-*`
12. verify no unresolved restore transaction journal remains

Recovery trees are cleanup-manual by design. Remove them only after independent validation.

## PASS criteria

M6.0 is PASS only when all of the following are demonstrated on the target Mystic runtime:

- baseline runtime/procfs discovery behaves correctly
- node exporter is qualified on a real session
- users exporter is qualified on real `getuserid()` data
- FidoNet explicit configuration and scan are qualified
- doors scan is qualified on real `tempN` data
- doctor has no unexplained critical finding
- disposable backup → verify → restore → rollback completes safely
- no credential leakage is observed in JSON, human output, logs, qualification evidence, or process argv reporting

A missing optional live condition, such as no active FidoNet poll during the test window, is not itself a failure if the corresponding static/runtime contract is otherwise verified and the omission is documented.

## Release consequence

After M6.0 PASS, the remaining v0.1.0 work should be release-candidate verification only: final CI, published OCI smoke, version bump, release notes, and tag. New feature work should remain deferred until after v0.1.0.
