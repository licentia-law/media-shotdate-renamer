# CRG — Coding Rules & Guidelines
> Repository: **media-shotdate-renamer**  
> Version: v1.0 (2026-01-07)  
> Target OS: Windows  
> Language/GUI: Python 3.x / tkinter  
> Packaging: PyInstaller (+ `.spec`)  
> Metadata Engine: ExifTool (bundled)

---

## 1. 목적
본 문서는 `PRD.md` 요구사항을 **일관되게 구현**하기 위한 코딩 규칙/가이드라인을 정의한다.

**핵심 원칙**
- **원본 비파괴**: 원본 파일은 절대 수정/삭제/rename 하지 않는다.
- **결정성**: 입력 동일 시 결과가 재현 가능해야 한다(정렬/규칙 고정).
- **멱등성**: 재실행 시 결과 파일이 있으면 스킵한다.
- **성능**: 수천 장에서도 ExifTool 호출 오버헤드를 최소화한다(배치/지속 프로세스).
- **UX**: GUI 프리징 금지(워커 + Queue 기반).

---

## 2. 저장소/폴더 구조(권장)
```
media-shotdate-renamer/
  docs/
    PRD.md
    CRG.md
    DTL.md
	README.md
  pyproject.toml            # (권장) ruff/mypy/pytest 설정
  requirements.txt          # (옵션) 고정 의존성
  src/
    msr/                    # package root (Media Shotdate Renamer)
      __init__.py
      app.py                # tkinter entry / wiring
      ui/                   # UI widgets, view models
        main_window.py
      core/
        scanner.py          # 파일 수집/정렬/필터
        patterns.py         # 정규식, PASS/IMG 판별
        metadata.py         # 메타데이터 모델/정규화
        exiftool.py         # ExifTool runner (batch or stay_open)
        planner.py          # 변환 계획(입력 -> 결과 경로/이름/액션)
        collision.py        # 충돌 해결 규칙
        copier.py           # copy executor + 멱등성 체크
        logger.py           # 한글 사용자 로그 + 파일 로그
        summary.py          # 처리 요약 집계
      util/
        paths.py            # Windows path 유틸
        timefmt.py          # 날짜/시간 포맷
        safe_io.py          # 안전한 파일 I/O 래퍼
  tools/
    exiftool/
      exiftool.exe
  build/
    media-shotdate-renamer.spec
  tests/
    test_patterns.py
    test_collision.py
    test_planner.py
    fixtures/
      ...
```
- 패키지명 `msr`는 예시이며, 일관되게 유지한다.
- `tools/exiftool/exiftool.exe`는 **상대경로 기준**으로 포함한다.

---

## 3. 코딩 표준
### 3.1 Python 버전/타이핑
- Python 3.11+ 권장(Windows 배포 안정성 고려).
- **Type hints 필수**(core 모듈 전반).
- `dataclasses` 적극 활용(메타데이터/계획/요약 구조체).

### 3.2 스타일/린트(권장)
- `ruff`(format+lint), `mypy`(type check), `pytest`(test).
- 모든 공개 함수에 docstring(간결하게: 입력/출력/예외).

### 3.3 예외 처리 원칙
- **파일 단위 격리**: 한 파일 실패로 전체 중단 금지.
- 예외는 `error.log`에 상세 기록(스택트레이스 포함 가능).
- 사용자 로그에는 **요약된 한글 메시지**만 출력(과도한 스택 출력 금지).

---

## 4. 기능 규칙(요구사항 고정)
### 4.1 지원 확장자
- 이미지: `.jpg`, `.jpeg`, `.png`, `.heic`, `.cr3`, `.dng`, `.gif`
- 동영상: `.mp4`, `.mov`
- 결과 확장자는 **소문자 통일**.

### 4.2 파일명 패턴
- IMG 패턴(대소문자 무시):
  - `IMG_<식별번호>`
  - 식별번호: `숫자 + 영문 0~10글자`
  - 권장 정규식: `^(?i)IMG_(?P<id>\d+[a-z]{0,10})$`
