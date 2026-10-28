---
name: editor-os
description: The thinking layer for editing video - how an editor decides what to cut, where, how fast, with which sound, and why. Holds eight selectable edit styles (caption-first social news, archive newsreel, real-time countdown split-screen, time-lapse symphony, visual investigation, beat-driven montage, sports telestrator, broadcast news package), a pacing and rhythm system (cuts per minute, shot-length bands, beat grid, reading time, acceleration, breath), a sound-effect cue-sheet method (layering, placement, silence, J/L-cuts, ducking, loudness), and scripts that measure pacing and snap cuts to a grid. Use whenever the user wants a video edited, re-paced, made punchier, given sound effects or music, cut to a beat, styled like a news bulletin / montage / documentary / explainer, or asks "how should this be edited", "why does this feel slow/flat", "what sound goes here", or "edit this like a pro". Works as the brain above edit-video, which runs the pipeline, and ffmpeg-edit-toolkit, which carries out the cuts.
---

# Editor OS

How a working editor thinks, written down so it can be run. It does not replace the pipeline skills; it decides **what the edit should be** so they can build it.

| Layer | Skill |
|---|---|
| **Decide** (style, pace, sound, checks) | **editor-os** (this) |
| Run the steps in order | `edit-video` |
| Generic craft: cut vocabulary, CPM, tempo | `video-editing-craft`, `comedy-editing-timing` |
| Mix and music basics | `video-sound-and-music` |
| Carry out cuts, mixes, encodes | `ffmpeg-edit-toolkit` (plus a vertical-export skill if you have one) |
| Graphics | `motion-graphics-for-video`, Remotion skills |
| Words from footage | `transcribe-local` (or a video-watching skill if installed) |

Style grammars come from the lemo-opuscar library (`github.com/lemomo-ai/lemo-opuscar`; its Edit & Documentary styles plus DIRECTOR.md / TECHNIQUE.md), with the code-rendering parts removed so they apply to footage edited in any tool. Grammar only: never copy a broadcaster's name, logo, font or jingle.

## Honest limits

You cannot hear audio or watch playback. You can read frames, transcripts, timestamps and measurements. So: make every measurable decision yourself (cut times, grid, loudness, reading time), show the numbers, and name what only a human ear or eye can judge (does the joke land, does the riser feel earned). Never say you "watched" something you only measured.

## The loop

Run these in order. Each step has an output; if you cannot write the output, you are not done with the step.

1. **Brief** → one line each: *platform and length*, *what the viewer should feel*, *sound on or off*, *must keep / must cut*. Ask once, only for what is missing.
2. **Read the footage** → transcript with timestamps, 1-second contact sheet, silence map, existing cut list. Output: what happens, the strongest moment, the dead stretches, the turn (the one moment that changes meaning).
3. **Pick a style mode** (table below) or blend two. Output: the mode name and why it fits the material, not just the topic.
4. **Write the shape** → logline + three candidate structures, choose one. Hook inside 3 seconds, one turn, an ending that echoes the opening. Output: `EDIT-PLAN.md` from `templates/edit-plan.md`.
5. **Build the clock** → decide what drives cuts (a beat grid, spoken calls, reading time, or story events) and write the numbers. Use `scripts/editgrid.py`. Output: cut list with times.
6. **Cut** → rough cut first, then pace pass, then picture layer (B-roll, graphics, captions). Run `scripts/pacing_report.py` after each pass.
7. **Sound** → fill `templates/cuesheet.csv`: every visible action has a sound, three layers, two silences, sound bridges across cuts. Output: cue sheet, then the mix.
8. **Check** → measure, look, read back (see Review loop). One fix round, then deliver.
9. **Report** → numbers before and after, what is placeholder, what you could not judge, one next step.

## Edit styles (pick a mode)

Pick by what the material is and what the viewer must do, then read that mode in `references/style-modes.md`.

