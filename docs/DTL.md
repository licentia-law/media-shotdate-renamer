# DTL — Development Task List
> Repository: **media-shotdate-renamer**  
> Version: v1.0 (2026-01-07)  
> 기준 문서: `PRD.md` / `CRG.md`

---

## 0. 완료 정의(Definition of Done)
- PRD의 AC-01 ~ AC-08을 만족한다.
- GUI가 프리징 없이 동작한다(워커 + Queue).
- ExifTool 성능 최적화(배치/태그 최소화)가 적용되어 수천 장 처리 시 체감 지연이 과도하지 않다.
- `.spec` 기반 PyInstaller 빌드가 가능하고, exiftool.exe가 번들에 포함된다.
- run.log/error.log/요약 통계가 요구대로 출력된다.

---

## 1. 마일스톤 개요
- **M0** 프로젝트 부트스트랩
- **M1** 코어 로직(패턴/플래너/충돌/복사/요약)
- **M2** ExifTool 배치 추출(성능 핵심)
- **M3** GUI 통합(워커/진행률/로그/완료)
- **M4** 패키징(PyInstaller .spec) + 실행 검증
- **M5** 테스트/QA + 문서화

---

## 2. 작업 항목

## M0. 프로젝트 부트스트랩
### M0-01 저장소 초기화
- [ ] GitHub repo 생성: `media-shotdate-renamer`
- [ ] 기본 브랜치 `main`
- [ ] `.gitignore`(Python, PyInstaller, dist/build, venv 등)
- [ ] `README.md` 생성(목적/사용법/주의사항/지원 확장자)

### M0-02 개발 환경/의존성
- [ ] Python 버전 고정(권장 3.11+)
- [ ] `pyproject.toml`(권장) 또는 `requirements.txt`
- [ ] 로컬 실행 방법 문서화(`python -m ...`)

---

## M1. 코어 로직(ExifTool 없이도 단위 검증 가능하게)
### M1-01 확장자/스캔(Scanner)
- [ ] 재귀 탐색 구현
- [ ] `result/` 하위 제외
- [ ] 대상 확장자 필터
- [ ] 파일 목록 정렬(전체 경로 오름차순)
- [ ] 단위 테스트: 스캔 결과 수/정렬/제외 규칙

### M1-02 패턴 판별(Patterns)
- [ ] IMG 정규식 구현(숫자+영문 0~10)
- [ ] PASS 정규식 구현(확장자 제외 본문)
- [ ] 단위 테스트: 정상/엣지 케이스(대소문자, 길이 제한, 언더바 포함 등)

### M1-03 메타데이터 모델/정규화(Metadata)
- [ ] `MetaRecord` 모델 정의(촬영일 str, 카메라 token, 원본 태그값 optional)
- [ ] 카메라 매핑 규칙 구현(EOSR7/EOS200D2/iPhone/UNKNOWN)
- [ ] UNKNOWN 로그 제외 정책은 플래너/로거에서 처리(메타데이터 모듈은 값만 산출)
- [ ] 단위 테스트: 다양한 Make/Model 조합 매핑

### M1-04 플래너(Planner)
- [ ] 입력: FileRecord + MetaRecord + 패턴 결과
- [ ] 출력: Plan(action, dst_dir, dst_name, reason)
- [ ] 정책 반영:
  - PASS → COPY_PASS(날짜 폴더는 촬영일 기반)
  - 촬영일 없음 → SKIP(reason="촬영일 없음")
  - IMG 아님 → SKIP(reason="IMG 패턴 아님")
  - 촬영일+IMG → COPY_RENAME(표준 파일명 생성)
- [ ] 확장자 소문자 통일 적용
- [ ] 단위 테스트: 각 분기(4가지) 검증

### M1-05 충돌 해결(Collision)
- [ ] 날짜 폴더 내에서 동일 파일명 충돌 탐지
- [ ] 식별번호 뒤 숫자 증가(언더바 없음) 구현
- [ ] 단위 테스트: 1회/다회 충돌 케이스

### M1-06 복사/멱등성(Copier)
- [ ] `copy2` 기반 복사
- [ ] “최종 결과 경로 존재 시 스킵” 구현
- [ ] 복사 결과 이벤트 반환(성공/스킵/에러)
- [ ] 단위 테스트(가능한 범위): 임시 디렉터리로 검증

### M1-07 요약 집계(Summary)
- [ ] 카운터 정의(총/변환/패스/스킵-촬영일없음/스킵-IMG아님/충돌/이미존재스킵/에러)
- [ ] 종료 시 요약 문자열 생성

---