- PASS 패턴(확장자 제외 본문):
  - `YYYY-MM-DD_HH-MM-SS_<식별번호>_<카메라>`
  - 권장 정규식:
    - `^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[^_]+_[A-Za-z0-9]+$`

### 4.3 촬영일 태그 우선순위(확정)
- 이미지: `DateTimeOriginal > CreateDate > MediaCreateDate`
- 동영상: `MediaCreateDate > CreateDate > TrackCreateDate`
- 시간대: offset 유무와 상관없이 **원문 그대로** 사용(변환 없음).

### 4.4 카메라 정규화(확정)
- 출력 토큰: `EOSR7`, `EOS200D2`, `iPhone`, `UNKNOWN`
- EOS 200D II 표기 다양성은 모두 `EOS200D2`로 매핑.
- `UNKNOWN`은 변환 결과에 사용 가능하며 **UNKNOWN 자체 로그는 남기지 않음**.

### 4.5 변환/복사 정책(확정)
- 저장(복사) 대상:
  1) **촬영일 있음 + IMG 패턴** → 표준 파일명으로 저장
  2) **PASS 패턴** → 이름 유지하여 저장(단, 날짜 폴더는 메타데이터 촬영일로 결정)
- 스킵 대상(저장하지 않음 + 로그):
  - 촬영일 없음
  - IMG 패턴 아님
  - 그 외 조건 미충족

### 4.6 결과 경로(확정)
- `[SourceRoot]/result/YYYY-MM-DD/<결과 파일>`
- 원본 폴더 구조는 유지하지 않는다(날짜 폴더 내 평탄화).

### 4.7 충돌 및 재실행 정책(확정)
- 충돌 처리(동일 실행 내):
  - 동일 결과명 존재 시 식별번호 뒤에 숫자를 **언더바 없이** 증가
  - 예: `..._9672_EOSR7` → `..._96721_EOSR7` → `..._96722_EOSR7`
- 재실행(멱등성):
  - 최종 결과 경로에 파일이 이미 있으면 **스킵**
- 결정성:
  - 파일 수집 목록은 항상 **정렬**하여 동일 규칙/동일 결과를 보장한다.

---

## 5. 아키텍처 가이드(권장)
### 5.1 핵심 데이터 모델(예시)
- `FileRecord`: 입력 파일의 경로/확장자/원본명
- `MetaRecord`: 촬영일(문자열), 카메라 토큰, 원본 태그값(선택)
- `Plan`: 입력 1개 파일의 액션
  - `action`: `COPY_PASS | COPY_RENAME | SKIP`
  - `dst_dir`, `dst_name`, `reason`, `collision_resolved_name`
- `Stats`: 요약 카운터(성공/스킵/충돌/에러 등)

### 5.2 처리 흐름(단일 책임)
1) `scanner`가 대상 파일 목록 생성 및 정렬
2) `exiftool`이 메타데이터를 **배치**로 추출(JSON)
3) `metadata`가 촬영일/카메라를 정규화
4) `planner`가 `Plan` 생성(정책/규칙 반영)
5) `collision`이 동일 실행 내 충돌명 계산
6) `copier`가 멱등성 체크 후 복사 실행
7) `summary`가 카운터 집계
8) `logger`가 한글 사용자 로그/파일 로그 기록

- UI는 위 코어 로직을 **블랙박스**로 호출하고, 이벤트만 수신한다.

---

## 6. ExifTool 연동 규칙(성능/안정)
### 6.1 필수 원칙
- “파일 1개당 exiftool 프로세스 1회 실행” 금지(성능 급락).
- 최소 1개 이상 적용(권장: 배치 + 태그 최소화):
  1) **배치 추출(chunk 200~1000)**
  2) **stay_open(지속 프로세스)** (추가 최적화 옵션)
  3) **태그 최소화**

