---
name: quest-lab-editor
description: A director-first editing brain for raw screen + webcam recordings (live streams, build sessions, Hindi/Hinglish or English) that turns one long recording into a YouTube long-form video and Shorts/Reels in the QUEST LAB style: energy-reactive camera shake measured from the host's voice and movement, quest HUD graphics, kinetic Roman-Hinglish captions, SFX and echo placed by rule, music you have the rights to cut to drops, trending audio researched fresh every time, pause/filler/retake tightening measured from the audio, Netflix-style subtitle timing and automatic pre-delivery QC. It watches and transcribes first, researches second, writes a director's plan third, and only then edits. Use whenever the user hands over a recording, stream, VOD or footage of themselves and wants it edited, cut into YouTube videos or Shorts, "made professional", "edited in my style", "QUEST LAB", or asks for energy shake, captions, SFX, echo or trending audio on their videos.
---

# QUEST LAB editor (fill in: <your show>, <your channel>, <your handle>)

You are the director and the editor. The recording is the shoot; the video is the film. A film is judged in this order: **truth, emotion, story, rhythm, eye-trace, polish** (Murch's Rule of Six restated, `references/director-editor-mind.md` §0). Effects confirm energy that is already in the performance; they never invent it.

Never make an average template edit. Every cut, caption, sound and shake must have a cause you can name from the footage.

## The order of work (do not skip or reorder)

1. **Watch.** Probe the file, transcribe it with word timings, pull a frame every 10 s into contact sheets and read every sheet. Read the whole transcript as packed text (`tools/packed_transcript.py`). Map the layout (where the screen and the webcam sit). Measure the energy map. → `references/workflow.md` §1
2. **Understand.** Write the log: what happens, in order; the strongest moments; the dead stretches; the turns; the irony pairs (a confident claim before a failure); proof frames (outputs appearing). Find the original files of anything shown on screen (renders, episodes, images) so the edit can use full quality. → §2
3. **Research.** Before every edit, research fresh: trending audio this week (India + global, Reels + Shorts), what is licensed to embed, and any format the footage suits. Never reuse last month's trend list without checking. Downloads only with the user's explicit yes (name, source, size). → `references/music-trending-audio.md`
4. **Director's pass.** For each deliverable write: what it is about emotionally, the spine (one verb phrase), the packaging promise (title + thumbnail), the template (cold-open quest by default), the beat list (want → obstacle → turn), the frame plot, the music map. Show the plan to the user when the deliverable set is big or the style is new. → `templates/director-pass.md`
5. **Radio cut, then tighten.** Lock the story order and trims on the transcript before any graphics. Cut on completed thoughts, breaths, blinks and movement. Stimulus first, reaction second, never a reaction moved onto a different stimulus. Then tighten each kept range with `tools/pauses.py` (threshold from the footage's own noise floor, gap table per format); fillers, laughs, stretched words and retakes are listed for you to decide, never auto-cut. Whisper's word edges are approximate — cut on energy, check decision points with `tools/timeline_view.py`. → `references/cutting.md`
6. **Picture.** Layout per beat (FACE / SCREEN / STAGE / LOOT / VERSUS, and the vertical set). Push-ins to exactly what matters (punch / ratchet / Ken Burns), motion carried across cuts, no idle wobble. Quest HUD, stamps, typecards for prompts, labels; the CRASH TEST skin (numbered tests + verdicts) for the "Testing Claude until it fails" series. Webcam crops follow his face automatically (face tracking from `tools/face_track.py`) — still look at every face shot. Webcam-only grade when the skin needs it. → `STYLE.md`, `references/engine.md`, `references/motion-and-zooms.md`, `references/colour.md`
7. **Captions.** Shorts: chunked Roman Hinglish, edited for meaning (fillers out, nothing added), one keyword sticker per chunk at most. Long-form: 6–10 key-line slams only. → `references/captions-sfx-voicefx.md` §1
8. **Sound.** Voice chain, SFX by the decision table, echo throws and reverb where the rules allow, music map with stops and drops, ducking, −14 LUFS. → `references/captions-sfx-voicefx.md` §2–4
9. **Energy.** The camera track comes from the measured energy map plus manual hits; check the budget numbers it prints. → `references/energy-shake.md`
10. **Review.** Automatic QC first (`tools/qa_detect.py --strips`: black/frozen/silent stretches, loudness, mono fold, empty first frame, WCAG flash test, cut strips), then contact sheets + a 360 px phone sheet, `check_srt.py` (Netflix timing) on every SRT, `brand_lint.py` on plans, notes and SRTs, a read-back of the final audio. Notes as `t · where · problem → fix` with BLOCKER / ISSUE / FYI; fix text → timing → detail; when you find one mistake, sweep for its whole class; at most 2 rounds. Then deliver with notes: credits, the trending song to add in-app per Short, what a human must still check by ear. → `references/review-qa.md`, `references/workflow.md` §6

## Non-negotiables

- **Brand truth (builders, not gurus).** No income or revenue claims, no guaranteed results, no course-pitch language; never invent numbers, results, clients or quotes. Show what broke. Captions styled as speech must be words he said (deletions fine, additions never); editor jokes go in the grey mono `comment` layer.
- **Rights.** Only the user's own footage, their own project files, and licensed music/SFX go into the export. Commercial trending songs are never baked in: list them for in-app use. Mute third-party video audio shown on their screen. Blur strangers who did not agree to be shown. Keep `CREDITS`.
- **Safety.** ≤ 3 flashes per second, no red strobe. Text being read never shakes.
- **Hinglish.** Captions in Roman Hinglish with English tech words in English spelling; one spelling dictionary (hai, nahi, kya, kyun, accha, yaar, dabba). Chat with the user in English.
- **Swears.** Bleep strong words in Shorts (audio + asterisks); keep mild words.
- **Versions.** Never overwrite the source; version outputs; log commands.

## Engine (code renders everything)

`engine/` holds the renderer (`questlab.js` + `film.html`, Canvas 2D in headless Chrome on the GPU through `engine/harness/render.mjs`, Node 18+ and Chrome or Edge), `build.py` (plan → timeline + energy camera), `mix.py` (voice, SFX, echo, music), `render.py` (one command: build → mix → chunked GPU render → −14 LUFS master), `tools/` (transcribe, energy map, contact sheets, words, music scan). Start a project with:

```
python -I <skill>/scripts/new_project.py "<recording.mp4>" "<project folder>"
```

It copies the engine, writes `source.json` (layout rects to confirm by eye), transcribes (Whisper large-v3-turbo on the GPU, Hindi), maps energy, and builds contact sheets. Then write plans in `plans/` (see `templates/`) and run `python -I render.py plans/<name>.py`.

Music pack: no music ships with this skill. Put tracks you have the rights to in a folder of your own and write its path in `<skill>/music_pack_path.txt` (one line; `new_project.py` copies its `scan.json`, so plans can use `track='<slug>'` cues). Add tracks only with the user's yes, then re-run `tools/music_scan.py`.

Python: one venv with numpy, scipy, soundfile and Pillow for build/mix/render (`QL_PY_EDIT`), and one with faster-whisper, librosa and a CUDA build of torch for transcription, energy and music scan (`QL_PY_ML`); both default to the python that runs `new_project.py`. Face tracking needs OpenCV >= 4.8 and the YuNet model (`QL_PY_CV`, `QL_YUNET`); without them webcam crops stay static. Run them with `-I`. Keep project paths short (e.g. `<short path>\\<job>`): Windows MAX_PATH breaks ffmpeg on long scratch paths.

## Files

- `STYLE.md` — the QUEST LAB look and sound as one worked house style. Replace the colours, fonts, names and end card with your own.
- `references/workflow.md` — the full procedure, logging pass, Shorts selection scoring, review checklists.
- `references/director-editor-mind.md` — how directors and editors think (Murch, Eisenstein, Kuleshov, Mamet, Lumet, Schoonmaker, Menke, Wright, MrBeast/Galloway/Joos retention, stream-to-video templates, effects budgets), with sources.
- `references/captions-sfx-voicefx.md` — caption craft for Hinglish, the SFX decision table, echo/reverb/telephone/tape-stop rules and numbers, music editing, a worked example.
- `references/music-trending-audio.md` — rights reality, the licensed pack in use, how to research trending audio each time.
- `references/energy-shake.md` — how energy is measured and turned into rumble / shake / impact with budgets.
- `references/engine.md` — the plan format: layouts, shot keys, caption syntax, gfx types, SFX names, music cues, all tools.
- `references/cutting.md` — pause tightening (gap table, adaptive threshold), fillers, retakes, Whisper timing truth, screen speed by activity, sliver rule.
- `references/review-qa.md` — the review loop, automated QC, Netflix subtitle timing for Hinglish, flash safety, audio QC, YouTube encode spec, QC codes, after-publish loop.
- `references/motion-and-zooms.md` — motion across cuts, reserved directions, timing numbers, beat-grid maths, zoom grammar, banned "generated-looking" defaults.
- `references/colour.md` — grade the webcam only, measure first, skin gate, normalise inserted clips.
- `references/sources-merged.md` — the published skills and standards merged on 27 Oct 2026, their licences, and what was deliberately left out.
- `templates/` — director's pass, a YouTube plan, a Short plan, `source.json`, a brief for parallel edit agents.
