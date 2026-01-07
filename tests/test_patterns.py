import pytest
from msr.core.patterns import is_img_pattern, is_pass_pattern, get_img_id

# --- is_img_pattern tests ---

@pytest.mark.parametrize("filename_stem", [
    "IMG_1234",
    "img_5678",
    "IMG_0",
    "IMG_9876543210", # 10 digits
    "IMG_123a",
    "IMG_456b",
    "IMG_789abcde",
    "IMG_1234567890a", # 10 digits + 1 char (total 11, should be valid as per regex)
    "IMG_1234567890abcdefghij", # 10 digits + 10 chars (total 20, should be valid)
    "IMG_1234567890abcde", # 10 digits + 5 chars (total 15, valid)
    "IMG_123456789012345678901", # 21 digits (valid)
])
def test_is_img_pattern_valid(filename_stem):
    """
    Test cases for valid IMG patterns.
    """
    assert is_img_pattern(filename_stem) is True

@pytest.mark.parametrize("filename_stem", [
    "IMG_ABC",          # Contains only letters after IMG_
    "IMG_1234567890abcdefghijk",  # 영문 11자 → invalid
    "NOT_IMG_1234",
    "1234_IMG",
    "IMG",
    "IMG_",
    "IMG_1234.jpg",     # Has extension (should be stem only)    
    "IMG_1a2b3c4d5e", # mixed digits and chars, 10 chars (invalid by \d+[a-z]{0,10})
])
def test_is_img_pattern_invalid(filename_stem):
    """
    Test cases for invalid IMG patterns.
    """
    assert is_img_pattern(filename_stem) is False

# --- is_pass_pattern tests ---

@pytest.mark.parametrize("filename_stem", [
    "2025-01-01_12-30-00_1234_EOSR7",
    "2023-11-22_09-15-30_abcde_iPhone",
    "2024-05-10_23-59-59_9876543210_UNKNOWN",
    "2020-02-29_00-00-00_ID_CAM",
    # "2021-07-15_10-20-30_long_id_with_underscores_CAM", # ID part should not contain underscores
])
def test_is_pass_pattern_valid(filename_stem):
    """
    Test cases for valid PASS patterns.
    """
    assert is_pass_pattern(filename_stem) is True

@pytest.mark.parametrize("filename_stem", [
    "2025-01-01_12-30-00_1234",         # Missing camera part
    "2025-01-01_12-30-00_EOSR7",        # Missing ID part
    "2025-01-01_12-30-00_1234_EOSR7.jpg", # Has extension
    "2025/01/01_12-30-00_1234_EOSR7",   # Wrong date separator
    "2025-1-1_12-30-00_1234_EOSR7",     # Single digit month/day
    "2025-01-01_12:30:00_1234_EOSR7",   # Wrong time separator
    "IMG_1234",                         # Not a PASS pattern
    "2021-07-15_10-20-30_long_id_with_underscores_CAM", # ID part should not contain underscores
    "2025-01-01_12-30-00_1234_EOSR7_extra", # Extra part
])
def test_is_pass_pattern_invalid(filename_stem):
    """
    Test cases for invalid PASS patterns.
    """
    assert is_pass_pattern(filename_stem) is False

# --- get_img_id tests ---

@pytest.mark.parametrize("filename_stem, expected_id", [
    ("IMG_1234", "1234"),
    ("img_5678", "5678"),
    ("IMG_123a", "123a"),
    ("IMG_1234567890abcde", "1234567890abcde"),
    ("IMG_123456789012345678901", "123456789012345678901"), # This is valid, so get_img_id should work
    ("NOT_IMG_1234", None),
    ("IMG_ABC", None),
    ("IMG_", None),
])
def test_get_img_id(filename_stem, expected_id):
    """
    Test cases for extracting the ID from IMG patterns.
    """
    assert get_img_id(filename_stem) == expected_id
