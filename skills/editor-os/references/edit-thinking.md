# How an editor thinks

The questions to ask, in the order an editor asks them. Use them as a checklist when planning, when reviewing a rough cut, and when a user says "it feels off".

## 1. Per film (before the first cut)

1. **Who is watching, where, with sound on or off?** (phone feed muted, laptop, TV, lean-forward or lean-back).
2. **What should they feel at the end, and what should they do?** One sentence each.
3. **What is the one turn?** The moment that changes the meaning of what came before. If there is none, you have a list, not a film: find the turn or restructure as a deliberate countdown.
4. **What is the hook, and is it an event?** A number landing, a motion, a claim, a freeze with a question.
5. **What is the signature move?** The one thing only this medium can do, placed at the emotional peak.
6. **What drives the clock?** Music beat, spoken calls, reading time, real event time. Pick one primary driver; the others follow it.
7. **What are the three candidate structures?** Write them (a few lines each) and pick one with a reason. The first idea for a style is usually its cliché.
8. **What is the benchmark?** One or two reference works for this style and topic. Write *what to learn* (composition, pacing, camera grammar, colour logic, score structure) and *what not to take* (characters, designs, melodies, specific shots, logos, fonts).
9. **What can the footage honestly support?** Do not plan a multi-angle sync if you have one camera; do not claim a number you cannot source.

## 2. Per scene

Ask the five tempo questions: Does this scene have one overall tempo? What is it? Does it change? Where? Why?

Then:
- What is its **emotional destination**? (the feeling it should leave)
- What is the **one fact or beat** it delivers?
- What does the viewer **see first**? (eye-trace from the last shot)
- What **moves**? (nothing static > ~1 s)
- What is the **sound plan**? (bed, foley, music state, silence?)
- Does it **finish completely** (cut, graphics, sound) before the next begins? Finish each section fully before starting the next; "70 % of everything, then a second pass" costs more.

## 3. Per cut

For each cut, write the cause (strongest first):
1. An event or a call happened.
2. New information arrives.
3. The beat says so.
4. Reading time elapsed.
5. Contrast is needed.

Then check:
- **Eye-trace:** where does the eye end in shot A and start in shot B? Same area, or the viewer refocuses and leaves.
- **Contrast with neighbours:** do adjacent shots conflict in direction, value, scale, geometry or speed? Two similar shots in a row either merge or jolt.
- **Length:** is the shot as long as the information needs plus a little, or longer because you did not decide?
- **Sound across the cut:** J-cut, L-cut, bridge, or a clean hard stop? Is there a reason it is silent?
- **Transition:** hard cut by default. A fancy transition needs a meaning (time passed, location change, section boundary, brand grammar).

## 4. The cut vocabulary, as decisions

| Cut | Use when | Risk |
|---|---|---|
| Hard cut | default; action, new fact | monotony if the only cut |
| Jump cut | tighten speech; energy | overused feels frantic; hide with punch-in alternation |
| J-cut | next scene's sound leads; smooths a topic change | none; cheap polish |
| L-cut | last scene's sound lingers; reaction while the voice continues | |
| Match cut | shape/motion continues across (clock → clock) | needs matching material; on the beat |
| Smash cut | jolt; silence → loud; calm → chaos | works only against a smooth baseline |
| Cutaway / insert | show what the words describe; hide a cut | irrelevant B-roll |
| Freeze | examine; ask the question | needs a purpose and a drawn finding |
| Speed ramp | emphasise; pass time | gimmick if unmotivated |
| Hard stop (picture and sound) | the ending, the turn | needs earlier build |

See `video-editing-craft/references/cut-vocabulary.md` for longer notes.

## 5. Worked examples

**"This 60 s reel feels flat."**
Run `pacing_report.py`. Typical findings: CPM constant (no variation), first cut at 6 s (hook missing), no silence, same shot size throughout. Fixes in order: replace the opener with the biggest number/claim on frame 4; plan one brake and one acceleration; add two silences; vary shot size and direction on adjacent cuts; put captions in chunks with one keyword; add the cue-sheet foley for captions and counters; re-measure. Report CPM before and after.

