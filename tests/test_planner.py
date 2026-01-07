import pytest
from pathlib import Path
from msr.core.metadata import MetaRecord
from msr.core.planner import Action, Plan, generate_plan

# Mock Path objects for testing
MOCK_SRC_PATH_IMG_JPG = Path("C:/source/photos/IMG_1234.JPG")
MOCK_SRC_PATH_PASS_MP4 = Path("C:/source/videos/2023-01-01_10-00-00_ID_CAM.mp4")
MOCK_SRC_PATH_OTHER_PNG = Path("C:/source/misc/MyPhoto.PNG")
MOCK_SRC_PATH_IMG_MOV = Path("C:/source/videos/IMG_5678.MOV")

# --- generate_plan tests ---

@pytest.mark.parametrize(
    "src_path, meta_record, expected_plan",
    [
        # Policy 1: PASS pattern file with valid datetime
        (
            MOCK_SRC_PATH_PASS_MP4,
            MetaRecord(
                datetime_original="2023:01:01 10:00:00",
                camera_make="Canon",
                camera_model="EOS R7",
                normalized_camera="EOSR7"
            ),
            Plan(
                action=Action.COPY_PASS,
                src_path=MOCK_SRC_PATH_PASS_MP4,
                dst_dir=Path("2023-01-01"),
                dst_name="2023-01-01_10-00-00_ID_CAM.mp4",
                reason=None
            )
        ),
        # Policy 1: PASS pattern file without datetime (should skip)
        (
            MOCK_SRC_PATH_PASS_MP4,
            MetaRecord(
                datetime_original=None,
                camera_make="Canon",
                camera_model="EOS R7",
                normalized_camera="EOSR7"
            ),
            Plan(
                action=Action.SKIP,
                src_path=MOCK_SRC_PATH_PASS_MP4,
                dst_dir=None,
                dst_name=None,
                reason="촬영일 없음 (PASS 패턴 파일)"
            )
        ),
        # Policy 4: IMG pattern file with valid datetime
        (
            MOCK_SRC_PATH_IMG_JPG,
            MetaRecord(
                datetime_original="2023:01:01 10:00:00",
                camera_make="Canon",
                camera_model="EOS R7",
                normalized_camera="EOSR7"
            ),
            Plan(
                action=Action.COPY_RENAME,
                src_path=MOCK_SRC_PATH_IMG_JPG,
                dst_dir=Path("2023-01-01"),
                dst_name="2023-01-01_10-00-00_1234_EOSR7.jpg",
                reason=None
            )
        ),
        # Policy 4: IMG pattern file with datetime including milliseconds/timezone
        (
            MOCK_SRC_PATH_IMG_MOV,
            MetaRecord(
                datetime_original="2024:02:15 14:30:05.123+09:00",
                camera_make="Apple",
                camera_model="iPhone 13 Pro",
                normalized_camera="iPhone"
            ),
            Plan(
                action=Action.COPY_RENAME,
                src_path=MOCK_SRC_PATH_IMG_MOV,
                dst_dir=Path("2024-02-15"),
                dst_name="2024-02-15_14-30-05_5678_iPhone.mov",
                reason=None
            )
        ),
        # Policy 3: File with valid datetime but not IMG pattern and not PASS pattern (should skip)
        (
            MOCK_SRC_PATH_OTHER_PNG,
            MetaRecord(
                datetime_original="2023:01:01 10:00:00",
                camera_make="Sony",
                camera_model="Alpha 7 III",
                normalized_camera="UNKNOWN"
            ),
            Plan(
                action=Action.SKIP,
                src_path=MOCK_SRC_PATH_OTHER_PNG,
                dst_dir=None,
                dst_name=None,
                reason="IMG 패턴 아님"
            )
        ),
        # Policy 2: File without datetime (neither IMG nor PASS pattern) (should skip)
        (
            MOCK_SRC_PATH_OTHER_PNG,
            MetaRecord(
                datetime_original=None,
                camera_make="Sony",
                camera_model="Alpha 7 III",
                normalized_camera="UNKNOWN"
            ),
            Plan(
                action=Action.SKIP,
                src_path=MOCK_SRC_PATH_OTHER_PNG,
                dst_dir=None,
                dst_name=None,
                reason="촬영일 없음"
            )
        ),
    ]
)
def test_generate_plan(src_path, meta_record, expected_plan):
    """
    Test generate_plan with various scenarios to ensure correct action and plan details.
    """
    actual_plan = generate_plan(src_path, meta_record)
    assert actual_plan == expected_plan
