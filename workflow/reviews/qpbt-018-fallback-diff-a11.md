# QPBT-018 fallback transplant scout (a11)

## Verdict

Manual transplant is appropriate; do not cherry-pick `e21c9cda11803f7564a500c005fd55882530538d`
onto the current worktree. Its implementation parent is
`1273f1dc9fed33b6a5eafd5e25e6081c8b32ceb7`, based on the pre-QPBT-021 cache
script, while the target is exactly `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`.

The minimal production change is confined to
`scripts/hot_main_cache.py:1891-1901`: replace the current two-command loop with
the clone/recovery/checkout body from the approved blob at
`e21c9cd:scripts/hot_main_cache.py:875-907`. No QPBT-021 Mathlib code should be
moved or changed. The transplant preserves the initial local clone, retries once
with `--no-local` only after newly appended clone diagnostics contain
`cross-device` or `EXDEV`, removes the partial checkout, logs the decision, and
then performs the same exact detached checkout.

The old two tests are useful but not sufficient verbatim for the strengthened
acceptance gates. Transplant their intent near
`tests/test_hot_main_cache.py:348-355`, strengthen command assertions, and add a
bounded/no-stale-diagnostic regression.

No files in either repository were edited and no tests, builds, warm/seed,
Lean/Lake, network, or cache operation was run.

## Evidence

The failure envelope is an exact match for the approved recovery:

- `failure.json:3-4` binds cache key
  `a58247f0df1a7ed05bdd72917f3fd9a404a82c542db4c4fa6a129d5dd9b63de0`
  to current main commit `c5a0fecc26eb18452219cf0df31ce2a9113e45f1`.
- `failure.json:70-73` records failure before Mathlib preparation:
  `detached clone command failed with exit code 128`,
  `mathlib_source_required: true`, and `mathlib_source: null`.
- `build.log:1` is the initial local clone destination.
- `build.log:2` is explicit EXDEV evidence from Git object hard-link creation:
  `Invalid cross-device link` under `checkout/.git/objects/...`.

The current regression is at `scripts/hot_main_cache.py:1891-1901`: it always
runs `git clone --local --no-checkout` and immediately raises on any nonzero
status, so it never reaches object-copy mode.

The approved implementation at
`e21c9cd:scripts/hot_main_cache.py:875-907` does the following in order:

1. Builds the unchanged initial command
   `git clone --local --no-checkout <repo> <checkout>` (`:876-877`).
2. Captures the pre-command log size (`:878-881`).
3. Runs the local clone and, only on failure, seeks to that saved offset and
   reads only bytes appended by this attempt (`:882-889`).
4. Recognizes lower-cased `cross-device` or `exdev` evidence (`:890`).
5. Unlinks a partial symlink/file or recursively removes the exact partial
   checkout directory (`:891-895`). If the path does not exist, it does nothing;
   if it is an unsupported special entry or cleanup fails, recovery safely does
   not proceed.
6. Appends the explicit fallback marker and mutates only option position 2 from
   `--local` to `--no-local` (`:896-899`). There is no loop around this retry, so
   a second failure falls through to the single error at `:900-901`.
7. Runs the unchanged exact checkout
   `git -C <checkout> checkout --detach <identity.main_commit>` and rejects any
   nonzero result (`:903-906`).

Logging remains append-only in production because current `_run_logged` opens
the log as `ab` at `scripts/hot_main_cache.py:1876-1889`. The original local-clone
diagnostic, the fallback marker, and subsequent clone/checkout diagnostics are
therefore all retained. On failure, current warm handling moves that log into
the retained envelope (`:2205-2217`), writes `failure.json` (`:2217-2227`), and
removes staging (`:2228-2229`).

## Exact patch shape

In `scripts/hot_main_cache.py`, replace only current lines `1893-1900` with the
approved shape below; leave the method signature and `return checkout` intact:

```python
clone = ["git", "clone", "--local", "--no-checkout", str(self.repo_root), str(checkout)]
try:
    clone_log_offset = log_path.stat().st_size
except FileNotFoundError:
    clone_log_offset = 0
return_code = self._run_logged(staging, clone, log_path)
if return_code != 0:
    try:
        with log_path.open("rb") as log:
            log.seek(clone_log_offset)
            clone_log = log.read().decode("utf-8", errors="replace").lower()
    except OSError:
        clone_log = ""
    cross_device = "cross-device" in clone_log or "exdev" in clone_log
    if cross_device:
        if checkout.is_symlink() or checkout.is_file():
            checkout.unlink()
        elif checkout.is_dir():
            shutil.rmtree(checkout)
        with log_path.open("ab") as log:
            log.write(
                b"[hot-main-cache] local clone failed with EXDEV; retrying --no-local\n"
            )
        clone[2] = "--no-local"
        return_code = self._run_logged(staging, clone, log_path)
if return_code != 0:
    raise CacheError(f"detached clone command failed with exit code {return_code}")

checkout_command = [
    "git", "-C", str(checkout), "checkout", "--detach", self.identity.main_commit
]
return_code = self._run_logged(staging, checkout_command, log_path)
if return_code != 0:
    raise CacheError(f"detached clone command failed with exit code {return_code}")
```

`shutil` is already imported at current `scripts/hot_main_cache.py:24`; no import,
schema, recipe, manifest, or metric change is needed. Keeping the existing
manifest value `source: detached-local-clone` at `:2161` is accurate at the
source-identity level, though it no longer distinguishes local-hardlink versus
object-copy transport. The fallback marker in `build.log` supplies that
operational distinction.

## Required focused regressions

Add tests after current `tests/test_hot_main_cache.py:348-353`.

### 1. Exact command order and partial-checkout cleanup

