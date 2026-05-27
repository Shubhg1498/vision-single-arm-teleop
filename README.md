# Vision-Based Dual-Arm Teleoperation and Demonstration Collection for Robotic Manipulation

This project uses a webcam or external camera to track human hand motion and gestures, map them to robot arm teleoperation commands, and record demonstrations for future imitation learning or reinforcement learning.

## MVP Goal

Webcam hand tracking → gesture detection → single-arm teleoperation command stream → gripper command → demonstration recording.

## Final Demo Goal

A short video showing:
1. Real-time hand tracking.
2. Pinch gesture detection.
3. Hand motion mapped to robot end-effector commands.
4. Simulated robot arm moving using teleoperation commands.
5. Pick-and-place attempt.
6. Demonstration data recorded to CSV.

## Project Roadmap

### Day 1
- Create repository.
- Implement webcam hand tracking.
- Detect left/right hands.
- Compute pinch/open gesture.
- Save first demo video.

### Day 2
- Convert hand movement into normalized velocity commands.
- Add smoothing, deadband, workspace clipping.
- Create command visualization.

### Day 3
- Create ROS2 teleoperation publisher.
- Publish right/left hand commands and gripper state.

### Day 4
- Connect to single-arm simulation using MoveIt Servo.
- Control end-effector velocity from webcam commands.

### Day 5
- Add gripper control.
- Start demonstration recorder.

### Day 6
- Extend to dual-arm command publishing.
- Record pick-and-place demonstrations.

### Day 7
- Polish README.
- Record final video.
- Add limitations and future work section.

## Quick Start: Webcam Tracking Only

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/run_hand_tracking.py
```

Press `q` to quit.

## Repository Structure

```text
vision_dual_arm_teleop/
├── vision_dual_arm_teleop/
│   ├── tracking/
│   │   ├── hand_tracker.py
│   │   └── gesture_detector.py
│   ├── mapping/
│   │   └── hand_to_twist.py
│   └── recording/
│       └── demo_recorder.py
├── ros2_ws/
│   └── src/
│       └── vdat_teleop/
│           ├── package.xml
│           ├── setup.py
│           └── vdat_teleop/
│               └── webcam_teleop_node.py
├── docs/
├── scripts/
├── videos/
└── data/
```


## Commands

# Webcam
cd /home/shubham.ghogare/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
source /home/shubham.ghogare/vision_dual_arm_teleop/.venv/bin/activate
export PYTHONPATH=/home/shubham.ghogare/vision_dual_arm_teleop:$PYTHONPATH

ros2 run vdat_teleop webcam_teleop_node

# ee_simulator

#cd /home/shubham.ghogare/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run vdat_teleop virtual_ee_simulator_node

