#!/usr/bin/env bash
# Trim a video with ffmpeg.
#
# Usage:
#   bash scripts/trim_video.sh INPUT START END [OUTPUT]
#
# Examples:
#   bash scripts/trim_video.sh ~/2026-06-06\ 15-51-56.mkv 0:30 2:45
#   bash scripts/trim_video.sh input.mkv 00:01:10 00:02:50 videos/demo.mp4
#
# START / END formats: seconds (90), MM:SS (1:30), or HH:MM:SS (0:01:30)
# OUTPUT defaults to videos/teleop_demo_trimmed.mp4

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 INPUT START END [OUTPUT]"
  echo "Example: $0 ~/2026-06-06\\ 15-51-56.mkv 0:45 2:30"
  exit 1
fi

INPUT=$1
START=$2
END=$3
OUTPUT=${4:-videos/teleop_demo_trimmed.mp4}

if [[ ! -f "$INPUT" ]]; then
  echo "Input file not found: $INPUT"
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

echo "Input:  $INPUT"
echo "Trim:   $START → $END"
echo "Output: $OUTPUT"
echo

# Re-encode to H.264 MP4 — reliable for upload (YouTube, GitHub Releases).
ffmpeg -y \
  -ss "$START" -to "$END" \
  -i "$INPUT" \
  -c:v libx264 -preset medium -crf 20 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  "$OUTPUT"

echo
echo "Done. Duration:"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT"
echo "Saved to: $OUTPUT"
