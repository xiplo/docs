"""Tests for backup/restore system."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.backup import BackupManager


@pytest.fixture
def backup_env(tmp_path):
    """Set up a temp data directory with sample data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample data files
    (data_dir / "content_queue.json").write_text(json.dumps([{"id": "1"}]))
    (data_dir / "post_history.json").write_text(json.dumps([{"post": "test"}]))

    return data_dir


class TestBackupManager:
    def test_create_backup(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        path = mgr.create_backup(label="test")

        assert path.exists()
        assert (path / "manifest.json").exists()
        assert (path / "content_queue.json").exists()
        assert (path / "post_history.json").exists()

    def test_list_backups(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        mgr.create_backup(label="first")
        mgr.create_backup(label="second")

        backups = mgr.list_backups()
        assert len(backups) >= 2

    def test_restore_backup(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        path = mgr.create_backup(label="restore_test")

        # Modify original data
        (backup_env / "content_queue.json").write_text(json.dumps([{"id": "modified"}]))

        # Restore
        restored = mgr.restore_backup(path.name)
        assert restored > 0

        # Verify data is restored
        data = json.loads((backup_env / "content_queue.json").read_text())
        assert data == [{"id": "1"}]

    def test_restore_nonexistent(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        assert mgr.restore_backup("nonexistent") == 0

    def test_retention(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        mgr.MAX_BACKUPS = 3

        for i in range(5):
            mgr.create_backup(label=f"b{i}")

        backups = mgr.list_backups()
        assert len(backups) <= 3

    def test_display(self, backup_env):
        mgr = BackupManager(data_dir=backup_env)
        mgr.create_backup(label="display_test")
        output = mgr.display()
        assert "Backups" in output
        assert "display_test" in output
