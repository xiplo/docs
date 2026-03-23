"""Tests for content versioning."""

from unittest.mock import patch

import pytest

from cms.versioning import VersionManager


@pytest.fixture(autouse=True)
def mock_file(tmp_path):
    f = tmp_path / "versions.json"
    with patch("cms.versioning.VERSIONS_FILE", f):
        yield f


class TestVersionManager:
    def test_save_version(self):
        vm = VersionManager()
        v = vm.save_version("content1", {"title": "Test", "caption": "Hello"}, message="Initial")
        assert v.version == 1
        assert v.content_id == "content1"

    def test_version_incrementing(self):
        vm = VersionManager()
        vm.save_version("c1", {"title": "v1"})
        vm.save_version("c1", {"title": "v2"}, changed_fields=["title"])
        vm.save_version("c1", {"title": "v3"}, changed_fields=["title"])

        versions = vm.get_versions("c1")
        assert len(versions) == 3
        assert versions[0].version == 1
        assert versions[2].version == 3

    def test_get_latest(self):
        vm = VersionManager()
        vm.save_version("c1", {"title": "v1"})
        vm.save_version("c1", {"title": "v2"})
        latest = vm.get_latest("c1")
        assert latest.version == 2
        assert latest.snapshot["title"] == "v2"

    def test_diff(self):
        vm = VersionManager()
        vm.save_version("c1", {"title": "Old", "caption": "Same"})
        vm.save_version("c1", {"title": "New", "caption": "Same"}, changed_fields=["title"])

        changes = vm.diff("c1", 1, 2)
        assert "title" in changes
        assert changes["title"]["from"] == "Old"
        assert changes["title"]["to"] == "New"
        assert "caption" not in changes

    def test_display(self):
        vm = VersionManager()
        vm.save_version("c1", {"title": "Test"}, message="Init")
        output = vm.display("c1")
        assert "Version History" in output
        assert "v1" in output

    def test_display_summary(self):
        vm = VersionManager()
        vm.save_version("c1", {"title": "A"})
        vm.save_version("c2", {"title": "B"})
        output = vm.display()
        assert "2 content items" in output
