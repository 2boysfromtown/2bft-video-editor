# Brief for a parallel edit agent (one file per agent)

Self-contained: the agent sees nothing else. Fill every field; delete nothing. (Pattern from browser-use/video-use and HyperFrames, MIT / Apache-2.0, adapted.)

**Goal (one sentence):** e.g. "Finish Shorts S06–S10 from the 25 Oct stream to delivery quality."

**Read first:** `<skill>/SKILL.md`, `STYLE.md`, `references/engine.md`, `references/cutting.md`, `references/review-qa.md`, and `EDIT-PLAN.md` (the log + your Shorts' director's passes).

**Work here (absolute paths):**
- project copy: `<short path>\\<job>\proj_<x>` (its own engine copy — never edit the main project's engine)
- plans to write/finish: `plans\s06_….py` … `plans\s10_….py`
- source + words + energy: as in `source.json`
- outputs: `out\<name>.mp4` and `out\<name>_clean.mp4`, notes `exports\shorts\<name>.txt`

**Exact specs:** 1080×1920, 30 fps, H.264 yuv420p BT.709 TV range, AAC 48 kHz stereo 384 kbps, −14 LUFS integrated, true peak ≤ −1.0 dBTP, Shorts safe zone x 65–850 / y 288–1248, hook top ≥ ~200 px.

**Look:** palette #4282F0 blue · #12EABB mint · #0B1220 ink · ivory · #FF4A3D red (fails only) · #FFD23F yellow (loot/numbers); fonts in `fonts\` (Bahnschrift Bold Condensed, Inter 900, JetBrains Mono).

**Per-Short timeline:** the director's pass from `EDIT-PLAN.md` (spine, beats with source times, hook line, music map, the one native move).

**Anti-list (do NOT):** add words he didn't say to captions · print a number not confirmed by two transcription passes · bake a commercial song into an export · add effects that aren't in the plan or the rules · change another agent's files · close the user's apps · download anything.

**Machine limits:** render with `--jobs 1` (shared NVENC/RAM slots — `render.py` waits for a slot; do not kill other renders).

**Deliverable checklist (report each line):**
1. `qa_detect.py` on every output — paste the findings; no BLOCKER left.
2. `check_srt.py` / `hook_audit.py` / `caption_audit.py` / `brand_lint.py` results.
3. Contact sheet path; anything you changed from the plan and why.
4. What a human must check by ear.

**When unsure:** pick the most obvious reading of the plan and note it — don't stop to ask.
