#!/usr/bin/env python3
"""Portable contribution checks. Python 3.9+, Git, and no network required."""

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
CORE = "tools/contribution-harness/"
CORE_FILES = ("check.py", "test_check.py", "CONTRACT.md")
ASSISTANTS = {
    "codex", "claude", "claude code", "copilot", "github copilot", "cursor",
    "cursor agent", "gemini cli", "aider", "devin",
}
ASSISTANT_EMAILS = {"noreply@openai.com", "noreply@anthropic.com", "copilot@github.com"}
POLICY_KEYS = {"schema_version", "allowed_bot_names", "path_exceptions", "extra_forbidden_globs"}


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def text(root, *args):
    return git(root, *args).decode("utf-8", "surrogateescape")


def snapshot_bytes(root, name, staged=False):
    if staged:
        mode = text(root, "ls-files", "--stage", "--", name).split(" ", 1)[0]
        if mode not in {"100644", "100755"}:
            raise ValueError("Managed harness file must be a regular staged file: " + name)
        return git(root, "show", ":" + name)
    path = root / name
    if any(p.is_symlink() for p in [path, *path.parents] if p != root and root in p.parents):
        raise ValueError("Managed harness file must not use symlinks: " + name)
    return path.read_bytes()


def policy_errors(policy):
    if not isinstance(policy, dict) or policy.get("schema_version") != 1:
        return ["contribution-harness.json requires schema_version 1"]
    errors = []
    if set(policy) != POLICY_KEYS:
        errors.append("Policy keys must be exactly: " + ", ".join(sorted(POLICY_KEYS)))
    for key in ("allowed_bot_names", "extra_forbidden_globs"):
        values = policy.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
            errors.append(key + " must be a list of nonempty strings")
    exceptions = policy.get("path_exceptions")
    if not isinstance(exceptions, dict) or not all(
        isinstance(k, str) and k and not PurePosixPath(k).is_absolute()
        and ".." not in PurePosixPath(k).parts and not any(c in k for c in "*?[")
        and isinstance(v, str) and v.strip() for k, v in exceptions.items()
    ):
        errors.append("path_exceptions must map exact relative paths to reviewable reasons")
    return errors


def forbidden_path(name, policy):
    if name in policy["path_exceptions"]:
        return False
    path = PurePosixPath(name.lower())
    parts = path.parts
    env_file = path.name == ".env" or path.name.startswith(".env.")
    example = path.name.endswith((".example", ".sample", ".template"))
    local_state = any(p in {".work", "__pycache__", ".venv", "node_modules"} for p in parts)
    local_state = local_state or path.name in {".ds_store", "claude.local.md", "settings.local.json"}
    for i, part in enumerate(parts[:-1]):
        if part in {".codex", ".claude", ".gemini"} and parts[i + 1] in {"sessions", "projects", "logs"}:
            local_state = True
    return (
        local_state or (env_file and not example)
        or path.suffix in {".pyc", ".pyo", ".pem", ".key"}
        or any(fnmatch.fnmatchcase(name, pattern) for pattern in policy["extra_forbidden_globs"])
    )


def identity_errors(name, email, policy):
    if not name.strip() or not email.strip():
        return ["Missing contributor identity"]
    if name.lower() in ASSISTANTS or email.lower() in ASSISTANT_EMAILS:
        return ["Assistant attribution is not permitted"]
    if "[bot]" in (name + email).lower() and name not in policy["allowed_bot_names"]:
        return ["Automation identity requires an explicit local policy entry: " + name]
    return []


def message_errors(message, policy):
    errors = []
    for line in message.splitlines():
        match = re.fullmatch(r"\s*(?:Co-authored-by|Signed-off-by):\s*(.*?)\s*<([^>]+)>\s*", line, re.I)
        if match:
            errors.extend(identity_errors(match[1], match[2], policy))
        if re.match(r"\s*(Generated-by|Assisted-by|Agent-session|Session-id):", line, re.I):
            errors.append("Tool attribution or session metadata is not permitted")
        if re.match(r"\W*(Generated|Written|Authored|Created|Assisted)\s+(with|by|using)\b", line, re.I) and re.search(
            r"\b(codex|claude|copilot|cursor|gemini|aider|devin|openai|anthropic|agent)\b", line, re.I
        ):
            errors.append("Assistant-generated commit footer is not permitted")
    return errors


