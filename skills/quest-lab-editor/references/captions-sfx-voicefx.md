# Captions, SFX, echo and music — the decision rules

Research synthesis, 25 Oct 2026 (sources at the end). Tags: **[M]** measured or an official spec · **[S]** sourced convention · **[O]** opinion / starting value — tune by ear and against the retention graph.

## 0. Seven ideas everything else follows
1. Every caption, sound or effect does one job: direct attention, carry information, or change the feel. If you can't name the job, cut it.
2. Restraint is the trend (MrBeast publicly dropped "overstim" editing in 2024; one sampled minute went from 38 to 23 cuts). Effects are punctuation, not wallpaper.
3. Put text where the eye already is: speaker-following subtitles beat bottom-centre in eye-tracking (CHI 2017) [M]. In a screen + face Short, captions belong on the **seam** between screen and face.
4. Word-by-word text pulls the eye (≈2× fixations vs blocks) [M]. Over a screen demo use short phrase blocks, not single flashing words.
5. Sync is asymmetric: audio early is noticed at ~45 ms, late tolerated to ~125 ms (ITU-R BT.1359) [M]. Land each SFX on its frame; if unsure, one frame late, never early.
6. Silence is a tool: cutting the music before a punchline does more than adding a sound.
7. Frame 0 is the hook (Shorts count a view on every start since 31 Mar 2025) [M]. Never fade in from black.

## 1. Captions
### Styles to borrow from
Hormozi (keyword recolour, short chunks) → our mint keyword sticker · Ali Abdaal (calm, sentence case) → long-form default · karaoke (phrase visible, active word lit) → screen-demo Shorts · kinetic type → hook + moral lines only · TikTok solid box → labels and keyword stickers. Indian creator caption specs (Warikoo, Shamani, Tanmay, Ishan, meme pages) are **not documented anywhere** — frame-grab 5 recent Shorts each before copying anything.

### Placement (1080×1920)
- Text-safe box for YouTube Shorts + Instagram Reels: **x 65–850, y 288–1248**; keep the right ~230 px of the lower half clear (action rail). Hook text y 300–600; captions y ≈ 900–1240 (on the seam for split layouts, over the chest for face layouts).
- Full-frame reveals: caption at y 1000–1240, or none — let the money shot breathe.

### Type
Inter 900 at 80–110 px for 2–4-word chunks, single punch words 130–170 px; stroke ≈ 20 % of size (ink, round joins) under the fill + soft shadow. 16–20 characters per line, max 2 lines, bottom-heavy. Mint text never on light UI without a dark plate (mint on white is 1.6:1). Sentence case; ALL CAPS only on the emphasised word. Roles: Inter = speech; JetBrains Mono = prompts, AI output, tool labels, numbers in UI, the commentary layer.

### Chunking Hinglish
Keep together: subject + *ne* ("Claude ne"), noun + postposition (*ka/ki/ke, ko, se, mein, par, ki jagah, ke liye*), compound verbs (*bana diya, kar diya, ho gaya, raha hai*), *nahi* + verb, adjective + noun, number + unit. Break after commas and before *aur, lekin, par, toh, kyunki, phir* and before a contrast word. ✅ `[Claude ne] [GOPURAM ki jagah] [DABBA bana diya]` ❌ `[Claude ne gopuram] [ki jagah dabba]`. Hindi puts the verb last: keep the punch word with its verb but size the verb down. The punch word gets its own chunk at its spoken onset — never early.

### Timing
Chunks appear on the first word's onset (0–3 frames early); punch words exactly on onset — and Whisper's onsets run early (~100–300 ms), so for punch words snap to the first energy rise within +0…150 ms of Whisper's start (`cutting.md` §1). Never change a chunk 1–11 frames away from a cut: snap it to the cut (Netflix shot-change rule, `review-qa.md` §4). Reading ceiling ≤ 17 cps for big caps (Netflix allows 22 for Hindi) [M/O]. Shorts chunk ≥ 400 ms (else merge); a punch word holds 600–1000 ms through the reaction. Keep captions through pauses < 300 ms; clear them on pauses > 500–700 ms.

