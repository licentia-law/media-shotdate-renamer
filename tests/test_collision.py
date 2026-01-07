import pytest
from pathlib import Path
from msr.core.collision import resolve_collision

@pytest.fixture
def setup_temp_dir(tmp_path):
    """
    Provides a temporary directory for creating test files.
    """
    return tmp_path

def create_dummy_file(path: Path):
    """Helper function to create a dummy file."""
    path.touch()

# --- resolve_collision tests ---

def test_resolve_collision_no_collision(setup_temp_dir):
    """
    Test case: The destination path does not exist, so no collision resolution is needed.
    """
    dst_path = setup_temp_dir / "photo.jpg"
    resolved_path = resolve_collision(dst_path)
    assert resolved_path == dst_path
    assert not resolved_path.exists()

def test_resolve_collision_first_collision_no_suffix(setup_temp_dir):
    """
    Test case: First collision for a file without a numeric suffix.
    e.g., photo.jpg -> photo1.jpg
    """
    original_path = setup_temp_dir / "photo.jpg"
    create_dummy_file(original_path)

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "photo1.jpg"
    assert original_path.exists()
    assert not resolved_path.exists()

def test_resolve_collision_multiple_collisions_no_suffix(setup_temp_dir):
    """
    Test case: Multiple collisions for a file without a numeric suffix.
    e.g., photo.jpg -> photo1.jpg -> photo2.jpg
    """
    original_path = setup_temp_dir / "photo.jpg"
    create_dummy_file(original_path)
    create_dummy_file(setup_temp_dir / "photo1.jpg")

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "photo2.jpg"
    assert original_path.exists()
    assert (setup_temp_dir / "photo1.jpg").exists()
    assert not resolved_path.exists()

def test_resolve_collision_first_collision_with_suffix(setup_temp_dir):
    """
    Test case: First collision for a file that already has a numeric suffix.
    e.g., photo1.jpg -> photo2.jpg
    """
    original_path = setup_temp_dir / "photo1.jpg"
    create_dummy_file(original_path)

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "photo2.jpg"
    assert original_path.exists()
    assert not resolved_path.exists()

def test_resolve_collision_multiple_collisions_with_suffix(setup_temp_dir):
    """
    Test case: Multiple collisions for a file that already has a numeric suffix.
    e.g., photo1.jpg -> photo2.jpg -> photo3.jpg
    """
    original_path = setup_temp_dir / "photo1.jpg"
    create_dummy_file(original_path)
    create_dummy_file(setup_temp_dir / "photo2.jpg")

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "photo3.jpg"
    assert original_path.exists()
    assert (setup_temp_dir / "photo2.jpg").exists()
    assert not resolved_path.exists()

def test_resolve_collision_filename_with_non_numeric_end(setup_temp_dir):
    """
    Test case: Filename stem ends with non-numeric characters, should append '1'.
    e.g., my_photo_final.jpg -> my_photo_final1.jpg
    """
    original_path = setup_temp_dir / "my_photo_final.jpg"
    create_dummy_file(original_path)

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "my_photo_final1.jpg"
    assert original_path.exists()
    assert not resolved_path.exists()

def test_resolve_collision_filename_with_numeric_in_middle(setup_temp_dir):
    """
    Test case: Filename stem has numbers in the middle but not at the end.
    e.g., photo_2023_event.jpg -> photo_2023_event1.jpg
    """
    original_path = setup_temp_dir / "photo_2023_event.jpg"
    create_dummy_file(original_path)

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "photo_2023_event1.jpg"
    assert original_path.exists()
    assert not resolved_path.exists()

def test_resolve_collision_different_extensions(setup_temp_dir):
    """
    Test case: Collision resolution should respect the file extension.
    e.g., photo.jpg -> photo1.jpg, not photo.png
    """
    original_path = setup_temp_dir / "image.png"
    create_dummy_file(original_path)

    resolved_path = resolve_collision(original_path)
    assert resolved_path == setup_temp_dir / "image1.png"
    assert original_path.exists()
    assert not resolved_path.exists()

def test_resolve_collision_complex_scenario(setup_temp_dir):
    """
    Test case: A more complex scenario with existing files.
    e.g., file_name1.txt, file_name2.txt, file_name3.txt exists.
    Calling resolve_collision(file_name1.txt) should return file_name4.txt
    """
    create_dummy_file(setup_temp_dir / "file_name1.txt")
    create_dummy_file(setup_temp_dir / "file_name2.txt")
    create_dummy_file(setup_temp_dir / "file_name3.txt")

    resolved_path = resolve_collision(setup_temp_dir / "file_name1.txt")
    assert resolved_path == setup_temp_dir / "file_name4.txt"
    assert not resolved_path.exists()
