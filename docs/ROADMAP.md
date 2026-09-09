# MysticTools roadmap

MysticTools is a Linux-first sysop, diagnostics, observability and guarded-recovery suite for Mystic BBS. The planned v0.1.0 tool surface is implemented; current work is release qualification and contract freeze rather than adding more tools.

## Completed foundation and observability

### M0 — Foundation

- [x] Python 3.10+ Linux-first CLI
- [x] MIT / Ploos AS
- [x] conservative Mystic root detection plus `--root` / `MYSTIC_ROOT`
- [x] human and JSON output
- [x] stable exit-code contract

### M0.1 — Runtime discovery

- [x] Linux procfs MIS/Mystic process discovery
- [x] conservative Mystic version detection
- [x] explicit `-N#` node detection
- [x] unknown node preserved when Mystic auto-selects internally
- [x] credential-redacted downstream argv

### M0.2 — Operational checks

- [x] ownership/permission diagnostics
- [x] disk-space checks
- [x] log discovery

### M1 — Sysop observability

- [x] M1.1 logs: bounded tail, selector/filter, human/JSON
- [x] M1.2 nodes: runtime/process detail
- [x] M1.3 network: TCP/TCP6 listener mapping and health
- [x] M1.4 metrics groundwork: versioned metrics + optional Prometheus

## Completed Mystic-aware providers

### M2.1–M2.3 — FidoNet and doors

- [x] FidoNet filesystem/semaphore/queue diagnostics
- [x] explicit FidoNet INI/environment provider with provenance
- [x] relative explicit paths anchored to Mystic root
- [x] malformed INI surfaced as unqualified configuration
- [x] filesystem scan degradation surfaced explicitly
- [x] MIS POLL detection
- [x] `tempN` and known door-dropfile metadata discovery
- [x] no door session-content parsing

### M2.4–M2.7 — Native node provider

- [x] schema-v1 `mystictools-nodes.json`
- [x] per-node `mystictools-nodes.d/node-N.json` fragments
- [x] Mystic-side `export_node.mpy`
- [x] freshness policy and stale/future timestamp rejection
- [x] procfs/native correlation without guessed liveness
- [x] provider qualification Prometheus metrics

### M2.8–M2.9 — Users and statistics

- [x] privacy-safe schema-v1 `mystictools-users.json`
- [x] Mystic-side `export_users.mpy` using documented `getuserid(ID)`
- [x] explicit maximum user-ID scan bound
- [x] freshness, type, duplicate-ID and completeness validation
- [x] aggregate stats only from qualified complete values
- [x] no false partial totals

### M2.10 — Doctor

- [x] cross-source findings
- [x] `ok`, `warning`, `unavailable`, `critical`
- [x] severity order with `critical` highest
- [x] provider/config/scan degradation visible in doctor
- [x] snapshot reuse to avoid inconsistent duplicate probes

## Completed backup and recovery

### M3.1 — Backup

- [x] offline by default
- [x] explicit live/unverified overrides
- [x] SHA-256 inventory and manifest
- [x] explicit vetted archive payload only
- [x] reject special files and external symlinks
- [x] unique temporary archive, mode 0600
- [x] self-verify before final publication

### M3.2–M3.3 — Restore verification and execution

- [x] preflight-only default
- [x] explicit `--execute`
- [x] explicit `--replace-existing`
- [x] strict archive/member/manifest contract
- [x] no generic tar extraction
- [x] staged extraction and checksum re-verification
- [x] runtime recheck before swap
- [x] rollback tree preservation

### M3.4 — Rollback lifecycle

- [x] `mysticrollback`
- [x] stopped-runtime preflight
- [x] sibling/root ownership contract
- [x] collision-free failed-tree preservation
- [x] manual-only cleanup policy

### M3.5 / M5.4–M5.5 — Recovery observability and transaction hardening

- [x] schema-v1 recovery state outside Mystic root
- [x] backup/restore/rollback result metrics
- [x] restore transaction journal
- [x] archive identity checks through verify/stage/commit
- [x] journal states `prepared`, `old-moved`, `new-installed`
- [x] journal-aware rollback recovery
- [x] exact journal-associated rollback requirement

## Completed live monitoring and deployment

### M4.1 — Terminal watch

