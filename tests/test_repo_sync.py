"""Tests for ELYSIUM.py repo bootstrap."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from elysium.bootstrap import repo_sync


class RepoSyncTests(unittest.TestCase):
    def test_is_complete_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(repo_sync.is_complete_install(tmp))
            os.makedirs(os.path.join(tmp, "elysium"))
            self.assertTrue(repo_sync.is_complete_install(tmp))

    def test_is_dev_checkout_when_git_tree_not_install_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            install_dir = os.path.join(tmp, "install")
            dev_dir = os.path.join(tmp, "dev")
            os.makedirs(install_dir)
            os.makedirs(os.path.join(dev_dir, "elysium"))
            os.makedirs(os.path.join(dev_dir, ".git"))

            entry = os.path.join(dev_dir, "ELYSIUM.py")
            with open(entry, "w", encoding="utf-8") as handle:
                handle.write("# dev")

            with patch.object(repo_sync, "resolve_install_dir", return_value=install_dir):
                self.assertTrue(repo_sync.is_dev_checkout(entry))

    def test_is_not_dev_checkout_for_install_dir(self):
        with tempfile.TemporaryDirectory() as install_dir:
            os.makedirs(os.path.join(install_dir, "elysium"))
            entry = os.path.join(install_dir, "ELYSIUM.py")
            with open(entry, "w", encoding="utf-8") as handle:
                handle.write("# install")

            with patch.object(repo_sync, "resolve_install_dir", return_value=install_dir):
                self.assertFalse(repo_sync.is_dev_checkout(entry))

    def test_skip_git_env(self):
        with tempfile.TemporaryDirectory() as install_dir:
            with patch.dict(os.environ, {"ELYSIUM_SKIP_GIT": "1"}, clear=False):
                repo_sync.sync_repo(install_dir)
            self.assertFalse(os.path.isdir(os.path.join(install_dir, ".git")))

    def test_github_zip_url(self):
        self.assertIn(
            "Protechas/Elysium/zip/refs/heads/main",
            repo_sync.github_zip_url("main"),
        )


if __name__ == "__main__":
    unittest.main()
