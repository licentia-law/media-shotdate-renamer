import pytest
from msr.core.summary import Summary

# --- Summary tests ---

def test_summary_initialization():
    """
    Test case: Summary object should initialize with all counters at zero.
    """
    summary = Summary()
    assert summary.total_files == 0
    assert summary.converted_success == 0
    assert summary.pass_copied == 0
    assert summary.skipped_no_datetime == 0
    assert summary.skipped_not_img_pattern == 0
    assert summary.collisions_resolved == 0
    assert summary.skipped_already_exists == 0
    assert summary.errors == 0

def test_summary_increment_methods():
    """
    Test case: Each increment method should correctly increase its respective counter.
    """
    summary = Summary()

    summary.increment_total_files()
    assert summary.total_files == 1

    summary.increment_converted_success()
    assert summary.converted_success == 1

    summary.increment_pass_copied()
    assert summary.pass_copied == 1

    summary.increment_skipped_no_datetime()
    assert summary.skipped_no_datetime == 1

    summary.increment_skipped_not_img_pattern()
    assert summary.skipped_not_img_pattern == 1

    summary.increment_collisions_resolved()
    assert summary.collisions_resolved == 1

    summary.increment_skipped_already_exists()
    assert summary.skipped_already_exists == 1

    summary.increment_errors()
    assert summary.errors == 1

    # Test multiple increments
    summary.increment_total_files()
    assert summary.total_files == 2

def test_summary_str_representation():
    """
    Test case: The __str__ method should return a correctly formatted summary string.
    """
    summary = Summary(
        total_files=10,
        converted_success=5,
        pass_copied=2,
        skipped_no_datetime=1,
        skipped_not_img_pattern=1,
        collisions_resolved=3,
        skipped_already_exists=1,
        errors=0
    )
    expected_str = (
        "--- 처리 요약 ---\n"
        "총 파일 수: 10\n"
        "변환 성공: 5\n"
        "PASS 복사: 2\n"
        "스킵 (촬영일 없음): 1\n"
        "스킵 (IMG 패턴 아님): 1\n"
        "충돌 해결: 3\n"
        "스킵 (이미 존재): 1\n"
        "오류 발생: 0\n"
        "-----------------"
    )
    assert str(summary) == expected_str
