# Demo videos

Place project demo recordings here (e.g. `teleop_pick_place_demo.mp4`).

Large video files are gitignored (`*.mp4`, `*.avi`); keep a copy locally or upload to your portfolio / YouTube / GitHub Releases.

## What the demo shows

1. Hand tracking with pinch gesture detection (webcam or external USB camera)
2. Real-time mapping of hand motion to Panda end-effector velocity in Gazebo
3. Scene camera views (overview, side, gripper, table top) during teleoperation
4. Physics-based pick-and-place: grasp, transport latch, lift, move, release

## Recording tips

- Use **Window Capture** in OBS for Gazebo + teleop windows (avoid full-display capture on Wayland)
- External camera on a tripod improves teleop ergonomics vs the laptop webcam
- Launch with `use_rviz:=false` for a cleaner layout
