# Simulation and Robot Choice

## MVP Simulation Choice

Use ROS2 + MoveIt 2 + MoveIt Servo + RViz first.

Reason:
- The first demo needs real-time end-effector teleoperation, not photorealistic simulation.
- MoveIt Servo accepts end-effector velocity commands, desired poses, or joint velocity commands.
- It also provides safety features such as collision checking and singularity handling.
- RViz is enough for the first video milestone.

## Robot Choice

### Phase 1: Franka Emika Panda
Use Panda for the first working single-arm demo.

### Phase 2: Dual Panda or Dual UR5e
For dual-arm control, use either dual Panda or dual UR5e.

---

## Phase 3: Real Physics (Gazebo Harmonic) — DONE (teleop)

The MVP used MoveIt + RViz with **fake grasp** (`demo_manipulation_object_node`).

**Gazebo Harmonic + gz_ros2_control** is now the primary simulation backend for teleop.

See:
- [gazebo_install.md](gazebo_install.md) — install + **final run command**
- [gazebo_simulation.md](gazebo_simulation.md) — architecture + roadmap

### Final command (Gazebo teleop)

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

### Phase 4 (next)

Physics grasp tuning — cube lift/slip after pinch (friction in SDF, not fake attach).
