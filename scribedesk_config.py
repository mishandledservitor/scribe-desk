#!/usr/bin/env python3
"""Project registry + per-project settings for Scribe Desk.

A *project* is a named transcription context (a company's meetings, a podcast,
a TTRPG table, ...) that carries its own ElevenLabs Scribe settings — most
usefully its own **keyterms** (people / product / jargon names to bias
recognition toward), plus speaker labels, diarization defaults, output format,
and where its transcripts get written.

Adapted from voxbox/projects (same architecture, same registry format).

Layout on disk (all under this folder):

    projects.json            registry of projects (slug = immutable id)
    config/<slug>.json       one settings profile per project
    inbox/                   SHARED drop-folder for audio (pick project per run)
    output/<slug>/           default per-project transcripts
    processed/               SHARED — audio moved here after a successful run

A project can send its transcripts somewhere else entirely via the `output_dir`
setting — the point of a project being a *context* is that its output usually
belongs with the rest of that context's work, not in a scratch folder here. See
`resolve_output_dir`.

Mirrors bankzero-ynab's account model: the slug is the stable identity, the
display name is editable, and the registry tracks which project you used last.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl  # POSIX only; the tool targets macOS.
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

SCRIPT_DIR = Path(__file__).resolve().parent
INBOX_DIR = SCRIPT_DIR / "inbox"            # shared across projects
OUTPUT_DIR = SCRIPT_DIR / "output"          # per-project subfolders live here
PROCESSED_DIR = SCRIPT_DIR / "processed"    # shared
CONFIG_DIR = SCRIPT_DIR / "config"
PROJECTS_FILE = SCRIPT_DIR / "projects.json"

REGISTRY_VERSION = 1
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
MAX_SLUG_LEN = 64                # a slug becomes a filename; stay well inside NAME_MAX

DEFAULT_PROJECT_NAME = "Default"

# One profile per project. Keyterms is the headline field; the rest are the
# Scribe knobs the GUI exposes so switching projects restores a full setup.
DEFAULT_SETTINGS: dict = {
    "model": "scribe_v2",
    "language": "",                 # "" = auto-detect
    "speakers": True,               # diarize
    "num_speakers_mode": "auto",    # "auto" | "fixed"
    "num_speakers": 2,
    "diarization_threshold": 0.22,
    "labels": "",                   # e.g. "0=DM,1=Player 1"
    "detect_speaker_roles": False,
    "tag_audio_events": False,
    "no_verbatim": True,            # scribe_v2 only
    "keyterms": [],                 # list[str]
    "temperature_enabled": False,
    "temperature": 0.0,
    "seed_enabled": False,
    "seed": 42,
    "timestamps": "word",           # word | character | none
    "format": "text",               # text | srt | vtt | json
    "inline_timestamps": True,
    "output_dir": "",               # "" = managed default, output/<slug>
}


class ConfigError(Exception):
    """User-facing configuration error (shown in a dialog)."""


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for d in (INBOX_DIR, OUTPUT_DIR, PROCESSED_DIR, CONFIG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def write_json_atomic(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def _lock(path: Path):
    """Best-effort advisory lock so two open GUIs don't corrupt the registry."""
    if fcntl is None:
        yield
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        finally:
            fh.close()


def slugify(name: str) -> str:
    n = unicodedata.normalize("NFKD", name or "")
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.encode("ascii", "ignore").decode("ascii").lower()
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    # Capped so a long project name can't produce a filename the OS refuses:
    # the write happens after the registry entry is committed, so the failure
    # would leave a project that half-exists.
    return n[:MAX_SLUG_LEN].strip("_") or "project"


def assert_safe_slug(slug: str) -> None:
    """Guard against path traversal from a hand-edited/corrupted registry."""
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise ConfigError(f"Unsafe project id: {slug!r}")
    if len(slug) > MAX_SLUG_LEN:
        raise ConfigError(f"Project id too long ({len(slug)} chars): {slug!r}")


def unique_slug(base: str, taken: set[str]) -> str:
    """base, else base-2, base-3... avoiding both live slugs and any orphaned
    config file. Archived settings (`<slug>.json.deleted-<stamp>`) deliberately
    don't reserve a slug: re-creating a deleted project should get the slug
    back, with the archive left beside it to restore from by hand."""
    base = (base or "project")[:MAX_SLUG_LEN].strip("_") or "project"

    def in_use(candidate: str) -> bool:
        return candidate in taken or (CONFIG_DIR / f"{candidate}.json").exists()

    if not in_use(base):
        return base
    i = 2
    while True:
        suffix = f"-{i}"
        # Budget for the suffix. A base already at the cap would otherwise
        # produce an over-long slug that assert_safe_slug rejects — after
        # add_project has committed the registry entry, which used to leave a
        # project the code could no longer load.
        candidate = base[:MAX_SLUG_LEN - len(suffix)].strip("_") + suffix
        if not in_use(candidate):
            return candidate
        i += 1


