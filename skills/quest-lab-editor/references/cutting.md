# Cutting — pauses, fillers, retakes, timing truth and screen speed

Merged 27 Oct 2026 from published agent skills and open-source cutters (sources at the end), rewritten for Hinglish streams and this engine. Tags: **[M]** measured / spec · **[S]** a source's working value · **[O]** starting value, tune by ear.

The radio cut (SKILL.md step 5) decides *which* thoughts stay. This file decides *how tight* the kept speech is, and how to find exact cut points when Whisper's timings are not good enough.

## 1. Word timings are approximate — trust them for finding, not for cutting
- Whisper word edges are off by ~100–300 ms and tend to land **early** (a 2026 benchmark puts large-v3 ~150 ms early) [S]. Only ~40–64 % of its word boundaries fall within 50 ms of the truth on clean English, less on conversational audio [M]. faster-whisper also clips sentence-final words that look too long.
- **Stretched words** (one word lasting > 1 s) swallow a pause or a retake. Never cut on their edges. `tools/packed_transcript.py` marks them `word~`; `tools/pauses.py` lists them.
- **Whisper invents text over silence** ("Thank you.", a repeated last line) and drops "um/uh" entirely. Treat a segment with no-speech probability > 0.6 or a stock phrase as suspect (`{HALLU?}` in the packed transcript). A transcript with > 20 % music/garbage tokens is a failed pass — re-run that window.
- For cut points use **energy**, not word edges: `pauses.py` finds the real silent run inside each word gap (search window widened 150 ms before the Whisper end, 100 ms after the next start).
- When a punch word must land on its exact onset (caption slam, SFX, zoom), move it to the first energy rise within +0…150 ms of Whisper's start (bias later). An early cut reads as a mistake; a late one reads as intent.
- Cutaways and graphics placed off a word: 0.2–0.5 s after Whisper's word end, or ~0.2 s before the keyword onset [S].
- **Forced alignment** (10–30 ms accuracy) is the upgrade when a cut list gets dense. Options for Hinglish, with licences: MMS/wav2vec2 CTC aligners take Roman text (most default models are **CC-BY-NC — not for this monetised channel** without checking); WhisperX's Hindi aligner needs Devanagari and gives numbers no timing (write numbers as words for alignment, show digits on screen). Ask before installing any of them.
- `transcribe_words.py` can be given a glossary (`hotwords` / `initial_prompt`: Claude, Unreal, Meld, ComfyUI, Flow, <your show name>) — Whisper copies the prompt's *style*, so write the glossary in the Roman Hinglish you want back. Only the last ~224 tokens count.

## 2. Read the stream as packed text first
`python -I tools/packed_transcript.py work/transcript_hi.json work/packed.md` → one phrase per line `[mm:ss.s–mm:ss.s] text`, a new line at every ≥ 0.5 s pause (and every ~8–15 s in run-on speech), long pauses shown as `...3.8s`. A 50-minute stream is ~55 KB — read all of it before choosing anything. Pull pictures only at decision points with `tools/timeline_view.py` (filmstrip + waveform with the silence threshold + words on a time axis; `--rect` crops the filmstrip to the webcam so mouths are readable).

## 3. Tightening pauses — `tools/pauses.py`
`python -I tools/pauses.py work/audio48k.wav work/transcript_hi.json <from> <to> --mode aggressive|balanced|gentle`
- **Threshold from the footage, never a fixed −30 dB:** noise floor F = 10th percentile of 0.5 s RMS (digital silence from a muted mic is ignored), speech S = 90th percentile, silence = below F + 6 dB [S]. If S − F < 8 dB (music or game audio under the voice) energy cannot separate speech — the tool says so and you cut from word timings and your eyes.
- **Gap table** (real silent gap → length kept) [S, adapted]:

  | mode | use | < 0.25 s | 0.25–1 s | 1–3 s | > 3 s |
  |---|---|---|---|---|---|
  | aggressive | Shorts | keep | 0.10 | 0.20 | 0.20 |
  | balanced | long-form | keep | 0.30 | 0.80 | 0.50 |
  | gentle | moral / emotional lines | keep | 0.50 | 1.50 | 1.00 |

- Of the kept gap, ≤ 0.10 s goes before the next word and the rest after the last word: voices decay, onsets are sharp. Pads in published tools: 30–50 ms before an onset, 40–80 ms after an offset (more for Whisper timings, which run early) [S].
- **A cut is a visible jump** in this engine (every kept range is a shot). Skip a cut that saves < 0.2 s (Shorts) / 0.3 s (long-form), and never leave a kept piece < 0.4 s. Same-layout face jumps are hidden by the engine's auto-punch alternation; screen jumps by a 1.0 → 1.02 zoom shift (§6).
- Loud blips shorter than 80 ms (mouse clicks, lip smacks) don't break a silence, and silences hidden *inside* a stretched word are listed as `(inside stretched '…')` cuts — verify those with `timeline_view.py`. Breaths in a long stare still split it: when the picture shows one continuous stare, cut it by hand.
- **Protected silences:** the planned beat before a punchline, the 400–1200 ms after a music stop, a reaction, a thinking face that *is* the moment. Comedic beats are trimmed to 0.4–0.6 s, never removed [S]. Never cut a pause < 0.2 s.
- **Density self-check** on the kept pieces: median > ~2 s = loose for a Short (fine for long-form); median < ~0.7 s = over-cut, merge [S]. Typical tightening is 5–15 % on a fluent speaker like our host, 40–60 % on retake-heavy footage.
- Long-form alternative to many jump cuts: fast-forward a dead stretch at ~6× with a chip, or a "later" card.
- Audio at every cut gets a short fade (the mix already applies 12 ms; 5–30 ms is the published range). A continuous room-tone bed (lifted from a pause in the same recording) under a run of jump cuts stops the background noise from stepping.