## M2. ExifTool 배치 추출(성능 핵심)
### M2-01 ExifTool 번들 경로 탐지
- [ ] 개발 모드: `tools/exiftool/exiftool.exe`
- [ ] 패키징 모드: `sys._MEIPASS` 기반 경로
- [ ] 경로가 없으면 UI에서 즉시 오류 표시(작업 시작 차단)

### M2-02 배치 JSON 추출 구현(필수)
- [ ] chunk 크기(기본 500) 상수/설정화
- [ ] `-json` + 태그 최소화 호출
- [ ] SourceFile 기반으로 결과를 파일 경로에 매핑
- [ ] 촬영일 태그 우선순위 적용:
  - 이미지: DTO > CreateDate > MediaCreateDate
  - 동영상: MediaCreateDate > CreateDate > TrackCreateDate
- [ ] offset 원문 그대로 유지(파싱 시 변환 금지)

### M2-03 ExifTool 오류/재시도(권장)
- [ ] 배치 호출 실패 시:
  - [ ] chunk를 반으로 쪼개 재시도(최대 N회) 또는 파일 단위 폴백(선택)
  - [ ] 최종 실패 파일은 error.log 기록 + 스킵 처리(정책 일관)

### M2-04 성능 계측(권장)
- [ ] 전체 처리 시간/초당 처리량을 요약에 포함(옵션)
- [ ] chunk 크기 튜닝 가이드(README에 기록)

---

## M3. GUI 통합(tkinter)
### M3-01 메인 윈도우
- [ ] 소스 폴더 선택(디렉터리 선택 다이얼로그)
- [ ] 변환 시작 버튼
- [ ] 진행률 바 + % + (처리/총)
- [ ] 로그 텍스트 박스(스크롤)
- [ ] 완료 팝업 + 결과 폴더 열기 버튼

### M3-02 워커/Queue 기반 실행
- [ ] 워커 스레드에서 코어 파이프라인 실행
- [ ] Queue로 UI 이벤트 전달(로그 라인/진행률/완료/에러)
- [ ] UI는 `after()`로 주기적 poll
- [ ] UI 갱신 빈도 제한(예: 100~250ms)

### M3-03 로그 정책(한글)
- [ ] 사용자 로그 메시지 템플릿 정의(한글 고정)
- [ ] run.log에 동일 내용 저장
- [ ] UNKNOWN은 로그로 남기지 않음(단, 변환 결과 파일명에는 UNKNOWN 포함 가능)

---

## M4. PyInstaller 패키징(.spec 포함)
### M4-01 .spec 생성/고정(필수)
- [ ] `build/media-shotdate-renamer.spec` 생성
- [ ] exiftool.exe를 datas/binaries로 포함
- [ ] onefile vs onedir 선택(권장: 초기 onedir)
- [ ] 실행 파일 아이콘/버전 정보(선택)

### M4-02 패키징 런타임 검증
- [ ] dist 실행 시 ExifTool 경로 탐지 정상
- [ ] 폴더 선택 → 변환 → result 생성/로그 생성 정상
- [ ] 한글 로그 출력 깨짐(인코딩) 여부 점검

---

## M5. 테스트/QA/문서
### M5-01 테스트 보강
- [ ] patterns/collision/planner 단위 테스트 완료
- [ ] 통합 테스트(작은 fixture 폴더) 1개 이상
- [ ] 결정성 테스트(입력 순서 변화에도 결과 동일) (권장)

### M5-02 수동 QA 체크리스트
- [ ] PASS 파일: 촬영일 기반 날짜 폴더에 저장됨
- [ ] 촬영일 없음: 스킵 + 로그, 결과 미생성
- [ ] IMG 아님: 스킵 + 로그, 결과 미생성
- [ ] 충돌: suffix 증가 규칙 정상
- [ ] 재실행: 결과 존재 시 스킵
- [ ] 확장자 소문자 통일
- [ ] GUI 프리징 없음(수천 개 샘플에서 체감 확인)
- [ ] error.log 기록 및 전체 중단 방지

### M5-03 문서화
- [ ] README: 사용 방법(설치/실행/결과 경로/로그 파일)
- [ ] 성능 옵션(chunk 크기) 설명
- [ ] 제한사항/주의사항(원본 비파괴, 시간대 변환 없음 등)

---

## 3. 산출물 체크리스트
- [ ] `PRD.md`(완료)
- [ ] `CRG.md`(완료)
- [ ] `DTL.md`(본 문서)
- [ ] `.spec` 파일(`build/`)
- [ ] dist 실행 파일(배포 패키지)
- [ ] run.log / error.log / 요약 통계 출력

