# v0.1.0 release contract

MysticTools v0.1.0 is the first release intended to expose the complete planned tool suite rather than a partial preview.

## Required tool surface

The release must provide these installed entry points:

```text
mystictools
mysticstatus
mysticcheck
mysticwho
mysticnodes
mysticwatch
mysticlog
mysticnet
mysticfidonet
mysticdoors
mysticusers
mysticstats
mystichealth
mysticdoctor
mysticbackup
mysticrestore
mysticrollback
mysticmetrics
mysticexporter
```

The umbrella CLI must expose:

```text
status check doctor backup restore who nodes users stats logs
network health metrics fidonet doors watch exporter
```

## Public behavioral contracts

- Linux-first, Python 3.10+.
- Mystic installation root is explicit or detected conservatively.
- Diagnostic/observability operations are read-only.
- Unknown Mystic node numbers are never guessed.
- Process argv stored downstream is credential-redacted.
- Native node and user enrichment requires versioned qualified sidecars/providers.
- User data is restricted to the privacy-safe allowlist documented in README/M2.8.
- Unavailable or incomplete data is not converted into false zeroes.
- Prometheus is optional and uses the frozen `mystictools_*` v0.1.0 contract in `PROMETHEUS.md`.
- FidoNet defaults remain explicitly unqualified unless paths are supplied through the supported provider.
- Door diagnostics never parse or expose dropfile session contents.

## Recovery contracts

Backup:

- offline consistency by default;
- live/unverified backup requires explicit override;
- destination must be outside the Mystic root and not already exist;
- only vetted regular files and safe internal symlinks are archived;
- special files and external symlinks are rejected;
- archive is mode 0600 and self-verifies before publication.

Restore:

- preflight-only by default;
- mutation requires `--execute`;
- replacing an existing root requires `--replace-existing`;
- no generic tar `extractall`;
- payload must match the manifest contract;
- archive identity is rechecked through staging/commit;
- runtime is rechecked immediately before commit;
- transaction journal records restore swap state;
- previous installations are preserved as rollback data.

Rollback:

- preflight-only by default;
- mutation requires `--execute`;
- runtime must be verifiably stopped;
- only sibling rollback trees belonging to the selected root are accepted;
- an unfinished restore journal permits only the exact journal-associated rollback tree;
- replaced active trees are preserved as collision-free failed recovery trees;
- cleanup remains manual-only.

## CI gates

A release candidate must pass, on the exact candidate commit:

- unit tests on Python 3.10;
- unit tests on Python 3.12;
- `python -m mystictools --help` smoke;
- OCI image build;
- Compose configuration validation;
- wheel build;
- sdist build;
- clean-venv wheel install;
- `--help` smoke for every installed console script;
- clean-venv sdist install smoke;
- published OCI smoke for the intended image workflow.

No release should be tagged from a commit whose required CI is merely queued or in progress.

## Remaining pre-v0.1.0 qualification gates

The implemented feature surface is complete. Before version bump/tag, the remaining work is qualification rather than adding tools:

1. Run real Mystic 1.12 A48 Linux qualification against a controlled installation/UBB environment.
2. Qualify `extras/mystic/export_node.mpy` from an actual Mystic Python session, including its output location assumptions.
3. Qualify `extras/mystic/export_users.mpy` against actual `getuserid(ID)` dictionaries and confirm the field aliases used for handle/security/calls/uploads/downloads/posts/last-on.
4. Exercise FidoNet diagnostics against a configured Mystic installation with explicit paths and representative queue/semaphore state.
5. Exercise door discovery against real `tempN` directories without reading session contents.
6. Run an end-to-end offline backup -> verify -> guarded restore -> rollback cycle on disposable test data/filesystem.
7. Re-run all CI and published OCI smoke on the final release-candidate commit.
8. Only after those gates pass: change version from `0.1.0.dev0` to `0.1.0`, update release notes, tag and publish.

## Explicitly not release blockers

These are useful later enhancements but are not required for v0.1.0:

- automatic stale-fragment cleanup;
- automatic recovery-tree cleanup;
- long-term recovery history beyond last-result-per-operation;
- parsing proprietary Mystic databases;
- built-in exporter TLS/authentication;
- web UI;
- high-cardinality per-user/per-node Prometheus labels;
- automatic repair of Mystic, FidoNet or door state.

The release should remain conservative rather than expanding scope immediately before v0.1.0.
