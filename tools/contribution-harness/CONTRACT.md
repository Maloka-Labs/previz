# Shared contribution contract

- Follow the requested task scope and preserve unrelated work.
- Read the repository's AGENTS.md and contribution guide, plus instructions scoped to the affected files. Repository-specific requirements remain in effect.
- Distinguish proposed decisions, implemented behavior, and verified results. Report the checks actually run and their limits.
- Keep credentials, private conversation payloads, personal configuration, and session artifacts out of Git. Use synthetic fixtures and credential-free environment examples.
- Preserve the contributor's configured Git identity and legitimate human credit. Do not add assistant identities, assistant attribution trailers, generated-by footers, or session metadata. Repository-approved dependency/release bots use their own identity; never impersonate a human contributor.
- Stage only intended changes and inspect the staged diff. Preserve required human DCO sign-offs and upstream contribution rules. Do not bypass failed hooks.
- Follow the user's requested review sequence. Explicit authorization to open PRs permits that step; it does not authorize merging or deployment.
- Keep application build, lint, test, and release checks in the owning repository. These portable checks do not prove runtime behavior, scan file contents for secrets, or establish authorship.
- Upgrade the shared core deliberately through a reviewed, commit-pinned import. Keep local policy and domain guidance outside the vendored core.
