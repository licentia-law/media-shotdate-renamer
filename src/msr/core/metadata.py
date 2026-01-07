"""
This module defines the metadata model and normalization logic.
- DTL M1-03: 메타데이터 모델/정규화(Metadata)
- CRG 4.3: 촬영일 태그 우선순위
- CRG 4.4: 카메라 정규화
""" 
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class MetaRecord:
    """
    Represents normalized metadata extracted from a media file.
    """
    datetime_original: Optional[str] = None  # 촬영일 (ExifTool 원본 문자열, offset 포함 가능)
    camera_make: Optional[str] = None       # 카메라 제조사 (정규화 전)
    camera_model: Optional[str] = None      # 카메라 모델 (정규화 전)
    normalized_camera: str = "UNKNOWN"      # 정규화된 카메라 토큰 (CRG 4.4)
    # TODO: M2-02 - 원본 태그값 (optional) 필드 추가 고려

def normalize_camera_model(make: Optional[str], model: Optional[str]) -> str:
    """
    Normalizes camera make and model into a standardized token.
    CRG 4.4: 카메라 정규화 규칙 적용.
    - 출력 토큰: `EOSR7`, `EOS200D2`, `iPhone`, `UNKNOWN`
    - EOS 200D II 표기 다양성은 모두 `EOS200D2`로 매핑.
    """
    if not make and not model:
        return "UNKNOWN"

    make_lower = make.lower() if make else ""
    model_lower = model.lower() if model else ""

    # Canon EOS R7
    if "canon" in make_lower and "eos r7" in model_lower:
        return "EOSR7"
    # Canon EOS 200D II (various spellings)
    if "canon" in make_lower and ("eos 200d ii" in model_lower or "eos 200d2" in model_lower or "eos kiss x10i" in model_lower):
        return "EOS200D2"
    # iPhone
    if "apple" in make_lower and "iphone" in model_lower:
        return "iPhone"
    
    return "UNKNOWN"


# CRG 4.3: 촬영일 태그 우선순위
DATETIME_TAG_PRIORITY_IMAGE = ["DateTimeOriginal", "CreateDate", "MediaCreateDate"]
DATETIME_TAG_PRIORITY_VIDEO = ["MediaCreateDate", "CreateDate", "TrackCreateDate"]

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".cr3", ".dng", ".gif"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov"}

def extract_and_normalize_metadata(src_path: Path, exif_data: dict) -> MetaRecord:
    """
    Extracts relevant metadata from raw ExifTool output for a single file
    and normalizes it into a MetaRecord.
    
    CRG 4.3: 촬영일 태그 우선순위 적용.
    CRG 4.4: 카메라 정규화 적용.
    
    Args:
        src_path: The original Path object of the file.
        exif_data: A dictionary containing raw metadata extracted by ExifTool for the file.
        
    Returns:
        A MetaRecord object containing the normalized metadata.
    """
    datetime_original: Optional[str] = None
    
    # CRG 4.3: 촬영일 태그 우선순위 적용
    if src_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
        priority_list = DATETIME_TAG_PRIORITY_IMAGE
    elif src_path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
        priority_list = DATETIME_TAG_PRIORITY_VIDEO
    else:
        priority_list = [] # Should not happen with proper filtering, but for safety

    for tag in priority_list:
        if tag in exif_data:
            datetime_original = exif_data[tag]
            break

    make = exif_data.get('Make')
    model = exif_data.get('Model')
    
    normalized_camera = normalize_camera_model(make, model)
    
    return MetaRecord(
        datetime_original=datetime_original,
        camera_make=make,
        camera_model=model,
        normalized_camera=normalized_camera
    )
