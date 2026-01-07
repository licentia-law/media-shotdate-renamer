import pytest
from pathlib import Path
from unittest.mock import patch
import shutil

from msr.core.copier import copy_file

@pytest.fixture
def setup_temp_files(tmp_path):
    """
    Creates a source file and a destination directory for testing.
    """
    src_dir = tmp_path / "source"
    dst_dir = tmp_path / "destination"
    src_dir.mkdir()
    
    src_file = src_dir / "test_file.txt"
    src_file.write_text("This is a test file content.")
    
    return src_file, dst_dir

# --- copy_file tests ---

def test_copy_file_success(setup_temp_files):
    """
    Test case: File is copied successfully when destination does not exist.
    """
    src_file, dst_dir = setup_temp_files
    final_dst_path = dst_dir / "new_file.txt"

    success, message, returned_path, _ = copy_file(src_file, final_dst_path)

    assert success is True
    assert "Copied" in message
    assert returned_path == final_dst_path
    assert final_dst_path.exists()
    assert final_dst_path.read_text() == "This is a test file content."
    assert dst_dir.exists() # Ensure parent directory was created

def test_copy_file_idempotency_skip(setup_temp_files):
    """
    Test case: Copy is skipped if the final destination path already exists.
    """
    src_file, dst_dir = setup_temp_files
    final_dst_path = dst_dir / "existing_file.txt"
    
    # Create the destination file beforehand
    dst_dir.mkdir()
    final_dst_path.write_text("Existing content.")

    success, message, returned_path, _ = copy_file(src_file, final_dst_path)

    assert success is False
    assert "Skipped: File already exists" in message
    assert returned_path == final_dst_path
    assert final_dst_path.exists()
    assert final_dst_path.read_text() == "Existing content." # Content should not be overwritten

def test_copy_file_error_handling(setup_temp_files):
    """
    Test case: Error during copying is handled gracefully.
    """
    src_file, dst_dir = setup_temp_files
    final_dst_path = dst_dir / "error_file.txt"

    # Mock shutil.copy2 to raise an exception
    with patch('shutil.copy2') as mock_copy2:
        mock_copy2.side_effect = OSError("Disk full error")
        success, message, returned_path, _ = copy_file(src_file, final_dst_path)

    assert success is False
    assert "Error copying" in message
    assert "Disk full error" in message
    assert returned_path == final_dst_path
    assert not final_dst_path.exists() # File should not exist if copy failed
    assert dst_dir.exists() # Parent directory should still be created
