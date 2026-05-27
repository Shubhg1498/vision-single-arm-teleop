import argparse
import cv2

from vision_dual_arm_teleop.tracking.hand_tracker import HandTracker
from vision_dual_arm_teleop.mapping.hand_to_twist import HandToTwistMapper
from vision_dual_arm_teleop.recording.demo_recorder import DemoRecorder


def draw_command_overlay(frame, cmd=None, gripper_close=False):
    h, w, _ = frame.shape

    center = (w // 2, h // 2)
    box_size = 140

    # Draw control deadband box
    top_left = (center[0] - box_size // 2, center[1] - box_size // 2)
    bottom_right = (center[0] + box_size // 2, center[1] + box_size // 2)
    cv2.rectangle(frame, top_left, bottom_right, (180, 180, 180), 2)

    # Draw center point
    cv2.circle(frame, center, 5, (255, 255, 255), -1)

    if cmd is not None:
        # vy maps to horizontal arrow, vz maps to vertical arrow
        arrow_scale = 350
        end_x = int(center[0] + cmd.vy * arrow_scale)
        end_y = int(center[1] - cmd.vz * arrow_scale)

        cv2.arrowedLine(
            frame,
            center,
            (end_x, end_y),
            (0, 255, 0),
            4,
            tipLength=0.25,
        )

        cv2.putText(
            frame,
            f"cmd vx={cmd.vx:+.2f} vy={cmd.vy:+.2f} vz={cmd.vz:+.2f}",
            (10, h - 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

    gripper_text = "GRIPPER: CLOSE" if gripper_close else "GRIPPER: OPEN"
    gripper_color = (0, 0, 255) if gripper_close else (0, 255, 0)

    cv2.putText(
        frame,
        gripper_text,
        (10, h - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        gripper_color,
        2,
    )

    return frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--output", type=str, default="data/demos/webcam_demo.csv")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.camera}")

    tracker = HandTracker()
    mapper = HandToTwistMapper()
    recorder = DemoRecorder(args.output) if args.record else None

    print("Running hand tracking. Press 'q' to quit.")
    print("Move your right hand around. Pinch thumb-index finger to close gripper.")

    last_cmd = None
    last_gripper_close = False

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        observations, results = tracker.process(frame)

        if "Right" in observations:
            obs = observations["Right"]
            cmd = mapper.map(obs.wrist_xy, obs.gesture.is_pinching)

            last_cmd = cmd
            last_gripper_close = cmd.gripper_close

            print(
                f"Right cmd: vx={cmd.vx:+.3f}, vy={cmd.vy:+.3f}, vz={cmd.vz:+.3f}, "
                f"gripper_close={cmd.gripper_close}",
                end="\r",
            )

            if recorder:
                recorder.write("Right", obs, cmd)
        else:
            # Safety behavior: if hand disappears, stop command
            last_cmd = None
            last_gripper_close = False

        frame = tracker.draw(frame, results, observations)
        frame = draw_command_overlay(frame, last_cmd, last_gripper_close)

        cv2.imshow("Vision Dual-Arm Teleop - Hand Tracking MVP", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    if recorder:
        recorder.close()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()