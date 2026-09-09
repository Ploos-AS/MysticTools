# Prometheus contract

This document defines the public Prometheus contract intended for MysticTools v0.1.0.

## Stability policy

All public metric names use the `mystictools_*` namespace. Once v0.1.0 is tagged, these names and their meanings are treated as a compatibility surface.

The current structured metrics schema is version 3. Schema version 3 is the v0.1.0 baseline unless a release-blocking defect requires one final pre-release change.

MysticTools follows these rules:

- Prometheus remains optional; human-readable and JSON output are equally supported.
- No user ID, handle, path, PID, address or other high-cardinality value is used as a Prometheus label.
- Source-dependent values are omitted when the source is unavailable or unqualified rather than emitted as false zeroes.
- Availability/qualification metrics are explicit where meaningful.
- A numeric user aggregate is emitted only when the corresponding field is complete and valid across the qualified users snapshot.
- Doctor severity codes are `0=ok`, `1=warning`, `2=unavailable`, `3=critical`.
- Health status codes are `0=ok`, `1=warning`, `2=unknown`, `3=critical`.

## v0.1.0 metric names

Runtime and operating state:

```text
mystictools_runtime_available
mystictools_network_available
mystictools_mis_running
mystictools_node_processes
mystictools_listener_count
mystictools_logs_discovered
mystictools_disk_free_bytes
mystictools_disk_free_percent
mystictools_operational_warnings
mystictools_health_status
mystictools_doctor_status
mystictools_doctor_warnings
mystictools_doctor_critical
mystictools_doctor_unavailable
```

Native node provider:

```text
mystictools_node_provider_available
mystictools_node_provider_qualified
mystictools_node_fragment_count
mystictools_node_fragment_fresh
mystictools_node_fragment_stale
mystictools_node_fragment_max_age_seconds
```

Users provider and aggregate statistics:

```text
mystictools_users_provider_available
mystictools_users_provider_qualified
mystictools_users_count
mystictools_users_total_calls
mystictools_users_total_uploads
mystictools_users_total_downloads
mystictools_users_total_posts
```

FidoNet and doors:

```text
mystictools_fidonet_config_qualified
mystictools_fidonet_busy_files
mystictools_fidonet_outbound_queue_candidates
mystictools_fidonet_inbound_packets
mystictools_fidonet_poll_active
mystictools_door_node_temp_dirs
mystictools_door_dropfiles
mystictools_door_unreadable_dropfiles
```

Recovery observability:

```text
mystictools_recovery_state_available
mystictools_recovery_state_qualified
mystictools_last_backup_success
mystictools_last_backup_age_seconds
mystictools_last_restore_success
mystictools_last_restore_age_seconds
mystictools_last_rollback_success
mystictools_last_rollback_age_seconds
mystictools_recovery_rollback_trees
mystictools_recovery_failed_trees
mystictools_recovery_trees
```

## Exporter

`mysticexporter` and `mystictools exporter` expose `/metrics` and `/healthz` and bind to `127.0.0.1:9108` by default.

Exporter service health is intentionally separate from BBS health: `/healthz` reports whether MysticTools can produce a snapshot, while the Prometheus/JSON payload carries the actual Mystic health and doctor states.

The core exporter provides no TLS or authentication. Remote exposure should use explicit bind configuration plus a firewall or reverse proxy.

## Change policy after v0.1.0

Compatible additions may add new metrics. Renaming, removing or materially changing the meaning of an existing metric requires an explicit compatibility decision and, when appropriate, a metrics schema increment. New high-cardinality labels are not acceptable merely for convenience.
