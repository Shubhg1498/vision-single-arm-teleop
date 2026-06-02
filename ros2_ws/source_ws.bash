#!/usr/bin/env bash
# Source the ROS 2 workspace (Jazzy + vdat_gazebo + vdat_teleop).
#
# vdat_teleop (ament_python) does not always register on AMENT_PREFIX_PATH via
# install/setup.bash alone; this script ensures both workspace packages are visible.
set -eo pipefail

_WS="$(builtin cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /opt/ros/jazzy/setup.bash
source "${_WS}/install/setup.bash"

if [[ -d "${_WS}/install/vdat_teleop" ]]; then
  case ":${AMENT_PREFIX_PATH:-}:" in
    *":${_WS}/install/vdat_teleop:"*) ;;
    *)
      export AMENT_PREFIX_PATH="${_WS}/install/vdat_teleop:${AMENT_PREFIX_PATH}"
      ;;
  esac
fi
