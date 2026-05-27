from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp

from .gesture_detector import GestureDetector, GestureState


@dataclass
class HandObservation:
    handedness: str
    wrist_xy: Tuple[float, float]
    index_tip_xy: Tuple[float, float]
    gesture: GestureState
    landmarks: object


class HandTracker:
    """Webcam hand tracker based on MediaPipe Hands.

    Output coordinates are normalized image coordinates in [0, 1].
    """

    def __init__(
        self,
        max_num_hands: int = 2,
        detection_confidence: float = 0.65,
        tracking_confidence: float = 0.65,
    ):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.gesture_detector = GestureDetector()

    def process(self, frame_bgr) -> Tuple[Dict[str, HandObservation], object]:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        observations: Dict[str, HandObservation] = {}

        if not results.multi_hand_landmarks:
            return observations, results

        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label  # "Left" or "Right"
            lm = hand_landmarks.landmark
            gesture = self.gesture_detector.detect(lm)

            observations[label] = HandObservation(
                handedness=label,
                wrist_xy=(lm[0].x, lm[0].y),
                index_tip_xy=(lm[8].x, lm[8].y),
                gesture=gesture,
                landmarks=hand_landmarks,
            )

        return observations, results

    def draw(self, frame_bgr, results, observations: Dict[str, HandObservation]):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame_bgr,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        y = 30
        for label, obs in observations.items():
            text = (
                f"{label}: wrist=({obs.wrist_xy[0]:.2f},{obs.wrist_xy[1]:.2f}) "
                f"pinch={obs.gesture.is_pinching} "
                f"d={obs.gesture.pinch_distance:.3f}"
            )
            cv2.putText(frame_bgr, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y += 30

        return frame_bgr