## 4. Fillers, breaths, laughs — never auto-cut
- Whisper usually leaves "um/uh/matlab" *out of the text*, so a transcript-driven filler cut misses them. `pauses.py` lists **unworded voice**: energy above the threshold for ≥ 0.15 s inside a Whisper gap → short = filler/breath? · long = aside or unheard words? · long + louder than speech = laugh/reaction (protect).
- Listen to each (or view it with `timeline_view.py`), then cut fillers by hand with 50 ms pads. Keep: laughs, gasps, sighs, a one-word punchline after a beat, "bhai" when it lands.
- Verbatim engines that do write fillers exist (CrisperWhisper — weights non-commercial; Sarvam saaras `verbatim` mode — paid API, check with the user).

## 5. Retakes and false starts
- **False start:** the same opening restated within ~3 s → drop the first attempt and the gap.
- **Full retake:** a phrase whose opening 3 words (or 3-gram overlap > 0.7) repeat within 60 s.
- Default keep = the **later** take, unless it is flubbed and an earlier one is clean. A long pause, a breath or a slate phrase ("ek baar phir", "wait, let me redo", "nahi nahi") marks the boundary.
- Repetition that *is* the joke ("oh my beauty, oh my beauty…", "dabbe… dabbe…") is not a retake — `pauses.py` lists candidates; you decide. Show every retake group in the plan so the user can override.

## 6. Screen recordings — speed by activity
| activity | speed |
|---|---|
| typing boilerplate | 2–3× |
| opening files, switching tabs | 1.5–2× |
| installs, builds, renders, AI thinking | 2–4×, or show only start + end (8–30× time-lapse with a chip and tick music if long) |
| writing the key prompt / key code | 1× |
| debugging, reasoning out loud | 1×, dead pauses cut |

Remove non-deliberate pauses > 1.5 s. Mute or duck sped-up audio hard (fast keyboard noise turns into harsh clicking). Freeze detection (`ffmpeg freezedetect`) finds idle spans in old recordings with no input logs; speed those, leave real animations at 1×. Hide a jump cut inside a continuous screen shot with a 1.0 → 1.02 zoom shift; hold each zoom position ≥ 3 s before moving again; zoom targets: code 1.5–2.0×, terminal 1.5×, one UI element 2.0–2.5×; callouts appear just *before* the action they describe [S].

## 7. Sliver rule for cutaways (screen ↔ face, media inserts)
Never leave the face on screen < ~2 s between two cutaways — extend the first cutaway to meet the second. In QA reject any sliver < 1 s. Cutaways run 2–4 s; < ~1.2 s is unreadable unless it is a deliberate burst (one burst of 3–4 quick stills per intro). Front-load cutaway density in the intro, keep the body sparse [S].

## 8. Check audio events against a frame
An energy peak says something *sounded* loud, not that it is visible. Before an impact, shake or punch-in lands on a detected peak, grab the frame (`tools/grab.py`): drop it if he is off-frame, blocked, or the peak is clip audio playing on his screen.

## 9. Next-stream setup notes (put in the delivery notes when the footage fought the edit)
IDE/terminal font ≥ 18–22 px (zoom 150–175 %), minimap off, sidebar collapsed, cursor 1.5–2×, record the screen at the highest resolution Meld allows (4K gives ~2× clean punch-in headroom), 60 fps for UI motion; Screen-Studio-style auto-zoom needs cursor/click logs recorded at capture time — they can't be recovered from pixels later [S].

## Sources (ideas re-derived in our own words; licences checked 27 Oct 2026)
louisedesadeleer/cut-video (MIT) — adaptive threshold, gap table, pads, retakes, density · louisedesadeleer/b-roll-finder (MIT) — sliver rule, late bias · louisedesadeleer/clipify (MIT) — verify audio events with a frame · browser-use/video-use (MIT) — packed transcript, timeline view · WyattBlue/auto-editor (Unlicense) — margins, smoothing, motion-based cutting · carykh/jumpcutter — fades at every cut · Descript help (shorten word gaps) · SYSTRAN/faster-whisper (MIT) — VAD and timing internals · arXiv 2509.09987 and FA-Bench (preprint) — Whisper timing error · OpenMontage (AGPL — ideas only) — screen-recording speed table, zoom shift, long-form fast-forward · connerkward/screenstudio-alternative-skill (MIT) — idle speed-up, capture-time logs · OpenAI Whisper prompting guide · CrisperWhisper, Sarvam saaras docs, WhisperX, ctc-forced-aligner (licences noted above).
