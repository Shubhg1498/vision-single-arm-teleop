# Gazebo Simulation

Real physics pick-and-place for the vision teleop project.

Install Gazebo first: [gazebo_install.md](gazebo_install.md)

---

## Project status

| Phase | Description | Status |
|-------|-------------|--------|
| A | Install Gazebo | Done |
| B | Panda in pick-place world | Done |
| C | MoveIt Servo + webcam teleop → Gazebo | Done |
| D | Physics grasp tuning (friction, reliable lift) | Partial |
| — | Scene cameras (4 views + 2×2 viewer) | Done |
| — | External USB camera support | Done |
| — | End-to-end demo video | Done |

**Primary demo:** `demo_pick_place_gazebo.launch.py` — Gazebo + Servo + teleop + gripper + scene cameras.

---

## Run the demo

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
source source_ws.bash
export VDAT_REPO=~/vision_dual_arm_teleop
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

**External camera** (recommended):

```bash
python ~/vision_dual_arm_teleop/scripts/list_cameras.py
ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py camera_device:=/dev/video4
```

Use **`source_ws.bash`** so both `vdat_gazebo` and `vdat_teleop` are on `AMENT_PREFIX_PATH`.

Wait ~17 s, press **Play** in Gazebo.

---

## Architecture (Gazebo)

```
webcam (built-in or USB) → HandToTwistMapper → webcam_teleop_node
              ↓
     servo_twist_relay_node → MoveIt Servo
              ↓
     gz_ros2_control (GazeboSimSystem) → Gazebo Harmonic
         - Franka Panda
         - Table + cube (real contact / friction / gravity)

pinch → gripper_relay_node → /panda_hand_controller/gripper_cmd

scene cameras → ros_gz_image → scene_camera_viewer_node (2×2 grid)
```

**Not used in Gazebo demo:** `demo_manipulation_object_node`, `scene_objects_node`, fake `ros2_control_node`.

---

## Launch files

| Launch file | What it does |
|-------------|--------------|
| `demo_pick_place.launch.py` | RViz + fake hardware (legacy) |
| `vdat_gazebo/panda_pick_place.launch.py` | Gazebo world + Panda only (no teleop) |
| `demo_pick_place_gazebo.launch.py` | **Full demo** — Gazebo + Servo + teleop + gripper |

Launch arguments for teleop camera:

| Argument | Default | Example |
|----------|---------|---------|
| `camera_index` | `0` | `camera_index:=4` |
| `camera_device` | `""` | `camera_device:=/dev/video4` |
| `flip_horizontal` | `true` | `flip_horizontal:=false` |

---

## Scene cameras (teleop views)

Four fixed cameras in `pick_place.sdf`:

| Camera | ROS topic | Purpose |
|--------|-----------|---------|
| Overview | `/scene_camera_overview` | Robot + table |
| Side | `/scene_camera_side` | Side approach angle |
| Gripper | `/scene_camera_gripper` | Close-up on pick area |
| Table Top | `/scene_camera_table_top` | Top-down view of cube on table |

Bridged with `ros_gz_image`, displayed in **Scene Cameras (Teleop)** as a 2×2 grid (~8 s after launch).

```bash
ros2 run rqt_image_view rqt_image_view /scene_camera_table_top
```

Disable viewer: `show_scene_cameras:=false`

---

## Pick-and-place workflow

Real physics — no fake attach.

### Controls

| Input | Action |
|-------|--------|
| **Pinch** | Freeze arm (safe entry) + close gripper |
| **Open hand** | Move arm (XY from wrist) |
| **W / S** | Depth forward/back — only when **not** pinching |
| **C** | Toggle **transport latch** — gripper stays closed while moving |

### Demo sequence

1. **Pinch** before entering frame → arm frozen.
2. **Open hand** → move above cube (W/S for depth).
3. **Pinch** at cube → gripper closes.
4. Press **C** to latch gripper closed.
5. **Release pinch**, **W** to lift.
6. **Open hand** → move to drop zone (gripper latched).
7. Press **C** to release.

---

## Limitations and next steps

- **Monocular teleop is hard** — XY from hand, depth from keyboard; scene cameras aid monitoring but not closed-loop control.
- **Grasp reliability** — cube can slip; friction tuned in SDF but not fully robust.
- **Next:** depth camera or stereo, richer demo recording, dual-arm, real robot port.

See README [Future scope](../README.md#future-scope).

---

## References

- [gazebo_install.md](gazebo_install.md)
- [simulation_choice.md](simulation_choice.md)
- [gz_ros2_control demos](https://github.com/ros-controls/gz_ros2_control/tree/jazzy/gz_ros2_control_demos)
