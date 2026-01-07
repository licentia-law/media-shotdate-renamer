import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from msr.core.exiftool import ExifToolError, get_exiftool_path

if TYPE_CHECKING:
    sys.frozen: bool  # type: ignore[assignment]
    sys._MEIPASS: str  # type: ignore[assignment]


@pytest.fixture(autouse=True)
def restore_pyinstaller_flags():
    """
    각 테스트가 끝난 뒤 sys.frozen / sys._MEIPASS를 원복한다.

    - PyInstaller 속성은 비표준이므로, 존재 여부까지 포함해 정확히 원복한다.
    """
    had_frozen = hasattr(sys, "frozen")
    had_meipass = hasattr(sys, "_MEIPASS")
    orig_frozen = getattr(sys, "frozen", None)
    orig_meipass = getattr(sys, "_MEIPASS", None)

    yield

    # restore frozen
    if had_frozen:
        sys.frozen = orig_frozen  # type: ignore[attr-defined]
    else:
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")

    # restore _MEIPASS
    if had_meipass:
        sys._MEIPASS = orig_meipass  # type: ignore[attr-defined]
    else:
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")


def test_get_exiftool_path_dev_mode_success(tmp_path: Path):
    """
    개발 모드: project_root/tools/exiftool/exiftool.exe 존재 시 경로 반환
    """
    # Simulate dev mode
    if hasattr(sys, "frozen"):
        delattr(sys, "frozen")
    if hasattr(sys, "_MEIPASS"):
        delattr(sys, "_MEIPASS")

    tools_dir = tmp_path / "tools" / "exiftool"
    tools_dir.mkdir(parents=True)
    expected = tools_dir / "exiftool.exe"
    expected.touch()

    got = get_exiftool_path(project_root=tmp_path)
    assert got == expected


def test_get_exiftool_path_dev_mode_not_found(tmp_path: Path):
    """
    개발 모드: project_root/tools/exiftool/exiftool.exe 미존재 시 예외
    """
    if hasattr(sys, "frozen"):
        delattr(sys, "frozen")
    if hasattr(sys, "_MEIPASS"):
        delattr(sys, "_MEIPASS")

    (tmp_path / "tools" / "exiftool").mkdir(parents=True)

    with pytest.raises(ExifToolError, match=r"ExifTool executable not found"):
        get_exiftool_path(project_root=tmp_path)


def test_get_exiftool_path_bundled_mode_success(tmp_path: Path):
    """
    번들 모드: sys._MEIPASS/exiftool/exiftool.exe 존재 시 경로 반환
    """
    sys.frozen = True  # type: ignore[attr-defined]
    sys._MEIPASS = str(tmp_path)  # type: ignore[attr-defined]

    bundle_exif_dir = tmp_path / "exiftool"
    bundle_exif_dir.mkdir(parents=True)
    expected = bundle_exif_dir / "exiftool.exe"
    expected.touch()

    got = get_exiftool_path()
    assert got == expected


def test_get_exiftool_path_bundled_mode_not_found(tmp_path: Path):
    """
    번들 모드: sys._MEIPASS/exiftool/exiftool.exe 미존재 시 예외
    """
    sys.frozen = True  # type: ignore[attr-defined]
    sys._MEIPASS = str(tmp_path)  # type: ignore[attr-defined]

    (tmp_path / "exiftool").mkdir(parents=True)

    with pytest.raises(ExifToolError, match=r"ExifTool executable not found"):
        get_exiftool_path()
