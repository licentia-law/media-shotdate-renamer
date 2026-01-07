import pytest
from pathlib import Path
from unittest.mock import MagicMock

from msr.core.file_processor import FileProcessor, SUPPORTED_EXTENSIONS

@pytest.fixture
def file_processor_instance(tmp_path):
    """
    Provides a FileProcessor instance with a temporary source directory.
    The `tmp_path` fixture from pytest creates a unique temporary directory for each test function.
    """
    mock_event_queue = MagicMock() # event_queue는 이 테스트에서 사용되지 않으므로 mock 처리
    return FileProcessor(str(tmp_path), mock_event_queue)

def create_files(base_path: Path, file_names: list[str]):
    """Helper function to create dummy files within a given base_path."""
    for name in file_names:
        (base_path / name).touch()

def test_scan_empty_directory(file_processor_instance):
    """
    Test case: Scanning an empty source directory should return an empty list.
    """
    files = file_processor_instance._scan_files()
    assert len(files) == 0

def test_scan_supported_and_unsupported_files(tmp_path, file_processor_instance):
    """
    Test case: Only supported file types should be returned.
    """
    create_files(tmp_path, ["image.jpg", "document.txt", "video.mp4", "archive.zip"])
    
    expected_files = [
        tmp_path / "image.jpg",
        tmp_path / "video.mp4"
    ]
    
    files = file_processor_instance._scan_files()
    assert len(files) == len(expected_files)
    # Convert to set for order-independent comparison, then back to list for sorting check if needed.
    assert set(files) == set(expected_files)

def test_scan_excludes_result_directory(tmp_path, file_processor_instance):
    """
    Test case: Files within the 'result' subdirectory should be excluded from scanning.
    """
    (tmp_path / "result").mkdir()
    create_files(tmp_path, ["photo_outside.jpg"])
    create_files(tmp_path / "result", ["processed_photo.jpg", "log.txt"])
    
    expected_files = [tmp_path / "photo_outside.jpg"]
    
    files = file_processor_instance._scan_files()
    assert len(files) == len(expected_files)
    assert set(files) == set(expected_files)

def test_scan_recursive_subdirectories(tmp_path, file_processor_instance):
    """
    Test case: The scanner should recursively find supported files in subdirectories.
    """
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir1" / "nested").mkdir()
    
    create_files(tmp_path, ["root_image.jpg"])
    create_files(tmp_path / "subdir1", ["sub_image.png"])
    create_files(tmp_path / "subdir1" / "nested", ["nested_video.mov"])
    
    expected_files = [
        tmp_path / "root_image.jpg",
        tmp_path / "subdir1" / "sub_image.png",
        tmp_path / "subdir1" / "nested" / "nested_video.mov"
    ]
    
    files = file_processor_instance._scan_files()
    assert len(files) == len(expected_files)
    assert set(files) == set(expected_files)

def test_scan_returns_sorted_paths(tmp_path, file_processor_instance):
    """
    Test case: The returned list of file paths should be sorted by their full path.
    """
    # Create files in an order that is not naturally sorted by name
    create_files(tmp_path, ["c_video.mp4", "a_image.png", "b_image.jpg"])
    
    # Define the expected sorted order
    expected_files = [
        tmp_path / "a_image.png",
        tmp_path / "b_image.jpg",
        tmp_path / "c_video.mp4"
    ]
    
    files = file_processor_instance._scan_files()
    assert files == expected_files # _scan_files already sorts, so compare directly with sorted expected.

def test_scan_case_insensitive_extensions(tmp_path, file_processor_instance):
    """
    Test case: File extensions should be handled case-insensitively (e.g., .JPG should be recognized).
    """
    create_files(tmp_path, ["photo.JPG", "movie.MOV", "document.TXT"])
    
    expected_files = [
        tmp_path / "movie.MOV",
        tmp_path / "photo.JPG"
    ]
    
    files = file_processor_instance._scan_files()
    assert len(files) == len(expected_files)
    assert set(files) == set(expected_files)

def test_scan_result_folder_name_as_part_of_other_folder(tmp_path, file_processor_instance):
    """
    Test case: A folder whose name *contains* 'result' but is not the designated 'result' folder
    should NOT be excluded.
    """
    (tmp_path / "my_result_folder").mkdir()
    create_files(tmp_path / "my_result_folder", ["image_in_my_result.jpg"])
    create_files(tmp_path, ["root_image.jpg"])

    expected_files = [
        tmp_path / "my_result_folder" / "image_in_my_result.jpg",
        tmp_path / "root_image.jpg"
    ]
    
    files = file_processor_instance._scan_files()
    assert len(files) == len(expected_files)
    assert set(files) == set(expected_files)