- [x] `mysticwatch` / `mystictools watch`
- [x] bounded refresh interval, one-shot/count modes and JSON
- [x] privacy-safe node/action display
- [x] single-observation snapshot reuse

### M4.2 — HTTP Prometheus exporter

- [x] `mysticexporter` / `mystictools exporter`
- [x] loopback default `127.0.0.1:9108`
- [x] `/metrics` and `/healthz`
- [x] GET/HEAD only
- [x] no access log or mutating endpoints

### M4.3–M4.5 — Deployment and OCI

- [x] hardened systemd example
- [x] Prometheus scrape example
- [x] Docker/Compose exporter deployment
- [x] amd64/arm64 OCI publication workflow
- [x] GHCR publication and optional Docker Hub publication
- [x] published-image smoke test
- [x] host PID visibility documented for containerized procfs discovery

### M4.6 — Complete standalone suite

- [x] standalone names for the planned suite
- [x] umbrella commands for the planned suite
- [x] standalone dispatcher qualified against the real argparse path

## Completed pre-release hardening

### M5.1 — Credential-safe runtime argv

- [x] redact Mystic short credential flags and common long forms
- [x] preserve raw argv only for internal classification/node parsing

### M5.2–M5.5 — Backup/restore/rollback hardening

- [x] hostile archive/member tests
- [x] exact manifest payload enforcement
- [x] safe symlink contract
- [x] streaming hashes
- [x] backup self-verification
- [x] restore archive TOCTOU/digest checks
- [x] transaction journal and journal-aware recovery

### M5.6 — Provider/data-quality hardening

- [x] future/stale node timestamp handling
- [x] duplicate/type validation
- [x] user snapshot freshness and explicit scan completeness
- [x] no partial user aggregate totals

### M5.7 — Doctor/health semantics

- [x] `critical > unavailable`
- [x] shared snapshots for doctor/metrics
- [x] watch avoids duplicate metrics probe round

### M5.8 — FidoNet/doors hardening

- [x] root-relative environment paths
- [x] malformed INI surfaced explicitly
- [x] per-entry filesystem scan errors surfaced
- [x] doctor sees scan/config degradation

### M5.9 — CLI/package qualification

- [x] correct standalone subcommand argument placement
- [x] real-parser tests for all dispatcher-based standalone tools
- [x] wheel + sdist build in CI
- [x] clean wheel install smoke
- [x] all installed console scripts `--help` smoke
- [x] clean sdist install smoke

### M5.10 — Release-contract/documentation freeze

- [x] refresh release-facing README
- [x] freeze intended v0.1.0 Prometheus namespace/semantics
- [x] document v0.1.0 CLI/recovery/CI contract
- [x] classify remaining work as qualification rather than feature expansion

## M6 — Release qualification

### M6.0 — Real Mystic runtime qualification — IN PROGRESS

- [x] define explicit real-runtime qualification protocol
- [x] add machine-readable read-only qualification harness
- [x] smoke qualification harness on Python 3.10/3.12 CI
- [ ] Real Mystic 1.12 A48 Linux qualification in a controlled installation/UBB environment
- [ ] Runtime-qualify `extras/mystic/export_node.mpy`, including output-location assumptions
- [ ] Runtime-qualify `extras/mystic/export_users.mpy` and exact field aliases returned by `getuserid(ID)`
- [ ] Qualify FidoNet diagnostics against explicit real Mystic paths and representative state
- [ ] Qualify door discovery against real `tempN` directories
- [ ] End-to-end disposable offline backup -> verify -> restore -> rollback qualification

See `M6_RUNTIME_QUALIFICATION.md` for the execution protocol.

### M6.1 — Release candidate

- [ ] Review/redact M6 qualification evidence and record final PASS report
- [ ] Final release-candidate CI + published OCI smoke
- [ ] Confirm metric schema 3 and CLI surface unchanged since freeze
- [ ] Version bump `0.1.0.dev0` -> `0.1.0`
- [ ] Release notes, tag and publication

## Post-v0.1.0 candidates

- optional stale-fragment cleanup command/design
- optional recovery-state history beyond last result per operation
- optional explicit recovery-tree cleanup tooling
- optional deeper Mystic-side menu/Python integration
- optional web UI
- additional low-cardinality metrics where justified

Not planned: reverse-engineering proprietary Mystic databases, automatic FidoNet repair, automatic door-state repair, or high-cardinality user/node Prometheus labels.
