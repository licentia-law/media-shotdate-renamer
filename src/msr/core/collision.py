"""
This module defines the collision resolution logic.
- DTL M1-05: 충돌 해결(Collision)
- CRG 4.7: 충돌 및 재실행 정책
"""
import re
from pathlib import Path

COLLISION_NUMERIC_SUFFIX_PATTERN = re.compile(r"^(?P<base>.*)(?P<suffix>\d+)$")

def is_same_file(src: Path, dst: Path) -> bool:
    """원본과 대상이 동일한 파일인지 크기와 수정시간으로 확인합니다."""
    try:
        s_stat = src.stat()
        d_stat = dst.stat()
        # shutil.copy2는 mtime을 보존하므로 0.1초 오차 범위 내에서 비교
        return s_stat.st_size == d_stat.st_size and abs(s_stat.st_mtime - d_stat.st_mtime) < 0.1
    except OSError:
        return False

def resolve_collision(src_path: Path, dst_path: Path, _is_retry: bool = False) -> Path:
    """
    Resolves filename collisions by adding a numeric suffix.
    CRG 4.7: 동일 결과명 존재 시 식별번호 뒤에 숫자를 언더바 없이 증가.
    """
    if not dst_path.exists():
        return dst_path

    # 멱등성 체크: 이미 동일한 파일이 결과 폴더에 있다면 해당 경로 반환 (복사 스킵 유도)
    if not _is_retry and is_same_file(src_path, dst_path):
        return dst_path

    name = dst_path.name
    suffix = dst_path.suffix
    stem = dst_path.stem

    parts = stem.split('_')

    # 표준 형식 (YYYY-MM-DD_HH-MM-SS_ID_CAMERA)인 경우 ID 파트 수정
    if len(parts) == 4:
        date_p, time_p, id_p, cam_p = parts
        
        if not _is_retry:
            # 첫 충돌 시 ID 뒤에 '1' 추가 (예: 9672 -> 96721)
            new_id = f"{id_p}1"
        else:
            # 재시도 시 ID 끝의 숫자 증가 (예: 96721 -> 96722)
            match = COLLISION_NUMERIC_SUFFIX_PATTERN.match(id_p)
            if match:
                base = match.group("base")
                num = int(match.group("suffix"))
                new_id = f"{base}{num + 1}"
            else:
                new_id = f"{id_p}1"
        
        new_stem = f"{date_p}_{time_p}_{new_id}_{cam_p}"
    else:
        # 비표준 형식에 대한 폴백
        match = COLLISION_NUMERIC_SUFFIX_PATTERN.match(stem)
        if match:
            base = match.group("base")
            num = int(match.group("suffix"))
            new_stem = f"{base}{num + 1}"
        else:
            new_stem = f"{stem}1"

    new_name = f"{new_stem}{suffix}"
    new_path = dst_path.with_name(new_name)

    if new_path.exists():
        # 이미 존재하는 파일이 원본과 같다면 해당 경로 반환
        if is_same_file(src_path, new_path):
            return new_path
        return resolve_collision(src_path, new_path, _is_retry=True)

    return new_path
