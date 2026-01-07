"""
This module defines the main application class, which orchestrates the UI and the core processing logic.
- CRG 5.2: UI는 코어 로직을 블랙박스로 호출하고, 이벤트만 수신.
- DTL M3: GUI 통합(워커/진행률/로그/완료)
"""
import tkinter as tk
from tkinter import messagebox
import os
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Event

from msr.ui.gui import MainWindow
from msr.core.file_processor import FileProcessor


class MediaShotdateRenamerApp(tk.Tk):
    """
    Main application class.
    
    This class initializes the main window and handles the overall application state.
    It will orchestrate the UI (in the main thread) and the file processing
    (in a worker thread).
    """

    def __init__(self):
        super().__init__()

        self.title("Media Shotdate Renamer (v1.0)")
        self.geometry("800x600")
        self.minsize(600, 500)

        # M3-02: 워커 스레드와 통신할 Queue 생성
        self.queue = Queue()
        self.stop_event = Event()

        self.main_window = MainWindow(self)
        self.main_window.pack(side="top", fill="both", expand=True)

        # M3-02: 주기적으로 Queue를 확인하는 `after` 콜백 설정
        self.after(100, self.on_processing_event)

    def start_processing(self, source_directory: str):
        """
        Starts the file processing in a separate worker thread.
        - Disables the 'Start' button to prevent multiple runs.
        - Creates and starts the worker thread.
        - PRD NFR-01: GUI 프리징이 없어야 한다.
        """
        if not source_directory or not os.path.exists(source_directory):
            messagebox.showwarning("경고", "유효한 소스 폴더를 선택해주세요.")
            return
        
        # M3-02: 워커 스레드 생성 및 시작 로직
        self.stop_event.clear()
        processor = FileProcessor(source_directory, self.queue, self.stop_event)
        worker = Thread(target=processor.process_files, daemon=True)
        worker.start()

    def on_processing_event(self):
        """
        Handles events from the worker thread's queue.
        - Updates the progress bar.
        - Appends messages to the log view.
        - Handles the completion event.
        - CRG 8.2: UI 업데이트는 너무 빈번하지 않게(100~250ms) 제한.
        """
        try:
            # 한 번의 after 호출에서 큐에 쌓인 이벤트를 여러 개 처리하여 반응성 향상
            for _ in range(50):
                event = self.queue.get_nowait()
                etype = event.get("type")

                if etype == "LOG":
                    self.main_window.append_log(event["msg"])
                elif etype == "PROGRESS":
                    self.main_window.update_progress(event["current"], event["total"])
                elif etype == "COMPLETE":
                    self.on_processing_complete(event["summary"])
                elif etype == "ERROR":
                    self.on_error(event["msg"])
                
                self.queue.task_done()
        except Empty:
            pass
        finally:
            # 주기적으로 다시 확인
            self.after(100, self.on_processing_event)

    def on_processing_complete(self, summary: dict):
        """
        Called when the worker thread finishes processing.
        - Displays a summary pop-up.
        - Re-enables the 'Start' button.
        - Activates the 'Open Result Folder' button.
        - PRD 2: 완료 팝업 -> "결과 폴더 열기" 버튼 활성화
        """
        # 완료 팝업 표시
        summary_msg = str(summary) if summary else "처리가 완료되었습니다."
        messagebox.showinfo("완료", summary_msg)
        
        # UI 상태 업데이트
        self.main_window.enable_result_button()
        self.main_window.set_start_button_state(True)

    def on_error(self, error_details: str):
        """Handles an error from the worker thread."""
        # TODO: M3-01 / FR-08-2 - 에러 로그 처리
        print(f"An error occurred: {error_details}")
        pass
