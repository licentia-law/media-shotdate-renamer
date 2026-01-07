"""
This module contains the core logic for processing files.
- DTL M1: 코어 로직
- DTL M2: ExifTool 배치 추출
"""
import os
from pathlib import Path
from typing import Iterator

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

    def __init__(self, source_dir: str, event_queue):
        # TODO: M1-01 / M3-02 - 초기화
        self.source_path = Path(source_dir)
        self.result_root_path = self.source_path / "result"
        self.event_queue = event_queue
        
        # TODO: M1-07 - 처리 요약(Summary) 객체 초기화

    def process_files(self):
        """
        The main entry point for the file processing pipeline.
        Executes all steps from scanning to copying.
        - PRD 7: 처리 파이프라인
        """
        try:
            # 1. (수집 단계) 대상 파일 목록 수집 및 정렬
            # TODO: M1-01 - 파일 스캐너 구현
            files_to_process = self._scan_files()
            
            # 2. (추출 단계) ExifTool로 메타데이터 추출
            # TODO: M2-02 - ExifTool 배치 추출 구현
            
            # 3. (판별/계획 단계)
            # TODO: M1-04 - Planner 구현: 각 파일에 대한 Plan(액션, 결과경로 등) 생성

            # 4. (저장 단계)
            # TODO: M1-05 - 충돌 해결 로직 적용
            # TODO: M1-06 - Copier 구현: 계획에 따라 파일 복사/스킵 수행
            # TODO: FR-06-2 - 재실행 시 멱등성 처리
            
            # 5. (피드백/요약 단계)
            # TODO: M1-07 - 처리 결과 요약
            
            # TODO: M3-02 - 완료 이벤트 전송
            pass
        except Exception as e:
            # TODO: M3-02 / FR-08-2 - 심각한 오류 발생 시 에러 이벤트 전송
            # (파일 단위 예외는 내부에서 처리되어야 함)
            print(f"A critical error occurred: {e}")


    def _scan_files(self) -> list[Path]:
        """
        Scans the source directory recursively for supported file types.
        - FR-01: 재귀 탐색, 'result' 폴더 제외, 정렬
        - DTL M1-01: 확장자 필터, 정렬
        """
        # TODO: M1-01 - 재귀 탐색, 'result' 제외, 확장자 필터, 정렬 기능 구현
        print("Scanning for files...")
        
        all_files = []
        for root, _, files in os.walk(self.source_path):
            # PRD FR-01: 'result' 폴더는 탐색에서 제외
            if self.result_root_path.as_posix() in Path(root).as_posix():
                continue
            
            for file in files:
                path = Path(root) / file
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    all_files.append(path)
        
        # PRD FR-01: 결정성을 위해 전체 경로 오름차순 정렬
        all_files.sort()
        
        # TODO: M3-02 - 총 파일 개수 이벤트 전송
        print(f"Found {len(all_files)} files.")
        return all_files

    def _generate_rename_plan(self, files: list[Path]):
        """
        Generates an action plan for each file (rename, copy, skip).
        - DTL M1-04: 플래너
        - DTL M2: ExifTool 연동
        """
        # TODO: M2-02 - ExifTool 배치/JSON 추출 호출
        # TODO: M1-03 - 메타데이터 정규화 (촬영일, 카메라)
        # TODO: M1-02 / M1-04 - 패턴 판별 및 정책에 따른 Plan 객체 생성
        # (action: COPY_RENAME, COPY_PASS, SKIP)
        pass

    def _execute_plan(self, plans: list):
        """
        Executes the generated plans (copying/renaming files).
        Handles collisions and idempotency checks.
        - DTL M1-05: 충돌 해결
        - DTL M1-06: 복사/멱등성
        """
        # TODO: M1-06 - 결과 폴더 생성 (exist_ok=True)
        # TODO: M1-05 - 충돌 해결 로직 구현 (동일 실행 내)
        # TODO: M1-06 - 멱등성 체크 (shutil.copy2 사용)
        # TODO: M3-02 - 파일 처리 시마다 진행률 이벤트 전송
        # TODO: FR-08-1 - 사용자 로그 이벤트 전송 (성공/스킵/충돌 등)
        # TODO: FR-08-2 - 파일 단위 예외 발생 시 error.log 기록
        pass
