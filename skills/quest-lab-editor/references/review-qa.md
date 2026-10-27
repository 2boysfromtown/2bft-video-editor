# Review and QC — before anything is called done

Merged 27 Oct 2026 from published agent review protocols, the MovieLabs QC vocabulary, Netflix timed-text specs, W3C/Ofcom flash rules, EBU R128 and YouTube Help (sources at the end). This file replaces "look at it and feel good" with a fixed loop. It runs after every render in `workflow.md` §6.

## 1. The review loop
1. **Automated pass first** (§3) — machines catch what eyes skip.
2. **Look:** contact sheet (1 s Shorts / 4 s long-form), the **cut strips** of every cut (`qa_detect.py --strips <dir>`: −0.2 s / −1 frame / cut / +0.2 s — flash frames, half words, captions hidden by a sticker), and a **360 px-wide phone sheet** of the beat frames (`tools/contact_sheet.py` at 360 px): every line meant to be read must read there.
3. **Listen** where a human must: the first 5 s, the turn, the ending, every inserted clip's level (DOUBLED-AUDIO, §6), on phone speaker and headphones — list these for the user; you cannot hear.
4. **Write notes** in one format, one line each:
   `t=4.20s · caption · hidden by stamp → move stamp to layer top · keep timing` · severity · QC code
   - **BLOCKER** breaks the read or the rules (illegible hook, wrong words in a caption, brand-truth violation, clipping, a flash failure) — fix before upload.
   - **ISSUE** weakens the film (late cut, level jump, sliver, caption reflow) — fix unless it is intended.
   - **FYI** creative intent or polish — say it, leave it.
5. **Fix order:** text → timing → detail. Re-render and re-check **only what changed**. When a fix fails, snapshot both sides, list every difference, change one thing.
6. **Error-class sweep:** when you find one instance of a mistake, search the whole deliverable set for the class (one translated caption → audit every caption; one hook off the safe zone → `hook_audit.py` on all; one missing frame → grep every render log for `WARN missing frame`).
7. **Stop rule:** at most 2 revision rounds by yourself; then deliver with the open items listed as warnings in the notes. Never score a film out of 10.
8. **Automatic repairs are kept only if the re-check strictly improves** (e.g. trimming a silent/black edge, a second loudness pass) — log every repair in the notes; never ship a flagged file silently.

## 2. The fresh reviewer (for big sets or new styles)
Give a fresh sub-agent only the plan, the contact sheets, the cut strips and the 360 px phone sheet — not your reasoning. It returns BLOCKER/ISSUE lines; you do the fixes. Its questions:
- Describe each beat frame in one sentence as a stranger would. Anything that needs explaining is a BLOCKER.
- Does each beat frame cause the next?
- Cover the words: does the story still read from the pictures alone?
- At phone width, is every line meant to be read readable? Is anything in the platform UI zones?
- Does any caption say something he didn't say (EXTRA-CONTENT)? Any income claim, guarantee, course pitch?

## 3. Automated checks (all in `engine/tools/`)
| tool | catches |
|---|---|
| `qa_detect.py <mp4…> [--strips dir] [--expect s]` | BLACK-FRAMES, DUPLICATE-FRAMES (stalls), DROPOUTS, LOUDNESS, CLIPPING, LEVEL-SHIFT (max short-term > integrated + 5 LU), OUT-OF-PHASE (mono fold), EMPTY-FIRST-FRAME, FLASH / RED-FLASH (WCAG 2.3.1), STATIC (> 4 s Short / > 8 s long with nothing changing), DURATION-MISMATCH, SPEC; cut list + cut strips. Exit code 2 on any BLOCKER. |
| `check_srt.py <dur> <srt…> [--cuts f] [--fix]` | Netflix timing rules below; `--fix` closes flicker gaps and snaps to cuts |
| `brand_lint.py <files/folders> [--numbers]` | banned words, income/pricing, course-pitch language, digits in captions |
| `caption_audit.py`, `lang_arbiter.py` | captions that are translations, not his words |
| `hook_audit.py` | hooks outside the Shorts safe zone |
| `qa_all.py` | duration, size, LUFS, true peak for every export |
Tested 27 Oct 2026 on the delivered 25 Oct set (all clean except audio bitrate, now 384 kbps) and on a deliberately broken file (every planted fault caught).