def manifest_errors(root, staged=False):
    manifest = json.loads(snapshot_bytes(root, CORE + "upstream.json", staged))
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "source_repository", "source_commit", "files"}:
        return ["Invalid upstream manifest fields"]
    if manifest["schema_version"] != 1 or manifest["source_repository"] != "https://github.com/Maloka-Labs/architecture":
        return ["Invalid upstream manifest version or source"]
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest["source_commit"])):
        return ["Upstream source must be pinned to a full commit SHA"]
    expected = {CORE + name for name in CORE_FILES}
    if not isinstance(manifest["files"], dict) or set(manifest["files"]) != expected:
        return ["Upstream manifest must cover exactly the shared core files"]
    errors = []
    for name, digest in manifest["files"].items():
        if hashlib.sha256(snapshot_bytes(root, name, staged)).hexdigest() != digest:
            errors.append("Vendored core differs from its pinned manifest: " + name)
    return errors


def check(root, base, staged=False, source=False):
    policy = json.loads(snapshot_bytes(root, "contribution-harness.json", staged))
    errors = policy_errors(policy)
    if errors:
        return errors
    if not source:
        errors.extend(manifest_errors(root, staged))
    # An unborn branch has no HEAD yet, but its first commit still needs checks.
    has_head = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], capture_output=True).returncode == 0
    ancestor = None
    if has_head or base != "HEAD":
        # Resolve the input as a commit before using it in a revision expression.
        base_sha = text(root, "rev-parse", "--verify", "--end-of-options", base + "^{commit}").strip()
        ancestor = text(root, "merge-base", base_sha, "HEAD").strip()
    args = ["diff", "--name-only", "-z", "--no-renames", "--diff-filter=ACMT"]
    if staged:
        args.append("--cached")
    paths = set(text(root, *args, ancestor, "--").split("\0")) if ancestor else set(text(root, "ls-files", "--cached", "-z").split("\0"))
    if not staged:
        paths.update(text(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    for path in sorted(paths - {""}):
        if forbidden_path(path, policy):
            errors.append("Local/credential artifact in change: " + path)
    if text(root, "ls-files", "--unmerged"):
        errors.append("Resolve unmerged index entries before checking")
    commits = text(root, "rev-list", ancestor + "..HEAD").splitlines() if ancestor else []
    for commit in commits:
        fields = text(root, "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", commit).split("\0", 4)
        for offset in (0, 2):
            errors.extend(commit[:12] + ": " + e for e in identity_errors(fields[offset], fields[offset + 1], policy))
        errors.extend(commit[:12] + ": " + e for e in message_errors(fields[4], policy))
        # Per-commit paths catch artifacts added and removed inside a PR.
        changed = text(root, "diff-tree", "--root", "-m", "--no-commit-id", "--name-only", "-r", "-z", "--no-renames", "--diff-filter=ACMT", commit).split("\0")
        errors.extend(commit[:12] + ": disallowed historical path " + p for p in set(changed) - {""} if forbidden_path(p, policy))
    if staged:
        for variable in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
            value = text(root, "var", variable).strip()
            match = re.fullmatch(r"(.*) <([^>]+)> \d+ [+-]\d{4}", value)
            errors.extend(identity_errors(match[1], match[2], policy) if match else ["Cannot resolve " + variable])
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="HEAD", help="PR base revision; defaults to uncommitted changes only")
    parser.add_argument("--staged", action="store_true", help="Check the index, including staged policy and manifest")
    parser.add_argument("--source", action="store_true", help="Canonical architecture source only: no upstream manifest")
    args = parser.parse_args()
    try:
        if Path(text(ROOT, "rev-parse", "--show-toplevel").strip()).resolve() != ROOT:
            raise ValueError("Run from a standalone repository checkout")
        errors = check(ROOT, args.base, args.staged, args.source)
    except (OSError, ValueError, UnicodeError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR: " + error, file=sys.stderr)
    if not errors:
        print("Contribution harness passed (file paths, commit hygiene, and core integrity).")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
