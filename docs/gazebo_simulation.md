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
| — | Scene cameras for teleop monitoring | Done |

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

scene cameras → ros_gz_image → scene_camera_viewer_node (3-view monitor)
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

## Scene cameras (teleop views)

Three fixed cameras in `pick_place.sdf` give workspace views while you teleoperate:

| Camera | ROS topic | Purpose |
|--------|-----------|---------|
| Overview | `/scene_camera_overview` | Robot + table |
| Side | `/scene_camera_side` | Side approach angle |
| Gripper | `/scene_camera_gripper` | Close-up on pick area |

They are bridged with `ros_gz_image` and displayed in the **Scene Cameras (Teleop)** OpenCV window (starts ~8 s after launch).

Single-camera view:

```bash
ros2 run rqt_image_view rqt_image_view /scene_camera_overview
```

Disable the viewer: `show_scene_cameras:=false`

---

## Phase D — Pick-and-place demo workflow

Yes — with the current Gazebo setup you can pick the cube and place it elsewhere using **real physics** (no fake attach).

### Controls

| Input | Action |
|-------|--------|
| **Pinch** | Freeze arm (safe entry into frame) + close gripper |
| **Open hand** | Move arm (XY from wrist) |
| **W / S** | Move forward / back (depth) — only when **not** pinching |
| **C** | Toggle **transport latch** — gripper stays closed while you move |

### Demo sequence

1. **Pinch** before entering the frame → arm frozen, safe entry.
2. **Open hand** → move above the blue cube (use W/S to adjust depth).
3. **Pinch** at the cube → gripper closes, arm freezes.
4. Press **C** to latch the gripper closed.
5. **Release pinch**, press **W** to lift the cube.
6. **Open hand** → move to the drop location (gripper stays latched).
7. Press **C** again to open and release the cube.

If the cube slips, approach slower and ensure the pinch is centered on the block.

---

## References

- [gazebo_install.md](gazebo_install.md)
- [simulation_choice.md](simulation_choice.md)
- [gz_ros2_control demos](https://github.com/ros-controls/gz_ros2_control/tree/jazzy/gz_ros2_control_demos)
