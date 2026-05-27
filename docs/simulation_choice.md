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

Reason:
- It is widely used in MoveIt tutorials.
- Existing MoveIt configs are easier to use.
- Good for showing gripper control and pick/place.

### Phase 2: Dual Panda or Dual UR5e
For dual-arm control, use either:
1. Dual Panda setup for easier manipulation demo.
2. Dual UR5e setup for a more industrial-looking demo.

Recommendation:
- Start with Panda.
- Move to dual Panda once single-arm teleoperation is stable.
- Consider UR5e later if you want a stronger industrial robotics portfolio angle.

## Why not Isaac Sim first?

Isaac Sim is powerful, especially for photorealistic robotics simulation, but it adds setup complexity.
For a one-week demo, MoveIt + RViz is faster and more reliable.
Isaac Sim can be a future extension.
