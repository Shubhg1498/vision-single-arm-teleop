from dataclasses import dataclass
import math


@dataclass
class GestureState:
    pinch_distance: float
    is_pinching: bool
    hand_open_score: float


class GestureDetector:
    """Simple gesture detector for MediaPipe hand landmarks.

    Uses normalized landmark coordinates. Pinch distance is computed between
    thumb tip and index finger tip.
    """

    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    WRIST = 0

    def __init__(self, pinch_threshold: float = 0.055):
        self.pinch_threshold = pinch_threshold

    @staticmethod
    def _dist(a, b) -> float:
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (getattr(a, "z", 0.0) - getattr(b, "z", 0.0)) ** 2)

    def detect(self, landmarks) -> GestureState:
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        wrist = landmarks[self.WRIST]

        pinch_distance = self._dist(thumb_tip, index_tip)
        is_pinching = pinch_distance < self.pinch_threshold

        fingertips = [
            landmarks[self.INDEX_TIP],
            landmarks[self.MIDDLE_TIP],
            landmarks[self.RING_TIP],
            landmarks[self.PINKY_TIP],
        ]
        avg_fingertip_distance = sum(self._dist(wrist, tip) for tip in fingertips) / len(fingertips)

        return GestureState(
            pinch_distance=pinch_distance,
            is_pinching=is_pinching,
            hand_open_score=avg_fingertip_distance,
        )