## 4. Subtitles / CC (SRT) — Netflix timing, adapted for Roman Hinglish
- **Gaps:** either 2 frames or ≥ 0.5 s — never 3–14 frames (it flickers). Close a short gap by extending the earlier cue to 2 frames before the next.
- **In-time** on the first audio frame (± 1–2 frames, from the waveform). **Linger** ~0.5 s after speech when no cue follows.
- **Shot changes** (cut list from `qa_detect.py`): speech starting ≤ 15 frames after a cut → in-time on the cut; a cue that would start < 15 frames before a cut → move it onto the cut; an out-time within 15 frames of a cut → 2 frames before the cut. A cue crosses a cut only if the speech does. In burned-in Shorts captions the same rule holds: never change a caption chunk 1–11 frames away from a cut — snap it to the cut.
- **Duration** 5/6 s (25 frames) to 7 s; only 1–2-word cues sit at the minimum.
- **Shape:** one line unless > 42 characters; max 2 lines; bottom-heavy (shorter top line); never 1–2 words alone on top.
- **Line breaks:** after punctuation, before *aur / lekin / kyunki / toh / par*. Never strand a postposition from its noun (*Claude | ne*, *screen | pe*, *mere | ko*), never split the verb cluster (*kar | raha hai*, *ho | gaya*, *nahi | hai*), never split first and last names.
- **Reading speed:** ≤ 20 characters/s for Roman Hinglish SRTs (Netflix's 22 cps for Hindi assumes Devanagari, which is shorter). Burned-in captions stay at ≤ 17 cps.
- **No spoilers:** a cue never shows the punch word before it is heard — split so the reveal starts its own cue on its audio frame.
- **Repetition:** a word said twice in a row is timed to the audio and written once, unless the repetition is the joke.
- **Typography:** the single ellipsis character (…) only for a pause ≥ 2 s or a trail-off; `--` for an interruption; one speaker per line with a leading hyphen for two speakers; digits for numbers (our spelling dictionary); bleeps one asterisk per letter (matches the burned-in rule).
- **Formats:** YouTube reads SRT/SBV as plain UTF-8 text with no position or style. If a CC cue would collide with a bottom graphic, ship WebVTT with the cue moved up. Check in Studio which language entry fits Roman Hinglish (a "Hindi (Latin)" entry is not confirmed) — a wrong tag is a LANGUAGE-TAG fault.

## 5. Photosensitivity (measurable, `qa_detect.py` FLASH / RED-FLASH)
- A **general flash** is a pair of opposing relative-luminance changes of ≥ 10 % where the darker state is below 0.80; a **red flash** involves saturated red (R/(R+G+B) ≥ 0.8). Content fails when there are **> 3 flashes in any 1 s** over **> 25 %** of the screen (W3C WCAG 2.3.1; Ofcom/ASA use 25 % of the screen).
- **Regular patterns:** > 5 high-contrast light/dark stripe pairs are a hazard, worse when they move, flash or reverse — watch glitch scanlines, RGB-split banding and striped wipes over > 25 % of the frame. The low-contrast dot grid is fine.
- Keep any compliant strobe or glitch run < 5 s.
- Automated checks are not a guarantee (Ofcom); the reference tools are Harding FPA and PEAT.

## 6. Audio QC
- **Integrated −14 LUFS ± 1, true peak ≤ −1.0 dBTP** (engine: −14 / −1.5 limiter). **Max short-term ≤ integrated + 5 LU** (≈ −9 LUFS) so a boom or drop never jumps out (idea from EBU R128 s1).
- **Voice consistency:** measure the voice per chapter; flag any chapter > 2 LU from the median (LEVEL-SHIFT).
- **Mono fold:** phones sum to mono — a fold that loses > ~4.5 dB more than a mono voice would means phase trouble (OUT-OF-PHASE).
- **Dropouts:** unintended silence ≥ 2 s below −50 dB in the final.
- **Edits:** pops/clicks at cuts (POP-CLICK-TICK) — every cut gets a 5–30 ms fade; room tone under jump-cut runs.
- **DOUBLED-AUDIO:** the stream's copy of a clip playing alongside the inserted original — mute the stream audio under every inserted clip. **SYNC-OFFSET / SYNC-DRIFT** on re-synced clips (`tools/sync_clip.py`).
- **Dialogue chain** (practitioner starting values, tune by ear on his mic): HPF 80 Hz (12–24 dB/oct against plosives); compression ~3:1, attack ~10 ms, release 80–120 ms, 3–6 dB on loud words (or two gentle 2–4 dB stages); **de-esser** on 5–8 kHz sibilance in ~1 dB passes (ffmpeg `deesser`; the mix has none yet — add only if the esses spit on a phone). Over-processing sounds lispy.
- **Music under voice:** besides ducking, dip the music 2–4 kHz under speech; if the voice disappears on phone speakers, lift the voice 2–4 kHz. A bed whose energy sits mostly below 150 Hz vanishes on phones. In typing-heavy stretches over strong music, drop clicks and key ticks; each SFX sits 3–6 dB above the bed.

## 7. Encode for YouTube (engine defaults in brackets)
H.264 High, progressive, 4:2:0, VBR, CABAC [h264_nvenc p7 VBR CQ 19, yuv420p] · closed GOP of half the frame rate and 2 consecutive B-frames (`-g 15 -bf 2` at 30 fps) · ~8 Mbps guide for 1080p30 SDR, no cap [CQ 19 lands higher — fine] · BT.709, TV range, tagged [yes] · **AAC-LC 48 kHz stereo 384 kbps** [raised from 256 k on 27 Oct] · MP4 with moov at the front [faststart] and **no edit lists** (ffmpeg can add them for AAC priming or concat; check with `ffprobe -show_entries format_tags` / an MP4 box viewer if sync looks off) · upload at the recorded frame rate — if Meld records at 60 fps, a 1080p60 long-form keeps cursor and scroll motion smooth.

## 8. QC codes to tag notes with (MovieLabs vocabulary, the ones that happen here)
**Video:** FLASH-FRAME (stray frame at a chunk join or cut) · DUPLICATE-FRAMES · OFFLINE-FRAMES / MISSING-MATERIAL · BLACKS-LIFTED / BLACKS-CRUSHED · BANDING · MACROBLOCKING / MOSQUITO-NOISE round small text · PIXELATION / STRETCHING on the webcam (face upscale > ~1.3×) · VISIBLE-WATERMARK (Meld overlay bits, third-party logos) · TEMPORARY-MATERIAL (placeholder text, temp music) · DURATION-MISMATCH.
**Audio:** POP-CLICK-TICK · LEVEL-SHIFT · DROPOUTS · DOUBLED-AUDIO · SYNC-OFFSET / SYNC-DRIFT · CLIPPING · OUT-OF-PHASE · SAMPLE-RATE (48 kHz) · TRUNCATED.
**Timed text:** LINE-LENGTH · LINE-COUNT · LINE-BREAK · SEGMENTATION · DURATION-SHORT / LONG · EVENT-SHOT-TIMING · EVENT-AUDIO-TIMING · MISHEAR · **EXTRA-CONTENT** (words he didn't say — the brand-truth rule as a QC code) · REDUNDANT-EVENTS · POSITION · LANGUAGE-TAG · TYPOS.

## 9. Keeping the pipeline honest
- **Decision log:** for each key choice (music track, template, Shorts picks, layout of the hook), write ≥ 2 options considered and the specific reason. All choices "obviously right" is a red flag.
- **Approved-beats manifest:** after the user approves a cut, list every beat with its asset and status, plus a "do not re-add" list; check it before every re-render so approved moments never silently disappear.
- **Living checklist:** add an item to "Pitfalls seen" (`workflow.md` §6) only after it caused a real revision; keep ~8–12 live items, retire the ones the engine now prevents.
- **Golden set:** hand-label 2–3 stream excerpts once (true words, true word times, the user's own Shorts picks). After any change to transcription or selection, measure word error rate, word-timing error (median, 95th percentile) and whether the agent's top 3/5 picks include the user's — so "better" is a number.
- **Time-box:** ~5 minutes per sourcing or fix attempt; a method that fails once is not retried the same way; after a second failed method, drop the item and flag it.

## 10. After publishing
- Check retention after a few days. If the intro leaks, trim it in **YouTube Studio → Editor → Trim** — the URL, views and comments stay. Saved Studio edits **can't be reverted** (since June 2025), and videos over 100 k views can't be edited outside the Partner Program — keep the master. (One case study: cutting a self-intro moved the content start from 0:38 to 0:11 and flattened the curve.)
- **Test & Compare:** up to **3 variants**, of title only, thumbnail only, or both; the winner is chosen on **watch-time share**, not CTR; a test runs a few days to 2 weeks; changing the title or thumbnail mid-test stops it; not available for Shorts, private, made-for-kids or Premieres until they end; every thumbnail must be ≥ 1280×720 or all variants drop to 480p. Results: Winner / Performed same / Inconclusive (first upload stays). Test older videos first.
- **Shorts → long-form:** set each Short's **Related video** (Studio → the Short → Related video) to the full episode, and end the Short with a spoken + visual pointer in its last 5 s.

## Sources
heygen-com/hyperframes review.md, captions.md, motion-doctrine (Apache-2.0) · OpenMontage reviewer.md, checkpoint-protocol (AGPL — ideas only) · HotClip (AGPL — ideas only) · browser-use/video-use (MIT) · louisedesadeleer/b-roll-finder (MIT) · MovieLabs QC Vocabulary (video, audio, timed text) · Netflix Partner Help: Timed Text Style Guide — Subtitle Timing, General Requirements, English (USA), Hindi; Netflix QC codes (black frame, silence) · W3C WCAG 2.2 Understanding 2.3.1 · Ofcom/ITC flashing guidance, ASA ruling · EBU R 128 s1 · YouTube Help: recommended upload encoding settings, supported subtitle files, A/B testing titles & thumbnails, trim videos · YouTube Blog: related-video traffic guide (Jul 2026) · Production Expert / iZotope (de-esser), Sound On Sound (dialogue HPF/compression) · George Blackman, Retention Review #7.
