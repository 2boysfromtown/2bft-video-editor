# Motion across cuts, zoom grammar, and what makes an edit look generated

Merged 27 Oct 2026 (sources at the end). Extends `STYLE.md` §5 and `director-editor-mind.md` §5–6; where they agree, those files stay the reference. Numbers are starting values for 30 fps.

## 1. Carry motion across a cut (the seam law)
- The incoming move keeps the outgoing move's **axis and direction** (x stays x, zoom stays zoom) — never mirror it.
- Match speed with mirrored eases: accelerate out of the cut (ease-in), decelerate into the next shot (ease-out).
- **Cut mid-motion:** the exit is still moving at the cut; the entry is already ≥ 50 % along its path. A move that settles before the cut, or a new one that starts from rest after it, makes a dead beat.
- The most common violation: a shrinking exit followed by a grow-from-small entry.
- The best seams pass a **physical carrier** across the cut — the cursor mid-path, a card docking into the next layout, a sticker flying into the next scene, a whip whose blur matches the incoming push.
- No crossfades between scenes (nothing carries across them) — matches STYLE.md's "no dissolves except into/out of black".

## 2. One direction, reserved meanings
One dominant direction for ordinary transitions within a piece (STYLE.md already says enter from one side consistently). Reserve:
- **upward** for a conclusion or reveal;
- **zoom forward** for "deeper into the same thought" (into the screen, into a detail);
- **zoom back** for "something big arrives" (the render, the full temple).
Change direction only with a visible cause (a click, an impact) or at a LEVEL card. No back-and-forth flips.

## 3. No idle wobble
Breathing, floating or pulsing loops on titles, stickers or HUD are filler — banned. A title that has landed stays perfectly still. **Pause test:** at any second something *meaningful* is in motion (his face counts). Any single treatment goes stale after ~6 s; a static card after ~8 s; past ~15 s a card needs a staged reveal.

## 4. Timing numbers
- Exits 40–50 % shorter than entries (STYLE.md: in 8–12 frames, out 6–8 — consistent).
- The next element starts when the previous one is 30–50 % done.
- Stagger: words 60–120 ms, list items 40–80 ms, whole stagger ≤ 500 ms.
- Overshoot (back-out 1.4–1.7) is fine; no bounce/elastic on UI. Spring damping 0.7–0.85 reads premium, 0.4–0.6 playful — QUEST LAB stickers sit near 0.6, typography and HUD near 0.8.
- **Reading hold** = 0.5 s + 0.3 s per word; the last line of a film holds ≥ 2 s.
- Card density (cards, typecards, stamps): one per 6–8 s under 1 min, 8–12 s up to 3 min, 12–20 s up to 10 min.
- Never animate both a caption group and its words' opacity — the opacities multiply into a visible pop.

## 5. Beat-grid maths (music-cut moments)
- Frame of beat k = round(k × fps × 60 / BPM) — compute each one; never add rounded intervals (at 128 BPM / 30 fps that drifts ~2 frames in 32 beats).
- A move that must land *on* a hit starts 40–190 ms early; a reaction starts 0–45 ms after; the hit itself is an instant set, never eased.
- On calm music, beat trackers invent a grid — cut on phrase and energy changes instead (`music/scan.json` drops are the anchors).

## 6. Transitions with a cause (3–5 types per film)
Each is triggered by something visible:
- **Dip cut:** darken the outgoing frame ~40 % over 3 frames, then hard cut — makes a long-form section change feel deliberate without a full LEVEL card.
- **Zoom through a button / UI element:** scale it from ~8 % to 250 % in ~0.35 s with a strong ease-in, land in the next scene.
- **Iris from the click point:** open onto the next scene from where he clicked, ~0.15 s.
- **Colour flood:** the background changes in ~0.4 s while the hero object stays put.
- Plus our own: LEVEL card (chapters), whip (fast jumps), glitch (machine moments only).

## 7. Zoom grammar (extends the two-size system)
- **Punch** on one stressed word: 1.18–1.30×, hard in and out (no ramp — ramps read as creeping), hold 0.2–0.5 s. Place it ~0.05 s (1–2 frames) before the word. Engine: `'punch': [(src_t, 'zoom', strength)]` or a camrect swap.
- **Ratchet** on a list of 2–4 items: each item steps up (1.12 → 1.18 → 1.24 → 1.28), then hard-cut back to 1.0 after the last. Engine: consecutive shots on the item onsets with tightening `camrect`s, or several `punch` zooms with rising strength.
- **Ken Burns** on the thesis line only: a slow push to 1.10–1.14× over the whole line — the only eased zoom.
- Most of the clip stays at 1.0× so the punches land. Default focal point slightly above centre of the face (eyes at ~0.42 of the height). Overlapping zoom events take the max, so a release never snaps down mid-word.
- **Resolution cap:** the 25 Oct webcam is only 388×765 px of the 1080p canvas, so the `v_face` card already shows it ~2.5× enlarged (the renderer sharpens above 1.55×). Extra punch on top goes soft fast — keep face punches ≤ 1.2× there, and say so in the next-stream notes (record the webcam larger or as its own file if Meld allows; record the scene at 1440p/4K).
- Screen zooms: code 1.5–2.0×, terminal 1.5×, one UI element 2.0–2.5×; hold each zoom position ≥ 3 s before panning; a 1.0 → 1.02 shift hides a jump cut inside a continuous screen shot.

## 8. Text behind the speaker (a new caption treatment — not in the engine yet)
The big word sits behind his head: footage → word → a person cut-out from a matte, all three moving with one shared transform so shake and punch keep them locked. Aim for 30–55 % of the word hidden (< 15 % looks like it floats, > 65 % is unreadable), measured against the matte over the caption's own time window. Matte models drop mic arms and flicker on headphones — check every frame. One per beat at most, never two in a row; a natural L3/L4 option on the caption ladder for a hook word. Needs a person-segmentation model (e.g. MediaPipe selfie segmentation) — ask the user before installing anything.

## 9. Contrast from measured brightness
Measure the brightness (0–255) behind a caption: < 60 a light treatment is fine; 60–180 needs the ink stroke + shadow; > 180 use an opaque plate. Plain subtitles over brightness > 60 get a 30–40 % scrim sized to the text, never a full-width bar. Flag any text smaller than 2.6 % of the frame's short side (~28 px at 1080 wide) and any line on screen for less than its reading time (§4).

## 10. Mapping feedback to one change
"Too fast" → slow only zooms and pans to ~0.7×, keep the cuts. "Feels like slides" → enter the next scene through an on-screen object and cut mid-move. "Titles move too much" → let them land, then hold still. "Busy" → remove about a third of the motion, keeping the moves that guide the eye. "Flat" → find the turn and give it the one native move; don't add effects everywhere.

## 11. Banned "generated-looking" defaults
Everything fades and slides up · every scene enters the same way · click rings on every click · slow creeping scale on a title · floating cards standing in for a real layout · idle wobble · a whoosh on every cut · the same caption pop on every chunk. Keep a project `BANNED:` line in `EDIT-PLAN.md`, add each new one the moment it appears, and check renders against it.

## Sources (ideas re-derived; licences checked 27 Oct 2026)
heygen-com/hyperframes skills — motion.md, film.md, overlays.md, captions.md, motion-doctrine and seam-gate (Apache-2.0) · louisedesadeleer/add-zooms (MIT) — punch / ratchet / Ken Burns, quality cap · OpenMontage screen-recording.md (AGPL — ideas only) — zoom targets, holds, jump-cut shift.