# --------------------------------------------------------------------------- #
# Registry (projects.json)
# --------------------------------------------------------------------------- #

def _new_registry() -> dict:
    return {"version": REGISTRY_VERSION, "last_used_slug": None, "projects": []}


def _read_registry_or_rebuild() -> dict:
    try:
        return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        if PROJECTS_FILE.exists():
            try:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                PROJECTS_FILE.rename(PROJECTS_FILE.with_name(
                    PROJECTS_FILE.name + f".corrupt-{stamp}"))
            except OSError:
                pass
        doc = _new_registry()
        write_json_atomic(PROJECTS_FILE, doc)
        return doc


def _validate(doc: dict) -> dict:
    if not isinstance(doc, dict):
        doc = _new_registry()
    projects = doc.get("projects")
    if not isinstance(projects, list):
        projects = []
    clean: list[dict] = []
    seen: set[str] = set()
    for p in projects:
        if not isinstance(p, dict):
            continue
        slug = p.get("slug")
        # Length is checked here too, not just in assert_safe_slug: an entry
        # the rest of the code refuses to load must be dropped on read, so a
        # registry that got poisoned once heals instead of failing forever.
        if (not (isinstance(slug, str) and SLUG_RE.match(slug))
                or len(slug) > MAX_SLUG_LEN or slug in seen):
            continue
        seen.add(slug)
        p.setdefault("name", slug)
        p.setdefault("created", now_utc_iso())
        p.setdefault("last_used", None)
        clean.append(p)
    doc["projects"] = clean
    slugs = {p["slug"] for p in clean}
    if doc.get("last_used_slug") not in slugs:
        doc["last_used_slug"] = clean[0]["slug"] if clean else None
    doc.setdefault("version", REGISTRY_VERSION)
    return doc


def _migrate_long_slugs(doc: dict) -> dict:
    """Shorten any slug from before MAX_SLUG_LEN existed, bringing its settings
    and transcripts along.

    Versions before the cap could write a slug of any length. `_validate` drops
    what it can't load, which is right for an entry whose settings write failed
    — nothing is orphaned — but wrong here: the project has a real config and a
    real output folder, and dropping it makes both unreachable while the empty
    registry seeds a fresh "Default" over the top. Rename instead.
    """
    projects = doc.get("projects")
    if not isinstance(projects, list):
        return doc
    over = [p for p in projects
            if isinstance(p, dict) and isinstance(p.get("slug"), str)
            and len(p["slug"]) > MAX_SLUG_LEN and SLUG_RE.match(p["slug"])]
    if not over:
        return doc
    taken = {p["slug"] for p in projects
             if isinstance(p, dict) and isinstance(p.get("slug"), str)}
    moved: list = []
    # Take the lock before anything moves, not just around the registry write.
    # `_lock` opens a file next to projects.json, so the one condition that
    # makes the write fail — an unwritable directory — makes acquiring the lock
    # fail too. Acquiring it afterwards meant the failure raised from the `with`
    # statement, before the rollback's `try` was ever entered: files renamed,
    # registry not, nothing put back. Failing here instead costs nothing,
    # because nothing has been touched yet.
    try:
        lock = _lock(PROJECTS_FILE)
        lock.__enter__()
    except OSError:
        return doc
    try:
        _migrate_locked(doc, over, taken, moved)
    finally:
        lock.__exit__(None, None, None)
    return doc


