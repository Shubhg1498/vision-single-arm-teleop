# Gazebo Simulation Migration Plan

Replace the **fake pick-and-place** (`demo_manipulation_object_node`) with **real physics** using Gazebo Harmonic + gz_ros2_control.

Install Gazebo first: [gazebo_install.md](gazebo_install.md)

---

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| A | Install Gazebo | Done |
| B | Panda in pick-place world | Done |
| C | MoveIt Servo + webcam teleop → Gazebo | Done |
| D | Physics grasp tuning (friction, lift cube) | Next |

---

## Run the demo (final command)

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
source source_ws.bash
export VDAT_REPO=~/vision_dual_arm_teleop
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

**Important:** use `source_ws.bash` so both `vdat_gazebo` and `vdat_teleop` are on `AMENT_PREFIX_PATH`.

---

## Architecture (Gazebo)

```
webcam → HandToTwistMapper → webcam_teleop_node
              ↓
     servo_twist_relay_node → MoveIt Servo
              ↓
     gz_ros2_control (GazeboSimSystem) → Gazebo Harmonic
         - Franka Panda
         - Table + cube (real contact / friction / gravity)

pinch → gripper_relay_node → /panda_hand_controller/gripper_cmd
```

**Not used in Gazebo demo:** `demo_manipulation_object_node`, `scene_objects_node`, fake `ros2_control_node`.

---

## Launch files

| Launch file | What it does |
|-------------|--------------|
| `demo_pick_place.launch.py` | RViz + fake hardware (legacy MVP) |
| `vdat_gazebo/panda_pick_place.launch.py` | Gazebo world + Panda only (no teleop) |
| `demo_pick_place_gazebo.launch.py` | **Full demo** — Gazebo + Servo + teleop + gripper |

---

## Project layout

```
ros2_ws/src/
├── vdat_gazebo/
│   ├── urdf/panda_gazebo.urdf.xacro
│   ├── config/panda_gazebo_controllers.yaml
│   ├── worlds/pick_place.sdf
│   └── launch/panda_pick_place.launch.py
└── vdat_teleop/
    └── launch/demo_pick_place_gazebo.launch.py

ros2_ws/source_ws.bash          # workspace setup (use this)
```

---

## Phase D — Real pick-and-place (next)

1. Tune gripper finger + cube friction in Gazebo SDF
2. Verify lift after pinch (cube moves with arm, not teleport attach)
3. Optional: remove legacy fake-grasp nodes from RViz demo docs

---

## References

- [gazebo_install.md](gazebo_install.md)
- [simulation_choice.md](simulation_choice.md)
- [gz_ros2_control demos](https://github.com/ros-controls/gz_ros2_control/tree/jazzy/gz_ros2_control_demos)
