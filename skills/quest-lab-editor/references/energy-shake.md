# Energy-reactive camera — "when I'm energetic, the video shakes"

The host asked for the picture to shake when he is energetic. The rule that keeps it professional: **effects confirm energy that is already in the performance; they never invent it.** So the shake is measured, not sprinkled.

## 1. Measuring energy (`engine/tools/energy.py`)
Per output frame (30 fps) over the whole recording:
| signal | how | why |
|---|---|---|
| loud | short-term voice RMS (dB) vs a rolling 30 s median, robust z (MAD floor 2 dB) | shouting, emphasis |
| pitch | YIN F0 in semitones vs a rolling baseline over voiced frames only (floor 1 st) | excitement raises pitch |
| flux | spectral flux / onset strength, robust z | bursts, laughs, slams |
| move | webcam crop frame difference with each frame's mean removed (light-colour changes don't count), z capped at 4 (leaving the chair isn't energy) | gestures, leaning in |
| words | exclamations from the transcript in English and Devanagari ("let's go", "oh my god", "wow", "beautiful", "bhai", "dekho", लेट्स गो, ओ माय गॉड, भाई…) | the words he uses when hyped |
`energy = 0.38·loud + 0.22·pitch + 0.12·flux + 0.20·move` (only while speaking) `+ 0.35·words`, smoothed 0.25 s, normalised so 0 = calm talking, 1 = clearly energetic, 2+ = peak (relative to that recording). Peaks above 0.85 with prominence ≥ 0.35 become events: **impact** ≥ 1.9, **shake** ≥ 1.2, else rumble. `tools/peaks.py energy.json 40` lists the strongest; read them against the transcript before trusting them (playback audio from videos on his screen can fake energy).

## 2. Turning energy into camera (`build.py camera_track`)
| level | trigger | motion | extras |
|---|---|---|---|
| hum | energy ≥ ~0.8 sustained ≥ 1.5 s (min-filter), face layouts only | ≤ 4 px, 1–4 Hz smooth sines, ≤ 0.2° | none |
| shake (L3) | measured shake event or manual `punch` 'shake' | 9–16 px (scaled by peak), 7–19 Hz noise, rotation ≈ 0.045°/px, attack 40 ms, decay τ 0.22 s | — |
| impact (L4) | the strongest measured peaks (max 2 auto per piece) or manual 'impact' | **3-frame hit-stop** (the impact frame holds), then 30 px shake, τ 0.32 s, zoom kick +10 % decaying 0.45 s | RGB split 7 px for 3 frames, 1.5-frame flash at 22 %, `impact` SFX |
| zoom punch | manual 'zoom' on a punchline | +9 % snap in 30 ms, decay 0.5 s | `punch` SFX |
Motion is smooth noise (summed sines with seeded phases), never per-frame random. Only the **footage layer** moves; HUD and captions stay still except on impact frames (35 % of the motion) and the impact word.

## 3. Budget and taste
- Visible shake (> 3 px) ≤ **5 %** of a long video, ≤ **10 %** of a Short (the build scales everything down if exceeded and prints `shake_share`).
- ≥ 3 s between shake/impact hits (manual hits win, then stronger peaks). ≤ 2 auto impacts per piece; the biggest effect goes on the biggest moment.
- Shake 0 on: screen-reading shots (typecards, code, UI), outputs (renders, episodes), versus cards, time-lapses, serious or devotional lines (Leela's Gita lines, the attention-span moral).
- Flash safety: ≤ 3 flashes in any second; no red strobe.
- When it gets cheap (remove it): an effect on almost every sentence; no trigger in the audio/gesture; it shakes text being read; it fights the music grid; it sits on a quiet/serious beat; the same effect at the same strength three times in a row.
- Starting values from game feel (Eiserloh's trauma model, Vlambeer) scaled down for video: video needs shorter decay and much less rotation so faces and text stay readable.
