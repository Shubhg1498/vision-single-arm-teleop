# Vision-Based Dual-Arm Teleoperation for Robotic Manipulation

Webcam hand tracking drives a simulated Franka Panda through ROS 2, MoveIt Servo, and Gazebo Harmonic. The pipeline maps human hand motion and gestures to end-effector velocity commands, with optional demonstration recording for imitation learning.

**Stack:** Ubuntu 24.04 · ROS 2 Jazzy · MoveIt 2 · Gazebo Harmonic · MediaPipe · OpenCV

---

## Architecture

```
Webcam
  → MediaPipe HandTracker + GestureDetector
  → HandToTwistMapper (normalized velocity + deadband + smoothing)
  → webcam_teleop_node          [/teleop/right_arm/twist_cmd, /teleop/right_gripper/close]
  → servo_twist_relay_node      [rate limiting, acceleration cap, deadman timeout]
  → MoveIt Servo                [collision checking, singularity handling]
  → ros2_control / gz_ros2_control
  → Gazebo Harmonic             [Panda + table + cube, real physics]

Parallel: scene cameras → ros_gz_image → scene_camera_viewer_node (workspace views)
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
- **Hand-to-twist mapping** — wrist position → normalized `(vy, vz)` velocity; deadband around image center; low-pass filter to reduce jitter
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

- Panda URDF with **gz_ros2_control** (`GazeboSimSystem`) — arm + gripper on one controller manager inside Gazebo
- Pick-place world: table, dynamic cube, tuned finger/cube friction
- Three fixed **scene cameras** (overview, side, gripper) bridged to ROS via `ros_gz_image`

---

## Key learnings

**MoveIt Servo as the control layer.** End-effector teleoperation maps naturally to `TwistStamped` inputs. Servo handles Jacobian-based velocity control, self-collision checking, and singularity slowdown — the vision layer only needs to publish clean velocity commands.

**Fake hardware vs real physics.** The RViz demo uses `mock_components/GenericSystem` and attaches objects in the planning scene on proximity — fast to iterate, but no contact physics. Gazebo requires a single `ros2_control` instance via `gz_ros2_control`; running a separate `ros2_control_node` alongside Gazebo causes conflicts.

**Gripper controller interface matters.** The Panda hand uses `position_controllers/GripperActionController`, not joint trajectories. Publishing `JointTrajectory` to the gripper silently fails; the fix was a `GripperCommand` action client in `gripper_relay_node`.

**Teleop UX for sim.** Pinch freezes hand-driven motion so the operator can enter the camera frame without moving the arm. A keyboard **transport latch (C)** decouples gripper state from hand open/close so the cube can be carried while repositioning. Depth (W/S) is disabled during pinch to avoid accidental motion.

**Isaac Sim was not viable on this hardware.** Blackwell GPU + driver 595 caused segfaults in Isaac Sim 5.1. Gazebo Harmonic integrates natively with ROS 2 Jazzy via apt packages and runs on modest GPU requirements.

**Workspace sourcing.** `ament_python` packages in an isolated colcon layout need `source_ws.bash` — `install/setup.bash` alone does not always register `vdat_teleop` on `AMENT_PREFIX_PATH`.

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

**Controls**

| Input | Action |
|-------|--------|
| Open hand | Move arm (XY from wrist) |
| Pinch | Freeze arm + close gripper |
| W / S | Depth forward / back (when not pinching) |
| C | Toggle transport latch (hold object while moving) |

**Windows:** ROS2 Webcam Teleop (hand control) + Scene Cameras (3-view monitor)

Optional: `show_scene_cameras:=false` · `use_rviz:=false`

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
├── scripts/                    # install_gazebo.sh, run_hand_tracking.py
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

- Ubuntu 24.04, ROS 2 Jazzy
- NVIDIA RTX PRO 2000 (Blackwell), driver 595
- Built-in / USB webcam for hand tracking

---

## License

MIT
