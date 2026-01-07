"""
msr.core.exiftool

ExifTool 실행 파일 경로 탐지 및 배치 메타데이터 추출 유틸리티.

DTL/CRG 매핑(요약)
- M2-01: ExifTool 번들 경로 탐지(get_exiftool_path)
- M2-02: 배치 추출(성능 저하 예방) - extract_metadata_batch
- M2-03 ExifTool 오류/재시도(권장)
- CRG 4.3: 촬영일 태그 우선순위는 msr.core.metadata.extract_and_normalize_metadata에서 적용
- CRG 4.4: 카메라 정규화는 msr.core.metadata.normalize_camera_model에서 적용

정책(중요)
- ExifTool은 Python 패키지로 설치하지 않고, repo 내부(개발 모드) 또는 PyInstaller 번들 내부(배포 모드)에 포함한다.
- 개발 모드: <project_root>/tools/exiftool/exiftool.exe
- 번들 모드: <bundle_dir>/exiftool/exiftool.exe   (bundle_dir == sys._MEIPASS)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, TYPE_CHECKING

class ExifToolError(RuntimeError):
    """ExifTool 관련 오류(경로 탐지 실패, 실행 실패, 파싱 실패 등)."""
    pass


def _default_exe_name() -> str:
    """OS에 따른 ExifTool 실행 파일명 결정."""
    return "exiftool.exe" if sys.platform.startswith("win") else "exiftool"


def is_bundled() -> bool:
    """PyInstaller 번들 실행 여부 판단."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def find_project_root(start: Path) -> Path:
    """
    개발 모드에서 프로젝트 루트를 상향 탐색하여 찾는다.

    우선순위:
    1) pyproject.toml 존재
    2) tools/exiftool 폴더 존재
    """
    start = start.resolve()
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").is_file():
            return p
        if (p / "tools" / "exiftool").is_dir():
            return p
    return start.parents[0] if start.parents else start


def get_exiftool_path(
    *,
    project_root: Optional[Path] = None,
    bundle_dir: Optional[Path] = None,
    exe_name: Optional[str] = None,
) -> Path:
    """
    ExifTool 실행 파일 경로를 반환한다.

    Parameters
    - project_root: 개발 모드에서 사용할 프로젝트 루트(테스트/주입용). None이면 자동 탐색.
    - bundle_dir: 번들 모드에서 사용할 번들 루트(테스트/주입용). None이면 sys._MEIPASS 사용.
    - exe_name: 실행 파일명(기본: OS에 따라 exiftool 또는 exiftool.exe)

    Raises
    - ExifToolError: 실행 파일을 찾지 못한 경우
    """
    exe = exe_name or _default_exe_name()

    if is_bundled():
        base = bundle_dir or Path(getattr(sys, "_MEIPASS"))
        exiftool_path = base / "exiftool" / exe
    else:
        root = project_root or find_project_root(Path(__file__).resolve())
        exiftool_path = root / "tools" / "exiftool" / exe

    if not exiftool_path.is_file():
        raise ExifToolError(f"ExifTool executable not found at: {exiftool_path}")

    return exiftool_path


# CRG 6.2: 필요한 태그만 조회 (SourceFile은 매핑을 위해 필수)
EXIFTOOL_TAGS = [
    "-charset", "filename=utf8",  # 인코딩 문제 방지 (특히 PyInstaller 환경)
    "-SourceFile",
    "-DateTimeOriginal",
    "-CreateDate",
    "-MediaCreateDate",
    "-TrackCreateDate",
    "-Make",
    "-Model",
]

MAX_RETRIES = 2


def extract_metadata_batch(files: list[Path], _retry_count: int = 0) -> dict[Path, "MetaRecord"]:
    """
    ExifTool을 1회 호출하여 여러 파일의 메타데이터를 JSON으로 추출 후,
    파일별로 MetaRecord(정규화 포함)로 변환하여 반환한다.

    - 빈 입력이면 {} 반환
    - ExifTool 실행 실패/파싱 실패 시 ExifToolError 발생 (재시도 로직 포함)
    - ExifTool JSON 엔트리 중 SourceFile이 누락된 항목은 skip

    Note:
    - MetaRecord/정규화 로직은 msr.core.metadata에 위임한다.
    """
    if not files:
        return {}

    # 지연 import(순환참조 방지)
    from msr.core.metadata import MetaRecord, extract_and_normalize_metadata

    exiftool = get_exiftool_path()

    # DTL 성능 정책: 배치 호출 1회 (argfile 사용으로 인코딩/길이 문제 해결)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
        for p in files:
            f.write(str(p.resolve()) + "\n")
        arg_file = f.name

    cmd: list[str] = [
        str(exiftool),
        "-json",
        "-s3",
        *EXIFTOOL_TAGS,
        "-@",
        arg_file
    ]

    # Windows에서 콘솔 창이 뜨는 것을 방지하기 위한 플래그
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        # text=True: stdout/stderr를 str로 받기
        # check=True: 비정상 종료 시 CalledProcessError
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
        )
        data = json.loads(proc.stdout or "[]")
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, OSError) as e:
        # DTL M2-03: 배치 호출 실패 시 chunk를 반으로 쪼개 재시도
        if len(files) > 1 and _retry_count < MAX_RETRIES:
            mid = len(files) // 2
            results = {}
            for chunk in [files[:mid], files[mid:]]:
                try:
                    results.update(extract_metadata_batch(chunk, _retry_count + 1))
                except ExifToolError:
                    pass  # 개별 실패는 결과에서 제외됨 (상위에서 비교하여 스킵 처리)
            return results

        # 최종 실패 시 예외 발생
        if isinstance(e, FileNotFoundError):
            msg = "ExifTool executable not found"
        elif isinstance(e, subprocess.CalledProcessError):
            msg = f"ExifTool batch command failed: {e.stderr or ''}"
        else:
            msg = f"Failed to parse ExifTool JSON output or OS error: {e}"
        raise ExifToolError(msg) from e
    finally:
        if os.path.exists(arg_file):
            try:
                os.unlink(arg_file)
            except OSError:
                pass

    result: dict[Path, MetaRecord] = {}

    if not isinstance(data, list):
        # 방어적 처리(정상이라면 list)
        raise ExifToolError("Failed to parse ExifTool JSON output")

    for entry in data:
        if not isinstance(entry, dict):
            continue

        source = entry.get("SourceFile")
        if not source:
            continue

        # ExifTool은 슬래시(/)를 반환하거나 경로 형식이 다를 수 있으므로,
        # 입력 Path와 일치시키기 위해 resolve()로 정규화합니다.
        src_path = Path(source).resolve()

        # 정규화는 metadata 모듈이 책임
        meta = extract_and_normalize_metadata(src_path, entry)
        result[src_path] = meta

    return result
