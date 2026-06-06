# Vision-Based Single-Arm Teleoperation for Robotic Manipulation

Webcam hand tracking drives a simulated Franka Panda through ROS 2, MoveIt Servo, and Gazebo Harmonic. The pipeline maps human hand motion and gestures to end-effector velocity commands, with optional demonstration recording for imitation learning.

**Stack:** Ubuntu 24.04 · ROS 2 Jazzy · MoveIt 2 · Gazebo Harmonic · MediaPipe · OpenCV

A **demo video** of the full pipeline (hand tracking → Gazebo teleop → pick-and-place) is in [`videos/`](videos/).

---

## What was achieved

This project delivers an end-to-end **vision-based teleoperation** system for a single Franka Panda arm in simulation:

1. **Real-time hand tracking** — MediaPipe detects hand landmarks and pinch/open gestures from a webcam or external USB camera.
2. **Command mapping** — Wrist position maps to end-effector XY velocity; keyboard W/S controls depth; a relay node smooths and rate-limits commands before MoveIt Servo.
3. **MoveIt Servo integration** — Jacobian velocity control with collision checking and singularity handling.
4. **Gazebo physics simulation** — Panda arm and gripper via `gz_ros2_control`; pick-place world with table, dynamic cube, and tuned friction.
5. **Real grasp workflow** — Pinch closes the gripper via `GripperCommand`; transport latch (C) holds the object while repositioning; physics-based lift and place (no fake attach).
6. **Scene monitoring** — Four fixed Gazebo cameras (overview, side, gripper, table top) displayed in a 2×2 viewer while teleoperating.
7. **Flexible camera setup** — Built-in or external USB camera (e.g. Logitech C270) selectable via launch arguments.

The RViz **fake-hardware** path remains available for quick iteration without Gazebo.

### Honest assessment

Single-camera teleoperation is a **solid first step**, but **operationally difficult**:

- Hand motion controls XY in the image plane, while depth is on the keyboard — there is no true 3D hand pose from one camera.
- The operator must split attention between the hand-tracking window, scene cameras, and Gazebo.
- Physics grasping is sensitive to approach angle, speed, and friction tuning.

