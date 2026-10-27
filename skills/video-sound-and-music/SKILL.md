---
name: video-sound-and-music
description: Sound design and music for video edits - the voice cleanup chain, sound effects (whooshes, risers, hits, ambience), layering, placing effects on the beat of the picture, choosing and fitting music, carving space for dialogue, ducking, music transitions and endings, panning, silence, and final loudness. Use when the user wants music or sound effects added to a video, a mix fixed, audio to sound professional, a track cut to length, beats synced to cuts, or the video to feel more immersive or emotional.
---

# Video sound and music

Sound is half of the edit and the half most editors skip. Work in three passes, in this order: **voice, sound effects, music**. Sources at the bottom; commands are in `ffmpeg-edit-toolkit/references/recipes.md`.

## Limits to state upfront

An AI agent can measure level, loudness and frequency balance and can generate or place sounds, but it cannot listen. Do the measurable parts, say what was changed and why, and ask the user to listen on laptop speakers, phone and headphones before calling it done.

## Pass 1: Voice (the foundation)

If the voice sounds bad the video is less engaging, whatever else is done. The same chain, in the same order, each time:

1. Subtle denoise (a heavy one makes speech watery); a gate to drop what's below a threshold if the room is noisy.
2. EQ: cut rumble below about 80 Hz and hiss above about 12-16 kHz (human voice lives between roughly 80 Hz and 12 kHz).
3. Gentle shaping EQ for warmth or clarity (a vocal preset, dialled back to subtle).
4. Compression to even out volume: threshold near the quieter parts of the voice (about -20 dB in the example), ratio about 2:1, make up the gain.
5. De-esser to soften harsh S sounds.
6. Limiter so peaks never clip.

## Pass 2: Sound effects

Order of layers: **ambience first**, then real-world effects and Foley, then creative effects.

- **Ambience** (wind, water, room tone, traffic, distant voices, a drone) grounds the scene. Keep it low: nobody notices it present, everybody notices it missing. Cross-fade it with J-cuts and L-cuts so scenes flow.
- **Real-world effects and Foley** for what would make a sound on screen (footsteps, a door). Record or source them to sync with the action; camera audio often isn't enough.
- **Creative effects**: *whooshes* make cuts, transitions and movement feel intentional; *risers* build anticipation (use only before something that deserves it, or they lose their power); *hits* release tension and mark a moment (alone or after a riser); *drones* add suspense and mood. Don't put a sound on every second: punctuate the moments that matter.

Shape each effect in five steps:

1. **Source** it (a consistent pack beats a random mix; commit to a style so gritty bass hits don't sit in a clean corporate video).
2. **Hone** it: pitch down for weight or up for snap; speed changes pitch and length; high-pass and low-pass to fit the space. One sound makes three: cut a whoosh at its peak for an impact, reverse it for a riser.
3. **Amplify by layering across frequencies.** A single whoosh is thin because it sits in one band. Add a copy pitched lower and another higher (or a different sound in another range) so the sound fills the spectrum. Think of cake layers.
4. **Place it.** Put the loudest moment of the sound on the exact frame of the loudest visual moment (the peak of a camera shake, the end of a swipe). Tens of milliseconds matter; this is the pro/amateur difference.
5. **Fix the environment.** Add diegetic ambience under it so the scene feels real. Use reverb for space (a small room needs little, a church a lot, distance needs more) and EQ to carve room under the voice.

**Emotional realism:** sound doesn't have to match the picture literally. Replacing a coffee-making sound with nature sounds (ice cracking, an ocean) can make the visuals mean more. Decide what the audience should feel, then pick the sound.

**Silence** is a sound. A quiet moment makes the return of sound or music hit harder; an abrupt music stop jolts attention and spotlights what follows.

**Pan** a sound to follow movement across the screen (left to right as the object moves). Subtle panning makes a soundscape more real.

## Pass 3: Music

- **Choose by emotion first.** What should the viewer feel? Search around that feeling ("ambient synth pads" for a fond memory) instead of browsing. Match the mood to each section; changing the track between sections can mark a topic shift. For documentary and educational voiceover, marimba and pizzicato strings are common: they sit away from the voice's frequencies and stay emotionally neutral.
- **Picking before shooting** can set energy and shape how you film.
- **Make space for the voice.** Don't only turn the music down: also cut the music's mid frequencies where the voice sits (EQ pocket), then duck the music a few dB while the voice plays. In tests, ducking of about 6-10 dB sounded controlled; 16 dB pumped.
- **Use a music sub-bus:** route every music track to one track so a single EQ and volume control covers all music.
- **Sync to the story.** Place music hits and builds on structural moments (the problem to solution shift, the reveal). If the track comes in stems, mute a distracting instrument.
- **Length.** To fit a long track to a short video, cut at phrase boundaries, use remix tools, or build a shorter arrangement; never chop mid-beat.
- **Getting in:** reverse the first beat (or the tail of a section) as a riser into the track; layer a riser, swell or suck-back under it. A quick volume fade between the two tracks hides the join.
- **Getting out:** cut before the next beat, add a long reverb or echo tail to the final beat (increase decay and wet), fade the dry original underneath; hit it with an impact on the last beat to end with a bang, or pull everything out into silence to emphasise a quiet moment.
- **Tension with fade:** a slow fade-out signals that a segment is closing and primes anticipation.

## Final mix

- Nothing clipping; levels consistent through the video; voice always clear.
- Loudness: normalise the whole mix (about -14 LUFS integrated, true peak -1.5 dB is a common streaming target; check the platform's current guidance).
- Listen on several speakers. Reduce the mix before it clips the master rather than leaving it in the red.
- Sometimes one or two layers are all a scene needs; a hundred tracks is not the goal.

## Process

1. Voice pass (chain), then listen/measure.
2. Lay ambience, then effects (use `make_sfx.py` placeholders if there is no library), place on peaks.
3. Choose music by emotion; fit length; EQ pocket; duck; transitions and ending.
4. Loudness-normalise; export; ask the user to listen and report anything that distracts.

## Sources (paraphrased, not quoted)

- Gavin Herman, "How To Sound Design ANY Video In 15 Minutes", https://www.youtube.com/watch?v=9jBic4IDfxA
- Herman Huang, "3 Sound Design Secrets That Feel Like CHEATING", https://www.youtube.com/watch?v=tzfzkTAQsnE
- Jacob Nordin, "Sound Design for Cinematic Filmmaking | My Process", https://www.youtube.com/watch?v=I66_LmOTlSk
- Learn By Leo, "How to edit SO good your viewers get addicted to your videos" (sound and music pillar), https://www.youtube.com/watch?v=sLgHqZSe2o0
- Digital Spaghetti with Daniel Thrasher (sound in comedy), https://www.youtube.com/watch?v=sbUrWuyJ43Q
