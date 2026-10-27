# Sound cue sheet

How to put sound effects and music into an edit so it is designed, not sprinkled. Basic voice chain, ducking and music-fitting recipes are in `video-sound-and-music` and `ffmpeg-edit-toolkit/references/recipes.md`; this file adds the **cue-sheet method**, the action → sound table, placement offsets and per-mode palettes.

## 1. Principles

1. **Sound is judged before picture** in the order: sound, rhythm, camera, directing. Good frames are only the starting point.
2. **Every visible action has a sound.** Landings, slams, page turns, cuts, drips, clicks, cloth, counters, labels. If it moves on screen and is silent, either give it a sound or remove the movement.
3. **Three layers**, always:
   - **Bed**: room tone / ambience / drone, under everything, first frame to last. Nobody notices it present; everybody notices it missing.
   - **Foley / effects**: tied to actions, sample-accurate.
   - **Music**: score or track, ducked under speech and key foley.
4. **Match the material:** paper, wood, metal, glass, ink, cloth, plastic all sound different. A stamp is a thump + a clack; a marker is filtered-noise scrub; a card is a whoosh + a snap.
5. **At least two real silences or near-silences**, one before the turn, one before the final hit/verdict. Silence is the loudest cue you have.
6. **Sound as transition at least twice:** a J-cut (next scene's sound starts early) and an L-cut (last scene's sound runs over the cut), or a sound bridge (a riser or sustained note crossing the cut).
7. **Emotional realism over literal realism:** sound need not match the picture literally. Decide what the viewer should feel, then pick the sound.
8. **Palette discipline:** commit to one family per piece. Gritty bass hits in a clean corporate video, or generic "piano and strings" in everything, are the two classic errors. Score in the instruments of the mode.

## 2. Build the cue sheet

Fill `templates/cuesheet.csv` (one row per sound):

| Column | Meaning |
|---|---|
| `t_in` | seconds in the final timeline when the sound's *peak* must land (not when the file starts) |
| `picture` | what is on screen at that moment |
| `sound` | what it is (whoosh, thump, tick, riser, ambience…) |
| `layer` | bed / foley / music / voice |
| `level_db` | level relative to dialogue (negative = quieter) |
| `pan` | −1 left … +1 right |
| `offset_ms` | how long before `t_in` the file must start so its peak lands on the peak of the picture |
| `source` | file or generator, and whether it is a placeholder |
| `note` | ducking, reverb, layering instructions |

Procedure:
1. Walk the cut list in order. For each cut, graphic arrival, text slam, counter, freeze and stamp, add a row.
2. Mark the **silences** and **the heaviest hit** first; everything else supports them.
3. Count: if you have a sound on every second, delete half. Punctuate the moments that matter.
4. Add the bed row (whole length) and the music rows (sections, hits, stops).
5. Render with `adelay` per row or in the NLE; keep the CSV with the project so the mix is reproducible.

## 3. Action → sound table

| On screen | Sound | Layering note |
|---|---|---|
| Hard cut | none; or a short low thump (timpani) on important turns | cuts are often best silent against a continuous bed |
| Whip, wipe, push transition | whoosh, rising pitch, peak on the cut frame | start 4-12 frames before the cut |
| Text/caption chunk slams in | click + low thump | one per chunk, 0.12 s apart |
| Counter rolling | rattle / ticks every ~45 ms, pitch up as it nears the value | stops with a tiny thump when it lands |
| Number lands big | stamp thump + brass stab | add a riser before it only if the number deserves it |
| Label pops | short pop / tick | quiet; do not cover speech |
| Card slides in | whoosh + soft snap | |
| Highlighter / marker | filtered-noise scrub, 2-5 kHz, with flutter | length = the sweep |
| Circle / line drawn | pencil/marker squeak, length = the draw | |
| Photo / document appears | shutter or paper slap | a flip-book: paper flick per page |
| Page turn | paper rustle, band-passed | |
| Typewriter / telegram | keystrokes / Morse dits | |
| Freeze frame | brass stab + timpani + low thump + camera shutter; music drops to sparse hi-hat only | music freezes with the picture |
| Rewind | tape-motor whine, rising, with noise bursts | |
| Stopwatch / clock | tick each second (alternate two pitches), accent every 5 | louder in the last ten seconds |
| Grid cell lights | pitched clank / xylophone note, one rising note per cell | |
| Stamp | thump + clack, once per story | low-pass the clack so it does not mask a keyword |
| Map line / pin | telegraph clicks; sonar ping on a city | |
| Impact / reveal | hit; alone or after a riser | a hit after a silence is stronger than a louder hit |
| Zoom / punch-in | short swell or air hit | |
| Glitch / digital | stutter + bit-crushed click | only if the mode is digital |
| Ambience change (new place) | new bed in 0.3 s early (J-cut) | |
| Hard stop at the end | all instruments cut in ~15 ms, reverb tail left ringing | the dry cut is the effect |

## 4. Shaping one effect (five steps)

