# Engine reference — writing a plan

A plan is a Python file `plans/<name>.py` that defines `PLAN`. All shot times are **source seconds** of the recording; graphics placed with `at=` use source seconds, `dt=` uses seconds from the shot start. Global `gfx`/`music`/`sfx` use **output** seconds (numbers, negative = from the end, `'start'`, `'end'`, `('shot', i)`, `('shot', i, 'end')`). Coordinates are in a 1920×1080 (16:9) or 1080×1920 (9:16) frame.

```python
A = dict(ue=r'D:\...\hero.png')                     # still images used as media ('img:ue')
CL = dict(ep2=dict(path=r'D:\...\leela_ep2_phone.mp4', size=(1080, 1920), wav=r'D:\Temp\job\project\cache\ep2.wav'))
PLAN = dict(
    name='s02_dabba', size='9x16', assets=A, clips=CL,
    shots=[ {...}, {...} ],
    gfx=[dict(type='progress', t0=0, t1='end', y=60)],                  # global graphics (output time)
    music=[(0, 'track', dict(track='monkeys_spinning', at=0, gain=-2)),   # track cues
           (6.2, 'stop', dict(tape=True)),                               # tape-stop into silence
           (9.0, 'track', dict(track='fight_in_me', hit=12.0))],         # drop of the track lands at out 12.0
    sfx=[(12.0, 'boom', -8)],                                           # extra global SFX (out time, name, dB)
    max_impacts=2, shake_budget=.10, fadeOut=0,
)
```

