# Simulation and Robot Choice

## Phase 1 — RViz + MoveIt Servo (done)

Used ROS 2 + MoveIt 2 + MoveIt Servo + RViz for the first working teleop loop.

- Real-time end-effector velocity control without photorealistic sim
- MoveIt Servo: collision checking, singularity handling
- RViz sufficient for validating the vision → command pipeline

**Fake grasp:** `demo_manipulation_object_node` attaches objects in the planning scene on proximity.

---

## Phase 2 — Robot choice (done for single-arm)

**Franka Emika Panda** — well-documented MoveIt config, gripper demos, gz_ros2_control support.

Dual Panda or dual UR5e remain options for a future dual-arm extension.

---

## Phase 3 — Gazebo Harmonic (done)

**Gazebo Harmonic + gz_ros2_control** is the primary simulation backend for teleop and the recorded demo.

See:
- [gazebo_install.md](gazebo_install.md)
- [gazebo_simulation.md](gazebo_simulation.md)

### Final command

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
source source_ws.bash
export VDAT_REPO=~/vision_dual_arm_teleop
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

### Launch files

| Launch file | Simulation | Physics |
|-------------|-----------|---------|
| `demo_pick_place.launch.py` | MoveIt fake hardware + RViz | Fake (collision attach) |
| `vdat_gazebo/panda_pick_place.launch.py` | Gazebo + Panda + world | Real (no teleop) |
| `demo_pick_place_gazebo.launch.py` | Gazebo + Servo + teleop + gripper | Real |

---

## Phase 4 — What’s next

| Priority | Item |
|----------|------|
| High | Depth sensing (stereo / RealSense) for easier 3D teleop |
| High | Synchronized demonstration recording (robot state + images + commands) |
| Medium | Physics grasp tuning — reliable cube lift without slip |
| Medium | Dual-arm teleoperation |
| Longer term | Real Franka hardware with validated safety limits |

---

## Why not Isaac Sim?

Isaac Sim 5.1 segfaulted on this hardware (Blackwell GPU, driver 595). Gazebo Harmonic installs via apt on Ubuntu 24.04 + ROS 2 Jazzy and was sufficient for the project goals.
