from pathlib import Path
import csv
import time


class DemoRecorder:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.output_path.open("w", newline="")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=[
                "time",
                "handedness",
                "wrist_x",
                "wrist_y",
                "pinch_distance",
                "is_pinching",
                "cmd_vx",
                "cmd_vy",
                "cmd_vz",
                "gripper_close",
            ],
        )
        self.writer.writeheader()

    def write(self, handedness, obs, cmd):
        self.writer.writerow(
            {
                "time": time.time(),
                "handedness": handedness,
                "wrist_x": obs.wrist_xy[0],
                "wrist_y": obs.wrist_xy[1],
                "pinch_distance": obs.gesture.pinch_distance,
                "is_pinching": int(obs.gesture.is_pinching),
                "cmd_vx": cmd.vx,
                "cmd_vy": cmd.vy,
                "cmd_vz": cmd.vz,
                "gripper_close": int(cmd.gripper_close),
            }
        )

    def close(self):
        self.file.close()
