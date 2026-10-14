# Phase 0 Research: A recycled project slug no longer adopts or destroys another project's transcripts

No NEEDS CLARIFICATION markers were left in the spec, and no new external technology choice is being made — every decision below is a design choice inside a single existing module, resolved by reading that module's own code and the adversarial review that found the bugs.

## Decision 1 — How to unify the three-way in-use check

**Decision**: Extract the collision test `_migrate_locked` already performs (`new in taken or (CONFIG_DIR / f"{new}.json").exists() or (OUTPUT_DIR / new).exists()`) into a single shared helper, e.g. `_slug_in_use(candidate, taken)`, and call it from both `unique_slug` and `_migrate_locked`.

**Rationale**: The review's own diagnosis of finding 0 is that the correct three-way check already exists in one place and was never carried to the other. A shared helper makes that the structural default rather than a convention two call sites have to remember — exactly what Constitution Principle III asks for ("must treat the registry, the config file, and the output folder as one three-way check, matching the standard `_migrate_locked` already sets").

**Alternatives considered**: Duplicating the three-way check inline into `unique_slug` (rejected — this is exactly the drift that caused the bug; a second inline copy is a second place to forget to update) — a shared helper is the only option that makes a future divergence structurally harder rather than merely documented against.

## Decision 2 — Where to draw the OSError/JSONDecodeError line

**Decision**: `_read_registry_or_rebuild` catches `json.JSONDecodeError` (including the case where the file is empty, which fails to parse as JSON) as the only trigger for archive-and-rebuild. A separate `except OSError` clause raises a new `ConfigError` naming `str(PROJECTS_FILE)` and the underlying `OSError` message, with no rename and no write.

**Rationale**: This is exactly the distinction the spec draws and the review names directly: "an `OSError` covers a permissions blip, `EIO`, an NFS/iCloud stall, a full disk, and a file momentarily locked by another tool. None of those means the registry is corrupt." `ConfigError` already exists in the module as "User-facing configuration error (shown in a dialog)" — reusing it rather than inventing a new exception type keeps one exception surface for the GUI to catch.

**Alternatives considered**: Adding a new dedicated exception subclass (e.g. `RegistryUnreadableError`) — rejected for this feature since `ConfigError`'s existing docstring already promises exactly the behavior needed (a dialog-worthy, user-facing error) and the GUI layer already has one place that would need to catch it either way; a subclass can be introduced later without breaking this contract if a caller ever needs to distinguish the two `ConfigError` causes programmatically.

## Decision 3 — How to stop keyterms splitting on comma

**Decision**: In both `load_settings` and `save_settings`, change the keyterm-normalization regex/split from `re.split(r"[,\n]", kt)` to splitting on newline only (`kt.splitlines()`), when `kt` arrives as a string. List-shaped input (already a `list[str]`, e.g. from a already-clean load) is unaffected — the `.strip()`-and-drop-empty pass after it is unchanged.

**Rationale**: The three-point trace in the review (`scribedesk_gui.py:985`, `:1015`, `scribedesk_stt.py:510`) shows comma-splitting happening at the *GUI/CLI* boundary — but the review's own proposed queue item suggests fixing it "at the GUI/CLI boundary... or the shared choke point," and `scribedesk_config.py`'s `load_settings`/`save_settings` is the one function pair every path (GUI save, GUI load, CLI's own settings read for defaults) passes through, per this repo's own module-boundary documentation. Fixing it there closes the gap without needing to touch `scribedesk_gui.py` or `scribedesk_stt.py`'s CLI argument parsing (which joins with `,`) — as long as the stored, round-tripped representation itself never re-splits on comma, a comma-containing term survives `load_settings`/`save_settings` round trips, which is what the spec's User Story 3 and SC-003 test.

**Alternatives considered**: Changing the GUI's `_collect_form` and the CLI's `--keyterms` argparse handling to a non-comma delimiter (e.g. repeated `--keyterm` flags, as the review's fuller proposal suggests) — out of scope for this feature; the spec's Assumptions section scopes this fix to the shared `scribedesk_config.py` normalization only, since GUI/CLI argv changes are a larger, separately-worth-speccing surface (finding 4's proposed queue item goes further than this feature claims to fix, e.g. the leading-hyphen argparse crash, which stays open).

## Decision 4 — Test sandboxing technique

**Decision**: Each test in `test_scribedesk_config.py` creates a fresh `tempfile.mkdtemp()`, monkeypatches the module's six path constants to point inside it, calls `ensure_dirs()`, and tears down (or relies on process exit / a per-test cleanup) rather than ever touching the real repo's `output/`, `config/`, or `projects.json`.

**Rationale**: This is the exact technique the review's own `probe1.py`/`probe3.py` used and that this feature's Constitution Principle IV requires. It reproduces bugs against the *real* `scribedesk_config.py` functions, not reimplementations of them.

**Alternatives considered**: `unittest.mock.patch` on individual functions (rejected — mocking the function under test defeats the point of a regression test); a `pytest` `tmp_path` fixture (rejected — the repo's two existing test files are plain `unittest` with no pytest dependency, and this feature follows that convention rather than introducing a new one for one file).
