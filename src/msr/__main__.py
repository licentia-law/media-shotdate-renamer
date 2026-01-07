"""
Main entry point for the msr package.
Allows execution via 'python -m msr'.
msr 패키지의 실행 진입점입니다.
"""
from msr.app import MediaShotdateRenamerApp

def main():
    """Initializes and runs the application."""
    app = MediaShotdateRenamerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
