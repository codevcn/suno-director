# Upstream Tracking & Sync Policy

This repository treats both upstream repositories as **read-only knowledge sources** via Git submodules:
- `upstream/bitwize` -> `https://github.com/bitwize-music-studio/claude-ai-music-skills.git`
- `upstream/composition` -> `https://github.com/jtydhr88/music-composition-skills.git`

Pinned commits and watched paths are recorded in `upstream-lock.yaml`.

---

## 1. Golden Rules

1. **Never edit files inside `upstream/`** directly.
2. **Never auto-merge or overwrite** local `skills/`, `schemas/`, or `adapters/` from upstream changes.
3. **Never copy third-party book quotations or Chinese reference prose** from `upstream/composition` (`NOTICE` restriction).

---

## 2. Standard Upstream Sync Pipeline

```text
Detect (check_upstreams.py)
  -> Diff (inspect changed watched_paths between locked commit and remote HEAD)
  -> Classify (relevant to V1 skills/adapters vs irrelevant/Phase-2-only)
  -> Review (human or architect review of impact on SONG-SPEC / Ownership / Adapters)
  -> Adapt (manually synthesize improvements into our skills/, schemas/, or adapters/)
  -> Tests (run pytest + validate_spec + render_suno_pack)
  -> Update Lock (update submodule pin & upstream-lock.yaml + governance/ADOPTION.md)
```

---

## 3. Running `scripts/check_upstreams.py`

`check_upstreams.py` is strictly **non-mutating** (read-only against local source and lockfile):
- Reads `upstream-lock.yaml`.
- Checks current submodule HEAD commit vs locked commit.
- Queries remote `HEAD` (via `git ls-remote`) or compares fetched refs without modifying working files or `upstream-lock.yaml`.
- Reports `UPSTREAM STATUS` and highlights any changed `watched_paths` when local/remote commits are available.
