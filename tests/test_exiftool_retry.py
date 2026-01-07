import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import json
from msr.core.exiftool import extract_metadata_batch, ExifToolError

@pytest.fixture
def mock_exiftool_path():
    """ExifTool 실행 파일 경로 탐지를 모킹합니다."""
    with patch("msr.core.exiftool.get_exiftool_path") as mock:
        mock.return_value = Path("exiftool.exe")
        yield mock

def test_extract_metadata_batch_retry_success(mock_exiftool_path):
    """
    전체 배치 호출은 실패하지만, 분할 재시도 시 성공하는 케이스를 테스트합니다.
    """
    files = [Path("photo1.jpg"), Path("photo2.jpg")]
    
    # 첫 번째 호출(2개)은 에러 발생, 이후 분할된 호출(각 1개)은 성공하도록 설정
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd"),  # 전체 배치 실패
            MagicMock(stdout=json.dumps([{"SourceFile": "photo1.jpg", "DateTimeOriginal": "2023:01:01 12:00:00"}])), # 첫 번째 조각 성공
            MagicMock(stdout=json.dumps([{"SourceFile": "photo2.jpg", "DateTimeOriginal": "2023:01:02 12:00:00"}])), # 두 번째 조각 성공
        ]

        results = extract_metadata_batch(files)

        # 결과 확인
        assert len(results) == 2
        assert results[Path("photo1.jpg")].datetime_original == "2023:01:01 12:00:00"
        assert results[Path("photo2.jpg")].datetime_original == "2023:01:02 12:00:00"
        
        # 총 3번의 subprocess 호출이 있어야 함 (1회 실패 + 2회 분할 성공)
        assert mock_run.call_count == 3

def test_extract_metadata_batch_partial_retry_success(mock_exiftool_path):
    """
    분할 재시도 중 일부는 성공하고 일부는 끝까지 실패하는 케이스를 테스트합니다.
    """
    files = [Path("good.jpg"), Path("bad.jpg")]

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd"),  # 전체 배치 실패
            MagicMock(stdout=json.dumps([{"SourceFile": "good.jpg", "DateTimeOriginal": "2023:01:01 12:00:00"}])), # good.jpg 성공
            subprocess.CalledProcessError(1, "cmd"),  # bad.jpg는 단일 파일임에도 실패 (재시도 중단)
        ]

        results = extract_metadata_batch(files)

        # 성공한 파일만 결과에 포함되어야 함
        assert len(results) == 1
        assert Path("good.jpg") in results
        assert Path("bad.jpg") not in results

def test_extract_metadata_batch_retry_on_json_error(mock_exiftool_path):
    """
    JSON 파싱 에러 발생 시에도 재시도 로직이 작동하는지 테스트합니다.
    """
    files = [Path("f1.jpg"), Path("f2.jpg")]

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(stdout="invalid json output"), # JSON 에러 발생
            MagicMock(stdout=json.dumps([{"SourceFile": "f1.jpg"}])), # 재시도 성공
            MagicMock(stdout=json.dumps([{"SourceFile": "f2.jpg"}])), # 재시도 성공
        ]

        results = extract_metadata_batch(files)
        assert len(results) == 2
        assert mock_run.call_count == 3

def test_extract_metadata_batch_max_retries_exceeded(mock_exiftool_path):
    """
    최대 재시도 횟수를 초과할 때까지 계속 실패하는 경우를 테스트합니다.
    """
    # 2개의 파일이므로 1번 분할 가능. 
    # MAX_RETRIES가 2이므로 깊이 2까지 내려감.
    files = [Path("fail1.jpg"), Path("fail2.jpg")]

    with patch("subprocess.run") as mock_run:
        # 모든 호출이 실패하도록 설정
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        results = extract_metadata_batch(files)
        
        # 모든 경로에서 실패했으므로 결과는 비어있어야 함
        assert results == {}

def test_extract_metadata_batch_single_file_failure_no_retry(mock_exiftool_path):
    """
    파일이 1개뿐일 때는 분할할 수 없으므로 즉시 에러를 발생시켜야 합니다.
    """
    files = [Path("single_fail.jpg")]

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

        with pytest.raises(ExifToolError, match="ExifTool batch command failed"):
            extract_metadata_batch(files)

def test_extract_metadata_batch_file_not_found_retry(mock_exiftool_path):
    """
    FileNotFoundError(실행 파일 미존재 등) 발생 시에도 재시도 로직이 작동하는지 확인합니다.
    """
    files = [Path("f1.jpg"), Path("f2.jpg")]
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [FileNotFoundError(), MagicMock(stdout="[]"), MagicMock(stdout="[]")]
        results = extract_metadata_batch(files)
        assert results == {}
