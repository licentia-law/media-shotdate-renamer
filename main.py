"""
This is the main entry point for the application.
It launches the GUI application defined in src/msr/app.py.
"""
from msr.app import MediaShotdateRenamerApp

def main():
    """Initializes and runs the Tkinter application."""
    # TODO: M3-01 - 애플리케이션 초기화 및 실행
    app = MediaShotdateRenamerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