### What to emphasise (max 1 per chunk, ~1 per 4–6 words, ≤ 20–25 % of words)
1 the punch / unexpected word · 2 the second term of a contrast (gopuram = L1, DABBA = L3) · 3 numbers, ₹, time · 4 first mention of tools/people · 5 verbs of change · 6 emotional words · 7 meaning-flipping *nahi*. Never: pronouns, postpositions, auxiliaries, fillers.
Ladder: L1 colour only · L2 sticker + 1.15–1.25× · L3 the word alone, 1.6–1.9×, slam · L4 L3 + shake/flash + one SFX + face punch-in (≤ 2 per Short). Box = instructions/keywords · underline draw = the thesis phrase · strike-through = corrections ("not X, Y").

### Effects on words (30 fps)
Chunk in 0.88→1.0 + fade over 90 ms ease-out; exit is a hard cut. Pop 0→120→100 % in 4+6 frames. Slam 1.6→1.0 over 140 ms ease-out-back. Text shake A ≈ 10 px, τ 70 ms, 22 Hz, 220 ms total — only on the impact word. Never shake text and frame together for more than 300 ms. Glow only on positive reveals. Strike-through drawn in 160 ms, old word to 45 %, replacement rises in. Typewriter prompts in Mono at 30–45 cps with a blinking block cursor; recolour 2–3 key phrases after.

