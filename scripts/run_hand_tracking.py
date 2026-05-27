import argparse
import cv2

from vision_dual_arm_teleop.tracking.hand_tracker import HandTracker
from vision_dual_arm_teleop.mapping.hand_to_twist import HandToTwistMapper
from vision_dual_arm_teleop.recording.demo_recorder import DemoRecorder


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
    print("Tip: move your right hand around and pinch thumb-index finger to close gripper.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        observations, results = tracker.process(frame)

        if "Right" in observations:
            obs = observations["Right"]
            cmd = mapper.map(obs.wrist_xy, obs.gesture.is_pinching)
            print(
                f"Right cmd: vx={cmd.vx:+.3f}, vy={cmd.vy:+.3f}, vz={cmd.vz:+.3f}, "
                f"gripper_close={cmd.gripper_close}",
                end="\r",
            )

            if recorder:
                recorder.write("Right", obs, cmd)

        frame = tracker.draw(frame, results, observations)
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
