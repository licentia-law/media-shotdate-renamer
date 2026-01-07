"""
This module contains the core logic for processing files.
- DTL M1: 코어 로직
- DTL M2: ExifTool 배치 추출
"""
import os
import time
import traceback
from pathlib import Path
from typing import List

from msr.core.summary import Summary
from msr.core.exiftool import extract_metadata_batch, ExifToolError
from msr.core.planner import generate_plan, Action
from msr.core.collision import resolve_collision
from msr.core.copier import copy_file

CHUNK_SIZE = 500  # CRG 6.1: 배치 추출 단위

# TODO: M1-01 - 지원 확장자 상수 정의 (CRG 4.1)
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".heic", ".cr3", ".dng", ".gif", # images
    ".mp4", ".mov" # videos
}

class FileProcessor:
    """
    Handles the main file processing pipeline.
    This class will be instantiated and run within a worker thread.
    """

    def __init__(self, source_dir: str, event_queue, stop_event=None):
        self.source_path = Path(source_dir)
        self.result_root_path = self.source_path / "result"
        self.event_queue = event_queue
        self.stop_event = stop_event
        
        # DTL M1-07: 처리 요약(Summary) 객체 초기화
        self.summary = Summary()

    def process_files(self):
        """
        The main entry point for the file processing pipeline.
        Executes all steps from scanning to copying.
        - PRD 7: 처리 파이프라인
        """
        try:
            if not self.source_path.exists():
                self._send_event("ERROR", msg=f"소스 폴더가 존재하지 않습니다: {self.source_path}")
                return

            # DTL M2-04: 전체 처리 시간 측정 시작
            self.summary.start_time = time.perf_counter()
            self._send_log("--- 작업을 시작합니다 ---")

            # 1. (수집 단계) 대상 파일 목록 수집 및 정렬
            files_to_process = self._scan_files()
            total_count = len(files_to_process)
            self.summary.total_files = total_count
            self._send_progress(0, total_count)

            if total_count == 0:
                self._send_log("처리할 파일이 없습니다.")
                self._finish_process()
                return

            # NFR-02: 결과 폴더 생성 및 쓰기 권한 체크
            try:
                self.result_root_path.mkdir(parents=True, exist_ok=True)
                # 실제 쓰기 가능 여부 테스트
                test_file = self.result_root_path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError) as e:
                self._send_event("ERROR", msg=f"결과 폴더 생성 또는 쓰기 권한이 없습니다: {e}")
                return

            run_log_path = self.result_root_path / "run.log"
            error_log_path = self.result_root_path / "error.log"

            processed_count = 0

            # 2. (추출/계획/저장 단계) Chunk 단위 처리
            for i in range(0, total_count, CHUNK_SIZE):
                if self.stop_event and self.stop_event.is_set():
                    self._send_log("작업이 사용자에 의해 중단되었습니다.")
                    break

                chunk = files_to_process[i : i + CHUNK_SIZE]
                
                try:
                    # ExifTool 배치 추출
                    metadata_map = extract_metadata_batch(chunk)
                except ExifToolError as e:
                    self._send_log(f"ExifTool 오류: {e}")
                    self._record_error(error_log_path, f"Batch {i//CHUNK_SIZE + 1}", str(e), include_traceback=True)
                    processed_count += len(chunk)
                    self.summary.errors += len(chunk)
                    continue

                for src_path in chunk:
                    if self.stop_event and self.stop_event.is_set():
                        break

                    processed_count += 1
                    try:
                        # ExifTool 결과와 매칭하기 위해 경로를 정규화(resolve)하여 조회합니다.
                        # Windows에서 슬래시/역슬래시 및 대소문자 차이로 인한 누락 방지.
                        resolved_path = src_path.resolve()
                        meta = metadata_map.get(resolved_path)
                        if not meta:
                            raise ValueError("메타데이터 추출 실패")

                        # 계획 생성
                        plan = generate_plan(src_path, meta)
                        
                        if plan.action == Action.SKIP:
                            self._send_log(f"스킵: {src_path.name} ({plan.reason})")
                            if "촬영일" in plan.reason:
                                self.summary.increment_skipped_no_datetime()
                            else:
                                self.summary.increment_skipped_not_img_pattern()
                            continue

                        # 최종 경로 결정 및 충돌 해결
                        dst_path = self.result_root_path / plan.dst_dir / plan.dst_name
                        final_dst_path = resolve_collision(src_path, dst_path)
                        
                        if final_dst_path != dst_path:
                            self.summary.increment_collisions_resolved()
                            self._send_log(f"충돌 해결: {dst_path.name} -> {final_dst_path.name}")

                        # 복사 실행
                        success, msg, _, _ = copy_file(src_path, final_dst_path)
                        
                        if success:
                            if plan.action == Action.COPY_RENAME:
                                self.summary.increment_converted_success()
                            else:
                                self.summary.increment_pass_copied()
                            self._send_log(f"성공: {src_path.name} -> {final_dst_path.name}")
                        else:
                            if "already exists" in msg:
                                self.summary.increment_skipped_already_exists()
                                self._send_log(f"스킵: 이미 존재함 ({final_dst_path.name})")
                            else:
                                raise RuntimeError(msg)

                    except Exception as e:
                        self.summary.increment_errors()
                        self._send_log(f"오류: {src_path.name} - {e}")
                        self._record_error(error_log_path, str(src_path), str(e), include_traceback=True)
                    
                    # 진행률 업데이트
                    self._send_progress(processed_count, total_count)

            self._finish_process()

        except Exception as e:
            self._send_event("ERROR", msg=f"치명적 오류 발생: {e}")
            print(traceback.format_exc())

    def _finish_process(self):
        self.summary.end_time = time.perf_counter()
        self._send_log("--- 모든 작업이 완료되었습니다 ---")
        self._send_event("COMPLETE", summary=self.summary)

    def _scan_files(self) -> List[Path]:
        """
        Scans the source directory recursively for supported file types.
        - FR-01: 재귀 탐색, 'result' 폴더 제외, 정렬
        - DTL M1-01: 확장자 필터, 정렬
        """
        self._send_log("파일 목록을 수집 중입니다...")
        
        all_files = []
        for root, _, files in os.walk(self.source_path):
            if Path(root).is_relative_to(self.result_root_path):
                continue
            
            for file in files:
                path = Path(root) / file
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    all_files.append(path)
        
        all_files.sort()
        self._send_log(f"총 {len(all_files)}개의 대상 파일을 찾았습니다.")
        return all_files

    def _send_event(self, etype: str, **kwargs):
        self.event_queue.put({"type": etype, **kwargs})

    def _send_log(self, msg: str):
        self._send_event("LOG", msg=msg)
        # run.log 파일 기록
        if self.result_root_path.exists():
            with open(self.result_root_path / "run.log", "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

    def _send_progress(self, current: int, total: int):
        self._send_event("PROGRESS", current=current, total=total)

    def _record_error(self, log_path: Path, file_info: str, error_msg: str, include_traceback: bool = False):
        with open(log_path, "a", encoding="utf-8") as f:
            # PRD FR-08-2: 시간(ISO) 형식 사용
            timestamp = time.strftime('%Y-%m-%dT%H:%M:%S')
            f.write(f"[{timestamp}] {file_info}: {error_msg}\n")
            if include_traceback:
                f.write(traceback.format_exc())
                f.write("-" * 40 + "\n")
