# Easing and timing recipes for video graphics

**Where the numbers come from.** The principles and the quoted overshoot values (about 110% scale-in, elastic 120% decaying) come from the tutorials listed in `SKILL.md`. The frame counts and bezier values below are my starting defaults for 30 fps video, not figures from the videos. Adjust by eye against the voice and music, and say so when you use them.

At 60 fps double the frame counts. Convert seconds to frames with `frames = seconds * fps`.

## Starting values (30 fps)

| Motion | Duration | Easing | Notes |
|---|---|---|---|
| Title / headline enters | 12-18 frames (0.4-0.6 s) | steep ease-out | Slide 40-80 px or reveal through a mask |
| Lower third / label enters | 9-12 frames | ease-out | Stagger text 3-4 frames behind its bar |
| Exit | 6-9 frames | ease-in | Leave faster than you arrive |
| Emphasis pop (callout, number) | 10-14 frames | overshoot to ~110%, settle | One hero element only |
| Word-by-word kinetic type | 6-10 frames per word | steep ease-out | Land on the spoken word's timestamp |
| Anticipation before a big move | 3-6 frames back, then go | ease-in-out | Longer for a dramatic slingshot |
| Stagger between elements | 2-4 frames offset | same easing for all | Lockstep motion looks mechanical |
| Hold before exit | read time x 2 | n/a | Short phrases: at least 1 s |
| Camera-style move on text (3D null) | 20-40 frames | steep ease in-out | Same curve for every move |

## Bezier starting points (CSS / Remotion)

| Feel | cubic-bezier |
|---|---|
| Steep ease-out (entrances, reveals) | `0.16, 1, 0.3, 1` |
| Ease-in (exits) | `0.7, 0, 0.84, 0` |
| Ease in-out (move between two points) | `0.65, 0, 0.35, 1` |
| Slight overshoot (back-out) | `0.34, 1.56, 0.64, 1` |

## Remotion

```tsx
import {interpolate, spring, Easing, useCurrentFrame, useVideoConfig} from 'remotion';

const frame = useCurrentFrame();
const {fps} = useVideoConfig();

// Entrance: slide up 60 px and fade in over 15 frames, starting at frame 30
const t = interpolate(frame, [30, 45], [0, 1], {
  easing: Easing.bezier(0.16, 1, 0.3, 1),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
const style = {opacity: t, transform: `translateY(${(1 - t) * 60}px)`};

// Overshoot pop: a spring that overshoots slightly and settles
const pop = spring({frame: frame - 30, fps, config: {damping: 12, stiffness: 160, mass: 0.8}});
// scale: pop (goes slightly past 1, then settles)

// Anticipation: pull back before the move (negative first, then past the target)
const x = interpolate(frame, [30, 36, 48], [0, -24, 400], {
  easing: Easing.bezier(0.65, 0, 0.35, 1),
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

Verified against the Remotion docs: `spring({frame, fps, config: {mass, damping, stiffness, overshootClamping}, delay, durationInFrames})`, and `interpolate(frame, input, output, {easing, extrapolateLeft, extrapolateRight})` with `Easing.bezier(x1, y1, x2, y2)`. Lower `damping` or higher `stiffness` means more bounce. For the full API see the Remotion docs.

Time word animations from the transcript:

```tsx
// words: [{text, startSec}] from transcribe-local
words.map((w) => {
  const start = Math.round(w.startSec * fps);
  const t = interpolate(frame, [start - 2, start + 6], [0, 1], {easing: Easing.bezier(0.16, 1, 0.3, 1), extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // ...use t for opacity / translate
});
```

Land the animation a couple of frames before the word is spoken so the eye is there when the ear hears it.

## GSAP

```js
gsap.from('.title', {y: 60, opacity: 0, duration: 0.5, ease: 'power4.out'});          // steep ease-out entrance
gsap.to('.title',   {y: -30, opacity: 0, duration: 0.25, ease: 'power2.in'});           // exit
gsap.from('.badge', {scale: 0, duration: 0.45, ease: 'back.out(1.7)'});                 // overshoot pop
gsap.from('.dot',   {scale: 0, duration: 0.8, ease: 'elastic.out(1, 0.4)'});            // elastic (use once)
gsap.from('.item',  {y: 30, opacity: 0, duration: 0.4, ease: 'power3.out', stagger: 0.1}); // stagger
```

Sequence with `gsap.timeline()` and the position parameter (see the GSAP timeline docs). GSAP drives web animation; for rendered video, drive it from Remotion's frame or use Remotion's own helpers.

## CSS

```css
.title { animation: in 500ms cubic-bezier(0.16, 1, 0.3, 1) both; }
@keyframes in { from { opacity: 0; transform: translateY(60px); } to { opacity: 1; transform: none; } }
```

## After Effects habits (when the user works there)

- Separate dimensions on position when a move is along one axis, so the value graph is readable.
- Select keyframes, F9 (easy ease), then pull the handles to make the curve steeper.
- Add anticipation by copying the first keyframe a few frames earlier and nudging it the opposite way; or lift one handle so the curve dips first.
- Roving keyframes plus time remapping give smooth path motion with hang time at chosen points.
- Preview at full speed with the voiceover on; slow previews hide timing problems.

## Check before you hand it over

- [ ] Anticipation, peak and settle frames each look right when exported as stills
- [ ] No element moves with a different easing family than its neighbours
- [ ] Text is readable at phone size and stays inside the safe area
- [ ] Each entrance has a sound or a reason for being silent
- [ ] Nothing animates just because it can
