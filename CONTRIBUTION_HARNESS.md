# Contribution harness

## Repository responsibilities

ComfyUI nodes for World Labs generation, panoramas, splats, and preview tooling.

Parse changed Python files with `ast.parse` for syntax without importing ComfyUI or calling external APIs. Runtime validation requires ComfyUI and the documented dependencies; no automated test entry point is currently declared.

Read [AGENTS.md](AGENTS.md), the [shared contract](tools/contribution-harness/CONTRACT.md), and the affected source before changing behavior. Repository-specific requirements take precedence over the shared defaults. This harness needs Python 3.9+ and Git, with no package installation or hosted agent runtime.

## Commands

Run from the repository root:

```sh
# Local changes relative to HEAD (including untracked, non-ignored files)
python3 tools/contribution-harness/check.py
# Exact index snapshot, including staged policy and core manifest
python3 tools/contribution-harness/check.py --staged
# Committed and uncommitted changes against the actual PR base
python3 tools/contribution-harness/check.py --base origin/BASE_BRANCH
# Shared checker regression tests
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/contribution-harness -p 'test_*.py' -v
```

Replace `origin/BASE_BRANCH` with the actual PR base, including a stacked base when applicable. Fetch that base and enough history for a merge base before reviewing. An unknown or unavailable base fails explicitly. The default HEAD comparison does not review previously committed changes.

Setup does not require replacing hooks or installing tool adapters. Existing setup commands and hook managers remain authoritative. For a repository without hooks, the staged command can be added to its chosen hook manager; do not overwrite personal hooks. The dedicated GitHub Actions workflow runs the checker and its tests on pushes and PRs. Required-check enforcement at merge is a separate repository setting.

## Policy and limits

[Local policy](contribution-harness.json) is reviewed separately from shared code. It records allowed automation names, additional forbidden path globs, and exact-path exceptions with reasons. Assistant attribution remains forbidden even if an assistant name is added to the bot list. Human sign-offs and coauthors remain allowed.

The core accepts binary assets, symlinks, submodules, credential-free `.env.example`/`.env.sample`/`.env.template` files, and maintained agent instructions or skills. Managed harness files themselves must be regular files. It rejects common credential filenames and local session/cache paths in changed files, including force-added files. It checks every new commit for attribution and transient disallowed paths. Pre-existing history is not retroactively rejected.

Filename checks are not secret-content scanning, identity authentication, or a guarantee that all private data is detected. Existing security scans and application tests remain necessary. The core does not impose architecture's documentation-only file restrictions on application repositories.

## Provenance and upgrades

The [upstream manifest](tools/contribution-harness/upstream.json) records the exact architecture commit and SHA-256 digest of every shared core file. This is a vendored snapshot; local policy and repository instructions are not overwritten by upstream imports. The checker verifies all three core files against the manifest offline. Commit provenance must also be reviewed against the source repository during upgrades.

To upgrade, review the source commit and compare the three core files, then copy those files from that exact Git revision and update the full source SHA and SHA-256 file digests in the manifest together. Keep this guide, AGENTS.md, local policy, workflow, and existing hooks repository-specific. Do not change only a digest to conceal a local core modification. Run the shared tests, staged check, branch-history check, and relevant repository checks before opening the upgrade PR. No runtime download or mutable-branch dependency is used.
