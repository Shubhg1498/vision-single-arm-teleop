# GitHub Setup

Recommended repository name:

```text
vision-dual-arm-teleop
```

## Option A: Using GitHub CLI

```bash
cd ~/Projects
mkdir -p vision-dual-arm-teleop
cd vision-dual-arm-teleop

git init
gh repo create Shubhg1498/vision-dual-arm-teleop --public --source=. --remote=origin --description "Vision-based dual-arm teleoperation and demonstration collection for robotic manipulation"

git add .
git commit -m "Initial project scaffold"
git branch -M main
git push -u origin main
```

## Option B: Manual GitHub Repo

Create a public repo on GitHub named:

```text
vision-dual-arm-teleop
```

Then locally:

```bash
cd ~/Projects/vision-dual-arm-teleop
git init
git add .
git commit -m "Initial project scaffold"
git branch -M main
git remote add origin git@github.com:Shubhg1498/vision-dual-arm-teleop.git
git push -u origin main
```
