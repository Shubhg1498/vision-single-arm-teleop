#!/usr/bin/env python3
"""Probe /dev/video* devices and show which ones produce frames."""

import glob
import platform
import sys

import cv2


def probe(source):
    backend = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_ANY
    cap = cv2.VideoCapture(source, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return None

    ok, frame = cap.read()
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    if not ok or frame is None:
        return None

    return width, height, fps


def main():
    devices = sorted(glob.glob("/dev/video*"))
    if not devices:
        print("No /dev/video* devices found.")
        return 1

    print("Scanning cameras (this opens each device briefly)...\n")
    working = []

    for path in devices:
        result = probe(path)
        if result is None:
            print(f"  {path}: no frame (metadata node or busy)")
            continue

        width, height, fps = result
        index = path.replace("/dev/video", "")
        print(f"  {path}  index={index}  {width}x{height}  {fps:.1f} fps")
        working.append((path, index, width, height))

    if not working:
        print("\nNo working capture devices found.")
        print("Check USB connection and that no other app is using the camera.")
        return 1

    print("\nUse one of these with teleop:")
    print("  python scripts/run_hand_tracking.py --camera INDEX")
    print("  ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py camera_index:=INDEX")
    print("  ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py camera_device:=/dev/videoN")

    if len(working) >= 2:
        ext = working[-1]
        print(
            f"\nTip: external USB cameras are often the highest index "
            f"(try index={ext[1]} or camera_device:={ext[0]})."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
