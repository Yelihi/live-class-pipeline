#!/usr/bin/env python3
# T-16: MediaPipe FaceLandmarker 기본 동작 확인
# 사전 조건: pip install mediapipe opencv-python
# 실행: python3 media/gstreamer/python/mediapipe_test.py [image.jpg]
#        python3 media/gstreamer/python/mediapipe_test.py  (인수 없으면 테스트 프레임 자동 생성)
import subprocess
import sys
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "media" / "models" / "face_landmarker.task"
DEFAULT_TEST_IMAGE = PROJECT_ROOT / "media" / "gstreamer" / "test_frame.jpg"


def capture_test_frame(output_path: Path) -> None:
    """GStreamer로 videotestsrc 첫 프레임을 JPEG로 저장 (얼굴 없는 가짜 영상)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "gst-launch-1.0", "-q",
            "videotestsrc", "num-buffers=1", "!",
            "videoconvert", "!", "jpegenc", "!",
            "filesink", f"location={output_path}",
        ],
        check=True,
    )
    print(f"==> 테스트 프레임 저장: {output_path}")


def run_detection(image_path: Path) -> None:
    if not MODEL_PATH.exists():
        print(f"오류: 모델 파일 없음 → {MODEL_PATH}")
        print("  wget -O media/models/face_landmarker.task \\")
        print("    https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task")
        sys.exit(1)

    base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        print(f"오류: 이미지를 읽을 수 없음 → {image_path}")
        sys.exit(1)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    result = detector.detect(mp_image)
    detector.close()

    h, w = img_bgr.shape[:2]
    print(f"==> 이미지 크기: {w}×{h}")
    print(f"==> 모델: {MODEL_PATH.name}")

    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
        print(f"==> 감지된 랜드마크 수: {len(landmarks)}")

        # 눈 관련 주요 랜드마크
        pts = {
            "왼쪽 눈 위  (#159)": landmarks[159],
            "왼쪽 눈 아래(#145)": landmarks[145],
            "오른쪽 눈 위 (#386)": landmarks[386],
            "오른쪽 눈 아래(#374)": landmarks[374],
            "코 끝       (#001)": landmarks[1],
        }
        for label, lm in pts.items():
            print(f"   {label}: x={lm.x:.4f}, y={lm.y:.4f}, z={lm.z:.4f}")

        left_ear_raw = abs(landmarks[159].y - landmarks[145].y)
        right_ear_raw = abs(landmarks[386].y - landmarks[374].y)
        print(f"==> 눈 수직 개방 (EAR 미리보기): L={left_ear_raw:.4f}  R={right_ear_raw:.4f}")
    else:
        print("==> 얼굴 미감지 (videotestsrc 가짜 영상이면 정상)")
        print("   실제 얼굴 사진 경로를 인수로 전달하세요:")
        print(f"   python3 {Path(__file__).name} /path/to/face.jpg")


def main() -> None:
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
    else:
        image_path = DEFAULT_TEST_IMAGE
        if not image_path.exists():
            capture_test_frame(image_path)

    run_detection(image_path)


if __name__ == "__main__":
    main()
