import math
from dataclasses import dataclass

LEFT_EYE = [33, 160, 158, 133, 153, 144]
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
    eye_score = min(avg_ear / 0.25, 1.0)
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