def _migrate_locked(doc: dict, over: list, taken: set, moved: list) -> None:
    """The moving half of `_migrate_long_slugs`, run under the registry lock."""
    for p in over:
        old = p["slug"]
        taken.discard(old)
        # Keep looking until BOTH destinations are free. Renaming the settings
        # but not the transcripts separates a project from its data — the exact
        # failure this migration exists to prevent — and `output/` can hold a
        # stray folder from a keep-files delete, so the collision is real.
        # Skipping instead would be worse than it looks: `_validate` drops what
        # it can't load, so a project left un-migrated disappears anyway.
        base = old[:MAX_SLUG_LEN].strip("_") or "project"
        new, i = base, 1
        while (new in taken or (CONFIG_DIR / f"{new}.json").exists()
               or (OUTPUT_DIR / new).exists()):
            i += 1
            suffix = f"-{i}"
            new = base[:MAX_SLUG_LEN - len(suffix)].strip("_") + suffix
        src_cfg, dst_cfg = CONFIG_DIR / f"{old}.json", CONFIG_DIR / f"{new}.json"
        src_out, dst_out = OUTPUT_DIR / old, OUTPUT_DIR / new
        try:
            if src_cfg.exists():
                src_cfg.rename(dst_cfg)
            if src_out.exists():
                src_out.rename(dst_out)
        except OSError:
            try:
                if dst_cfg.exists() and not src_cfg.exists():
                    dst_cfg.rename(src_cfg)
            except OSError:
                pass
            taken.add(old)
            continue
        taken.add(new)
        p["slug"] = new
        moved.append((src_cfg, dst_cfg, src_out, dst_out, p, old))
        if doc.get("last_used_slug") == old:
            doc["last_used_slug"] = new
    if not moved:
        return
    try:
        write_json_atomic(PROJECTS_FILE, doc)
    except OSError:
        # The files moved but the registry didn't. Left alone, the next run
        # would find the new names occupied, pick <new>-2, and point the
        # project at a slug with no config. Put the files back so the retry
        # starts from the state it expects.
        for src_cfg, dst_cfg, src_out, dst_out, p, old in moved:
            for dst, src in ((dst_cfg, src_cfg), (dst_out, src_out)):
                try:
                    if dst.exists() and not src.exists():
                        dst.rename(src)
                except OSError:
                    pass
            if doc.get("last_used_slug") == p["slug"]:
                doc["last_used_slug"] = old
            p["slug"] = old


def load_registry() -> dict:
    """Load (validating), seeding a default project on very first run."""
    ensure_dirs()
    doc = _validate(_migrate_long_slugs(_read_registry_or_rebuild()))
    if not doc["projects"]:
        doc = _seed_default(doc)
    return doc


def _seed_default(doc: dict) -> dict:
    slug = unique_slug(slugify(DEFAULT_PROJECT_NAME), set())
    doc["projects"].append({
        "slug": slug,
        "name": DEFAULT_PROJECT_NAME,
        "created": now_utc_iso(),
        "last_used": None,
    })
    doc["last_used_slug"] = slug
    write_json_atomic(PROJECTS_FILE, doc)
    save_settings(slug, dict(DEFAULT_SETTINGS))
    return doc


def list_projects() -> list[dict]:
    return list(load_registry()["projects"])


def get_project(slug: str) -> dict | None:
    for p in load_registry()["projects"]:
        if p["slug"] == slug:
            return p
    return None


def last_used_slug() -> str | None:
    return load_registry().get("last_used_slug")


def add_project(name: str) -> dict:
    name = (name or "").strip()
    if not name:
        raise ConfigError("Project name cannot be empty.")
    with _lock(PROJECTS_FILE):
        doc = _validate(_read_registry_or_rebuild())
        taken = {p["slug"] for p in doc["projects"]}
        slug = unique_slug(slugify(name), taken)
        # Validate before the registry is written, not after. The settings
        # write happens outside the lock; if the slug were rejected there, the
        # registry would already hold — and point last_used_slug at — an entry
        # nothing could load, which took the whole app down.
        assert_safe_slug(slug)
        entry = {"slug": slug, "name": name,
                 "created": now_utc_iso(), "last_used": None}
        doc["projects"].append(entry)
        doc["last_used_slug"] = slug
        write_json_atomic(PROJECTS_FILE, doc)
    if not (CONFIG_DIR / f"{slug}.json").exists():
        save_settings(slug, dict(DEFAULT_SETTINGS))
    return entry


def duplicate_project(src_slug: str, name: str) -> dict:
    """New project seeded with a copy of src's settings (keyterms and all).

    Except `output_dir`: the copy gets its own managed folder. Two projects
    writing into one folder interleaves their transcripts with nothing left to
    say which produced which, and a duplicate is a new context by definition —
    it inherits the setup, not the destination.
    """
    assert_safe_slug(src_slug)
    src_settings = load_settings(src_slug)
    src_settings["output_dir"] = ""
    entry = add_project(name)
    save_settings(entry["slug"], src_settings)
    return entry


def rename_project(slug: str, new_name: str) -> None:
    assert_safe_slug(slug)
    new_name = (new_name or "").strip()
    if not new_name:
        raise ConfigError("Project name cannot be empty.")
    with _lock(PROJECTS_FILE):
        doc = _validate(_read_registry_or_rebuild())
        for p in doc["projects"]:
            if p["slug"] == slug:
                p["name"] = new_name
                write_json_atomic(PROJECTS_FILE, doc)
                return
    raise ConfigError(f"Unknown project: {slug}")


