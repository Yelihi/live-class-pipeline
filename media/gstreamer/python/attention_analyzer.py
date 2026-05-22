#!/usr/bin/env python3
# T-18: Eye Aspect Ratio(EAR) 계산 + attention score 산출
# 의존성: mediapipe (pip 설치 가능)
# 단독 실행: python3 media/gstreamer/python/attention_analyzer.py [face_image.jpg]
import math
import sys
from dataclasses import dataclass
from pathlib import Path

# 왼쪽 눈 랜드마크 번호 (p1..p6 순서)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
# 오른쪽 눈 랜드마크 번호
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
NOSE_TIP = 1


@dataclass
class AttentionResult:
    face_detected: bool
    left_ear: float
    right_ear: float
    avg_ear: float
    is_facing_front: bool
    attention_score: float  # 0.0 ~ 1.0


def _dist(a, b) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _ear(landmarks, eye_indices: list[int]) -> float:
    """Eye Aspect Ratio = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)"""
    p = [landmarks[i] for i in eye_indices]
    vertical = _dist(p[1], p[5]) + _dist(p[2], p[4])
    horizontal = 2.0 * _dist(p[0], p[3])
    if horizontal < 1e-6:
        return 0.0
    return vertical / horizontal


def analyze(face_landmarks) -> AttentionResult:
    if not face_landmarks:
        return AttentionResult(
            face_detected=False,
            left_ear=0.0,
            right_ear=0.0,
            avg_ear=0.0,
            is_facing_front=False,
            attention_score=0.0,
        )

    lm = face_landmarks[0]
    left_ear = _ear(lm, LEFT_EYE)
    right_ear = _ear(lm, RIGHT_EYE)
    avg_ear = (left_ear + right_ear) / 2.0

    is_facing_front = abs(lm[NOSE_TIP].x - 0.5) < 0.15

    eye_score = min(avg_ear / 0.25, 1.0)       # EAR 0.25 이상이면 만점
    face_score = 1.0 if is_facing_front else 0.4
    score = round(eye_score * face_score, 3)

    return AttentionResult(
        face_detected=True,
        left_ear=round(left_ear, 4),
        right_ear=round(right_ear, 4),
        avg_ear=round(avg_ear, 4),
        is_facing_front=is_facing_front,
        attention_score=score,
    )


# ── 단독 실행 시 smoke test ───────────────────────────────────────────────
def _smoke_test(image_path: str) -> None:
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    project_root = Path(__file__).parent.parent.parent.parent
    model_path = project_root / "media" / "models" / "face_landmarker.task"

    base_options = python.BaseOptions(model_asset_path=str(model_path))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
    )
    detector = vision.FaceLandmarker.create_from_options(options)

    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    result = detector.detect(mp_image)
    detector.close()

    att = analyze(result.face_landmarks)
    print(f"face_detected   : {att.face_detected}")
    print(f"left_ear        : {att.left_ear}")
    print(f"right_ear       : {att.right_ear}")
    print(f"avg_ear         : {att.avg_ear}  (눈 뜨면 > 0.20)")
    print(f"is_facing_front : {att.is_facing_front}")
    print(f"attention_score : {att.attention_score}  (0.0 ~ 1.0)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"사용: python3 {Path(__file__).name} <face_image.jpg>")
        sys.exit(1)
    _smoke_test(sys.argv[1])
