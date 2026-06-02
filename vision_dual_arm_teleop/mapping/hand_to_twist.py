from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class TeleopCommand:
    vx: float
    vy: float
    vz: float
    gripper_close: bool


class LowPassFilter:
    def __init__(self, alpha: float = 0.25):
        self.alpha = alpha
        self.prev: Optional[Tuple[float, float]] = None

    def update(self, xy: Tuple[float, float]) -> Tuple[float, float]:
        if self.prev is None:
            self.prev = xy
            return xy

        x = self.alpha * xy[0] + (1.0 - self.alpha) * self.prev[0]
        y = self.alpha * xy[1] + (1.0 - self.alpha) * self.prev[1]
        self.prev = (x, y)
        return self.prev


class HandToTwistMapper:
    """Maps normalized hand position to a simple end-effector velocity command.

    Camera frame:
    - image x right
    - image y down

    Robot command convention (base_link / panda_link0):
    - hand right/left -> robot right/left (+y is robot-left, so lateral sign is negated)
    - hand up/down -> robot +/- z
    - depth is initially 0.0 until we add hand-size depth proxy
    """

    def __init__(self, deadband: float = 0.06, max_speed: float = 0.20):
        self.deadband = deadband
        self.max_speed = max_speed
        self.filter = LowPassFilter(alpha=0.25)

    def _apply_deadband(self, value: float) -> float:
        if abs(value) < self.deadband:
            return 0.0
        return value

    def map(self, wrist_xy: Tuple[float, float], gripper_close: bool) -> TeleopCommand:
        x, y = self.filter.update(wrist_xy)

        # Center image at (0.5, 0.5)
        dx = self._apply_deadband(x - 0.5)
        dy = self._apply_deadband(0.5 - y)

        vy = max(-self.max_speed, min(self.max_speed, -dx * self.max_speed * 2.0))
        vz = max(-self.max_speed, min(self.max_speed, dy * self.max_speed * 2.0))

        return TeleopCommand(
            vx=0.0,
            vy=vy,
            vz=vz,
            gripper_close=gripper_close,
        )
