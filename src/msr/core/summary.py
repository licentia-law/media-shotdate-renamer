"""
This module defines the Summary functionality for aggregating processing results.
- DTL M1-07: 요약 집계(Summary)
- PRD FR-08-3: 처리 요약(종료 시)
- DTL M2-04: 성능 계측
"""
from dataclasses import dataclass
import time

@dataclass
class Summary:
    """
    Aggregates the results of the file processing operation.
    """
    total_files: int = 0
    converted_success: int = 0
    pass_copied: int = 0
    skipped_no_datetime: int = 0
    skipped_not_img_pattern: int = 0
    collisions_resolved: int = 0
    skipped_already_exists: int = 0
    errors: int = 0

    # DTL M2-04: 성능 계측용 필드
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def throughput(self) -> float:
        return self.total_files / self.duration if self.duration > 0 else 0.0

    def increment_total_files(self):
        self.total_files += 1

    def increment_converted_success(self):
        self.converted_success += 1

    def increment_pass_copied(self):
        self.pass_copied += 1

    def increment_skipped_no_datetime(self):
        self.skipped_no_datetime += 1

    def increment_skipped_not_img_pattern(self):
        self.skipped_not_img_pattern += 1

    def increment_collisions_resolved(self):
        self.collisions_resolved += 1

    def increment_skipped_already_exists(self):
        self.skipped_already_exists += 1

    def increment_errors(self):
        self.errors += 1

    def __str__(self):
        """
        Generates a formatted summary string for display.
        """
        return (
            f"--- 처리 요약 ---\n"
            f"총 파일 수: {self.total_files}\n"
            f"변환 성공: {self.converted_success}\n"
            f"PASS 복사: {self.pass_copied}\n"
            f"스킵 (촬영일 없음): {self.skipped_no_datetime}\n"
            f"스킵 (IMG 패턴 아님): {self.skipped_not_img_pattern}\n"
            f"충돌 해결: {self.collisions_resolved}\n"
            f"스킵 (이미 존재): {self.skipped_already_exists}\n"
            f"오류 발생: {self.errors}\n"
            f"소요 시간: {self.duration:.2f}초\n"
            f"처리 속도: {self.throughput:.2f} 파일/초\n"
            f"-----------------"
        )
