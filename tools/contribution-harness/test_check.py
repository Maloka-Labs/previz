import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("contribution_check", Path(__file__).with_name("check.py"))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)
POLICY = {"schema_version": 1, "allowed_bot_names": [], "path_exceptions": {}, "extra_forbidden_globs": []}


class PolicyTests(unittest.TestCase):
    def test_application_files_and_maintained_skills_are_allowed(self):
        for name in ("logo.png", ".env.example", "config/.env.test.sample", "CLAUDE.md", ".agents/skills/test/SKILL.md", ".claude/skills/test.md", "dist/fixture.js", "certs/public.crt"):
            with self.subTest(name=name):
                self.assertFalse(CHECK.forbidden_path(name, POLICY))

    def test_credentials_and_local_state_are_rejected(self):
        for name in (".env", "service/.env.production", ".work/session.md", "x/__pycache__/a.pyc", ".codex/sessions/one.json", ".claude/settings.local.json", "private.pem", "keys/token.key", "node_modules/a.js"):
            with self.subTest(name=name):
                self.assertTrue(CHECK.forbidden_path(name, POLICY))

    def test_exceptions_are_exact_and_require_reasons(self):
        policy = dict(POLICY, path_exceptions={"test/fixture.key": "Public synthetic fixture"})
        self.assertEqual(CHECK.policy_errors(policy), [])
        self.assertFalse(CHECK.forbidden_path("test/fixture.key", policy))
        self.assertTrue(CHECK.forbidden_path("other/fixture.key", policy))
        for exceptions in ({"*.key": "Too broad"}, {"test/key": ""}, {"../key": "Outside"}):
            self.assertTrue(CHECK.policy_errors(dict(POLICY, path_exceptions=exceptions)))

    def test_invalid_policy_fails_closed(self):
        for policy in ([], {}, dict(POLICY, unexpected=True), dict(POLICY, allowed_bot_names="any")):
            self.assertTrue(CHECK.policy_errors(policy))

    def test_assistants_rejected_but_explicit_bots_and_humans_allowed(self):
        policy = dict(POLICY, allowed_bot_names=["dependabot[bot]"])
        self.assertEqual(CHECK.identity_errors("Human", "human@example.test", policy), [])
        self.assertEqual(CHECK.identity_errors("dependabot[bot]", "bot@example.test", policy), [])
        self.assertTrue(CHECK.identity_errors("other[bot]", "bot@example.test", policy))
        self.assertTrue(CHECK.identity_errors("Codex", "human@example.test", policy))
        self.assertTrue(CHECK.identity_errors("Human", "noreply@openai.com", policy))

    def test_human_dco_and_coauthors_survive(self):
        self.assertEqual(CHECK.message_errors("Fix\n\nSigned-off-by: Human <human@example.test>\nCo-authored-by: Other <other@example.test>", POLICY), [])
        for message in ("Co-authored-by: Codex <noreply@openai.com>", "Generated with Claude", "Session-id: private"):
            self.assertTrue(CHECK.message_errors(message, POLICY))


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="contribution-harness-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.environment = patch.dict(os.environ, env, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test Contributor")
        self.git("config", "user.email", "contributor@example.test")
        self.write("README.md", "# Example\n")
        self.git("add", "README.md")
        self.git("commit", "-m", "Initial")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.write("contribution-harness.json", json.dumps(POLICY))
        manifest = {"schema_version": 1, "source_repository": "https://github.com/Maloka-Labs/architecture", "source_commit": "a" * 40, "files": {}}
        for name in CHECK.CORE_FILES:
            content = Path(__file__).with_name(name).read_bytes()
            target = CHECK.CORE + name
            self.write(target, content)
            manifest["files"][target] = hashlib.sha256(content).hexdigest()
        self.write(CHECK.CORE + "upstream.json", json.dumps(manifest))

    def git(self, *args):
        return CHECK.text(self.root, *args)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode() if isinstance(content, str) else content)

    def test_binary_assets_symlinks_and_env_examples(self):
        self.write("assets/logo.png", b"\x89PNG\x00\xff")
        self.write(".env.example", "TOKEN=\n")
        (self.root / "overview").symlink_to("README.md")
        self.assertEqual(CHECK.check(self.root, self.base), [])

    def test_staged_policy_cannot_be_hidden_by_unstaged_exception(self):
        self.write(".env", "TOKEN=synthetic\n")
        self.git("add", ".")
        self.write("contribution-harness.json", json.dumps(dict(POLICY, path_exceptions={".env": "Synthetic fixture"})))
        self.assertTrue(any(".env" in e for e in CHECK.check(self.root, self.base, staged=True)))
        self.assertEqual(CHECK.check(self.root, self.base), [])

    def test_staged_core_cannot_be_hidden_by_unstaged_fix(self):
        path = self.root / CHECK.CORE / "CONTRACT.md"
        original = path.read_bytes()
        path.write_text("Changed\n")
        self.git("add", ".")
        path.write_bytes(original)
        self.assertTrue(CHECK.manifest_errors(self.root, staged=True))
        self.assertEqual(CHECK.manifest_errors(self.root), [])

    def test_transient_artifacts_fail_history(self):
        self.git("add", ".")
        self.git("commit", "-m", "Adopt harness")
        self.write(".work/private.txt", "Synthetic\n")
        self.git("add", ".work/private.txt")
        self.git("commit", "-m", "Add scratch")
        self.git("rm", ".work/private.txt")
        self.git("commit", "-m", "Remove scratch")
        self.assertTrue(any("historical path" in e for e in CHECK.check(self.root, self.base)))

    def test_existing_history_is_not_retroactively_rejected(self):
        self.write(".env", "SYNTHETIC=1\n")
        self.git("add", ".")
        self.git("commit", "-m", "Existing baseline")
        base = self.git("rev-parse", "HEAD").strip()
        self.write("README.md", "# Updated\n")
        self.assertEqual(CHECK.check(self.root, base), [])

    def test_missing_or_incomplete_manifest_fails(self):
        path = self.root / CHECK.CORE / "upstream.json"
        manifest = json.loads(path.read_text())
        manifest["files"].pop(CHECK.CORE + "check.py")
        path.write_text(json.dumps(manifest))
        self.assertTrue(CHECK.manifest_errors(self.root))
        path.unlink()
        with self.assertRaises(OSError):
            CHECK.manifest_errors(self.root)

    def test_managed_symlinks_are_refused(self):
        path = self.root / "contribution-harness.json"
        path.unlink()
        path.symlink_to("README.md")
        with self.assertRaisesRegex(ValueError, "symlink"):
            CHECK.check(self.root, self.base)

    def test_invalid_base_fails(self):
        with self.assertRaises(ValueError):
            CHECK.check(self.root, "missing-base")

    def test_first_commit_checks_staged_files(self):
        self.git("checkout", "--orphan", "initial")
        self.git("add", ".")
        self.assertEqual(CHECK.check(self.root, "HEAD", staged=True), [])
        self.write(".env", "SYNTHETIC=1\n")
        self.git("add", ".env")
        self.assertTrue(CHECK.check(self.root, "HEAD", staged=True))

    def test_diverged_base_checks_only_branch_commits(self):
        self.git("add", ".")
        self.git("commit", "-m", "Adopt harness")
        self.git("branch", "feature")
        self.write("unrelated.md", "# Unrelated\n")
        self.git("add", ".")
        self.git("commit", "-m", "Other change")
        self.git("checkout", "feature")
        self.write("README.md", "# Feature\n")
        self.git("add", ".")
        self.git("commit", "-m", "Feature")
        self.assertEqual(CHECK.check(self.root, "main"), [])


if __name__ == "__main__":
    unittest.main()
