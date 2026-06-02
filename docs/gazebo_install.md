# Gazebo Harmonic Installation Guide

This project uses **Gazebo Harmonic** (Gazebo Sim 8) with **ROS 2 Jazzy** and **gz_ros2_control** for real physics simulation.

Works on your machine without Isaac Sim's driver/GPU constraints. Your existing teleop stack stays unchanged.

---

## Prerequisites

You already have:
- Ubuntu 24.04
- ROS 2 Jazzy (`/opt/ros/jazzy`)
- MoveIt Servo + Panda (fake hardware demo working)
- Python venv with `colcon` (`.venv` in repo root)

---

## Step 1 — Install Gazebo + ROS 2 integration

Run the project install script:

```bash
cd ~/vision_dual_arm_teleop
bash scripts/install_gazebo.sh
```

Or install manually:

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-gz-ros2-control-demos \
  ros-jazzy-ros-gz-sim-demos
```

---

## Step 2 — Verify installation

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch ros_gz_sim_demos diff_drive.launch.py
```

---

## Step 3 — Build workspace packages

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
colcon build --packages-select vdat_gazebo vdat_teleop
```

Always source the workspace with **`source_ws.bash`** (not `install/setup.bash` alone — that misses `vdat_teleop` on `AMENT_PREFIX_PATH`):

```bash
source ~/vision_dual_arm_teleop/ros2_ws/source_ws.bash
```

Verify both packages are visible:

```bash
ros2 pkg prefix vdat_gazebo vdat_teleop
```

---

## Step 4 — Run the full Gazebo teleop demo (Phase C)

Single terminal — Gazebo + MoveIt Servo + webcam teleop + gripper:

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
source source_ws.bash
export VDAT_REPO=~/vision_dual_arm_teleop
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

Wait ~17 seconds for all nodes to start. Press **Play** in Gazebo if the sim is paused.

**Webcam controls:** hand position → arm XY, W/S → forward/back, pinch → close gripper, release → open.

Optional: `use_rviz:=false` if you only want the Gazebo GUI.

---

## Architecture

```
webcam → webcam_teleop_node → servo_twist_relay_node → MoveIt Servo
                                                      ↓
                              gz_ros2_control → Gazebo (Panda + table + cube)
pinch → gripper_relay_node → panda_hand_controller (GripperCommand action)
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Package 'vdat_teleop' not found` | Use `source source_ws.bash`, not `install/setup.bash` alone |
| `colcon: command not found` | `source ~/vision_dual_arm_teleop/.venv/bin/activate` |
| `Could not get lock /var/lib/dpkg/lock-frontend` | Another `apt` is running — wait or `Ctrl+C` and retry |
| Gazebo window is black | Try `export LIBGL_ALWAYS_SOFTWARE=1` (slow) |
| Arm doesn't move | Press Play in Gazebo; wait for Servo (~12 s) |
| Pinch doesn't move gripper | Check `ros2 action list \| grep gripper`; rebuild after gripper fix |
| Gripper closes but cube doesn't lift | Phase D — tune friction in SDF (physics grasp) |

Manual gripper test (with demo running):

```bash
ros2 action send_goal /panda_hand_controller/gripper_cmd control_msgs/action/GripperCommand \
  "{command: {position: 0.0, max_effort: 20.0}}"
```

Open:

```bash
ros2 action send_goal /panda_hand_controller/gripper_cmd control_msgs/action/GripperCommand \
  "{command: {position: 0.04, max_effort: 20.0}}"
```

---

## References

- [gazebo_simulation.md](gazebo_simulation.md) — migration plan
- [simulation_choice.md](simulation_choice.md) — project decisions
- [gz_ros2_control](https://github.com/ros-controls/gz_ros2_control)
