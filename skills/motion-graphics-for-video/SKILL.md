---
name: motion-graphics-for-video
description: How to design motion graphics, animated text and kinetic typography for video so they feel professional - timing and spacing, easing, anticipation, overshoot, weight, follow-through, staging and eye-tracing, kinetic type synced to voiceover, and 3D camera-style text moves. Includes frame-based starting values for 30 fps video and Remotion, GSAP and CSS equivalents. Use when adding titles, lower thirds, animated captions, callouts, explainer graphics or transitions to a video, or when an animation feels stiff, robotic or too busy. Not for UI or web micro-interactions.
---

# Motion graphics for video

Animation principles from motion designers, translated into decisions you can type into Remotion, GSAP, CSS or After Effects. For building the animation in code use Remotion or GSAP (their own Claude skills help if installed); for text behind a speaker and karaoke captions use `talking-head-polish`; for the sound that sells it use `video-sound-and-music`; for where graphics belong in the edit use `video-editing-craft`. Numbers and code in `references/easing-and-timing-recipes.md`.

## Why graphics at all

Motion graphics explain complicated or abstract things faster than a face or ordinary B-roll can, and they add visual variety without a new camera shot. They only help if they are readable, motivated and in tune with the voice and music.

## The principles that matter most in video

1. **Timing and spacing.** Timing is how long a move takes (frames A to B). Spacing is how far it travels each frame. The same distance at 24, 12 and 6 fps looks smooth, choppy and very choppy; spacing is what easing edits. If a move feels wrong, check these first.
2. **Easing.** Linear motion looks robotic. Ease-out (fast then settling) suits things entering; ease-in (slow then accelerating) suits things leaving; ease both ends for moves between two points. Make the curve noticeably steep: a gentle default ease barely reads. In After Effects work in the value graph to see the shape; use the speed graph for the feel.
3. **Anticipation.** A small move opposite to the main move, before it. It signals "something is about to happen", tells the viewer how much energy is coming, and draws the eye to the spot ("eye tracing"). It reads even when tiny: three hold poses with one pose slightly backwards is enough. It can last longer than the main move (up to about three times) for a dramatic slingshot; keep a little drift in the hold so it doesn't freeze. It need not be on the same property: anticipate a slide with a small rotation or scale.
4. **Overshoot and settle.** Go past the target (about 110% for a scale-in is a common value), then settle. Elastic bounces use decaying overshoots (for instance 120%, then smaller) spaced a few frames apart. Don't wobble everything: use it on one hero element.
5. **Weight.** Light things are snappy and bouncy; heavy things move slower, squash more, bounce less. A falling object accelerates, hits with impact, and does not slow down before the ground.
6. **Arcs.** Almost nothing natural moves in a straight line; curve the path.
7. **Follow-through and overlap.** Nothing stops all at once: secondary parts drag, overshoot, or arrive a few frames later than the main shape. Stagger multiple elements instead of moving them in lockstep.
8. **Secondary animation.** One motion triggers another (a card lands, its icon bounces).
9. **Squash and stretch.** Keep it tight; used too much it looks out of place.
10. **Staging and appeal.** Move only what the viewer should look at, and make that thing look good: colour, glow, clean shapes, a consistent rhythm. If everything moves, nothing is seen.

## Kinetic typography

- **Reveal with a mask.** Put the word in a mask (or clip the container) and slide it in from outside the mask, easing steeply. It reads as clean and cinematic.
- **Sync to the voice.** Each word's animation should land on the spoken word. A fast word gets a quick animation, a slow word a slower one. Animate against the transcript timestamps (`transcribe-local`).
- **Camera-style moves.** In After Effects, make the text layers 3D and parent them to a 3D null; animate the null's position, rotation and scale to move a "camera" through the words. Use the same strong easing for each move; hold on the key word.
- **Vary scale and colour for emphasis,** not decoration; one dark or accent word per line.
- **Anchor points matter:** set the anchor where the word should scale or rotate from.
- Length: let each beat breathe; for fast speech keep each word on screen only as long as it takes to read.

## Rules for graphics in an edit

- Enter with motion or a sound; never pop in silently without a reason.
- Don't hold a graphic longer than it takes to read it twice.
- Place graphics where the viewer is already looking at the end of the previous shot (eye-trace), and keep text inside the safe area.
- One idea per graphic.
- Match motion to tempo: fast, small and snappy in a fast section; slower, bigger and softer in a reflective one.
- Brand: if the project has brand notes (colours, fonts, motion rules), read them first.

## Process

1. List each graphic with its purpose (explain, emphasise, label, transition) and its start/end time in the edit.
2. Choose the motion for each from the table in the reference file; keep the set consistent.
3. Build; render frames or a short clip; check frames at the start, peak and end of each move (anticipation, overshoot, settle) and read the text at the size it will be viewed.
4. Add the matching sound at each graphic's peak.
5. Overlay on the edit (Remotion composition, or ffmpeg `overlay`) and re-check against the voice.

## Sources (paraphrased, not quoted)

- Joshua Craigie, "10 Motion Design Principles Every Animator Needs", https://www.youtube.com/watch?v=Cz-GcIITNrs
- Ben Marriott, "The #1 Skill All Animators Need" (anticipation), https://www.youtube.com/watch?v=LcWJKYbYvi8
- MotionXP, "After Effects Easing...like a pro", https://www.youtube.com/watch?v=HpVtzOtaHlg
- Skillshare / Emanuele Colombo, "The 12 Principles of Animation", https://www.youtube.com/watch?v=EqMi1AzbFqs
- Motion Nations, "Typography Motion Graphics Animation in After Effects", https://www.youtube.com/watch?v=UahA-6QYfC0
