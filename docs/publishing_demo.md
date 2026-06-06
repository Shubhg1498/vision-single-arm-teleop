# Publishing the demo video

Trimmed file: `videos/teleop_demo_trimmed.mp4` (~10 MB, 2 min)

Use **two placements** — GitHub (repo) and portfolio (website). One file, two upload steps.

---

## 1. GitHub — project repo

Repo: [github.com/Shubhg1498/vision-dual-arm-teleop](https://github.com/Shubhg1498/vision-dual-arm-teleop)

**Recommended: GitHub Release** (keeps git history small; video stays gitignored)

```bash
cd ~/vision_dual_arm_teleop

# Install GitHub CLI once: sudo apt install gh && gh auth login

gh release create v1.0.0 \
  videos/teleop_demo_trimmed.mp4 \
  --title "v1.0 — Vision teleop demo" \
  --notes "$(cat <<'EOF'
End-to-end demo:
- MediaPipe hand tracking (external USB camera)
- MoveIt Servo → Gazebo Harmonic
- Physics-based pick-and-place with transport latch
EOF
)"
```

After release, the download URL is:

```text
https://github.com/Shubhg1498/vision-dual-arm-teleop/releases/download/v1.0.0/teleop_demo_trimmed.mp4
```

Add that link to `README.md` (already has a Demo section placeholder).

**Alternative — commit the MP4** (only if you want the file inside the repo):

```bash
git add -f videos/teleop_demo_trimmed.mp4
git commit -m "Add teleop demo video"
git push
```

GitHub allows files up to 100 MB; ~10 MB is fine but Releases is cleaner.

**README embed tip:** GitHub README does not inline-play MP4 reliably. Use a link, or upload the video once via **Issues → drag & drop** to get a `githubusercontent.com` URL for an `<img>` poster + link.

---

## 2. Website — portfolio (GitHub Pages)

Site repo: [github.com/Shubhg1498/shubhg14981.github.io](https://github.com/Shubhg1498/shubhg14981.github.io)  
Live URL: **https://shubhg1498.github.io/shubhg14981.github.io/**

The video is copied to:

```text
shubham-portfolio/public/projects/vision-teleop-demo.mp4
```

`src/data/content.ts` references it on the **Vision Dual-Arm Teleoperation** project card.

Deploy:

```bash
cd ~/shubham-portfolio
git add public/projects/vision-teleop-demo.mp4 src/data/content.ts
git commit -m "Add vision teleop demo video to projects"
git push origin master
```

GitHub Actions builds and publishes to `gh-pages` (~1–2 min).  
Video URL after deploy:

```text
https://shubhg1498.github.io/shubhg14981.github.io/projects/vision-teleop-demo.mp4
```

---

## 3. Optional — YouTube (best for sharing)

For LinkedIn / email / embeds anywhere:

1. Upload `teleop_demo_trimmed.mp4` to YouTube (Unlisted or Public).
2. In portfolio `content.ts`, switch to:

```ts
media: { type: "youtube", id: "YOUR_VIDEO_ID" }
```

3. Link YouTube from the GitHub README as well.

YouTube handles bandwidth and mobile playback better than self-hosted MP4.

---

## Checklist

| Step | Where | Action |
|------|--------|--------|
| 1 | Local | Confirm `videos/teleop_demo_trimmed.mp4` looks good |
| 2 | GitHub Release | `gh release create v1.0.0 ...` |
| 3 | README | Push README with release + portfolio links |
| 4 | Portfolio | Commit video + `content.ts`, push `master` |
| 5 | Verify | Open portfolio `#projects` and release download link |

---

## Link both places together

**README (teleop repo):**

```markdown
**Demo video:** [Watch on portfolio](https://shubhg1498.github.io/shubhg14981.github.io/#projects) · [Download MP4](https://github.com/Shubhg1498/vision-dual-arm-teleop/releases/download/v1.0.0/teleop_demo_trimmed.mp4)
```

**Portfolio project** already links `repo` to the GitHub project.
