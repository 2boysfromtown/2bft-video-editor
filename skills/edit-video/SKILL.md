---
name: edit-video
description: End-to-end workflow for editing a video from footage or a rough draft - look at it, transcribe it, plan the tempo, make the rough cut, add B-roll or graphics, comedic timing, sound effects and music, then export and check. Orchestrates transcribe-local, video-editing-craft, comedy-editing-timing, video-sound-and-music, motion-graphics-for-video, ffmpeg-edit-toolkit, long-to-shorts and talking-head-polish. Use when the user says edit this video, cut this, tighten it, make it punchier or funnier, add music or sound effects, add motion graphics, clean up the audio, make a rough cut, cut Shorts or Reels from a long recording, or hands over footage, a file path or a link and wants it improved or finished.
---

# Edit video

The entry point. It runs the whole edit in order and calls the specialist skills at the right moment. Work on copies, show numbers, and be honest about what an AI agent can and can't judge.

## What you can and can't do

- **Can:** read files and metadata; get frames and look at them; transcribe speech with timestamps (`transcribe-local`); detect silence and measure level and loudness; cut, join, zoom, speed-change, overlay, mix and encode with ffmpeg; build animated graphics with Remotion or GSAP; generate placeholder sounds.
- **Can't:** hear the audio or watch playback, feel a joke, judge whether music "feels right". Say that, make the measurable decisions yourself, and ask the user to watch and listen for the rest.
- **Must not:** claim to have watched a video without having read its frames and transcript; overwrite the original; spend a long render without telling the user.

## Step 0: Intake (ask only what's missing, in one message)

1. Source: file path(s) or link; anything the user already cut.
2. Goal and platform: YouTube long-form, Shorts/Reels/TikTok (9:16), ad, course, meeting recap. Target length.
3. The experience the viewer wants: hang out, be entertained, learn (`video-editing-craft` section 1).
4. Style references or a brand (if the project has brand notes such as colours, fonts and motion rules, read them).
5. Assets: music, logos, B-roll, sound effects. If none, source them with `asset-library` (where to find and download music, SFX, memes, stock footage, fonts, with licences) or say what you'll use as placeholders. Noisy audio, music bleeding under the voice, cutouts or slow motion: `local-av-tools`.
6. Constraints: must keep, must cut, deadlines, music licensing.

## Step 1: Look and listen (never edit blind)

- `ffprobe` duration, resolution, frame rate, audio present.
- Frames: `ffmpeg -i in.mp4 -vf "fps=1/5,scale=640:-2" frames/f_%03d.png` (one every 5 s, denser around key moments), then read them.
- Transcript with timestamps: `transcribe-local`. For a link, download it first (yt-dlp) or use the platform's own captions.
- Read the frames and the transcript. Write down: what happens in order, the strongest moments, the weak or dead stretches, and (if already cut) the starting CPM.

## Step 2: Plan (short, shown to the user before heavy work)

A table of sections: time range, purpose, emotional destination, target tempo (slow/medium/fast), visuals (A-roll, B-roll, graphic), sound plan, and what gets cut. Mark joke candidates if it's comedy. Keep the plan to one screen. Proceed unless the user wants changes or the file is long (over about 30 minutes: confirm first).

## Step 3: Rough cut

- Dead air and filler: `ffmpeg-edit-toolkit` `remove_silence.py` (dry run first), then remove false starts and tangents by transcript.
- Open on the strongest moment or the question; cut ahead to the point.
- Structure for the experience chosen; keep sections self-contained so each can be finished completely.
- Output `edits/<name>_v1.mp4`. Report the length before and after and cuts per minute.

## Step 3b: Shorts from a long recording (when asked)

Read the transcript, pick the moments that stand alone (a hook in the first line, a payoff, under 60 s), write a `plan.json` and build them with `long-to-shorts`. Proofread every caption against the audio.

## Step 4: Pacing and picture

- Apply tempo variation per section (`video-editing-craft`): change CPM at story change points; add punch-ins, B-roll, speed contrast; remove or add pauses with intent.
- Comedy: apply `comedy-editing-timing` (setup room, punchline featured, reaction holds, the button).
- Graphics: list each with purpose and timing, then `motion-graphics-for-video`; build and overlay.
- Captions: only where they earn their place (three words or fewer, emphasis). Talking-head reels: karaoke captions and text behind the speaker with `talking-head-polish`.

## Step 5: Sound

`video-sound-and-music`: voice chain, ambience and effects placed on visual peaks, music chosen by emotion and fitted to length, EQ pocket and ducking, transitions and ending, loudness. Be explicit about which sounds are placeholders.

## Step 6: Export and QA

1. Encode (`recipes.md` delivery encode); `-movflags +faststart`; 9:16 deliveries at 1080x1920, H.264, yuv420p, text inside the safe zone (`long-to-shorts` builds the vertical layout).
2. Verify: duration matches the plan; resolution, codec, audio present (`ffprobe`); loudness measured; 4-6 frames pulled across the timeline and looked at (start, each section, ending); transcribe the result and read it end to end for cut words or broken sentences.
3. Checklist: first five seconds earn the next thirty; no unmotivated pop-in graphics; no clipped words; music never fights speech; ending lands on a high.

## Step 7: Report

Short summary: what changed, numbers (length before/after, CPM before/after, loudness), what is placeholder, what you could not judge and need the user to check (listen on speakers/phone, watch for beats that don't land). Offer one specific next step. Keep earlier versions so the user can go back.

## Working rules

- Version outputs (`_v1`, `_v2`), never overwrite; keep a log of commands/graphs used in `edits/edit-log.md` so any step can be reproduced.
- One change-set at a time when the user is reviewing; combine passes only when asked for a finished video in one go.
- If a decision is taste, offer two short options instead of an essay.
- Source rights: use only music and footage the user has the right to use; flag anything that may need a licence.

## Related skills

In this pack: `editor-os` · `video-editing-craft` · `comedy-editing-timing` · `video-sound-and-music` · `motion-graphics-for-video` · `ffmpeg-edit-toolkit` · `transcribe-local` · `long-to-shorts` · `talking-head-polish`

Optional, if installed: Remotion or GSAP skills for code-built graphics.
