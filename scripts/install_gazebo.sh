#!/usr/bin/env bash
# Install Gazebo Harmonic + ROS 2 Jazzy integration packages.
# Usage: bash scripts/install_gazebo.sh
set -euo pipefail

PACKAGES=(
  ros-jazzy-ros-gz
  ros-jazzy-ros-gz-sim
  ros-jazzy-ros-gz-bridge
  ros-jazzy-gz-ros2-control
  ros-jazzy-gz-ros2-control-demos
  ros-jazzy-ros-gz-sim-demos
)

echo "=== Gazebo Harmonic + ROS 2 Jazzy installer ==="
echo ""

if ! command -v apt-get &>/dev/null; then
  echo "ERROR: apt-get not found. This script is for Ubuntu/Debian."
  exit 1
fi

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "ERROR: ROS 2 Jazzy not found at /opt/ros/jazzy/setup.bash"
  echo "Install ROS 2 Jazzy first: https://docs.ros.org/en/jazzy/Installation.html"
  exit 1
fi

# Fail fast if another apt/dpkg operation is in progress.
if fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/dpkg/lock >/dev/null 2>&1; then
  echo "ERROR: Another apt/dpkg operation is already running."
  echo ""
  ps aux | grep -E '[a]pt|[d]pkg' | head -8 || true
  echo ""
  echo "Wait for it to finish, then re-run:"
  echo "  bash scripts/install_gazebo.sh"
  echo ""
  echo "If it is stuck, check with:  ps aux | grep apt"
  exit 1
fi

echo "Installing packages:"
printf '  - %s\n' "${PACKAGES[@]}"
echo ""

sudo apt update
sudo apt install -y "${PACKAGES[@]}"

echo ""
echo "=== Verifying installation ==="
# shellcheck source=/dev/null
source /opt/ros/jazzy/setup.bash

echo ""
echo "ROS packages:"
ros2 pkg list | grep -E '^(ros_gz_sim|ros_gz_bridge|gz_ros2_control)$' || true

echo ""
echo "Gazebo Sim version:"
if command -v gz &>/dev/null; then
  gz sim --versions 2>&1 | head -3 || gz --versions 2>&1 | head -3
else
  echo "WARNING: 'gz' command not in PATH. Try: source /opt/ros/jazzy/setup.bash"
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Smoke test:"
echo "  source /opt/ros/jazzy/setup.bash"
echo "  ros2 launch ros_gz_sim_demos diff_drive.launch.py"
echo ""
echo "Full guide: docs/gazebo_install.md"
