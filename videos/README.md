# Demo videos

Place project demo recordings here (e.g. `teleop_pick_place_demo.mp4`).

Large video files are gitignored (`*.mp4`, `*.avi`); keep a copy locally or upload to your portfolio / YouTube / GitHub Releases.

## Trim before upload

Your OBS recording is likely an `.mkv` in your home folder. Inspect it:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
  "$HOME/2026-06-06 15-51-56.mkv"
# → ~196 s (3 min 16 s) at 1080p60
```

**Option A — project script** (exports trimmed MP4 for upload):

```bash
cd ~/vision_dual_arm_teleop
bash scripts/trim_video.sh "$HOME/2026-06-06 15-51-56.mkv" 0:45 2:30
# keeps 0:45 → 2:30, writes videos/teleop_demo_trimmed.mp4

# custom output path:
bash scripts/trim_video.sh "$HOME/2026-06-06 15-51-56.mkv" 1:00 2:50 videos/demo.mp4
```

**Option B — ffmpeg directly** (fast cut, no re-encode — MKV only):

```bash
ffmpeg -ss 0:45 -to 2:30 -i "$HOME/2026-06-06 15-51-56.mkv" -c copy videos/demo_trim.mkv
```

**Option C — GUI** (scrub timeline visually):

```bash
sudo apt install losslesscut   # or: flatpak install flathub com.github.mifi.LosslessCut
losslesscut &
```

Open the `.mkv`, drag start/end handles, export as MP4.

### Picking start/end times

1. Open the full recording in VLC or LosslessCut.
2. Note **start** (first frame you want — e.g. when Gazebo is running and hand appears).
3. Note **end** (after pick-and-place completes — skip long startup/shutdown).
4. Leave ~2–3 s padding at start/end for a clean cut.

## What the demo shows

1. Hand tracking with pinch gesture detection (webcam or external USB camera)
2. Real-time mapping of hand motion to Panda end-effector velocity in Gazebo
3. Scene camera views (overview, side, gripper, table top) during teleoperation
4. Physics-based pick-and-place: grasp, transport latch, lift, move, release

## Recording tips

- Use **Window Capture** in OBS for Gazebo + teleop windows (avoid full-display capture on Wayland)
- External camera on a tripod improves teleop ergonomics vs the laptop webcam
- Launch with `use_rviz:=false` for a cleaner layout
