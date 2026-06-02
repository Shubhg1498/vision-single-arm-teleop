# Gazebo Simulation

Real physics pick-and-place for the vision teleop project.

## Final command (full teleop demo)

```bash
cd ~/vision_dual_arm_teleop/ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
source source_ws.bash
export VDAT_REPO=~/vision_dual_arm_teleop
export PYTHONPATH=$VDAT_REPO:$PYTHONPATH

ros2 launch vdat_teleop demo_pick_place_gazebo.launch.py
```

Use **`source_ws.bash`** — `install/setup.bash` alone does not register `vdat_teleop`.

## Install

```bash
bash scripts/install_gazebo.sh
```

Full guide: [docs/gazebo_install.md](../docs/gazebo_install.md)

## Panda only (no teleop)

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
source ~/vision_dual_arm_teleop/.venv/bin/activate
colcon build --packages-select vdat_gazebo
source source_ws.bash
ros2 launch vdat_gazebo panda_pick_place.launch.py
```

## Architecture

```
webcam teleop → MoveIt Servo → gz_ros2_control → Gazebo Harmonic
pinch → gripper_relay_node → GripperCommand action
```

Migration plan: [docs/gazebo_simulation.md](../docs/gazebo_simulation.md)
