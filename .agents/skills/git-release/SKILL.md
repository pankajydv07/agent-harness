---
name: git-release
description: Standard workflow for preparing git release notes and tagging releases
---

# Git Release Skill

When the user asks to prepare a release:
1. Run `git status` using bash to ensure working tree is clean.
2. Check recent commits with `git log -n 5 --oneline`.
3. Draft a semantic version tag (e.g. `v0.1.0`) and summarize the highlights.
