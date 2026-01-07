"""
This module defines the file copying and idempotency logic.
- DTL M1-06: 복사/멱등성(Copier)
- CRG 4.7: 충돌 및 재실행 정책
- CRG 7: 파일 I/O 규칙
"""
import shutil
from pathlib import Path
from typing import Tuple, Optional

# Define a return type for copy_file to indicate status
# (success: bool, message: str, final_dst_path: Path, collision_resolved_from: Optional[Path])
# collision_resolved_from is for logging if a collision was resolved, though not directly used here.
CopyResult = Tuple[bool, str, Path, Optional[Path]]

def copy_file(src_path: Path, final_dst_path: Path) -> CopyResult:
    """
    Copies a file from src_path to final_dst_path.
    Handles idempotency: if final_dst_path already exists, it skips the copy.
    Assumes final_dst_path is the result of prior planning and collision resolution
    (if any) and represents the *intended* final destination.
    """
    # CRG 7: 결과 폴더 생성은 exist_ok=True
    final_dst_path.parent.mkdir(parents=True, exist_ok=True)

    # DTL M1-06: “최종 결과 경로 존재 시 스킵” 구현 (Idempotency)
    if final_dst_path.exists():
        return False, f"Skipped: File already exists at {final_dst_path}", final_dst_path, None

    try:
        shutil.copy2(src_path, final_dst_path)
        return True, f"Copied: {src_path.name} to {final_dst_path.name}", final_dst_path, None
    except Exception as e:
        return False, f"Error copying {src_path.name}: {e}", final_dst_path, None