**"Make this explainer punchier."**
Don't just raise CPM. Ask the experience: learning needs clarity, not noise. Add B-roll or a graphic to each claim (strongest B-roll for abstract content is a motion graphic), tighten dead air, move the answer earlier, add a source tag to every number, keep the pace set by the explanation. Punchier = fewer words per screen and faster arrivals, not shorter holds.

**"Cut this to the beat."**
Pick the track's BPM and the beat-0 anchor (first downbeat or end of sting); `editgrid.py beats` gives the grid; move big cuts to bar lines; check `pacing_report.py --bpm` shows ≥ 90 % of cuts within ±40 ms. Do not cut on every beat; keep long shots across several beats where the content needs it. If voice carries the piece, let the voice's calls set cuts and use music only as bed.

**"Add sound effects."**
Don't sprinkle. Build the cue sheet: list every visible action; bed; two silences; a heaviest hit; two sound bridges; peak-aligned placements (whoosh starts 4-12 frames early). Replace placeholders; check loudness and that voice is still clear.

**"Make it look like a news bulletin / documentary / a montage."**
Pick the matching mode in `style-modes.md`; apply its transition grammar and sound palette; set one accent colour; keep the package consistent for the whole piece; do not mix two transition vocabularies.

**"A joke is not landing."**
Comedy timing: setup needs room, the punchline needs to be featured, the reaction needs a hold, then the button. See `comedy-editing-timing`.

## 6. Diagnosing "it feels off"

| Symptom | Likely cause | Fix |
|---|---|---|
| Feels slow | constant tempo; wide shots; no movement; long holds on unchanged picture | add a stretch of tighter shots, push-ins, a new element every 1-2 s; shorten shots, not reading holds |
| Feels frantic/exhausting | one tempo, too fast, too many words per screen | add a brake, a breath, a silence; cut words not time |
| Feels flat | no sound design; no variation; same shot type | cue sheet; vary scale/direction; a signature move |
| Feels amateur | random transitions; graphics that pop in; music fighting voice | one transition grammar; motion or sound on arrival; duck and EQ pocket |
| Boring beginning | slow logo, long intro | start on the strongest event; logo as a bug later |
| Dead middle | no turn; one fact repeated | find or insert the turn; cut the repeat; add a layer deeper |
| Ending fizzles | fade of energy | button: hard stop, echo of opening, heaviest hit after silence |
| Can't follow | captions too fast; two ideas per shot | reading time; one idea per shot; split captions |
| Doesn't land emotionally | pace opposite to feeling; sound generic | slow a heavy beat; palette of the mode; silence before the peak |

## 7. Taste vs measurement

Measurable (do it yourself): cut times, CPM, grid error, reading holds, loudness, peak, silences present, black frames, duration, transcript accuracy, contrast and size of subject in frame.

Taste (offer two options, then ask the user): does the joke land, does the music feel right, is the transition elegant, is the red the right red. Say so plainly. Never claim a perception you cannot have.

## 8. Failure catalogue (look for these in every review)

- Subject too small, too far away, or against the frame edge.
- Too dark to read; a colour on the same colour (red on red).
- Captions covering the subject or the key action.
- A gag/failure too fast to understand.
- Blank frames inside transitions (start the transition 0.1-0.15 s before the cut).
- A timed effect (iris, zoom, spotlight) not following the subject after the camera moves.
- Per-frame auto-levels or grading making footage pump (one level set per clip).
- Upscaled archive on a full frame (window it; stay inside the upscale limit).
- Watermarks, slates, station logos, burned-in text left in.
- Captions that fade before they can be read (fix the words, not the hold).
- A number without a source or a unit; words stronger than the source.
- Speech check shows a mangled name or number.
- Sound: peak after the cut; no silence; music never stops; placeholders left in.
