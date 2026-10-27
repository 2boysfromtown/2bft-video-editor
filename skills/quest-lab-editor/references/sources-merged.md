# What was merged from the web on 27 Oct 2026 — and what was not

The host asked to find existing editing skills and `.md` guides on the internet and merge the useful parts. Three research passes read ~50 sources: published agent skills (SKILL.md / AGENTS.md / rules), open-source clipping and caption tools, and human editing standards. Everything was **re-written in our own words** and adapted to Hinglish screen + webcam streams and this engine — no text or code was copied, nothing was installed, and no installer from any of these projects was run.

## Where each idea landed
| source | licence | what we took (ideas only) | where |
|---|---|---|---|
| browser-use/video-use | MIT | packed transcript, timeline view at decision points, auditable plan fields, session log, sub-agent briefs, cut-boundary self-checks | `cutting.md` §2, `workflow.md` §1/§4/§6, `templates/agent-brief.md`, `tools/packed_transcript.py`, `tools/timeline_view.py` |
| heygen-com/hyperframes skills (review, motion, film, captions, sound, overlays, motion-doctrine) | Apache-2.0 | severity review loop, fresh reviewer, seam law, reserved directions, no idle wobble, timing numbers, beat-grid maths, causal transitions, text-behind-speaker, contrast by brightness, hallucination-over-silence filter | `review-qa.md` §1–2, `motion-and-zooms.md` |
| louisedesadeleer/cut-video | MIT | noise-floor threshold, gap table, pads, retake detection, protect reactions, density self-check, second-ASR diff | `cutting.md` §3–5, `tools/pauses.py` |
| louisedesadeleer/b-roll-finder, add-zooms, clipify | MIT | sliver rule, late bias for cutaways, approved-beats manifest, time-boxing, punch/ratchet/Ken Burns, face upscale cap, check audio events against a frame | `cutting.md` §7–8, `motion-and-zooms.md` §7, `review-qa.md` §9 |
| louisedesadeleer/color-correct | **none stated** | ideas only, no values: classify layers, measure percentiles, correction order, skin gate, look menu | `colour.md` |
| OpenMontage | **AGPL-3.0** | ideas only: error-class sweep, 2-round stop rule, decision log with alternatives, speed by activity, 1.0→1.02 jump-cut shift, sample-first render | `review-qa.md`, `cutting.md` §6, `workflow.md` §4 |
| HotClip | **AGPL-3.0** | ideas only: per-export QC report, repair kept only if it improves, golden set, reference-clip targets | `review-qa.md` §1/§9, `tools/qa_detect.py` |
| erichowens/some_claude_skills (video-processing-editing) | MIT | colour-space normalisation, HDR tone-map, generation loss | `colour.md` §4 |
| connerkward/screenstudio-alternative-skill | MIT (per registry) | idle speed-up from freeze detection, capture-time cursor logs | `cutting.md` §6/§9 |
| WyattBlue/auto-editor | Unlicense | margins, smoothing, motion-based cutting | `cutting.md` §3 |
| ClipsAI, AI-Youtube-Shorts-Generator | MIT | topic-shift boundaries, 2× candidates, overlap de-dupe, hook sentence, static crops per segment with a 4 % merge rule | `workflow.md` §5 |
| faster-whisper, WhisperX, stable-ts, arXiv 2509.09987, FA-Bench | MIT / BSD-2 / MIT / paper / preprint | Whisper timing error and early bias, hotwords, hallucination threshold, forced-alignment options | `cutting.md` §1, `tools/transcribe_words.py` |
| Netflix Timed Text Style Guides (timing, general, English USA, Hindi) | public spec | gaps, in/out, shot-change snapping, durations, line breaks, reading speed, spoilers | `review-qa.md` §4, `tools/check_srt.py` |
| MovieLabs QC Vocabulary | public spec | QC codes for video, audio, timed text | `review-qa.md` §8 |
| W3C WCAG 2.2 (2.3.1), Ofcom/ITC, ASA | public | flash and red-flash definitions, 25 % area, patterns, duration | `review-qa.md` §5, `tools/qa_detect.py` |
| EBU R128 s1, Netflix sound spec | public | short-term ceiling (+5 LU), dialogue-gated consistency | `review-qa.md` §6 |
| YouTube Help + Blog | official | upload encode spec (AAC 384 kbps → engine changed), Test & Compare rules, Studio trim, Related video, inauthentic-content policy, Shorts/claims | `review-qa.md` §7/§10, `workflow.md` §5, `engine/render.py` |
| Instagram creators site | official | originality, watermarks, Trial Reels, 3-minute Reels | `workflow.md` §5 |
| Production Expert/iZotope, Sound On Sound | practitioner | dialogue chain and de-esser starting values | `review-qa.md` §6 |

## Deliberately left out
- **Unsourced statistics** (completion-rate tables, "distribution multipliers", "visual change every 3–5 s", "pattern interrupt every 10–15 s", Hormozi "style specs" from caption vendors): they contradict each other and cite nothing. The skill keeps its own measured rules and the retention graph.
- **Vendor virality scores** (OpusClip etc.): black boxes; only their named factors (flow, trend) were kept as rubric lines.
- **Non-commercial models** (CrisperWhisper weights, default MMS/ctc-forced-aligner models, FA-Bench data): not usable on a monetised channel without a licence check.
- **Installers and auto-setup prompts:** video-use's install flow force-links into global skill folders and runs unpinned `npx`; cut-video and add-zooms install toolchains on first run. None were run. Several skill directories (skills.sh, claudskills, skillselion, vibeindex) offer one-line installers — none used.
- A skills.sh page ("retention-editing") contained instructions aimed at AI agents; ignored as data.
- BBC subtitle numbers (teletext-era, second-hand copy) — Netflix's streaming rules were used instead.

## Open items worth a later look
- Text-behind-speaker needs a person-segmentation matte (not installed).
- Forced alignment for exact cut points in Hinglish needs a commercially licensed aligner.
- Whether YouTube Studio offers a "Hindi (Latin)" caption language for `.hi-Latn.srt` — check once in Studio.
- Sarvam saaras `translit` / `codemix` mode as a second opinion in `lang_arbiter.py` (paid API — ask first).