| If the material is… and you want… | Mode | Signature |
|---|---|---|
| Social video that must work with sound off; stats, news, explainers | **Caption-first** | huge captions slam in chunks, one keyword highlighted, frame-4 number hook, source tag on every figure |
| Old footage, period pieces, "history in a hurry" | **Newsreel** | fast patter over archive, place·date card, one story per place, iris/wipe punctuation, band stops dead for the punchline |
| One real event with a known zero (launch, verdict, final whistle, polls closing) | **Live countdown** | real time never cut; screen splits into more cells nearer zero; many cells merge into one at zero |
| A place, a city, a process; no narrator, music leads | **Time-lapse symphony** | score first; cuts get denser with the subdivisions; one slowed fragile thing; hard cut to black on a downbeat |
| Proving what happened from several sources | **Investigation** | sources meet at one sync moment; red circle only on what matters; known vs unknown kept apart |
| Many people / machines / documents making one argument; punchy anything | **Montage** | cuts on a 120 BPM machine beat; acceleration by halving; A + B collide into a third idea; documents marked, not quoted |
| One decisive play or moment that needs explaining | **Telestrator** | play → rewind → freeze → draw → play on; one freeze, one finding; music stops with the picture |
| A weekly or multi-item bulletin, product news, a "state of X" round-up | **Broadcast package** | sting becomes the bug, rundown opens and closes, strap never leaves, one fact per screen |

No fit? Use the universal rules below and say you are not using a named mode. Blending is fine (a caption-first reel with one telestrator freeze); keep **one** accent colour, one transition grammar, one sound palette.

## Universal rules (every mode)

**Shape**
- Hook in the first 3 seconds, and it must be an *event* (a number landing, a motion, a claim), not a logo or a slow fade.
- One subject, one goal, one turn. The ending echoes the opening, or does the thing right the second time.
- One signature move at the emotional peak. Everything before it is setup; cut the extras. A gag the viewer can read at thumbnail size beats three they cannot.
- If a beat needs explaining, remove it.

**Cause of every cut** (a cut with no cause is noise). Valid causes, strongest first:
1. A spoken call or on-screen event happened (the line starts, the ball is struck, the number changes).
2. New information arrives (new fact, new source, new place).
3. The beat says so (music grid), at a bar line for big changes, half-beats for small.
4. The eye finished reading (reading time elapsed).
5. Contrast is needed (direction, value, scale, speed) because the last two shots were too alike.
Write the cause next to the cut in the plan. If you cannot name it, delete or merge the cut.

**Pace is variation, not speed**
- Alternate fast and slow, include one clear acceleration or deceleration, and give the viewer one breath (a long take or a held pause). A film at one even speed has failed.
- Perceived pace = cut rate + movement in frame + subject size + camera movement. To slow a scene change any of the four, not just the cuts.
- Fast is made with *fewer words per screen*, never by cutting before people finish reading.
- Nothing static for more than about 1 second without something moving (push, counter, line drawing, new element). Planned exceptions: reading holds, one comparison hold, one silence beat, the end card.

**Reading time** (hold from the moment the text is fully on screen)
- English: `letters ÷ 15 + 1.5` s. Chinese: `characters ÷ 4.5 + 1.5` s. Hindi / Tamil: treat like English by letter count, add 20 %.
- Any caption lasts ≥ 1.8 s and ≥ spoken line + 0.6 s. A title card ≥ 4 s. A comparison stays until every item has been fully visible ≥ 2.5 s.
- One line per language, never wrapped; if it would wrap, split into two captions.
- `scripts/editgrid.py read "text"` prints the number.

**Camera and transitions**
- Use real changes of framing, not the same shot twice. Reasons: push to focus, pull to reveal, parallax for depth, freeze to examine.
- Pick **one transition grammar** and keep it (wipe, flash, slam, iris). Hard cut is the default; dissolves only into/out of black or between time jumps. No random effect packs.
- Eye-trace: where the eye ends in shot A is where it starts in shot B. Anything that appears gets motion or a sound on arrival.

**Honesty** (documentary, news, explainer modes)
- Every number carries its source on screen in the same shot. Never write a word stronger than the source ("stressor", not "killer"). Mark inference as inference (`≈`, "inferred", dashed). Illustrative footage never carries a place label it does not have.

## Pacing: see it, don't guess

```
python -I skills/editor-os/scripts/pacing_report.py --video edits\name_v1.mp4
python -I skills/editor-os/scripts/pacing_report.py --cuts 0,1.5,3.0,4.0,4.5,5.0 --bpm 120
python -I skills/editor-os/scripts/editgrid.py beats --bpm 120 --fps 30 --bars 8
python -I skills/editor-os/scripts/editgrid.py snap --bpm 120 --fps 30 1.37 2.98 4.1
python -I skills/editor-os/scripts/editgrid.py read "Bees lost 62 percent of colonies"
```

