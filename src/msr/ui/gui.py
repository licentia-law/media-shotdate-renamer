"""
This module contains the UI components for the main application window.
- PRD 7: UI 및 피드백
- DTL M3-01: 메인 윈도우
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

class MainWindow(ttk.Frame):
    """The main window frame containing all UI widgets."""

    def __init__(self, container):
        super().__init__(container)
        self.app = container

        # TODO: M3-01 - UI 위젯 초기화
        # - 소스 폴더 선택 (경로 표시 라벨, '찾아보기' 버튼)
        # - 변환 시작 버튼
        # - 진행률 표시 (ProgressBar + % 텍스트)
        # - 실시간 로그창 (ScrolledText)
        # - '결과 폴더 열기' 버튼 (초기 비활성화)

        self._create_widgets()
        self._create_layout()

    def _create_widgets(self):
        """Create all the necessary UI widgets."""
        # --- Folder Selection ---
        self.folder_frame = ttk.LabelFrame(self, text="1. 소스 폴더 선택")
        self.source_dir_var = tk.StringVar()
        self.source_dir_entry = ttk.Entry(
            self.folder_frame, textvariable=self.source_dir_var, state="readonly", width=80
        )
        self.browse_button = ttk.Button(
            self.folder_frame, text="찾아보기...", command=self._select_source_directory
        )

        # --- Execution Control ---
        self.control_frame = ttk.LabelFrame(self, text="2. 실행")
        self.start_button = ttk.Button(
            self.control_frame, text="변환 시작", command=self._start_processing
        )

        # --- Progress & Logging ---
        self.progress_frame = ttk.LabelFrame(self, text="3. 진행률 및 로그")
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient="horizontal", mode="determinate"
        )
        self.progress_label_var = tk.StringVar(value="0 / 0 (0.0%)")
        self.progress_label = ttk.Label(self.progress_frame, textvariable=self.progress_label_var)
        self.log_view = scrolledtext.ScrolledText(self.progress_frame, state="disabled", height=15)
        
        # --- Result ---
        self.result_frame = ttk.LabelFrame(self, text="4. 결과")
        self.open_result_button = ttk.Button(
            self.result_frame, text="결과 폴더 열기", state="disabled", command=self._open_result_folder
        )


    def _create_layout(self):
        """Arrange widgets in the main window."""
        self.folder_frame.pack(padx=10, pady=5, fill="x")
        self.source_dir_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.browse_button.pack(side="right", padx=5, pady=5)

        self.control_frame.pack(padx=10, pady=5, fill="x")
        self.start_button.pack(pady=5)
        
        self.progress_frame.pack(padx=10, pady=5, fill="both", expand=True)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_label.pack(padx=5)
        self.log_view.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.result_frame.pack(padx=10, pady=5, fill="x")
        self.open_result_button.pack(pady=5)


    def _select_source_directory(self):
        """
        Open a dialog to select the source directory.
        - FR-01: 사용자는 GUI에서 소스 루트 폴더를 선택할 수 있어야 한다.
        """
        directory = filedialog.askdirectory(
            title="미디어 파일이 있는 소스 폴더를 선택하세요",
            mustexist=True
        )
        if directory:
            self.source_dir_var.set(directory)
            # TODO: 로그창에 폴더 선택 기록
            self.log_message(f"선택된 폴더: {directory}")

    def _start_processing(self):
        """
        Validate input and delegate the start call to the main app instance.
        """
        source_dir = self.source_dir_var.get()
        if not source_dir:
            # TODO: 사용자에게 폴더 선택하라는 경고 메시지 표시
            self.log_message("[오류] 먼저 소스 폴더를 선택하세요.", error=True)
            return

        # TODO: M3-01 / M3-02 - UI 컨트롤 비활성화 (시작 버튼 등)
        self.start_button.config(state="disabled")
        self.browse_button.config(state="disabled")
        self.app.start_processing(source_dir)

    def _open_result_folder(self):
        """
        Opens the result folder in the file explorer.
        - PRD 2: 완료 팝업 -> “결과 폴더 열기” 버튼 활성화
        """
        # TODO: 결과 폴더 경로를 알아내서 열어야 함
        # 이 경로는 file_processor 또는 app 레벨에서 관리되어야 함
        print("Opening result folder...")
        pass

    def log_message(self, message: str, error: bool = False):
        """Appends a message to the log view."""
        self.log_view.config(state="normal")
        self.log_view.insert(tk.END, message + "\n")
        # TODO: 에러 태그(스타일) 적용
        self.log_view.see(tk.END) # Auto-scroll
        self.log_view.config(state="disabled")

    def update_progress(self, current: int, total: int):
        """Updates the progress bar and label."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar["value"] = percentage
            self.progress_label_var.set(f"{current} / {total} ({percentage:.1f}%)")
        else:
            self.progress_bar["value"] = 0
            self.progress_label_var.set("0 / 0 (0.0%)")
        self.update_idletasks()