def projects_using_output(path: Path,
                          *, exclude_slug: str | None = None) -> list[tuple[str, str]]:
    """`(slug, reason)` for every project that blocks `path` being deleted.

    Two projects can share a folder — one pointed at another's managed dir, or
    a pair pointed at the same place by hand — so "is this folder mine alone?"
    is a real question that can't be answered from the slug.

    Reason is `"shares"` or `"unreadable"`. This gates a deletion, so a project
    that can't be checked blocks it too: the cost is a folder left alone, and
    the alternative is a gate that opens whenever it errors. The two are told
    apart so the dialog can say which it is rather than accusing a project of
    sharing a folder it may well not.
    """
    out = []
    for p in load_registry()["projects"]:
        if p["slug"] == exclude_slug:
            continue
        try:
            if same_dir(output_dir_for(p["slug"]), path):
                out.append((p["slug"], "shares"))
        except (ConfigError, OSError, ValueError):
            out.append((p["slug"], "unreadable"))
    return out


def delete_project(slug: str, *, delete_output: bool = False) -> bool:
    """Remove a project. Returns whether its transcripts were deleted, so a
    caller that offered to delete them can tell the truth about what happened.

    `delete_output` only ever removes the managed output/<slug>, and only when
    no other project writes there — read before the settings file goes, and
    gated on `is_managed_output`. The GUI doesn't offer the option for a folder
    we don't own; this is the backstop.

    The settings file is archived rather than unlinked. A project's keyterms
    are hand-curated over months and live nowhere else — not in git, by design
    — so "remove the project" should not be indistinguishable from "burn the
    list". The archive is what makes an accidental delete recoverable.
    """
    assert_safe_slug(slug)
    out = output_dir_for(slug) if delete_output else None
    with _lock(PROJECTS_FILE):
        doc = _validate(_read_registry_or_rebuild())
        before = len(doc["projects"])
        doc["projects"] = [p for p in doc["projects"] if p["slug"] != slug]
        if len(doc["projects"]) == before:
            raise ConfigError(f"Unknown project: {slug}")
        if doc["last_used_slug"] == slug:
            doc["last_used_slug"] = (doc["projects"][0]["slug"]
                                     if doc["projects"] else None)
        write_json_atomic(PROJECTS_FILE, doc)
    cfg = CONFIG_DIR / f"{slug}.json"
    if cfg.exists():
        # Second-resolution stamps collide, and rename() overwrites silently —
        # which would let the archive destroy the archive. Microseconds, then
        # an explicit uniqueness loop.
        stamp = now_utc_iso().translate({ord(c): None for c in ":-"})[:21]
        dest = cfg.with_name(f"{slug}.json.deleted-{stamp}")
        i = 2
        while dest.exists():
            dest = cfg.with_name(f"{slug}.json.deleted-{stamp}-{i}")
            i += 1
        try:
            cfg.rename(dest)
        except OSError:
            # Leave the live config in place rather than unlinking it. An
            # orphan config is something unique_slug already copes with; a
            # settings file deleted with neither archive nor error is not.
            pass
    if (out is None or not is_managed_output(slug, out)
            or projects_using_output(out, exclude_slug=slug)):
        return False
    # Delete the managed folder itself, never the path the user typed to reach
    # it. `out` may be a symlink aliasing this folder, and rmtree refuses
    # symlinks — with ignore_errors that failed silently, so the dialog
    # promised a deletion that never happened.
    import shutil
    target = managed_output_dir(slug)
    if target.is_symlink():
        # A managed folder that is itself a symlink points at transcripts kept
        # elsewhere on purpose. Removing the link would strand them and
        # removing its target is not ours to do, so leave both — and say so,
        # rather than reporting a deletion that didn't happen.
        return False
    if not target.exists():
        # Nothing was ever written — the commonest delete of all, a project
        # made by mistake. "Were the transcripts deleted?" is vacuously yes;
        # answering no makes the caller explain an absence that needs none.
        return True
    if not target.is_dir():
        return False
    shutil.rmtree(target, ignore_errors=True)
    return not target.exists()


def set_last_used(slug: str) -> None:
    assert_safe_slug(slug)
    with _lock(PROJECTS_FILE):
        doc = _validate(_read_registry_or_rebuild())
        found = False
        for p in doc["projects"]:
            if p["slug"] == slug:
                p["last_used"] = now_utc_iso()
                found = True
        if found:
            doc["last_used_slug"] = slug
            write_json_atomic(PROJECTS_FILE, doc)