`pacing_report.py` prints: cuts, overall and per-window cuts per minute, shot-length min/median/max, windows with no cut (flat), the tempo trend (accelerating, decelerating, flat, wave), the hook check (first cut and first 3 s), and, with `--bpm`, how many cuts sit on the beat grid and each off-grid cut's error in ms. Read it against the mode's targets in `references/pacing-and-rhythm.md` and **state both before and after numbers** in the report.

## Sound: cue sheet method

Do not "add some sound effects". Build a table (`templates/cuesheet.csv`): *time · what you see · sound · layer · level · note*. Rules, detail in `references/sound-cue-sheet.md`:
- Every visible action has a sound: a landing, a slam, a swipe, a counter, a stamp, a page, a click. Match the material (paper, wood, metal, glass sound different).
- Three layers: **bed** (room / ambience / low drone, always there), **foley** (tied to actions, sample-accurate), **music** (score or track, ducked under speech).
- At least **two real silences or near-silences** before the turn or the peak. The first sound after silence is one of the most important in the piece.
- Sound as transition at least twice: J-cut (next scene's sound arrives early) and L-cut (last scene's sound runs over the cut).
- Peak of the sound on the exact frame of the peak of the picture; whooshes *start* before the cut so their peak lands on it.
- Music in the palette of the mode, not generic piano-and-strings. Duck 6-10 dB under voice (16 dB pumps); voice ≈ 8-12 dB over music. Master about −14 LUFS, true peak ≤ −1.2 dB. Fade the first 25 ms of the file so a hit on sample 0 does not overshoot in the AAC encode.
- Placeholders from `ffmpeg-edit-toolkit/scripts/make_sfx.py` are for the rough cut only; say so.

## Review loop (before delivering)

1. **Contact sheet**: one frame every 1-2 s, twice (rough and final). Look for blank frames at transitions, subject too small or at the edge, text over the subject, red on red, unreadable low contrast.
2. **Key-action strips**: frames every 0.2 s around each key action (hand-overs, freezes, slams).
3. **Measure**: duration equals plan; `ffmpeg -af ebur128` loudness; `blackdetect`; `silencedetect` shows the planned silences exist; `pacing_report.py` meets the mode's numbers.
4. **Read back**: transcribe the final file and read it. Words cut mid-sentence? Names mangled by TTS? Numbers match the sources?
5. **One full-speed viewing with sound by the user** (you cannot do this one). Ask them to check three things: first 5 seconds, the turn, the ending.
6. **One fix round.** Fix everything the checks found at once; anything bigger, say so in one line. User notes after delivery are new rounds: change only what they ask.

## Common failures (check before shipping)

Subject too small or hard against the frame edge · too dark to read · captions covering the subject · a gag or failure too fast to understand · blank frames inside transitions · effects (zoom, spotlight, ring) that do not track the subject after the camera moves · text cut before it can be read · music fighting the voice · a graphic that just pops in · constant pace for the whole piece · ending on a fade of energy instead of a button.

## Working rules

- Version outputs (`_v1`, `_v2`); never overwrite originals; log commands in `edits/edit-log.md`.
- Tell the user before any long render, and before downloading any footage or music (what, from where, licence). Where to find assets and how to download them with their licence recorded: `asset-library`.
- Use only material the user owns or has rights to, or properly licensed (public domain, CC0, CC BY with credit). Keep a `CREDITS` note.
- When taste decides, offer two short options, not an essay.
- Language: captions and voice in the language the user writes in. Voiceover, if needed, comes from whatever TTS or voice skill the user has (for Indian languages, local IndicF5 or a stock-voice API).

## Files

- `references/style-modes.md`: the eight modes in full (when, cut grammar, numbers, transitions, text, sound palette, signature moves, pitfalls, how to do it in ffmpeg/Remotion/an NLE).
- `references/pacing-and-rhythm.md`: beat-grid maths, shot-length bands by material, CPM targets, acceleration patterns, breath and silence, tension curves.
- `references/sound-cue-sheet.md`: action → sound table, layer recipes, timing offsets, per-mode palettes, mix numbers.
- `references/edit-thinking.md`: the questions an editor asks per cut, per scene and per film, with worked examples.
- `templates/edit-plan.md`, `templates/cuesheet.csv`
- `scripts/pacing_report.py`, `scripts/editgrid.py`
