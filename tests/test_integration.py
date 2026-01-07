import pytest
import json
from pathlib import Path
from queue import Queue
from unittest.mock import patch, MagicMock

from msr.core.file_processor import FileProcessor
from msr.core.metadata import MetaRecord
from msr.core.planner import Action

@pytest.fixture
def integration_setup(tmp_path):
    """
    통합 테스트를 위한 소스 폴더와 샘플 파일들을 생성합니다.
    """
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    
    # 1. 정상 변환 대상 (IMG 패턴 + 촬영일)
    file_valid = src_dir / "IMG_1234.jpg"
    file_valid.write_text("valid_content")
    
    # 2. 충돌 발생 대상 (다른 폴더에 동일한 IMG 번호)
    sub_dir = src_dir / "sub"
    sub_dir.mkdir()
    file_collision = sub_dir / "IMG_1234.jpg"
    file_collision.write_text("collision_content")
    
    # 3. PASS 패턴 대상 (이미 표준화됨)
    file_pass = src_dir / "2023-01-01_12-00-00_5678_EOSR7.jpg"
    file_pass.write_text("pass_content")
    
    # 4. 스킵 대상 (촬영일 없음)
    file_no_meta = src_dir / "IMG_9999.jpg"
    file_no_meta.write_text("no_meta_content")
    
    # 5. 스킵 대상 (IMG 패턴 아님)
    file_not_img = src_dir / "random_photo.jpg"
    file_not_img.write_text("not_img_content")
    
    # 6. 지원하지 않는 확장자 (스캔에서 제외되어야 함)
    file_unsupported = src_dir / "document.txt"
    file_unsupported.write_text("unsupported_content")
    
    return src_dir, {
        "valid": file_valid,
        "collision": file_collision,
        "pass": file_pass,
        "no_meta": file_no_meta,
        "not_img": file_not_img
    }

def test_full_pipeline_integration(integration_setup):
    """
    전체 파이프라인(스캔 -> 추출 -> 계획 -> 복사 -> 요약) 통합 테스트
    """
    src_dir, files = integration_setup
    event_queue = Queue()
    processor = FileProcessor(str(src_dir), event_queue)
    
    # ExifTool 배치 추출 결과 모킹
    # FileProcessor 내부에서 사용하는 Path 객체와 일치해야 함
    mock_metadata = {
        files["valid"]: MetaRecord(datetime_original="2023:01:01 10:00:00", normalized_camera="EOSR7"),
        files["collision"]: MetaRecord(datetime_original="2023:01:01 10:00:00", normalized_camera="EOSR7"),
        files["pass"]: MetaRecord(datetime_original="2023:01:01 12:00:00", normalized_camera="EOSR7"),
        files["no_meta"]: MetaRecord(datetime_original=None),
        files["not_img"]: MetaRecord(datetime_original="2023:01:01 15:00:00")
    }
    
    with patch("msr.core.file_processor.extract_metadata_batch", return_value=mock_metadata):
        # 파이프라인 실행
        processor.process_files()
        
    # 결과 확인을 위해 큐에서 COMPLETE 이벤트 가져오기
    summary = None
    while not event_queue.empty():
        event = event_queue.get()
        if event["type"] == "COMPLETE":
            summary = event["summary"]
            
    assert summary is not None
    
    # 1. 요약 통계 검증
    # 총 파일: jpg 5개 (txt 제외)
    assert summary.total_files == 5
    # 변환 성공: IMG_1234.jpg (2개 - 충돌 포함)
    assert summary.converted_success == 2
    # PASS 복사: 1개
    assert summary.pass_copied == 1
    # 스킵 (촬영일 없음): 1개 (IMG_9999)
    assert summary.skipped_no_datetime == 1
    # 스킵 (IMG 아님): 1개 (random_photo)
    assert summary.skipped_not_img_pattern == 1
    # 충돌 해결: 1개
    assert summary.collisions_resolved == 1
    
    # 2. 파일 시스템 결과 검증
    result_dir = src_dir / "result" / "2023-01-01"
    assert result_dir.exists()
    
    # 표준 변환 파일 존재 확인
    assert (result_dir / "2023-01-01_10-00-00_1234_EOSR7.jpg").exists()
    # 충돌 해결 파일 존재 확인 (언더바 없이 숫자 증가)
    assert (result_dir / "2023-01-01_10-00-00_12341_EOSR7.jpg").exists()
    # PASS 파일 존재 확인
    assert (result_dir / "2023-01-01_12-00-00_5678_EOSR7.jpg").exists()
    
    # 3. 로그 파일 검증
    assert (src_dir / "result" / "run.log").exists()
    log_content = (src_dir / "result" / "run.log").read_text(encoding="utf-8")
    assert "변환 성공" in log_content or "성공" in log_content
    assert "충돌 해결" in log_content

def test_idempotency_on_re_run(integration_setup):
    """
    재실행 시 이미 존재하는 파일은 스킵되는지(멱등성) 테스트합니다.
    """
    src_dir, files = integration_setup
    event_queue = Queue()
    processor = FileProcessor(str(src_dir), event_queue)
    
    mock_metadata = {
        files["valid"]: MetaRecord(datetime_original="2023:01:01 10:00:00", normalized_camera="EOSR7")
    }
    
    with patch("msr.core.file_processor.extract_metadata_batch", return_value=mock_metadata):
        # 첫 번째 실행
        processor.process_files()
        # 두 번째 실행
        processor.process_files()
        
    # 두 번째 실행 결과에서 '이미 존재하여 스킵' 카운트 확인 (Summary 초기화 로직에 따라 다를 수 있음)
    assert processor.summary.skipped_already_exists > 0