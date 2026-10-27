---
name: video-editing-craft
description: How to edit a video so it holds attention - pacing and tempo design, cuts per minute, when to cut fast or slow, A-roll vs B-roll vs graphics rhythm, punch-in zooms and highlights, invisible continuity, the cut vocabulary (jump, J, L, match, smash, cutaway) and editing habits. Use when the user wants a video edited, tightened, made punchier or more engaging, asks why an edit feels flat or slow, wants a rough cut reviewed, or asks how to pace, cut or structure a video for YouTube, Shorts, Reels or TikTok.
---

# Video editing craft

Learned from tutorials by working editors (sources at the bottom) and turned into decisions you can apply to a real timeline. Use with `ffmpeg-edit-toolkit` to carry the decisions out, and with `comedy-editing-timing`, `video-sound-and-music` and `motion-graphics-for-video` for those layers.

## 1. Decide the experience before any cut

Every edit choice serves one experience, and a choice that fights it loses viewers even if it is "better editing".

| The viewer came for | Edit like this | Avoid |
|---|---|---|
| Hanging out with someone (vlog, talk, podcast cut) | Remove dead parts only; long takes are fine (one example channel averaged about 90 seconds between cuts); keep it authentic | Flashy animation, rapid cuts that break the intimacy |
| Entertainment (challenge, comedy, explainer, shorts) | Remove every pause; change what is on screen every few seconds; sound and graphics on every beat | Long static A-roll |
| Learning something | Clear B-roll or graphics for each claim, pace set by the explanation, calm music | Visual noise that competes with the lesson |

Ask which one if it is not obvious. When unsure, favour what the footage can honestly support.

## 2. Design tempo, don't let it happen

- **Variation is the product.** A video at one constant speed feels either relentless or dull. Plan fast and slow stretches like a roller coaster: where is the slow climb, where is the drop.
- **Start from the emotion, then pick the pace.** Reflective, tender or heavy moment: cut slower so it lands. Tense, rushed or exciting: cut faster. Write the emotional destination of each section first.
- **Measure it.** Cuts per minute (CPM) is the editor's speedometer: count the cuts in a 30-60 s sample and scale. One worked example went from about 10 CPM to about 33 CPM when a chase began. Change tempo at story change points: more energy needed, raise CPM; more introspection, lower it. Never change it at random, because random pace changes read as amateur.
- **Ask five questions per scene:** does it have one overall tempo, what is it, does it change, where, and why.
- **Four things set perceived pace, and they add up:** how fast the cuts are; how much movement is in the frame; how close the subject is (tight and busy feels faster than wide); how much the camera moves. Lots of cuts plus whip pans plus close-ups is much faster than cuts alone. To slow a scene, change any of them, not just the cut count.
- **Exercise:** cut a scene at the intended tempo, duplicate it, and cut the opposite tempo. Compare. Then try changing tempo mid-scene for a reason.
- **Speed contrast** works inside a clip too: ramp 400-800% fast sections against normal speed. Film at 60 fps if you may want 50% slow motion that still looks smooth.
- Short-form is simple and fast; long-form is varied and complex. Don't paste short-form tempo onto a 20-minute video.

## 3. Keep the picture changing, without turning to mush

- **A-roll** (you see and hear the speaker) feels personal and holds attention; use it for short stretches and the most important statements, spoken with confidence.
- **B-roll** shows what the words describe, explains faster than a face does, and is more interesting than A-roll: use as much as the story supports. Stock footage is the lazy version; **motion graphics** are the strongest B-roll for anything abstract or complicated.
- **Switch what is on screen every few seconds** when the goal is engagement. But do not shorten shots just to shorten them: a 10-second shot is fine if it is interesting for 10 seconds.
- **Add life without a new clip:** slow scale or position drift on stills; an abrupt punch-in on the line that matters (see the zoom recipe); a tiny shake only if it suits the style.
- **Guide the eye in an image or screen:** animate or underline the key text, darken or blur the surroundings, circle or arrow it, tint it (red reads as negative, yellow or green as positive), make the subject glow.
- **Captions** only to stress words or fill genuinely empty visual space; three words or fewer at a time; don't use them as filler.
- **Voiceover beats on-camera explaining** for facts: one example condensed a long explanation to 23 seconds of voiceover; it felt like information, not a lecture. Keep sections of a multi-part video to a few minutes each.

## 4. Make the edit invisible, then break it on purpose

- **Where the eye is at the end of shot A should be where it is at the start of shot B.** Cutting from eyes at one side of the frame to a subject at the other makes the viewer refocus and breaks immersion.
- **A graphic should not just appear.** Move it in, or cover the arrival with a sound effect (pop, shutter, whoosh).
- **Use a full-screen transition** to hide a cut when shots can't be matched.
- **Deliberately break continuity** now and then (a smash cut, an abrupt music stop): the jolt wakes attention. It only works against a smooth baseline.
- Transitions: simple beats flashy. Reserve effects for moments where they mean something.

## 5. Habits that save the edit

- Finish each section completely (cut, graphics, sound, colour) before starting the next; "70% of everything, then a second pass" costs more time.
- Perfection doesn't exist; from about 90% to 100% is ego. Details only you and a few peers will notice are permitted.
- Trim the dead start: viewers decide within the first seconds. Open on the strongest moment or the question.
- End on a high, not a fade-out of energy.
- Watch for a flat edit: usually it has no tempo change, no sound design, and the same kind of shot too long.

## Review checklist

- [ ] Experience chosen and every choice serves it
- [ ] Emotional destination per section; tempo matches it; tempo changes have reasons
- [ ] CPM measured before and after (state both)
- [ ] Nothing on screen unchanged for longer than it earns
- [ ] Eye-trace across cuts; graphics enter with motion or sound
- [ ] First 5 seconds earn the next 30; ending lands
- [ ] Sound pass done (see `video-sound-and-music`)

## More

- Cut-by-cut guide with when to use each: `references/cut-vocabulary.md`
- Comedy: `comedy-editing-timing`. Sound and music: `video-sound-and-music`. Graphics: `motion-graphics-for-video`. Commands: `ffmpeg-edit-toolkit`.

## Sources (paraphrased, not quoted)

- Inside The Edit, "Pacing in Film Editing: Techniques Every High-End Editor Must Know", https://www.youtube.com/watch?v=CdyTIng0M8Q
- Austen Menges, "How PRO Video Editors Change RHYTHM For EMOTION", https://www.youtube.com/watch?v=jY6hT8-SR3g
- Learn By Leo, "How to edit SO good your viewers get addicted to your videos", https://www.youtube.com/watch?v=sLgHqZSe2o0
- Digital Spaghetti, "Doobydobap's Editing Hacks to Improve Your Pacing", https://www.youtube.com/watch?v=fH_6iL2EmHM
- Shutterstock Tutorials, "9 Cuts Every Video Editor Should Know", https://www.youtube.com/watch?v=Wv3Hmf2Dxlo
- Jonny Duncan, "10 Editing Cuts Every Video Editor Should Know", https://www.youtube.com/watch?v=YtULPT1aBWM
