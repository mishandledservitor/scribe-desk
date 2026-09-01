# Phase 1 Data Model: A recycled project slug no longer adopts or destroys another project's transcripts

This feature changes behavior, not schema — no on-disk JSON shape changes. This document instead names the entities and the key operations (this module's closest thing to a contract) that the feature touches.

## Entities

### Project registry entry (inside `projects.json`)

| Field | Type | Notes |
|---|---|---|
| `slug` | `str` | Immutable identity; matches `SLUG_RE`, capped at `MAX_SLUG_LEN`. Unaffected by this feature's schema — only *how it is chosen* changes. |
| `name` | `str` | Editable display name. |
| `created` | ISO 8601 `str` | Set once at `add_project` time. |
| `last_used` | ISO 8601 `str` or `None` | Updated by `set_last_used`. |

No field is added or removed by this feature.

### Per-project settings (`config/<slug>.json`)

Unchanged shape (`DEFAULT_SETTINGS` keys). The only behavior change is in how the `keyterms` field is *parsed* when it arrives as a raw string (newline-split only, not comma-split); the stored shape is still `list[str]`.

## Key operations (the module's contract)

### `unique_slug(base: str, taken: set[str]) -> str` — CHANGED

- **Before**: a candidate is "in use" if it is in `taken` or `(CONFIG_DIR / f"{candidate}.json").exists()`.
- **After**: a candidate is "in use" if additionally `(OUTPUT_DIR / candidate).exists()`, via the new shared helper (Decision 1 in research.md).
- **Callers unaffected in signature**: `add_project`, `_seed_default` — both already pass `taken` computed from the live registry; no caller change needed beyond the internal in-use check.

### `_slug_in_use(candidate: str, taken: set[str]) -> bool` — NEW (private helper)

- Encapsulates the three-way check: `candidate in taken or (CONFIG_DIR / f"{candidate}.json").exists() or (OUTPUT_DIR / candidate).exists()`.
- Used by both `unique_slug` and `_migrate_locked` (replacing `_migrate_locked`'s inline `while` condition body, behavior-preserving there).

### `_read_registry_or_rebuild() -> dict` — CHANGED

- **Before**: `except (OSError, json.JSONDecodeError)` — both trigger rename-to-`.corrupt-<stamp>` and a fresh empty registry.
- **After**: `except json.JSONDecodeError` triggers the existing rename-and-rebuild path, unchanged. A new `except OSError as e` clause raises `ConfigError(f"Could not read project registry at {PROJECTS_FILE}: {e}")` and performs no rename and no write.
- **Callers affected**: `load_registry` (and therefore `list_projects`, `get_project`, `last_used_slug`, every registry-mutating function that calls `_read_registry_or_rebuild` under `_lock`) now propagate `ConfigError` instead of silently returning an emptied-then-reseeded registry when the underlying error is an `OSError`. This is the intended behavior change (FR-004): the caller (eventually the GUI) sees an error instead of a lie.

### `load_settings(slug: str) -> dict` / `save_settings(slug: str, settings: dict) -> None` — CHANGED

- The keyterms-normalization sub-step changes from `re.split(r"[,\n]", kt)` to `kt.splitlines()` when `kt` is a `str`. The subsequent `[str(t).strip() for t in kt if str(t).strip()]` pass is unchanged, so whitespace-only lines still drop and every entry is still stripped.
- Signature and return shape unchanged.

## State transitions

No new state machine. The only transition of note, made safe by this feature: **project deleted (transcripts kept) → same-named project created** no longer transitions the new project into occupying the old project's `output/<slug>` — the allocator instead produces a fresh, never-before-used slug (e.g. `acme-2`), matching the transition `_migrate_locked` already guarantees when resolving a long-slug collision.
