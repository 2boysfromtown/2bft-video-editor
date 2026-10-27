---
name: comedy-editing-timing
description: How to edit comedy and funny videos - cut tempo for jokes, setup and punchline, where to hold or remove a pause, reaction shots and the reality-check cut, wide vs tight, the button, sound and music as comedic tools, visual gags, and writing the line itself. Use when the user wants a video made funnier, sketch or comedy edited, timing of a joke fixed, a punchline to land harder, or reaction shots, sound effects and music used for comedic effect.
---

# Comedy editing and timing

From working comedy editors and creators (sources below). Comedy is mostly timing, and in an edit, timing is what you keep, what you cut and where you hold. Pair with `video-editing-craft` for pace, `video-sound-and-music` for the sound layer, and `ffmpeg-edit-toolkit` to execute.

## Limits to state upfront

An AI editing agent can read a transcript with timestamps, measure pauses and level changes, and look at frames. It cannot hear the laugh or feel the beat. So: propose the edit and its reason, mark the joke candidates and the cut decisions, and ask the user to watch and judge. Do not claim a result is funny.

## The rules

1. **Faster is funnier, with intent.** Remove every unnecessary pause, stumble and "you know". Aim for a high jokes-per-minute rate, and raise the stakes and momentum as the scene goes. Speeding up for its own sake is not the point; pacing is.
2. **The enemy is the unnecessary pause.** A pause is allowed only when the pause is the joke (awkward silence, a held look, a comedian's deliberate beat). If you are not looking at the speaker, you control the dialogue: take out gaps and filler under a reaction shot.
3. **Fix the setup before blaming the punchline.** When a joke doesn't work, check the setup first: can the audience understand the situation without effort? Laughing and working out what is going on use different parts of the brain; if they are still figuring it out, they can't laugh. Give the setup room and clarity, then pay it off.
4. **Protect the A-jokes.** A few big laughs rooted in a situation between people are what people remember; many small quips aren't. Be willing to cut weaker jokes so the strong ones have space to land. Plot beats wordplay.
5. **Enter late, leave early.** Start the scene as late as it can and still work, end it at the biggest laugh. The funniest moment may be mid-scene in the footage, so end the scene there.
6. **The button.** The last, biggest laugh ends the scene or video. End on a high; a fizzling end is the most common failure. If an ending drifts away from the main joke, cut the extra.
7. **Feature every frame of the punchline.** Show it on camera in the best available shot, to the last frame: not from the side, not the back of a head, not in a wide that hides the face.
8. **Cut to the reaction.** The reaction is often the true punchline. Cut to it right after the line or the surprise, and hold it only as long as the beat needs: the hold length is the comic timing. Don't linger on the original action. An obviously forced overreaction undercuts the joke.
9. **Wide for funny, tight for feeling.** Wider shots show body language and awkward interaction; cut tight for serious emotion.
10. **Reality check.** Alternate the insane situation with a straight-faced reaction (a "straight man") or a pull-back to a wider shot. Without it you get "a hat on a hat": an odd thing on top of an odd thing, and the viewer doesn't know where to look. Comedy, like horror, needs contrast and surprise.
11. **Set a clean world first.** Establish a believable, even high-stakes style (a parodied TV-drama look, serious music, shallow depth of field), so the silly break stands out against it. Paint on a clean surface.
12. **Say "yes, and" in the edit room.** Try the idea before judging it; combine takes; don't reject a version before you've cut it.
13. **Real honesty is funny.** Look for the true moment in a performance (usually the eyes), and keep takes where the performer is connected, not waiting for their cue. Often the line improvised on the day beats the scripted one: do the scripted takes, then a free one.
14. **Test on a fresh pair of eyes.** After many viewings you stop laughing and only analyse. Screen it to someone and watch their reaction (screen-record the reviewer's face if they review remotely).

## Sound and music as comedy tools

- **Guide focus.** The sound decides what the viewer pays attention to. Strip music and effects away when the joke arrives; cut the music out when someone does something they shouldn't.
- **Time effects to actions.** Add sound effects where the camera audio is weak (scrubbing dishes) and sync to the motion. A tiny sound on a visual detail (a knife "shing") draws the eye there.
- **Motifs.** Give a character a musical cue each time they appear, and use classical or dramatic music for villains or serious tone before breaking it.
- **Sense of space.** A whoosh or a stretched shot can show where something is (the door is far away); a long, slow entrance can be funnier than a quick one. Muffle a voice with high-pass and low-pass filters for "other side of the door", and cut the effect as soon as the speaker is in the room.
- **Anthropomorphise.** A human scream or an animal sound under an object tells the audience a history without words.
- **Same cue, take two.** Repeat the exact sound for a deliberately restarted "bad take" gag.
- **Silence is a tool.** Hold the quiet before a punchline only if the silence itself is the setup.

## Visual gags (staging)

Things entering the frame, leaving the frame, there-and-back-again, matched scene transitions, a perfectly timed sound effect, action synced to music, dramatic lighting cues, fence gags. A joke can come from picture and sound alone: a travel montage, a TV in the background that foreshadows, a pan, a zoom, a crane. When a scene is just people in close-ups talking, ask what the frame could do instead.

## Writing or fixing the line itself

- A joke is a setup that establishes a premise and a punchline that breaks the expectation while still fitting the premise. To generate options, name the audience's expectation, then break it in different ways; the best break also keeps the premise true.
- Close the loop on the setup before the punchline, or the audience is still working on the previous sentence.
- **Commit to delivery.** Hesitation tells the audience you don't believe it.
- **Specific beats general** (a four-door model and a stated angle beats "my car"), and cadence matters: precision of writing with the fluency of speech.
- No subject is off limits if the joke is funnier than it is offensive; you can't laugh and be offended at the same time.

## Process

1. Transcribe (`transcribe-local`) and list each setup/punchline pair with its timestamps.
2. Mark every pause longer than needed; cut or tighten (`remove_silence.py` for a first pass, then by hand around jokes).
3. For each punchline: is the best shot on it? is there a reaction to cut to? what is the hold length?
4. Find the button and the entry point; trim the scene to them.
5. Sound pass: remove effects at the joke, add effects at actions, check the motif.
6. Ask the user to watch the cut and mark the beats that did not land. Revise those only.

## Sources (paraphrased, not quoted)

- Digital Spaghetti with Daniel Thrasher, "Daniel Thrasher's Secrets to Editing Comedy", https://www.youtube.com/watch?v=sbUrWuyJ43Q
- This Guy Edits with Roger Nygard, "You'll Never Edit an Unfunny Film Again", https://www.youtube.com/watch?v=W1Mafk58zS0
- Every Frame a Painting, "Edgar Wright - How to Do Visual Comedy", https://www.youtube.com/watch?v=3FOzD4Sfgag
- Casually Explained, "Getting a Laugh: How to Make Something Funny", https://www.youtube.com/watch?v=QGj15uvuPLA
