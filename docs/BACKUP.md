# MysticTools backup consistency model

`mystictools backup` creates a gzip-compressed tar archive of the Mystic installation root plus a versioned `mystictools-backup-manifest.json`.

## Safety defaults

The default mode is an **offline backup**. MysticTools refuses to create the archive when it detects running `MIS` or `mystic` processes. This is intentional: copying a live BBS tree can capture mutually inconsistent application files even when every individual filesystem read succeeds.

A destination must be outside the Mystic installation root and must not already exist. MysticTools writes to a temporary sibling archive and atomically renames it into place only after archive creation succeeds.

If procfs runtime state is unavailable, backup is refused by default. `--allow-unverified` exists only for a sysop who has independently established that Mystic is stopped.

`--allow-live` permits a **best-effort live backup**. Such an archive is explicitly marked `best-effort-live`; MysticTools does not claim application-level consistency for it.

## Manifest schema v1

The embedded manifest records:

- schema version
- creation timestamp
- original source root
- consistency classification (`offline`, `best-effort-live`, or `unverified`)
- whether runtime state was available
- whether the BBS was detected running
- regular-file count
- every regular file's relative path, size, mode, mtime and SHA-256
- every symbolic link's relative path and link target

The completed archive itself is also SHA-256 hashed and the CLI reports that digest.

## Scope

M3.1 intentionally backs up the complete Mystic root rather than guessing which Mystic files are disposable. No proprietary data structures are parsed or modified and no transient files are silently excluded. A future exclusion policy may only be added when its semantics are documented and qualification-tested.

## Restore boundary

M3.1 does not implement restore. Restore must first validate the archive shape and manifest, reject unsafe paths/symlink traversal, verify checksums, require an inactive target BBS, and provide preflight/dry-run behavior before writing any Mystic file.