# --------------------------------------------------------------------------- #
# Per-project settings (config/<slug>.json)
# --------------------------------------------------------------------------- #

def settings_path(slug: str) -> Path:
    assert_safe_slug(slug)
    return CONFIG_DIR / f"{slug}.json"


def load_settings(slug: str) -> dict:
    """Return the project's settings, merged over defaults (missing keys filled,
    unknown keys dropped)."""
    path = settings_path(slug)
    merged = dict(DEFAULT_SETTINGS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for k in DEFAULT_SETTINGS:
                if k in raw:
                    merged[k] = raw[k]
    except (OSError, json.JSONDecodeError):
        pass
    # keyterms is always a clean list[str].
    kt = merged.get("keyterms")
    if isinstance(kt, str):
        kt = re.split(r"[,\n]", kt)
    if not isinstance(kt, list):
        kt = []
    merged["keyterms"] = [str(t).strip() for t in kt if str(t).strip()]
    od = merged.get("output_dir")
    merged["output_dir"] = od.strip() if isinstance(od, str) else ""
    return merged


def save_settings(slug: str, settings: dict) -> None:
    assert_safe_slug(slug)
    clean = dict(DEFAULT_SETTINGS)
    for k in DEFAULT_SETTINGS:
        if k in settings:
            clean[k] = settings[k]
    kt = clean.get("keyterms") or []
    if isinstance(kt, str):
        kt = re.split(r"[,\n]", kt)
    clean["keyterms"] = [str(t).strip() for t in kt if str(t).strip()]
    od = clean.get("output_dir")
    clean["output_dir"] = od.strip() if isinstance(od, str) else ""
    write_json_atomic(settings_path(slug), clean)


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

def managed_output_dir(slug: str) -> Path:
    """The folder this tool owns for a project: output/<slug>."""
    assert_safe_slug(slug)
    return OUTPUT_DIR / slug


def resolve_output_dir(slug: str, raw: str | None) -> Path:
    """Where a project's transcripts go.

    Blank means the managed default. Anything else is the user's own folder —
    typically the project it belongs to (a repo's docs/, a meetings archive),
    which is the whole point of the setting. `~` expands; a relative path
    resolves against this folder so a hand-edited config behaves predictably.
    """
    assert_safe_slug(slug)
    raw = (raw or "").strip()
    if not raw:
        return managed_output_dir(slug)
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = SCRIPT_DIR / p
    # Collapse any .. without requiring the path to exist yet.
    return Path(os.path.normpath(p))


def output_dir_for(slug: str) -> Path:
    return resolve_output_dir(slug, load_settings(slug).get("output_dir"))


def same_dir(a: Path, b: Path) -> bool:
    """Whether two paths name the same directory.

    String comparison is not enough and the difference is a data-loss bug, not
    a nicety. `os.path.normpath` is purely textual: it sees through neither a
    symlink nor macOS's case-insensitive filesystem, so `output/target` and
    `output/TARGET` — the same directory, one of them merely typed differently
    — compared unequal, and the delete guard opened on both.

    Identity comes from `st_dev`/`st_ino` when both paths exist, which settles
    symlinks and case together. When one doesn't exist yet there is nothing to
    stat, so this falls back to `realpath` and then to a casefolded `realpath`
    — deliberately over-matching. That last branch is a real false positive on
    a case-sensitive volume, and it is the direction to err in: in
    `projects_using_output` a false "same" costs a folder left alone.

    It is NOT a blanket guarantee, and the asymmetry is worth stating because
    the next change here will be made against it: in `is_managed_output` a
    false "same" would mean the tool deciding someone's folder is its own
    scratch space. What keeps that safe is not this function — it is that
    `delete_project` removes `managed_output_dir(slug)` itself and never the
    path it was handed.
    """
    a, b = Path(os.path.normpath(a)), Path(os.path.normpath(b))
    if a == b:
        return True
    try:
        if a.exists() and b.exists():
            sa, sb = a.stat(), b.stat()
            return (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino)
    except (OSError, ValueError):
        pass
    ra, rb = os.path.realpath(a), os.path.realpath(b)
    return ra == rb or ra.casefold() == rb.casefold()


def is_managed_output(slug: str, path: Path) -> bool:
    """True only for the tool's own output/<slug>.

    The gate on deleting a folder: a project pointed at somewhere real holds
    files this tool never wrote, and losing those is not a recoverable mistake.
    """
    try:
        return same_dir(path, managed_output_dir(slug))
    except (OSError, ValueError, ConfigError):
        return False