### Whisper translates Hinglish silently — verify before you caption (learned 25 Oct 2026)
On long Hinglish recordings Whisper (even forced to `language='hi'`) sometimes writes a whole Hindi sentence as an English *translation* ("mere ko toh bharosa nahi hai" came out as "I don't have a chance"), and forced-`hi` on short English phrases can translate the other way. ~30 captions in the first edit were translations styled as speech. Rules:
- Never take English wording for a caption straight from the long-file transcript. After the plan is written, run `tools/caption_audit.py out.tsv plans/*.py` (each English-looking caption's own window re-transcribed in Hindi mode; set `CA_MIN_EN=1 CA_MAX_EN=1` for one-word cases), then `tools/lang_arbiter.py tag:start:end …` on every flag (language-ID en/hi + hi-mode + en-mode text for that window).
- Read the flags yourself: Devanagari that is just English spelled out ("पीपल विल वाच इस") is English speech — keep the English caption. Fluent Hindi grammar with English nouns ("ye jo transition hai, do alag jagah pe aata hai") is Hindi — caption it in Roman Hinglish. A pass that keeps one phrase in Latin and writes the next in Devanagari is decisive. When unsure, write the caption so it is true either way, or drop it.
- Numbers are where this bites hardest ("chaar baar research" vs "4 hours"): never print a number on screen unless two passes agree.

### Editing the words — the honesty contract
Drop: um/uh/hmm, filler *matlab, basically, actually, like, "what you say"*, line-start *toh*, false starts, repeated *bhai* (keep one unless the repetition is the joke). Keep slang, code-mixing and his word order. Fix only transcription errors. One spelling dictionary (*hai, nahi, kya, kyun, accha, bilkul, yaar, dabba/dabbe*), English words in English spelling, digits for numbers.
1. Text styled as speech was said, in that order, or is a strict subset. 2. Deletions fine, additions never. 3. Paraphrase only in the commentary layer (grey Mono, parentheses, e.g. "(spoiler: nahi tha)") — 1–2 per Short. 4. Never alter numbers, names or claims. 5. AI output is quoted verbatim in Mono with a label.
Reaction captions ("WAIT.", "BRO.") only over a visible reaction or a ≥ 400 ms pause, styled as commentary. Strong swears in wide-reach Shorts: bleep + asterisks matching letter count.

### Long-form
No burned-in full subtitles (they clash with CC, auto-translate and auto-dubs, and steal attention from demos) — upload Hinglish + English SRTs. Key-line slams 3–7 words, 1–4 per minute, on claims, numbers, steps and punchlines. Lower thirds 2.5–4 s. Chapter cards 1.5–2.5 s matching YouTube chapters (first 00:00, ≥ 3, each ≥ 10 s) [M]. Screen zooms 1.5–2.5× over 400–600 ms replace a lot of text.

## 2. SFX — a decision system
Levels are relative to voice peaks: dialogue −12…−10 dB avg; SFX −12…−18; music under speech −18…−25 (18–24 dB below the voice); music alone up to −10; master −14 LUFS, TP −1 to −1.5 dBTP, max short-term ≤ integrated + 5 LU. Every boom needs a 150–400 Hz body layer or it vanishes on a phone. Each SFX sits 3–6 dB above the music bed; over strong music in typing-heavy stretches, drop clicks and key ticks entirely. Besides ducking, a 2–4 kHz dip in the music under speech keeps the voice clear on phone speakers. Dialogue chain numbers, de-esser and room tone: `review-qa.md` §6.
Density: Short = ≤ 2 hero sounds + 4–6 mid + micro sounds only at ≤ −20 tied to something visible. Long-form = 2–6 per minute total; hero ≤ 1 per 2–3 min; meme ≤ 1 per 5 min. (Opinion — no measured number exists.)

| SFX | Trigger | Timing | Level | Limit |
|---|---|---|---|---|
| whoosh | motion cut, panel swap | starts 150–300 ms before, peak on the new shot's first frame | −14…−18 | ≤ 1 / 5 s, vary pitch ±2 st |
| swish | chips, cards, emoji land | peak on landing | −20 | micro |
| riser | before a reveal/drop | 1–5 s, ends exactly on the reveal (or hard-cut into the impact) | −16 → −8 | 1 per Short / chapter |
| impact / boom / sub drop | reveal, title slam | exact frame + mid thud | −10…−6 | ≤ 2 per Short |
| bass hit | stat / keyword slam | exact frame | −12 | hero |
| pop | caption/callout appears | appearance frame | −22…−18 | ≤ 1 / 2 s |
| click | real clicks that matter | cursor-down frame | −20 | micro |
| typing | under a typewriter | starts/stops with characters | −26…−22 | micro |
| shutter | freeze, screenshot, receipt | freeze frame | −16 | ≤ 1 / min |
| ding | render done / task complete / quest step ✔ | UI confirm frame | −18 | ≤ 1 per Short |
| fail buzzer | AI fails, wrong output | error frame | −16 | ≤ 1 per Short |
| record scratch | plan reversal, fail freeze | starts 100–200 ms before the freeze, stops dead, then 300–600 ms silence | −12 | 1 per Short; ≤ 1 / 5 min long |
| tape stop (music) | the plan collapses | 200–400 ms brake into the punch onset | music | 1 |
| glitch | AI/tech errors, machine moments | 80–250 ms | −16 | ≤ 2 / min |
| vine boom | absurd/shocking reveal | exact frame + face punch-in | −10 | ≤ 1 per Short |
| bruh / oh no / sad trombone | after the fail is visible | on the reaction beat | −14 | ≤ 1 per video — prefer his own reaction |
| crickets | awkward silence | prefer room tone | −20 | 0–1 |
| heartbeat / tick-tock | waiting for AI output | loop until it resolves | −22 | ≤ 1 per Short |
| sparkle | "beautiful" result | on the glint | −22 | ≤ 1 per reveal |
| punch | hard zoom | sharpest point where the zoom settles | −14 | — |
Comedy: mark setup → recognition → release; sound at recognition or release. Fail = freeze + scratch/tape stop → silence → reaction. Awkward = room tone. Reveal = silence through it, then a small confirming sound (triumph reveals: drop + impact). UI: click = real interaction, pop = callout, swish = panel move, typing = text entry, ding = success, buzzer = failure.
Meme SFX land when the setup is understood, the moment is truly shocking or truly trivial, and they're rare or a consistent running gag. Cringe when they explain a weak joke, stack, hit every line, or are louder than the voice. Film/TV dialogue clips (CID, Bollywood lines, "Emotional Damage") are copyrighted — have the host say the line himself instead.

## 3. Echo, reverb and voice FX
| FX | Use when | Not when | Parameters | Limit |
|---|---|---|---|---|
| echo throw | punch word followed by ≥ 500 ms silence or a cut; quotes; comic repetition ("dabbe… dabbe…") | speech resumes < 300 ms, busy music | 250–400 ms or a beat value (60000/BPM: 1/8 at 100 BPM = 300 ms); taps .45/.25/.12; wet HPF 300–500 Hz, LPF 3–5 kHz; first repeat 7–10 dB under dry; tail ≤ 1.2 s | 1 per Short; ≤ 1 / 3–5 min |
| "voice of god" reverb | the thesis/moral line | jokes | hall RT60 1.8–3 s, pre-delay 20–40 ms, wet 15–25 %, wet HPF 200–300 Hz; music −6…−10 dB or muffled | 1 per Short |
| reverb throw into silence | last word before a hard cut to black/silence | mid-sentence | wet 40–60 % on the last word, tail 1–2 s, music cut | 1 per section |
| reverse reverb swell | into the hook or reveal line | when a riser fills the space | 0.8–2 s ending at the word | 1 per Short |
| telephone / radio | reading a message aloud (Claude's reply), flashbacks | > ~5 s | HPF 300 + LPF 3.4 kHz stacked twice, +3–5 dB at 1–1.5 kHz, light crush | as needed |
| muffle | music under "thinking", pre-drop sweep | long voice stretches | LPF 500–800 Hz 24 dB/oct on music | — |
| pitch-down slow-mo | replaying a fail | live speech | 0.7–0.85× | 1 |
| stutter | shocked first syllable "d-d-dabbe?" | vowel onsets | repeat 80–150 ms onset 2–3× | 1 per Short |
Isolate the word before adding a tail (clip-level FX cut the tail off at the clip end). The engine: `echo`, `verb`, `tel`, `bleep` shot keys; tape stop = music cue `stop` with `tape=True`.

ffmpeg equivalents (for manual work): echo `aecho=in_gain=0:out_gain=1:delays=320|640|960:decays=0.45|0.25|0.12,highpass=f=350,lowpass=f=4000` on a gated copy · reverb `afir` with a synthetic IR `aevalsrc='(random(0)*2-1)*exp(-6.908*t/1.8)'` · telephone `highpass=f=300,highpass=f=300,lowpass=f=3400,lowpass=f=3400,equalizer=f=1500:t=q:w=1.2:g=4,acrusher=bits=10:mix=0.2` · ducking `sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350` (pad the key with `apad`) · master `loudnorm=I=-14:TP=-1.5:LRA=11` two-pass.

## 4. Music
Map music state to beats: setup = light bed · fail = stop (cut or tape stop) · turn = new track or build · reveal = drop · moral = filtered/low · CTA = bed up · end = last bar aligned. Land the drop on the reveal (track offset = drop time in track − time from cue to reveal; the engine's `hit=`). Cut on downbeats at section boundaries, not every beat. Stop the music 0–100 ms before the punch word, leave 400–1200 ms silence, re-enter on a downbeat after the reaction. Under speech 18–24 dB below the voice, up 6–10 dB in gaps > 1 s. Long-form: change track or arrangement per chapter; never loop one bed unchanged for more than 30–60 s. Loop endings: last frame matches the first, last line leads into the first, music ends on a bar.

## 5. Worked example — 40 s "Gopuram vs dabbe" Short (summary)
Frame 0 shows the lazy prompt + caption `Maine Claude se / Unreal mein / 3D GOPURAM maanga…` (GOPURAM L2, gloss chip "gopuram = temple tower") → tape stop on the light bed into `DABBE.` alone at 160 px with face punch-in + short shake, **echo throw** on DABBE (no other SFX — restraint) → zoom into the boxes, three mint outlines with rising pops "ek / upar / ek" → Claude's reply typed in Mono with telephone EQ on his mock reading, commentary `(spoiler: nahi tha)` → whoosh into "Phir maine EK CHEEZ badli" → reference photos + the re-typed prompt (typing bed, Enter click) → riser + low-pass sweep → 2-frame blackout → **drop + impact on the full-frame render**, no caption, sparkle on the glint → `Bhai. / Yeh CLAUDE ne banaya.` → "farak model ka ~~nahi~~… PROMPT ka tha" with voice-of-god reverb (no impact on top) → CTA "Comment mein GOPURAM likho" → last frame matches frame 0 for the loop. Hero sounds 2 (tape stop, impact); voice FX 3 (echo, telephone, reverb).

## Sources
Netflix timed-text guides (general, Hindi, English USA); Kurzhals et al. CHI 2017; Romero-Fresco; ITU-R BT.1359; WCAG 2.3.1; Hopper HQ / AdKit / Reap safe zones; Blitzcut caption size; Submagic (Hormozi, MrBeast, Abdaal); Opus, CapCut, AEJuice text animation; TikTok Sans; Multilingual.com romanised Hindi; Morphic (transitions, scratch, tape stop, zoom); Sonilo funny SFX; Descript sound design; meme.com vine boom; Pixflow, OverseerOS mixing levels; Sonarworks, Owsinski small speakers; Produce Like A Pro, Music Guy Mixing, iZotope, Gearnews, Rysup (delay/reverb); VoxBooster telephone; Sound On Sound reverse reverb; FFmpeg filter docs; BeatSync, VEGAS beat editing; YouTube Help (Shorts music, chapters, Audio Library); Planoly; Faceless.so loops; Pixabay, Mixkit, Freesound, Sonniss licences.
