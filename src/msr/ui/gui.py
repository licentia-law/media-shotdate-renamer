import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path

class MainWindow(ttk.Frame):
    """
    Main UI Frame containing all widgets.
    - PRD FR-07: UI 구성 요소 구현
    """
    def __init__(self, master):
        super().__init__(master, padding="10")
        self.master = master
        self.source_dir = tk.StringVar()
        
        self._create_widgets()

    def _create_widgets(self):
        # 1. Folder Selection Area
        folder_frame = ttk.LabelFrame(self, text="소스 폴더 선택", padding="5")
        folder_frame.pack(fill="x", pady=(0, 10))

        ttk.Entry(folder_frame, textvariable=self.source_dir, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(folder_frame, text="찾아보기...", command=self._browse_folder).pack(side="right")

        # 2. Control Area
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=5)

        self.start_btn = ttk.Button(control_frame, text="변환 시작", command=self._on_start_click)
        self.start_btn.pack(side="left", padx=5)

        self.open_result_btn = ttk.Button(control_frame, text="결과 폴더 열기", command=self._open_result_folder, state="disabled")
        self.open_result_btn.pack(side="left", padx=5)

        # 3. Progress Area
        progress_frame = ttk.LabelFrame(self, text="진행률", padding="5")
        progress_frame.pack(fill="x", pady=10)

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="대기 중... (0/0)")
        self.progress_label.pack()

        # 4. Log Area
        log_frame = ttk.LabelFrame(self, text="로그", padding="5")
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_frame, height=15, state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    def _browse_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            self.source_dir.set(directory)
            self.open_result_btn.configure(state="disabled")

    def _on_start_click(self):
        path = self.source_dir.get()
        if path:
            self.set_start_button_state(False)
            self.open_result_btn.configure(state="disabled")
            self.clear_logs()
            self.master.start_processing(path)

    def _open_result_folder(self):
        """Opens the [SourceRoot]/result folder in Windows Explorer."""
        path = self.source_dir.get()
        if path:
            result_path = Path(path) / "result"
            if result_path.exists():
                os.startfile(result_path)

    # --- UI Update Methods ---

    def set_start_button_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.start_btn.configure(state=state)

    def enable_result_button(self):
        self.open_result_btn.configure(state="normal")

    def update_progress(self, current: int, total: int):
        if total > 0:
            percent = (current / total) * 100
            self.progress_bar["value"] = percent
            self.progress_label.configure(text=f"처리 중... {percent:.1f}% ({current}/{total})")

    def append_log(self, message: str):
        """Appends a message to the log window in a thread-safe way (via master.after if needed)."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_label.configure(text="대기 중... (0/0)")