Adapt old `test_detached_clone_retries_without_local_hardlinks_on_exdev`
(`e21c9cd:tests/test_hot_main_cache.py:219-244`) but strengthen it to:

- append, rather than overwrite, `Invalid cross-device link` in the fake;
- create a marker inside the failed partial checkout and assert the fallback
  invocation sees that the old checkout/marker is gone before recreating it;
- assert the complete command list, not slices:
  local clone; same clone with only `--no-local`; exact `git -C ... checkout
  --detach manager.identity.main_commit`;
- assert both the original diagnostic and fallback marker remain in the log.

This proves initial `--local`, object-copy fallback, safe cleanup, exact checkout,
and command order.

### 2. Newly appended evidence and bounded retry

Add a focused test (two subtests are reasonable):

- Prepopulate `build.log` with an old `EXDEV` line; have the initial local clone
  append only an unrelated failure and return nonzero. Assert `CacheError`, one
  command total, no `--no-local`, and no retry marker. This proves detection is
  limited to newly appended diagnostics.
- Have the local clone append an EXDEV diagnostic and fail, then have the
  `--no-local` clone append another EXDEV diagnostic and fail. Assert exactly two
  commands total and no checkout command. This proves retry is bounded to one.

The approved implementation already has both properties structurally, but the
old tests did not lock them down.

### 3. Invalid fallback checkout never publishes

Transplant old
`test_warm_exdev_fallback_checkout_failure_publishes_no_snapshot`
(`e21c9cd:tests/test_hot_main_cache.py:246-277`) against the current test recipe.
Retain its local-fail, fallback-success, checkout-fail sequence and strengthen
the assertions to:

- compare all three commands exactly, including `--no-checkout`, repository and
  destination paths, and `manager.identity.main_commit`;
- assert `manager.is_ready()` is false;
- assert `manager.snapshot_dir` does not exist and
  `list(manager.runtime_dir.rglob("READY")) == []`;
- assert exactly one failure envelope exists, it has no `READY`, and its log
  contains local EXDEV evidence, the retry marker, and checkout failure;
- optionally assert `failure.json["mathlib_source"] is None`, consistent with
  failure before QPBT-021 source preparation.

Using `TEST_RECIPE` here is intentional: it isolates clone/publication behavior
without making the test depend on the canonical Mathlib environment. It does not
bypass production behavior, because `_detached_clone` is recipe-independent and
the same warm exception/publication path is exercised.

## QPBT-021 compatibility

Current local-Mathlib behavior must stay exactly where it is:

- Canonical recipes alone require Mathlib (`scripts/hot_main_cache.py:1598-1601`).
- Warm authenticates the runtime Mathlib source/archive before a hit decision
  and again under the lock (`:1988-1990`, `:2009-2011`). Therefore an absent or
  invalid local Mathlib input still fails before any clone attempt.
- After fallback and exact detached checkout, warm verifies the detached
  project's cache-key inputs (`:2070-2074`) before materialization/build setup.
- Mathlib source preparation and `LAKE_PKG_URL_MAP` binding remain after project
  materialization/package setup and before Lake commands (`:2104-2112`).
- Post-build identity remains enforced by exact HEAD equality, cache-key input
  equality, clean tracked/untracked source, source evidence, and Mathlib source
  reauthentication (`:2130-2142`).
- Publication remains after all these gates (`:2143-2190`). A fallback checkout
  cannot create `READY` merely by returning a path.

Existing current tests already cover canonical local-Mathlib construction and
identity preservation at `tests/test_hot_main_cache.py:923-992`, archive staging
at `:994-1056`, and no READY/publication after a downstream authenticated
Mathlib build failure at `:1058-1105`. The new clone tests should not duplicate
that large setup.

## Risks and review notes

1. **Do not cherry-pick the old commits.** `1273f1d` and `e21c9cd` are based on
   `687e182`, before QPBT-021. A textual/manual transplant avoids reverting the
   extensive Mathlib authentication and command-environment work now occupying
   the surrounding class.
2. **Diagnostic matching is deliberately narrow in time, but broad in text.**
   The approved predicate accepts any newly appended occurrence of
   `cross-device` or `exdev`, case-insensitively. This matches the observed Git
   error exactly and is the smallest approved transplant. A newly appended
   unrelated error containing one of those strings (for example in a path)
   could cause one harmless extra object-copy attempt. If "explicit evidence"
   is interpreted more strictly than the approved behavior, narrow the predicate
   to recognized diagnostic phrases and add a path-containing-`exdev` negative
   test; that is an optional hardening, not necessary for this recorded failure.
3. **Log append behavior is a contract.** The old positive test used
   `write_text`, which truncates and does not model `_run_logged`. New tests must
   append so the offset regression is meaningful.
4. **Cleanup failure must fail closed.** Do not catch and suppress unlink/rmtree
   errors, and do not delete anything except the fixed `staging/checkout` path.
   The approved shape has this property.
5. **No recursive recovery.** Keep fallback as a single conditional call, not a
   loop and not a generic retry wrapper. Non-EXDEV local failures and all
   `--no-local` failures must preserve their exit code and flow to the retained
   failure envelope.
6. **No identity weakening.** Do not replace checkout with clone `--branch`, do
   not use an ambient ref, and do not remove either the immediate detached input
   hash check (`scripts/hot_main_cache.py:2073-2074`) or post-build HEAD/input
   checks (`:2130-2133`).
7. **Metrics need no schema change.** The current failure metrics and retained
   evidence record the resulting error and log path. The log marker is enough to
   audit whether fallback occurred; adding mutable transport detail to cache
   identity or manifest would be incorrect and unnecessary.
