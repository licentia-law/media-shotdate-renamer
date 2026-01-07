import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import json
import sys

from msr.core.exiftool import extract_metadata_batch, ExifToolError, get_exiftool_path
from msr.core.metadata import MetaRecord, extract_and_normalize_metadata

# Mock ExifTool executable path for all tests in this module
@pytest.fixture(autouse=True)
def mock_get_exiftool_path():
    with patch('msr.core.exiftool.get_exiftool_path') as mock_path_getter:
        mock_path_getter.return_value = Path("mock/path/to/exiftool.exe")
        yield mock_path_getter

# Fixture to reset sys.frozen and sys._MEIPASS after each test
@pytest.fixture(autouse=True)
def restore_pyinstaller_flags():
    """
    각 테스트가 끝난 뒤 sys.frozen / sys._MEIPASS를 원복한다.
    """
    had_frozen = hasattr(sys, "frozen")
    had_meipass = hasattr(sys, "_MEIPASS")
    orig_frozen = getattr(sys, "frozen", None)
    orig_meipass = getattr(sys, "_MEIPASS", None)

    yield

    # restore frozen
    if had_frozen:
        sys.frozen = orig_frozen  # type: ignore[attr-defined]
    else:
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")

    # restore _MEIPASS
    if had_meipass:
        sys._MEIPASS = orig_meipass  # type: ignore[attr-defined]
    else:
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")


def test_extract_metadata_batch_success(tmp_path, mock_get_exiftool_path):
    """
    Test case: Successful batch extraction of metadata for multiple files.
    """
    file1 = tmp_path / "photo1.jpg"
    file2 = tmp_path / "video1.mp4"
    file1.touch()
    file2.touch()

    mock_exiftool_output = [
        {
            "SourceFile": str(file1),
            "DateTimeOriginal": "2023:01:01 10:00:00",
            "Make": "Canon",
            "Model": "EOS R7"
        },
        {
            "SourceFile": str(file2),
            "MediaCreateDate": "2023:01:01 11:00:00",
            "Make": "Apple",
            "Model": "iPhone 13 Pro"
        }
    ]

    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(
            stdout=json.dumps(mock_exiftool_output),
            stderr="",
            returncode=0
        )
        
        # We are testing the integration, so extract_and_normalize_metadata should run its actual logic
        # No need to mock extract_and_normalize_metadata here.

        result = extract_metadata_batch([file1, file2])

        assert len(result) == 2
        assert file1 in result
        assert file2 in result

        meta1 = result[file1]
        assert meta1.datetime_original == "2023:01:01 10:00:00"
        assert meta1.camera_make == "Canon"
        assert meta1.camera_model == "EOS R7"
        assert meta1.normalized_camera == "EOSR7"

        meta2 = result[file2]
        assert meta2.datetime_original == "2023:01:01 11:00:00"
        assert meta2.camera_make == "Apple"
        assert meta2.camera_model == "iPhone 13 Pro"
        assert meta2.normalized_camera == "iPhone"

        # Verify subprocess.run was called correctly
        mock_subprocess_run.assert_called_once()
        args = mock_subprocess_run.call_args[0][0]
        assert str(mock_get_exiftool_path.return_value) in args
        assert "-json" in args
        assert "-s3" in args
        assert str(file1) in args
        assert str(file2) in args

def test_extract_metadata_batch_empty_files_list():
    """
    Test case: Calling with an empty list of files should return an empty dictionary.
    """
    with patch('subprocess.run') as mock_subprocess_run:
        result = extract_metadata_batch([])
        assert result == {}
        mock_subprocess_run.assert_not_called() # subprocess should not be called

def test_extract_metadata_batch_exiftool_not_found_error():
    """
    Test case: ExifTool executable not found should raise ExifToolError.
    """
    with patch('msr.core.exiftool.get_exiftool_path', side_effect=ExifToolError("Not found")):
        with pytest.raises(ExifToolError, match="Not found"):
            extract_metadata_batch([Path("dummy.jpg")])

def test_extract_metadata_batch_subprocess_file_not_found_error():
    """
    Test case: subprocess.run raises FileNotFoundError (e.g., exiftool.exe not in PATH).
    """
    with patch('subprocess.run', side_effect=FileNotFoundError("ExifTool not found")):
        with pytest.raises(ExifToolError, match="ExifTool executable not found"):
            extract_metadata_batch([Path("dummy.jpg")])

def test_extract_metadata_batch_subprocess_called_process_error():
    """
    Test case: subprocess.run raises CalledProcessError (e.g., exiftool returns non-zero exit code).
    """
    mock_stderr = "ExifTool error message"
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, "cmd", stderr=mock_stderr)):
        with pytest.raises(ExifToolError, match=f"ExifTool batch command failed with error: {mock_stderr}"):
            extract_metadata_batch([Path("dummy.jpg")])

def test_extract_metadata_batch_json_decode_error():
    """
    Test case: ExifTool returns invalid JSON output.
    """
    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(
            stdout="this is not json",
            stderr="",
            returncode=0
        )
        with pytest.raises(ExifToolError, match="Failed to parse ExifTool JSON output"):
            extract_metadata_batch([Path("dummy.jpg")])

def test_extract_metadata_batch_missing_source_file_entry(tmp_path):
    """
    Test case: An entry in ExifTool JSON output is missing 'SourceFile'.
    It should be skipped.
    """
    file1 = tmp_path / "photo1.jpg"
    file2 = tmp_path / "photo2.jpg"
    file1.touch()
    file2.touch()

    mock_exiftool_output = [
        {
            "SourceFile": str(file1),
            "DateTimeOriginal": "2023:01:01 10:00:00",
        },
        {
            # Missing SourceFile
            "DateTimeOriginal": "2023:01:02 11:00:00",
        },
        {
            "SourceFile": str(file2),
            "DateTimeOriginal": "2023:01:03 12:00:00",
        }
    ]

    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(
            stdout=json.dumps(mock_exiftool_output),
            stderr="",
            returncode=0
        )
        result = extract_metadata_batch([file1, file2])

        assert len(result) == 2 # Only file1 and file2 should be in the result
        assert file1 in result
        assert file2 in result
        assert result[file1].datetime_original == "2023:01:01 10:00:00"
        assert result[file2].datetime_original == "2023:01:03 12:00:00"
