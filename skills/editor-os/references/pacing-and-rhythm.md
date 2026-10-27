# Pacing and rhythm

Numbers for deciding how fast, how long, and when. Use with `scripts/pacing_report.py` (measures a cut list) and `scripts/editgrid.py` (beat grid, snapping, reading time).

## 1. What pace actually is

Perceived pace is the sum of four things, so check all four before touching the cut count:

1. **Cut rate** (cuts per minute, CPM).
2. **Movement in the frame** (subject and graphic motion).
3. **Subject size** (tight and busy feels faster than wide).
4. **Camera movement** (push, pan, shake).

Many cuts + whip pans + close-ups is far faster than cuts alone. To slow a scene, reduce any of the four. To speed one up, raise any of them. Information density is a fifth, hidden one: more words per screen reads as slower, not faster.

## 2. Tempo is designed, never accidental

- Write the **emotional destination** of each section first, then choose the pace. Heavy, reflective, tender: slower. Tense, rushed, joyful: faster.
- Vary on purpose. Every piece of 30 s or more needs: one fast stretch, one slow stretch, one clear acceleration **or** deceleration, one breath (a long take or a held pause), one planned silence.
- Change tempo only at story change points. Random tempo change reads as amateur.
- A constant tempo for the whole piece has failed, however good each cut is.
- Short-form is simple and fast; long-form is varied. Do not paste short-form tempo onto a 20-minute piece.

## 3. Shot-length bands (starting points, then measure)

| Material | Typical hold | Notes |
|---|---|---|
| Talking head, intimate vlog/podcast | 6-90 s | cuts only to remove dead parts; authenticity is the product |
| Talking head, entertainment | 2-5 s with a change on screen every few seconds | remove every pause |
| Footage / B-roll under captions | 1.5-3 s | |
| Archive footage | 1-2.5 s | |
| Print, documents, charts (must be read) | 2.5-4.5 s | add reading time, never less |
| Data card with a comparison | until every item fully on screen ≥ 2.5 s | |
| Map long take as a breath | 6-12 s | |
| Machine-beat montage | 0.5-2 s | may accelerate to 0.125 s, not below 3 frames |
| Time-lapse symphony | 2 bars → 2 frames, driven by score | |
| Freeze (analysis) | 1.8-2.4 s | longer needs a second action inside |
| Title card | ≥ 4 s | |
| Caption | ≥ 1.8 s and ≥ spoken line + 0.6 s | |
| End card | 4-5 s | long credits lose the audience; keep fine print small, the last moving shot runs under it |

## 4. Cuts per minute (CPM)

Rule of thumb for a first target; override with the experience (see `video-editing-craft` §1).

| Experience | CPM |
|---|---|
| Hang-out / intimate | 1-8 |
| Calm explainer / documentary | 8-20 |
| Entertainment, caption-first, news | 20-40 |
| Hype, montage, trailer-style sections | 40-120 |
| Peak accelerations (a few seconds) | far above; judge by shot length, not CPM |

Measure in windows (default 10 s), not just overall: an overall average hides the shape. A good edit shows a curve with deliberate lows and highs. Flag any window with **no cut** longer than the plan allows; if something is moving in it (counter, push, drawn line, source camera), that is fine.

## 5. Acceleration and deceleration patterns

- **Halving:** 2 s → 1 s → 0.5 s → 0.25 s (each step usually one bar, one beat, one half-beat). Stop at 3 frames.
- **Beat ladder (score-led):** 2 bars → 1 bar → 2 beats → 1 beat → ½ beat → triplets → sixteenths → 4 frames → 2 frames → hard stop.
- **Brake:** fast run, then one long shot (3-4 s) under a held chord. The brake is what makes the acceleration land; plan it before the acceleration.
- **Stories get shorter toward the end** (newsreel): 2-3 bars → 1 bar → beats → one held button.
- **Cut count tracks cell count** (countdown): more cells = more tension; the fewest cells are nearest zero.
- **Slow-fast-slow** for a section arc: set up (slow), turn (fast), consequence (slow).

## 6. Beat grid

For tempo `B` BPM and frame rate `F`:

- beat = `60 / B` s · bar (4/4) = `240 / B` s · beat in frames = `F × 60 / B`.
- 120 BPM: beat 0.5 s, bar 2 s. At 30 fps: beat 15 frames, half 7.5 (use 7/8 alternating), sixteenth 3.75.
- Pick tempos whose beat is a whole number of frames: at 30 fps → 120 (15), 100 (18), 112.5 (16), 150 (12); at 24 fps → 120 (12), 96 (15), 144 (10).
- Anchor beat 0 to a real event (end of the sting, the first word, the downbeat of the track), not to time 0.
- Big changes (new section, new location, turn) sit on **bar lines**; small changes on beats or half-beats; quick inserts on off-beats. Do not cut on every beat: leave time to see.
- When the audio is a **real recording or a spoken line**, the cut follows the audio's own events (a call, a word, a hit). Music grid applies only when music leads.
- Check every cue with a script: aim for 0 ms between a visual hit and the sound cue it should land on, and report the worst offender.

Tool: `python -I editgrid.py snap --bpm 120 --fps 30 --grid half 1.37 2.98` returns the nearest grid time and the shift in ms.

## 7. Holds, breath and silence

- **Breath:** at least one 2-3 s stretch where the viewer just sees (after the turn is ideal). Text-only beats are valid breaths.
- **Silence:** at least two per piece: one before the turn, one before the final hit or verdict. A silence can be total (music stops dead for a beat, a quarter-second before zero in a countdown) or near-total (room tone only). The first sound after the silence should be one of the most important.
- **The hold after the punchline/reveal** is as important as the cut into it (comedy and reveal: hold the reaction).
- **Nothing static > ~1 s** except planned reading holds, one comparison hold, one silence beat, the end card. Fill otherwise with a slow push (1.00 → 1.03-1.06), a rolling counter, a drawn line, a highlighter sweep, a new element.

## 8. Reading time

`hold = letters ÷ 15 + 1.5 s` (English/Latin) · `characters ÷ 4.5 + 1.5 s` (CJK). Hindi/Tamil: count letters, add ~20 %. The clock starts when the text is fully on screen. Round up. Exempt: counters mid-roll and axis tick labels.

Practical: ≤ 6-8 English words per caption in caption-first; ≤ 12 English words (≤ 23 CJK characters) per announcer line when subtitles must keep up. If the line is too long for its slot, shorten the words or split the caption; never shrink the type or cut early.

## 9. Hooks and endings

- **First 3 seconds:** an event. The biggest number lands in the first 0.15 s and rolls to its value; or a document headline highlighted in the first second; or a freeze on the event with the question; or the clock alone on black, then the first cell opens. No slow logo reveal before anything happens.
- **First 5 seconds earn the next 30**; **first 30 earn the rest**: check the retention logic of the plan, not only of the first shot.
- **Ending options:** bookend (back to the opening image, now re-read) · scale reveal · the character/subject does the thing right the second time · the final data point becomes the closing caption · back to the hook's number · hard stop then a quote. Avoid ending on a fade of energy; end on a button.

## 10. Tension curve template (30-90 s)

```
0-3 s    hook (event, loud)               | CPM high
3-15 s   setup, one new fact per shot     | medium, steady
15-30 s  build: acceleration, more layers | rising
~60 %    silence #1, then THE TURN        | stop, hit
60-85 %  explanation, each shot goes deeper | medium
~85 %    silence #2, verdict/peak         | drop out, heaviest hit
85-100 % button / echo of opening         | slow, hold
```

Adjust for length: for 15 s reels compress to hook / turn / button; for 5+ minutes repeat the build-turn cycle per section and make each section finish completely.

## 11. Checks to run

- `pacing_report.py`: overall CPM, per-window CPM, shot-length min/median/max, trend, flat windows, hook check, grid alignment.
- Compare to the plan: did the accelerations and brakes land where planned? Are the silences really silent (`silencedetect`)?
- Read-through: caption holds ≥ reading time (`editgrid.py read`).
- Watch with sound off, then with sound only (user): does the sound-off version still tell the story? Does the audio-only version still have a rhythm?
