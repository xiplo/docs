"""Tests for data export/import."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.export_import import DataExporter


@pytest.fixture
def mock_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create sample data files
    (data_dir / "cms_content.json").write_text(json.dumps([{"id": "c1", "title": "Test"}]))
    (data_dir / "campaigns.json").write_text(json.dumps([{"id": "camp1", "name": "Test"}]))
    (data_dir / "content_queue.json").write_text(json.dumps([{"id": "q1"}]))
    (data_dir / "post_history.json").write_text(json.dumps([{"timestamp": "2026-03-23"}]))

    with patch("utils.export_import.DATA_DIR", data_dir):
        yield data_dir


class TestExport:
    def test_export_creates_file(self, mock_data_dir):
        output = mock_data_dir / "test_export.json"
        path = DataExporter.export_all(str(output))
        assert path.exists()

        archive = json.loads(path.read_text())
        assert archive["version"] == "2.0.0"
        assert "data" in archive
        assert "stats" in archive

    def test_export_includes_data(self, mock_data_dir):
        output = mock_data_dir / "test_export.json"
        path = DataExporter.export_all(str(output))
        archive = json.loads(path.read_text())

        assert len(archive["data"]["cms_content"]) == 1
        assert len(archive["data"]["campaigns"]) == 1


class TestImport:
    def test_import_replaces(self, mock_data_dir):
        # Export first
        export_path = mock_data_dir / "export.json"
        DataExporter.export_all(str(export_path))

        # Modify data
        (mock_data_dir / "cms_content.json").write_text(json.dumps([{"id": "modified"}]))

        # Import should restore
        with patch("utils.export_import.DATA_DIR", mock_data_dir):
            summary = DataExporter.import_all(str(export_path))
        assert len(summary["imported"]) > 0

    def test_import_merge(self, mock_data_dir):
        # Export
        export_path = mock_data_dir / "export.json"
        DataExporter.export_all(str(export_path))

        # Add new item
        existing = json.loads((mock_data_dir / "cms_content.json").read_text())
        existing.append({"id": "c2", "title": "New"})
        (mock_data_dir / "cms_content.json").write_text(json.dumps(existing))

        # Import with merge
        with patch("utils.export_import.DATA_DIR", mock_data_dir):
            summary = DataExporter.import_all(str(export_path), merge=True)
        assert len(summary["imported"]) > 0

    def test_import_nonexistent(self, mock_data_dir):
        with pytest.raises(FileNotFoundError):
            DataExporter.import_all("/nonexistent.json")

    def test_display_archive(self, mock_data_dir):
        export_path = mock_data_dir / "export.json"
        DataExporter.export_all(str(export_path))
        output = DataExporter.display_archive(str(export_path))
        assert "Export Archive" in output
