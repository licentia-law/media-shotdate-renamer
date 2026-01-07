import pytest
from msr.core.metadata import MetaRecord, normalize_camera_model, extract_and_normalize_metadata

# --- MetaRecord tests ---

def test_metarecord_default_values():
    """
    Test MetaRecord instantiation with default values.
    """
    record = MetaRecord()
    assert record.datetime_original is None
    assert record.camera_make is None
    assert record.camera_model is None
    assert record.normalized_camera == "UNKNOWN"

def test_metarecord_custom_values():
    """
    Test MetaRecord instantiation with custom values.
    """
    record = MetaRecord(
        datetime_original="2023-01-01 10:00:00",
        camera_make="Canon",
        camera_model="EOS R7",
        normalized_camera="EOSR7"
    )
    assert record.datetime_original == "2023-01-01 10:00:00"
    assert record.camera_make == "Canon"
    assert record.camera_model == "EOS R7"
    assert record.normalized_camera == "EOSR7"

# --- normalize_camera_model tests ---

@pytest.mark.parametrize("make, model, expected_token", [
    # EOS R7
    ("Canon", "EOS R7", "EOSR7"),
    ("canon", "eos r7", "EOSR7"),
    ("CANON", "EOS R7", "EOSR7"),
    # EOS 200D II (various spellings)
    ("Canon", "EOS 200D II", "EOS200D2"),
    ("canon", "eos 200d2", "EOS200D2"),
    ("Canon", "EOS Kiss X10i", "EOS200D2"),
    ("canon", "eos kiss x10i", "EOS200D2"),
    # iPhone
    ("Apple", "iPhone 13 Pro", "iPhone"),
    ("apple", "iphone se", "iPhone"),
    # UNKNOWN cases
    (None, None, "UNKNOWN"),
    ("Sony", "Alpha 7 III", "UNKNOWN"),
    ("Nikon", "Z 6", "UNKNOWN"),
    ("Canon", "PowerShot G7 X Mark III", "UNKNOWN"), # Not a recognized EOS model
    ("Apple", "iPad Pro", "UNKNOWN"), # Not an iPhone
    ("Samsung", "Galaxy S23", "UNKNOWN"),
    ("Canon", None, "UNKNOWN"),
    (None, "EOS R7", "UNKNOWN"),
    ("", "", "UNKNOWN"),
    (" ", " ", "UNKNOWN"),
])
def test_normalize_camera_model(make, model, expected_token):
    """
    Test various combinations of camera make and model for correct normalization.
    """
    assert normalize_camera_model(make, model) == expected_token

# --- extract_and_normalize_metadata tests ---

def test_extract_and_normalize_metadata_basic():
    """
    Test basic extraction and normalization with valid make/model.
    """
    exif_data = {
        'Make': 'Canon',
        'Model': 'EOS R7',
        'DateTimeOriginal': '2023:01:01 10:30:00' # This will be handled in M2-02
    }
    record = extract_and_normalize_metadata(exif_data)
    assert record.camera_make == "Canon"
    assert record.camera_model == "EOS R7"
    assert record.normalized_camera == "EOSR7"
    assert record.datetime_original is None # As per M1-03, datetime_original is not yet extracted

def test_extract_and_normalize_metadata_unknown_camera():
    """
    Test extraction and normalization for an unknown camera.
    """
    exif_data = {
        'Make': 'Sony',
        'Model': 'Alpha 7 III'
    }
    record = extract_and_normalize_metadata(exif_data)
    assert record.camera_make == "Sony"
    assert record.camera_model == "Alpha 7 III"
    assert record.normalized_camera == "UNKNOWN"
    assert record.datetime_original is None

def test_extract_and_normalize_metadata_missing_make_model():
    """
    Test extraction when make and/or model are missing from exif_data.
    """
    exif_data = {
        'DateTimeOriginal': '2023:01:01 10:30:00'
    }
    record = extract_and_normalize_metadata(exif_data)
    assert record.camera_make is None
    assert record.camera_model is None
    assert record.normalized_camera == "UNKNOWN"
    assert record.datetime_original is None