### 6.2 권장 ExifTool 호출 형태(배치 JSON)
- JSON 출력 사용: `-json`
- 필요한 태그만 조회(예시):
  - 촬영일 후보: `DateTimeOriginal`, `CreateDate`, `MediaCreateDate`, `TrackCreateDate`
  - 카메라: `Make`, `Model`
  - 파일명/경로 매핑을 위해 `SourceFile` 포함
- Windows 경로/인코딩에 주의:
  - `subprocess.run(..., text=True, encoding="utf-8", errors="replace")` 권장
  - 경로에 공백/한글 포함 가능하므로 리스트 인자 방식 사용(쉘 사용 금지)

### 6.3 오류 처리
- ExifTool 호출 실패:
  - 해당 배치 전체를 실패로 처리하지 말고, 가능한 경우 “개별 파일 재시도(소량)” 전략을 마련(옵션).
  - 재시도도 실패하면 해당 파일은 `error.log`에 기록 후 스킵 처리(정책 일관).

---

## 7. 파일 I/O 규칙(안전/결정성)
- 복사는 `shutil.copy2` 사용(타임스탬프 보존).
- 결과 폴더 생성은 `exist_ok=True`.
- 멱등성 체크는 “최종 결과 경로” 기준으로 수행한다.
- 동일 실행 내 충돌 해결은 **날짜 폴더 내**에서만 판단한다.
- 확장자는 `lower()`로 통일한다(파일명 본문은 규칙대로).

---

## 8. UI/스레딩 규칙
- 백그라운드 워커 스레드에서 처리.
- UI 스레드는 Queue에서 이벤트를 주기적으로 poll(`after`)하여 반영.
- UI 업데이트는 너무 빈번하지 않게(예: 100~250ms 단위) 제한.
- 중단/취소 버튼을 추가할 경우:
  - `threading.Event`로 graceful stop 구현(중간 파일 단위에서 종료).

---

## 9. 로깅 규칙
### 9.1 사용자 로그(한글)
- 핵심 이벤트만 간결하게:
  - 스킵: `촬영일 없음`, `IMG 패턴 아님`, `이미 존재하여 스킵`, `PASS 복사`, `변환 성공`, `충돌 해결`
- 파일 로그는 `[SourceRoot]/result/run.log`에 저장.

### 9.2 error.log
- `[SourceRoot]/result/error.log`
- 최소: 시간(ISO), 원본 전체경로, 예외 메시지, stacktrace(가능하면).

---

## 10. 테스트 규칙
- 단위 테스트(필수):
  - 패턴 판별(IMG/PASS)
  - 충돌 해결(증가 규칙)
  - 플래너(정책에 따른 action 결정)
- 통합 테스트(권장):
  - 작은 fixture 폴더에 대해 end-to-end 실행(메타데이터는 mock 또는 샘플 파일 사용)
- 결정성 테스트(권장):
  - 입력 순서가 달라도 정렬 후 동일 결과 계획이 생성되는지 확인

---

## 11. PyInstaller 패키징 규칙
- `.spec` 파일은 `build/`에 보관하고, 커밋에 포함한다.
- ExifTool은 `tools/exiftool/exiftool.exe`를 dist에 포함해야 한다.
- 런타임에서 exiftool 경로 탐색:
  - 개발 환경: repo 상대경로
  - 패키징 환경: `sys._MEIPASS` 기반 경로
- 결과/로그는 항상 `[SourceRoot]/result/`에 생성(프로그램 설치 경로 금지).

---

## 12. 버전/커밋 가이드(권장)
- 브랜치: `main` + 기능 브랜치(`feat/...`)
- 커밋 메시지 예:
  - `feat(ui): add folder picker and progress bar`
  - `feat(exif): implement batch json extraction`
  - `fix(collision): apply numeric suffix without underscore`
  - `chore(build): add pyinstaller spec and bundle exiftool`

