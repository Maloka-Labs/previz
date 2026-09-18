# Repository instructions

## Context

ComfyUI nodes for World Labs generation, panoramas, splats, and preview tooling.

Read README.md and any instructions scoped to the affected files before editing.

## Repository validation

Parse changed Python files with `ast.parse` for syntax without importing ComfyUI or calling external APIs. Runtime validation requires ComfyUI and the documented dependencies; no automated test entry point is currently declared.

## Shared contribution harness

Follow the [shared contribution contract](tools/contribution-harness/CONTRACT.md) alongside the repository-specific rules above. See [local commands and upgrade policy](CONTRIBUTION_HARNESS.md). The shared checks supplement the existing build, lint, test, hook, and review requirements.
