# Decisions

Decisions about how the project is run and released. Design choices for each feature are in its folder under `specs/`.

| # | Decision | Who, when |
|---|---|---|
| 1 | The project is published as a fresh public repository with a single initial commit. The earlier history is not public, so commit hashes and dates in older specs refer to it. | Owner, 2026-10-14 |
| 2 | `CLAUDE.md` is self-contained. It no longer syncs rules from the owner's private template repo, and it names only tools and skills that are present in this repository. | Owner, 2026-10-14 |
| 3 | Spec Kit governs every change a user can see, and every behaviour change is test-first. This replaces an older line in `CLAUDE.md` that said Spec Kit was not used here. | Owner, 2026-10-14 |
| 4 | The first public release is version 1.0.0, dated 2026-10-14, and versions follow Semantic Versioning from here. | Owner, 2026-10-14 |
| 5 | The tool reads its key and virtual environment only from the repository or the environment. Hardcoded home-folder paths and the fallback to another local tool were removed (spec 004). | Owner, 2026-10-14 |
| 6 | `Scribe Desk.app` is no longer tracked, because a tracked bundle cannot find a clone in an arbitrary folder once moved. `setup.sh` builds it with the clone's path written in, and its icon is kept at `app/icon.icns`. | Owner, 2026-10-14 |
| 7 | Security problems are reported privately through GitHub's private vulnerability reporting, not in public issues. | Owner, 2026-10-14 |
