"""
This module defines the main application class, which orchestrates the UI and the core processing logic.
- CRG 5.2: UI는 코어 로직을 블랙박스로 호출하고, 이벤트만 수신.
- DTL M3: GUI 통합(워커/진행률/로그/완료)
"""
import tkinter as tk
from tkinter import ttk

from msr.ui.gui import MainWindow

# TODO: M3-02 - 워커 스레드 및 Queue 임포트
# from queue import Queue
# from threading import Thread


class MediaShotdateRenamerApp(tk.Tk):
    """
    Main application class.
    
    This class initializes the main window and handles the overall application state.
    It will orchestrate the UI (in the main thread) and the file processing
    (in a worker thread).
    """

    def __init__(self):
        super().__init__()

        # TODO: M3-01 - 메인 윈도우 설정
        # - 타이틀 설정
        # - 창 크기 및 초기 위치 설정
        # - 창 크기 조절 가능 여부 설정
        self.title("Media Shotdate Renamer (v1.0)")
        self.geometry("800x600")

        # TODO: M3-02 - 워커 스레드와 통신할 Queue 생성

        # TODO: M3-01 - 메인 UI 프레임 생성 및 표시
        self.main_window = MainWindow(self)
        self.main_window.pack(side="top", fill="both", expand=True)

        # TODO: M3-02 - 주기적으로 Queue를 확인하는 `after` 콜백 설정

    def start_processing(self, source_directory: str):
        """
        Starts the file processing in a separate worker thread.
        - Disables the 'Start' button to prevent multiple runs.
        - Creates and starts the worker thread.
        - PRD NFR-01: GUI 프리징이 없어야 한다.
        """
        # TODO: M3-02 - 워커 스레드 생성
        # - file_processor.process_files를 target으로 지정
        # - UI 업데이트를 위한 Queue를 인자로 전달
        print(f"Request to start processing in: {source_directory}")
        pass

    def on_processing_event(self):
        """
        Handles events from the worker thread's queue.
        - Updates the progress bar.
        - Appends messages to the log view.
        - Handles the completion event.
        - CRG 8.2: UI 업데이트는 너무 빈번하지 않게(100~250ms) 제한.
        """
        # TODO: M3-02 - Queue에서 이벤트 가져오기 및 처리
        # - 진행률 업데이트
        # - 로그 메시지 추가
        # - 완료/에러 상태 처리
        pass

    def on_processing_complete(self, summary: dict):
        """
        Called when the worker thread finishes processing.
        - Displays a summary pop-up.
        - Re-enables the 'Start' button.
        - Activates the 'Open Result Folder' button.
        - PRD 2: 완료 팝업 -> "결과 폴더 열기" 버튼 활성화
        """
        # TODO: M3-01 - 완료 팝업 표시
        # TODO: FR-08-3 - 처리 요약 표시
        print("Processing complete!")
        print(summary)
        pass

    def on_error(self, error_details: str):
        """Handles an error from the worker thread."""
        # TODO: M3-01 / FR-08-2 - 에러 로그 처리
        print(f"An error occurred: {error_details}")
        pass
