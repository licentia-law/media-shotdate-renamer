"""
This module defines the Planner functionality, which generates an action plan
for each file based on its metadata and filename patterns.
- DTL M1-04: 플래너(Planner)
- CRG 4.5: 변환/복사 정책
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime

from msr.core.metadata import MetaRecord
from msr.core.patterns import is_img_pattern, is_pass_pattern, get_img_id


class Action(Enum):
    """Defines the possible actions for a file."""
    COPY_RENAME = "COPY_RENAME"  # Rename and copy
    COPY_PASS = "COPY_PASS"      # Copy with existing name (already standardized)
    SKIP = "SKIP"                # Skip processing


@dataclass
class Plan:
    """
    Represents the processing plan for a single media file.
    """
    action: Action
    src_path: Path
    dst_dir: Optional[Path] = None    # Destination directory (relative to result root)
    dst_name: Optional[str] = None    # Final filename in destination
    reason: Optional[str] = None      # Reason for skipping or other notes


def generate_plan(src_path: Path, meta_record: MetaRecord) -> Plan:
    """
    Generates a processing plan for a given source file based on its metadata.
    Applies policies defined in PRD FR-05 and CRG 4.5.
    """
    filename_stem = src_path.stem
    suffix = src_path.suffix.lower()  # CRG 4.1: 결과 확장자는 소문자 통일

    date_str_for_folder: Optional[str] = None
    datetime_str_for_filename: Optional[str] = None

    if meta_record.datetime_original:
        try:
            # PRD FR-03-2: 시간대(Timezone) 처리 - 원문 그대로 사용 (변환/보정 없음)
            # ExifTool 출력은 'YYYY:MM:DD HH:MM:SS' 또는 'YYYY:MM:DD HH:MM:SS.ms+TZ' 형태일 수 있음.
            # .ms+TZ 부분을 제거하고 파싱 시도.
            dt_str_clean = meta_record.datetime_original.split('.')[0].split('+')[0].strip()
            dt_obj = datetime.strptime(dt_str_clean, "%Y:%m:%d %H:%M:%S")
            date_str_for_folder = dt_obj.strftime("%Y-%m-%d")
            datetime_str_for_filename = dt_obj.strftime("%Y-%m-%d_%H-%M-%S")
        except ValueError:
            # 파싱 실패 시, 촬영일이 없는 것으로 간주 (PRD FR-03-3)
            pass

    # Policy 1: PASS 패턴 파일 (CRG 4.5)
    if is_pass_pattern(filename_stem):
        if date_str_for_folder:
            dst_dir = Path(date_str_for_folder)  # CRG 4.6: 결과 경로 [SourceRoot]/result/YYYY-MM-DD/
            dst_name = f"{filename_stem}{suffix}"
            return Plan(Action.COPY_PASS, src_path, dst_dir, dst_name)
        else:
            return Plan(Action.SKIP, src_path, reason="촬영일 없음 (PASS 패턴 파일)")

    # Policy 2: 촬영일 없음 (CRG 4.5)
    if not datetime_str_for_filename:
        return Plan(Action.SKIP, src_path, reason="촬영일 없음")

    # Policy 3: IMG 패턴 아님 (CRG 4.5)
    if not is_img_pattern(filename_stem):
        return Plan(Action.SKIP, src_path, reason="IMG 패턴 아님")

    # Policy 4: 촬영일 있음 + IMG 패턴 (COPY_RENAME) (CRG 4.5)
    img_id = get_img_id(filename_stem)  # is_img_pattern이 True이면 img_id는 항상 존재
    normalized_camera = meta_record.normalized_camera
    dst_name = f"{datetime_str_for_filename}_{img_id}_{normalized_camera}{suffix}"
    dst_dir = Path(date_str_for_folder)  # date_str_for_folder는 이 시점에서 항상 존재
    return Plan(Action.COPY_RENAME, src_path, dst_dir, dst_name)