The demo proves the architecture works; making teleop practical would need richer sensing and UX improvements (see [Future scope](#future-scope)).

---

## Architecture

```
Webcam (built-in or USB)
  → MediaPipe HandTracker + GestureDetector
  → HandToTwistMapper (normalized velocity + deadband + smoothing)
  → webcam_teleop_node          [/teleop/right_arm/twist_cmd, /teleop/right_gripper/close]
  → servo_twist_relay_node      [rate limiting, acceleration cap, deadman timeout]
  → MoveIt Servo                [collision checking, singularity handling]
  → ros2_control / gz_ros2_control
  → Gazebo Harmonic             [Panda + table + cube, real physics]

Parallel: scene cameras → ros_gz_image → scene_camera_viewer_node (2×2 workspace views)
          pinch → gripper_relay_node → GripperCommand action → simulated gripper
```

Two simulation backends share the same teleop nodes:

| Launch file | Backend | Physics |
|-------------|---------|---------|
| `demo_pick_place.launch.py` | MoveIt fake hardware + RViz | Collision attach (fake grasp) |
| `demo_pick_place_gazebo.launch.py` | Gazebo + gz_ros2_control | Real contact, friction, gravity |

---

## What is implemented

### Vision and command mapping (`vision_dual_arm_teleop/`)

- **Hand tracking** — MediaPipe Hands, 21 landmarks per hand, left/right classification
- **Gesture detection** — pinch vs open via thumb–index distance threshold
- **Hand-to-twist mapping** — wrist position → normalized `(vy, vz)` velocity; deadband; low-pass filter
- **Demo recorder** — CSV logging of observations and commands for IL/RL datasets

### ROS 2 teleop nodes (`vdat_teleop`)

| Node | Role |
|------|------|
| `webcam_teleop_node` | Camera capture, hand tracking, twist + gripper publishing, keyboard depth (W/S) |
| `servo_twist_relay_node` | Scales, smooths, and rate-limits commands before MoveIt Servo |
| `gripper_relay_node` | Maps pinch to `GripperCommand` action for Gazebo gripper controller |
| `scene_camera_viewer_node` | Multi-view OpenCV display of Gazebo scene cameras |
| `demo_manipulation_object_node` | RViz-only fake grasp via planning scene attach (legacy) |

### Gazebo simulation (`vdat_gazebo`)

- Panda URDF with **gz_ros2_control** — arm + gripper on one controller manager inside Gazebo
- Pick-place world: table, dynamic cube, tuned finger/cube friction
- Four fixed **scene cameras** bridged to ROS via `ros_gz_image`

### Utilities (`scripts/`)

| Script | Purpose |
|--------|---------|
| `run_hand_tracking.py` | Standalone hand tracking test |
| `list_cameras.py` | Probe `/dev/video*` and find working cameras |
| `install_gazebo.sh` | One-time Gazebo + ROS 2 install |

---

## Key learnings

**MoveIt Servo as the control layer.** End-effector teleoperation maps naturally to `TwistStamped` inputs. Servo handles Jacobian control, collision checking, and singularity slowdown.

**Fake hardware vs real physics.** RViz uses planning-scene attach for fake grasp — fast to iterate, no contact physics. Gazebo needs a single `ros2_control` instance via `gz_ros2_control`.

**Gripper controller interface matters.** The Panda hand uses `GripperActionController`, not joint trajectories. `GripperCommand` action is required.

**Teleop UX for sim.** Pinch freezes arm motion for safe frame entry. Transport latch (C) decouples gripper from hand state during transport. Depth (W/S) disabled during pinch.

**One camera is not enough for easy 3D teleop.** Monocular hand tracking gives 2D wrist position; depth is a separate input. Scene cameras help monitoring but do not close the control loop.

**External USB camera improves ergonomics.** A tripod-mounted camera (e.g. Logitech C270) lets the operator teleoperate without leaning into the laptop webcam.

**Isaac Sim was not viable on this hardware.** Gazebo Harmonic integrates natively with ROS 2 Jazzy via apt.

**Workspace sourcing.** Use `source_ws.bash` after colcon build — `install/setup.bash` alone may not register `vdat_teleop`.

---

## Future scope

| Area | Direction |
|------|-----------|
| **Depth sensing** | Stereo camera, depth camera (RealSense), or hand landmark Z estimation for true 3D teleop |
| **Dual-arm** | Architecture already has left/right topic names; extend to two Panda arms |
| **Demonstration dataset** | Record synchronized robot state, scene camera images, and commands for imitation learning |
| **Grasp reliability** | Physics tuning, grasp planning, or compliant gripper control in Gazebo |
| **Teleop UX** | Gamepad/SpaceMouse for depth, haptic feedback, or shared-autonomy (human + planner) |
| **Real robot** | Same ROS pipeline on Franka ROS 2 with safety limits validated in sim first |
| **Vision for manipulation** | Object detection / pose estimation to assist approach (cube localization) |

---

## Quick start

### 1. Python environment (hand tracking only)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/run_hand_tracking.py
```

### 2. Full Gazebo teleop demo

```bash
# One-time
bash scripts/install_gazebo.sh

# Every session
cd ros2_ws
source /opt/ros/jazzy/setup.bash
source ../.venv/bin/activate
colcon build --packages-select vdat_gazebo vdat_teleop
source source_ws.bash
export VDAT_REPO=$(pwd)/..
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

Wait ~17 s for startup. Press **Play** in Gazebo.

**External USB camera** (recommended for comfortable teleop):

```bash
python scripts/list_cameras.py   # find index, e.g. /dev/video4

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py camera_device:=/dev/video4
```

**Controls**

| Input | Action |
|-------|--------|
| Open hand | Move arm (XY from wrist) |
| Pinch | Freeze arm + close gripper |
| W / S | Depth forward / back (when not pinching) |
| C | Toggle transport latch (hold object while moving) |

**Windows:** ROS2 Webcam Teleop (hand control) + Scene Cameras (2×2 monitor)

Optional: `show_scene_cameras:=false` · `use_rviz:=false` · `flip_horizontal:=false`

### 3. RViz-only demo (fake hardware)

```bash
cd ros2_ws && source /opt/ros/jazzy/setup.bash && source source_ws.bash
source ../.venv/bin/activate
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place.launch.py
```

---

## Repository layout

```text
vision_dual_arm_teleop/
├── vision_dual_arm_teleop/     # Python: tracking, mapping, recording
├── ros2_ws/
│   ├── source_ws.bash          # workspace setup (use after colcon build)
│   └── src/
│       ├── vdat_teleop/        # ROS 2 teleop nodes + launch files
│       └── vdat_gazebo/        # Gazebo world, Panda URDF, controllers
├── docs/                       # Install guides, architecture, simulation notes
├── scripts/                    # install, hand tracking, list_cameras
├── videos/                     # Demo recordings
└── gazebo/                     # World assets (reference copy)
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/gazebo_install.md](docs/gazebo_install.md) | Gazebo + ROS 2 install and troubleshooting |
| [docs/gazebo_simulation.md](docs/gazebo_simulation.md) | Architecture, scene cameras, pick-and-place workflow |
| [docs/simulation_choice.md](docs/simulation_choice.md) | RViz vs Gazebo decision record |
| [docs/version_1.md](docs/version_1.md) | Detailed project guide (math, nodes, Q&A) |

---

## Hardware tested

- Lenovo ThinkPad P1 Gen 8, Ubuntu 24.04, ROS 2 Jazzy
- NVIDIA RTX PRO 2000 (Blackwell), driver 595
- Built-in webcam + Logitech Webcam C270 (USB)

---

## License

MIT
