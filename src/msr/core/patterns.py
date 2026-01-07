"""
This module defines the regular expressions for identifying file patterns.
- PRD FR-04: 파일명 패턴 판별
- CRG 4.2: 파일명 패턴
- DTL M1-02: 패턴 판별(Patterns)
"""
import re

# TODO: M1-02 - IMG/PASS 정규식 구현 및 테스트
# PRD FR-04-1: IMG 패턴
# - 파일명이 `IMG_<식별번호>` 패턴
# - 식별번호: 숫자 + 영문 0~10글자
# - 대소문자 무시
# - 정규식: ^(?i)IMG_(?P<id>\\d+[a-z]{0,10})$
IMG_PATTERN = re.compile(r"^(?i)IMG_(?P<id>\\d+[a-z]{0,10})$")

# PRD FR-04-2: PASS 패턴
# - 파일명이 `YYYY-MM-DD_HH-MM-SS_<식별번호>_<카메라>.<ext>` 형식
# - 확장자를 제외한 본문 기준
# - 정규식: ^\\d{4}-\\d{2}-\\d{2}_\\d{2}-\\d{2}-\\d{2}_[^_]+_[A-Za-z0-9]+$
PASS_PATTERN = re.compile(r"^\\d{4}-\\d{2}-\\d{2}_\\d{2}-\\d{2}-\\d{2}_[^_]+_[A-Za-z0-9]+$")


def is_img_pattern(filename_stem: str) -> bool:
    """Checks if the filename (without extension) matches the IMG pattern."""
    # TODO: M1-02 - 함수 구현
    return bool(IMG_PATTERN.match(filename_stem))

def is_pass_pattern(filename_stem: str) -> bool:
    """Checks if the filename (without extension) matches the PASS pattern."""
    # TODO: M1-02 - 함수 구현
    return bool(PASS_PATTERN.match(filename_stem))

def get_img_id(filename_stem: str) -> str | None:
    """Extracts the identifier from an IMG pattern filename."""
    # TODO: M1-02 - 함수 구현
    match = IMG_PATTERN.match(filename_stem)
    if match:
        return match.group("id")
    return None

# TODO: DTL M5-01 - 패턴 판별 단위 테스트 작성 (tests/test_patterns.py)
# - 정상 케이스 (IMG_1234, img_5678, IMG_123a, img_456b)
# - 실패 케이스 (IMG_12345678901a, IMG_ABC, 1234_IMG)
# - PASS 패턴 정상/실패 케이스