## Shot keys
| key | meaning |
|---|---|
| `in`, `out` | source seconds (use `{'in': .., 'out': ..}` dict literals — `in` is a Python keyword) |
| `freeze`, `dur` | a held frame instead of in/out (freeze-frames: add `fx={'freezeColor':'red'}` for the fail freeze + record scratch) |
| `layout` | 16:9 `screen` `stage` `face` `loot` `versus` `full` `tallscreen` (a vertical video on his screen as a tall card + cam) · 9:16 `v_split` `v_face` `v_screen` `v_loot` `v_output` `v_tall` (the stream's vertical player as a tall card, face bubble top-right) `v_full` (a vertical region of the stream fills the frame) `v_cam` (portrait phone footage: the camera fills the frame, face-tracked; `camrect` = source crop) |
| `rect`, `rect1`, `ease` | screen crop (source px of the full 1920×1080 frame) and its end for a push-in (`io` `out` `punch` `lin`) |
| `cam` | `'card'` (default) · `'bubble'` (round face) · `None`; `camrect` source crop of the webcam; `camd` dest rect |
| `media`, `media2`, `msize`, `mrect`, `mrect1`, `md`, `clip0`, `media_audio`, `mvol` | outputs: `'img:<asset>'` or `'clip:<name>'`; `media_audio=True` plays the clip's own audio |
| `bg` | `'blue'` (default world) · `'ink'` (dark, for reveals/versus) · `'blur'` |
| `side` | FACE layout: `'screen'` (small screen card on the right) or `'none'` (room for slams) |
| `speed` | e.g. 8 for a time-lapse (voice dropped; add a chip "⏩ 8×" and ticking/elevator music) |
| `vol`, `mute` | voice gain / mute this shot's voice |
| `fx` | `{'flash':1}` `{'whip':'left'|'right'}` `{'glitch':1}` `{'freeze':1,'freezeColor':'red'}` `{'rewind':1}` |
| `shake` | energy-camera multiplier (default 1 on face layouts, .6 elsewhere, 0 = locked camera) |
| `punch` | `[(src_t, 'zoom'|'shake'|'impact', strength)]` manual hits on the exact transient |
| `caps` | `[(src_t, "text", {y, size, align, x, maxW, dx, end})]` |
| `gfx` | `[dict(type=..., at=src_t | dt=sec, dur=sec, ...)]` |
| `sfx` | `[(src_t or ('dt', s), name, gain_dB)]` |
| `echo` | `[(src_t0, src_t1, {delay:.3, fb:.45, taps:4, wet:.75})]` echo throw on a word |
| `verb` | `[(src_t0, src_t1, wet)]` reverb on a line (voice of god ~.3) |
| `tel` | `[(src_t0, src_t1)]` telephone EQ (reading Claude's reply) |
| `bleep` | `[(src_t0, src_t1)]` mute + 1 kHz bleep (strong swears) |
| `silence` | `[(src_t0, src_t1)]` mute his voice inside a shot without a bleep (e.g. under third-party audio or a mumble) |
| `music` | change music from this shot: `'stop'` or `('track', {track:.., at:.., gain:..})` |
| `duck` | dB cap for music under this shot (e.g. -40 under a playback with its own music) |
| `beat`, `quote`, `why` | notes for reviewers and the next session (HOOK / SETUP / TURN / PROOF / PAYOFF / CTA, first … last words kept, the reason) — ignored by the engine |

## Caption syntax
Words separated by spaces; ` / ` forces a new line. `{word}` mint sticker · `{!word}` red · `{$word}` yellow · `{~word}` blue · `{two words}` one sticker · `^word` big (1.3×) · `*word*` shakes on impacts · `~~word~~` strike-through (draws 0.25 s after it appears) · `_word_` mint underline draw. Words appear across the spoken span of the chunk (from the transcript word times); a chunk lasts until the next chunk or `end`.

## Graphics (`type=`)
| type | keys |
|---|---|
| `quest` | `title`, `steps=[dict(tx, at_src=src_t, state='fail'|None|'active')]`, `at`, `w`, `scale`, `kicker` |
| `meter` | `label`, `from`, `to`, `max`, `fmt='{v}%'`, `at`, `w`, `roll`, `color` |
| `chip` | `text`, `at`, `fill` (mint/ink/red/yellow/ivory), `size`, `anchor`, `rot`, `fam` |
| `label` | sticker label on a card: `text`, `at`, `fill`, `anchor`, `size` |
| `note` | mono lab note typed on: `text`, `at` |
| `comment` | grey mono `(editor commentary)`: `text` (` / ` = line break; the brackets are added for you), `at` (default above captions, centred) |
| `typecard` | prompt card: `text`, `title`, `at=[x,y]`, `w`, `size`, `cps`, `hl=[words to mint]` |
| `stamp` | `text`, `color` (red/mint/yellow), `at`, `size`, `rot`, `sub` — add `layer='top'` to sit over captions |
| `level` | chapter card across a cut (global gfx with `t=('shot', i)`): `num`, `title` ('A / B' = two lines), `sub`, `lastMint`, `hold` |
| `lower3` | `name`, `role`, `at` |
| `circle` | `rect=[x,y,w,h]` (output px), `label`, `color` — `layer='world'` to move with the camera |
| `arrow` | `from`, `to`, `bend`, `color` |
| `spot` | `rect` — dims everything else |
| `vs` | `at`, `r` |
| `hook` | Short header: `lines=['text {key}', ...]`, `y`, `size`, `key` |
| `progress` | follower-goal style bar for Shorts: `y` |
| `bars` | cinematic letterbox: `h` |
| `flash` | `dur`, `a` (≤ 3 per second) |
| `black` | full black (2-frame blackout before a reveal) — `layer='top'` |
| `endcard` | `line`, `handle` |

## SFX names
`whoosh` (peak lands on the cue), `whoosh_s`, `pop`, `click`, `slam`, `stamp`, `fail`, `scratch`, `glitch`, `typing` (with `dur`), `ticks`, `marker`, `ding`, `levelup`, `sparkle`, `hit`, `punch`, `impact`, `boom`, `riser` (ends on the cue), `shutter`, `rewind`, `thump`. Gains are dB relative to the voice's speaking level (−8 hero … −22 micro). Real samples dropped in `sfx_lib/<name>.wav` replace the synth automatically.
Automatic SFX: keyword stickers (pop), quest steps (ding/fail), stamps, level cards (whoosh + slam), meters (ticks), typecards (pop + typing), freezes (scratch/shutter), energy impacts (impact).

## Music tracks (scan in `music/scan.json`: bpm, drops)
`mortals_funk` (phonk, beat from 35.6 s, drop ~113 s) · `montagem_india` (Indian phonk, drops 15.2 / 44.1 s) · `invincible` (hype, drop 10.9 s) · `sky_high` (house 128, drop 46.8 s) · `fight_in_me` (cinematic dubstep, drop 95.7 s, build 63 s) · `heroes_tonight` (uplifting, 76.2 s) · `dreams` (chill trap, 66.3 s) · `on_and_on` (feel-good) · `investigations` (comic detective, in at 8.3 s) · `monkeys_spinning` (goofy) · `local_forecast` (elevator/waiting) · `fluffing_duck` (cheery comedy).
Cue options: `track`, `at` (start offset in the track) or `hit` (output time where the track's drop lands; `drop` index or `drop_t`), `gain` (dB), `fade_in`, `fade_out`; a `'stop'` cue with `tape=True` brakes the music.

## Commands
```
python -I render.py plans/<name>.py [--chunk 2400] [--jobs 2] [--stills 1.0,4.2] [--no-video]
python -I build.py plans/<name>.py --no-frames        # quick check of shot count, duration, shake stats
```
Output: `out/<name>.mp4` (H.264 NVENC, AAC 384k (YouTube's recommendation; 256k before 27 Oct), −14 LUFS, brick-wall limiter at −1.5 dBFS after the linear loudnorm) and, with `clean=True` in the plan, `out/<name>_clean.mp4` (no music — for adding a trending song in-app). Stills: `review/stills/<name>_<t>.png`.
`mrect` crops a still image source (`img:`) as well as clips; `mrect1` animates from it.
PLAN keys: `vface='high'` (default: face high in `v_face`, chest captions never cover it) or `'classic'`; `cap_reveal='speech'|'fast'`; `clean=True` (also export the no-music version); `max_impacts`, `shake_budget`, `fadeIn`, `fadeOut`, `auto_punch`; `cam_grade=dict(contrast=1.03, bright=1.02, grade='saturate(0.95) hue-rotate(-3deg)')` — a webcam-only grade (also settable once in `source.json`; screen panes untouched; measure first, `colour.md`).
More layouts: `v_versus` (two outputs stacked: `media` top, `media2` bottom, `mrect2`, `msize2`). Shot key `main_hold=src_t` freezes the screen pane on one frame while the face keeps playing. Caption sticker in any colour: `{=#RRGGBB:word}`.

`tools/` also holds job helpers from the original edit — `hook_audit.py`, `qa_all.py` — whose folder paths at the top are that job's: edit them for a new project. (Three other job-only helpers were left out of this copy.)

Added 27 Oct (general, no job paths; run with your editing venv, `-I`):
| tool | use |
|---|---|
| `packed_transcript.py <transcript.json> <out.md> [--gap .5] [--from --to]` | the whole stream as one phrase per line with marks for stretched words, low confidence, Whisper fill-ins, long pauses (`cutting.md` §2) |
| `pauses.py <audio48k.wav> <transcript.json> <from> <to> [--mode aggressive|balanced|gentle] [--min-save .2] [--json f]` | pause tightening from the footage's own noise floor → `PLAN SHOTS`; lists fillers/laughs, stretched words, retakes without cutting them (`cutting.md` §3–5) |
| `timeline_view.py <video> <audio.wav> <transcript.json|-> <from> <to> <out.png> [--frames 8] [--rect x,y,w,h]` | filmstrip + waveform + words for one decision point (Devanagari renders) |
| `qa_detect.py <mp4…> [--strips dir] [--expect s] [--short]` | automatic QC with BLOCKER/ISSUE/FYI + MovieLabs codes; cut list and cut strips (`review-qa.md` §3) |
| `check_srt.py <dur> <srt…> [--cuts f] [--fps 30] [--fix]` | Netflix timing rules for Roman Hinglish SRTs; `--fix` writes `.fixed.srt` (gaps, shot snapping, min duration) |
| `brand_lint.py <files/folders> [--numbers]` | brand-truth flags in plans (string literals only), notes and SRTs |
Added 27 Oct (second batch, built on the EP 02 stream):
| tool / key | use |
|---|---|
| `face_track.py <video> <out.json> [--cam x,y,w,h]` | run with any python that has OpenCV >= 4.8 (FaceDetectorYN) and the YuNet ONNX model from the OpenCV zoo (`QL_PY_CV`, `QL_YUNET`). 10 fps face/eye-line track of the webcam, smoothed with a deadzone. `new_project.py` runs it and writes `"facetrack"` into source.json. |
| face tracking in plans | on by default when source.json has `facetrack`: every webcam crop (cards, `v_face`, `v_split`, bubbles, punch crops) follows his eyes per frame, eyes held at 30–50 % of the crop height, crop clamped inside the webcam. Off per shot `'track': False`, per plan `face_track=False`; `face_ref_ey=` overrides his usual eye line. The crop presets still set the composition. |
| `window_words.py <hi|en|auto> a:b …` | re-transcribe short windows with word times when the long transcript is garbage (Hinglish stretches) |
| `unmix_ref.py <stream48k> <ref> <offset> <learn_a> <learn_b> <fix_a> <fix_b> <out.wav>` | subtract a known track (you have the file) from the stream audio. Works on a clean digital copy; music that reached the mic through the room only dropped ~3 dB — then cut around it instead |
| `lang_arbiter.py`, `caption_audit.py` | now read `work/audio16k.wav` of the current project (or `QL_AUDIO16K`); they were hardcoded to the 25 Oct job |
| gfx `tape` | series/section band: `text`, `at`, `size`, `rot`, `w`, `h`, `from_` — yellow plate, 3 static chevrons each end (photosensitivity-safe) |
| `level` `kicker=` | replaces "LEVEL nn" (e.g. `kicker='TEST 01'`); `quest` `kicker=` relabels the HUD (e.g. `'TEST LOG'`) |
Clip inserts: frames past a clip's own end are no longer requested (a 5 s clip in a 5 s shot used to crash extraction). Two shots with the same `in` make `idx(src)` lookups ambiguous — give each shot a distinct `in`.

Running the renderer by hand from Git Bash: set `MSYS_NO_PATHCONV=1`, or the `--mount=/frames=…` arguments get rewritten into Git's install folder and every frame 404s (render.py itself is not affected). A missing font in `fonts/` (e.g. `bahnschrift.ttf`, copied from Windows by `new_project.py`) makes the page wait until the timeout.
