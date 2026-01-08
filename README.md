# 미디어 파일명 표준화 도구 (media-shotdate-renamer)

`media-shotdate-renamer`는 대량의 사진 및 동영상 파일의 이름을 촬영 날짜를 기준으로 변경해주는 Windows용 프로그램입니다.

## 1. 주요 기능

*   **촬영일 기반 파일명 변경**: 사진/동영상 파일에 기록된 촬영 날짜와 시간 정보를 이용해 `YYYY-MM-DD_HH-MM-SS` 형식의 파일명을 만듭니다.
*   **안전한 복사 방식**: 원본 파일은 그대로 두고, 이름이 변경된 새로운 파일을 지정된 폴더에 복사하여 원본 파일의 손상을 방지합니다.
*   **다양한 파일 지원**: `.jpg`, `.png`, `.heic`, `.mov`, `.mp4` 등 다양한 종류의 이미지 및 동영상 파일을 지원합니다.
*   **하위 폴더 포함**: 선택한 폴더와 그 안의 모든 하위 폴더를 탐색하며 파일을 찾아 처리합니다.
*   **충돌 방지**: 만약 같은 이름의 파일이 이미 존재할 경우, 파일명 뒤에 숫자를 붙여 덮어쓰기를 방지합니다.
*   **상세 로그**: 어떤 파일이 어떻게 처리되었는지, 오류가 발생했는지 등을 로그 파일에 기록하여 쉽게 확인할 수 있습니다.

## 2. 사용법

1.  프로그램을 실행합니다.
2.  `소스 폴더 선택` 버튼을 클릭하여 정리할 사진/동영상 파일이 들어있는 폴더를 선택합니다.
3.  `변환 시작` 버튼을 클릭하면 작업이 시작됩니다.
4.  처리 과정이 실시간으로 로그 창에 표시되며, 진행률 표시줄을 통해 전체 진행 상황을 확인할 수 있습니다.
5.  작업이 완료되면 "완료" 팝업창이 뜹니다.
6.  `결과 폴더 열기` 버튼을 눌러 결과물을 바로 확인할 수 있습니다. 결과물은 원본 폴더 내의 `result` 폴더에 저장됩니다.

## 3. 처리 규칙

*   **파일명 형식**: `YYYY-MM-DD_HH-MM-SS_<식별번호>_<카메라모델>.<확장자>`
    *   예: `2023-10-27_15-30-00_1234_iPhone14Pro.jpg`
*   **결과 폴더**: 원본 폴더 안에 `result` 라는 이름의 폴더가 생성되고, 그 안에 `YYYY-MM-DD` 형식의 날짜별 폴더를 만들어 결과 파일을 저장합니다.
*   **처리 대상**: 파일 이름이 `IMG_` 로 시작하는 등 특정 패턴을 가진 파일들을 주로 변환합니다. 이미 표준 형식으로 이름이 변경된 파일은 그대로 복사만 합니다.
*   **스킵 대상**: 촬영 날짜 정보가 없는 파일이나, 지원하지 않는 형식의 파일은 처리하지 않고 넘어갑니다.

## 4. 설치 및 실행

### 사용자용

*   [Releases 페이지](https://github.com/your-username/media-shotdate-renamer/releases)에서 최신 버전의 `media-shotdate-renamer-v1.0.zip` 파일을 다운로드 받으세요.
*   압축을 푼 후, `main.exe` 파일을 실행하세요. 

### 개발자용

1.  **저장소 복제**
    ```powershell
    git clone https://github.com/your-username/media-shotdate-renamer.git
    cd media-shotdate-renamer
    ```

2.  **가상 환경 생성 및 패키지 설치**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    .\venv\Scripts\pyinstaller.exe main.py -w -F --name msr --add-data "tools/exiftool;exiftool" --paths "src"
    ```

3.  **프로그램 실행**
    ```powershell
    $env:PYTHONPATH = ".\src"
    python -m src.msr
    ```

## 5. 프로젝트 정보

*   **언어**: Python
*   **GUI**: Tkinter
*   **메타데이터 처리**: ExifTool (프로그램에 포함되어 있어 별도 설치가 필요 없습니다.)
*   **라이선스**: MIT License