1. **Source** from one consistent pack or generate (`ffmpeg-edit-toolkit/scripts/make_sfx.py` for placeholders).
2. **Hone:** pitch down for weight, up for snap; high-pass/low-pass to fit the space; one sound makes three (cut a whoosh at its peak for an impact, reverse it for a riser).
3. **Layer across frequencies:** a single whoosh is thin in one band. Add a copy pitched lower and another higher, or a different sound in another range. Think cake layers: sub (thump), body (the sound), top (air/click).
4. **Place:** the loudest moment of the sound on the exact frame of the loudest visual moment. Tens of milliseconds matter. Offsets: whoosh/riser start before (peak on the cut), impacts start at or 1-2 frames before the visual hit, ticks and clicks on the frame.
5. **Environment:** reverb for space (small room little, hall a lot, distance more), EQ to carve room under the voice, a bed underneath so the effect sits in a world.

## 5. Voice

- Chain, in this order: gentle denoise → EQ (cut < 80 Hz, tame > 12-16 kHz) → shaping EQ → compression (~2:1, threshold near the quieter words) → de-ess → limiter.
- TTS has a high peak-to-average ratio: **compress the voice first, then balance by RMS**; voice ≈ 8-12 dB above music.
- Ducking: music under speech by 6-10 dB (16 dB pumps), and thin the music's 1.2-5 kHz band under speech (EQ pocket). Foley ducked ~35 % under speech; keep key accents audible.
- One narrator, one sentence per graphic, starting ~0.1 s after the cut. Lines that end on the cut feel rushed: speed it (TTS ≤ ~1.17×, faster mangles names) or shorten.
- Names and numbers for TTS: spell phonetically or as words in the voice text, keep the real spelling in the subtitle, and add the expected transcript for the speech check.
- Speech check: transcribe every generated line and the final mix; fix mishears by rewriting, not by trusting.

## 6. Music

- Choose by emotion first; match the section; change the track at topic shifts.
- Write or pick music in the **mode's palette** (section 7). Avoid generic piano-and-strings bed.
- Build the **cue map** before cutting when music leads: tempo, bar grid, instrumentation per section, and on which beat each cut, key action and caption lands.
- Structure that works: hook hit on the first frames → groove → **hard stop into silence before the turn** → major-key or heavy hit on the turn → half-time/low strings for threat → build (snare roll, riser) into the spike → short silence before the verdict → resolve.
- Fit length at phrase boundaries; never chop mid-beat. Getting in: reverse the first beat or tail as a riser; getting out: end on an impact, or a long reverb tail, or pull everything out to silence.
- Balance the low end: synthetic scores get bass-heavy. Keep 20-120 Hz about −3 dB relative to the rest, skip pad notes below MIDI 48, give the bass some 2nd/3rd harmonics so it speaks on phone speakers.
- If the user swaps in their own track: never move the cuts; pick or stretch a track so a downbeat lands on the turn/zero and a section change on the planned point; keep the planned silence.

## 7. Per-mode palettes

| Mode | Bed | Music | Signature sound |
|---|---|---|---|
| Caption-first | natural sound of the location, J-cut | 120 BPM kit + eighth bass + marimba ostinato + vibes + glock + brass stabs | hard stop before the turn; chunk-slam click + thump; counter rattle |
| Newsreel | projector (24 Hz clatter, hum, hiss) | tuba, banjo, trombones, snare, honky-tonk piano, muted trumpet; second "band" for the other side | band stop + one stab; needle drop; carbon-arc snap |
| Live countdown | native sound on top, never ducked | 60 BPM drone with opening low-pass, bass drum per beat, timpani roll, brass chord at zero | tick every second; silence a quarter-second before zero |
| Time-lapse symphony | none (music only) | pipe organ, staccato winds, spiccato strings, horns, bass drum, cymbal crescendos | additive arpeggios; the break; dry hard stop with reverb tail |
| Investigation | low D drone + room tone ~30 dB under voice | pizzicato ostinato, tremolo clusters, slow chords, vibraphone resolve | pendulum tick; original sound band-passed; thump at impact then near-silence |
| Montage | real site/street recording, out for the silence | machine ostinato (cellos, bassoon), tuba, snare, xylophone counts, timpani, gong | silence beat then heaviest hit; xylophone note per count |
| Telestrator | crowd bed low-passed during freezes | kit, bass, trumpet/trombone, timpani, glock, cellos ~120 BPM | drums stop on freeze; marker squeak; tape whine |
| Broadcast package | server hum/air very low | spiccato violins, pizzicato bass, horn pads, kick 1&3, snare 2&4 | sting tutti; glock on rundown rows; one beat of silence before the biggest break |

## 8. Mix and master

- Order: voice → effects → music; then group (music bus, effects bus).
- Target about **−14 LUFS integrated**, **true peak ≤ −1.2 dB** (two-pass loudnorm). Hot peaks from broadcast audio or a big hit can miss true-peak: pre-limit the mix near −4 dBFS after normalising, then master.
- Fade the first ~25 ms of the file (a hit at sample 0 overshoots in the AAC encode).
- Grain/noise bed belongs to the master, not baked into frames.
- Check: `ffmpeg -af ebur128=peak=true` for loudness; `silencedetect` for the planned silences; speech check on the final mix; listen on laptop speakers, phone and headphones (user).
- Every row of the cue sheet is actually in the mix: tick them off before delivery.

## 9. Common sound mistakes

Sound on every second · whoosh peak landing after the cut · music never stops · music fights voice at 2-4 kHz · same whoosh 20 times in a row (vary pitch/length) · hit with no preceding silence · effects louder than dialogue · reverb mismatched to the picture's space · placeholder sounds shipped as final · a stamp or hit covering a key word · no bed, so each effect floats in a void · loudness measured on the music only.
