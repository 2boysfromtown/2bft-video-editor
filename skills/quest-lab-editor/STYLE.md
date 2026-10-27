# QUEST LAB — the <your show> style

Approved by the host on 2026-10-25 (style frames + motion test).

**Essence.** <your show> brings the energy: the host live, reacting, gamified ("Quest of the Day", follower goal). The lab brings the honesty: builders, not gurus — show the work, show what broke. Every video is **a quest run live in the lab**: a goal, attempts, fails, loot, an honest result.
**What it is not.** Not a template with random effect packs; not hype-guru editing; not the raw stream layout re-uploaded; not wall-to-wall shake.

## 1. Colour (taken from the host's own stream overlay: use yours)
| Token | Hex | Job |
|---|---|---|
| Blue | `#4282F0` | the world: background field with the dot grid (dots `rgba(12,32,96,.32)` every 22 px) |
| Blue deep | `#2A60E4` / `#173E9E` | meter tracks, depth |
| Mint | `#12EABB` | the one accent shared by both brands: keywords, quest header, wins, success ticks |
| Ink | `#0B1220` | outlines, hard shadows, dark plates, text on mint |
| Ivory | `#F7F5EF` | text |
| Red | `#FF4A3D` | only fails: FAILED/DABBA stamps, ✖ steps, error words |
| Yellow | `#FFD23F` | only loot and numbers: LOOT tags, ₹/% figures, challenge chip |
Mint text never sits on light UI without a dark plate (contrast 1.4–1.6:1).

## 2. Type
- **Bahnschrift Bold Condensed** (`Bahn`, `fontStretch: condensed`): quest titles, level cards, stamps, labels, meters — the game-HUD voice.
- **Inter Black 900**: captions and slams. Sentence case; ALL CAPS only for the emphasised word.
- **JetBrains Mono Bold**: the lab layer — prompts (typecards), `// lab notes`, model/tool labels, the grey `(commentary)` layer, LEVEL numbers.

## 3. Materials: the sticker system
Flat colour blocks with a **4–7 px ink outline and a hard ink offset shadow (6–14 px)**, small radius, slight tilt (−3°…+3°). Footage sits in such cards on the blue world, tilted ±0.6–2°. Subtle film grain (4.5 %) and vignette on every frame.

## 4. Framing (the raw stream layout never appears)
16:9: **SCREEN** (screen full-bleed with 4 % overscan, push-ins to the exact UI that matters, cam sticker) · **STAGE** (screen card + tall cam card — use sparingly, it echoes the stream) · **FACE** (cam is the show, big slams on the right) · **LOOT** (an output from the original file, cam reacting) · **VERSUS** (reference vs result + VS badge).
9:16: **v_split** (proof top y 300–900, face card below, captions on the seam ~y 905) · **v_face** (face card y 270–1570, captions over the chest ~y 1150) · **v_loot** (output top, face below) · **v_output** (a 9:16 output full frame + face bubble) · **v_screen**.
Safe box for Shorts + Reels: x 65–850, y 288–1248; keep the right 230 px of the lower half clear.
Webcam source is 388×765 px: never upscale more than ~2.5×; switch layout on story beats (face when emotional, screen when showing proof).

## 5. Motion
- Elements enter with a spring (overshoot settle) in 8–12 frames, exit in 6–8. New things arrive from the right/left consistently within a piece.
- **Transition grammar:** hard cuts by default; the **LEVEL card** (blue dot-grid panel wipes across the cut, mint/ink edge, "LEVEL nn" mono sticker, title slam, giant outlined number) for chapters; **whip** (blurred push) for fast jumps; **glitch** only on machine moments (AI thinking, errors). No dissolves except into/out of black.
- **Energy camera** (signature): hum / shake / impact from the measured energy map, impacts with 3-frame hit-stop + RGB split + zoom kick + flash. Footage layer only. Budget: ≤ 5 % of a long video shaking, ≤ 10 % of a Short; ≤ 2 auto impacts per piece; ≥ 3 s between hits.
- Push-ins: base 100 % → punch 112–125 %; come back out for the next idea; never two punches in a row.

## 6. The Quest HUD (signature graphics)
- `quest` tracker: mint header "QUEST · <goal>", steps that tick ✔ (mint + ding) or fail ✖ (red + strike + buzzer) at the moment they happen.
- `meter`: the follower-goal bar reused for **real** numbers only (Claude weekly limit 1 % / 3 %, progress).
- `chip`: "25 NOV · 30-DIN CHALLENGE" (the birthday deadline, the series device).
- `stamp`: FAILED / DABBA! (red), LOOT (yellow), QUEST ACCEPTED / QUEST COMPLETE (mint).
- `level` cards = YouTube chapters. `typecard` = his prompt re-typed so it is readable. `note` = `// opus 5.5 · unreal mcp · 31:02` provenance.
- End card: your show name as an ivory sticker (`brand=`) + a mint partner sticker (`partner=`, `''` for none) + handle + next-quest line.

## 7. Captions
Shorts: Roman Hinglish chunks of 1–4 words, Inter 900 at 80–110 px with ink stroke (20 % of size) and soft shadow; one keyword sticker per chunk max (mint = key, red = fail word, yellow = numbers/₹/%); words pop 1.12→1 (keyword 1.28→1) in 110 ms; strike-through for corrections; grey mono `(commentary)` for the editor's voice.
Long-form: no full subtitles (upload SRTs instead); 6–10 key-line slams per video at 90–110 px, plus labels and notes.

## 8. Sound palette
- Voice: HPF 80 Hz, presence lift, leveller + light compression, −14 LUFS master, true peak ≤ −1.5 dBTP.
- Music: licensed tracks switched per chapter (phonk/hype for cold opens, steady electronic under building, comedic pizzicato under fails, cinematic drop on reveals, chill under reflection); **music stops dead before punchlines**, tape-stop on fails, drop lands on reveals; 18–24 dB under the voice, up in gaps.
- SFX mapped to graphics: pop (stickers/keywords), whoosh (level cards, whips — peak on the cut), slam (titles), stamp thump, fail buzzer, record scratch (freeze on fails), ding (quest step done), ticks (meters), typing (typecards), marker squeak (circles), bass hit / impact / boom (reveals and energy impacts), glitch (machine moments), sparkle (loot), level-up (quest complete).
- Voice FX: echo throw on a punch word followed by ≥ 0.5 s silence (taps ~300 ms, decays .45/.25/.12, darker each repeat, ping-pong); "voice of god" reverb on the one moral line; telephone EQ when he reads Claude's reply; bleep on strong swears.

## 9. Native moves (one per piece, at its peak)
- **The DABBA moment:** freeze on the fail + record scratch + red stamp + echo throw on the punch word.
- **The loot reveal:** riser → 2-frame black → drop + impact + full-quality output with a slow push.
- **The level wipe:** the overlay's blue world sweeps across the cut carrying the chapter title.

## 10. Pitfalls seen
Webcam crops that cut the face (crop the cam rect to the face, not the full cam column); empty right halves on FACE layouts (fill with a big slam or a screen card); unreadable Claude UI text (re-type prompts as typecards, push in); the stream layout reappearing (prefer SCREEN/FACE/LOOT over STAGE); trending songs baked in (never).

## 11. Series skin — CRASH TEST ("Testing Claude until it fails", from EP 02, 27 Oct 2026)
A layer on top of QUEST LAB for his test series (same world, colours, stickers, fonts). Every segment is a numbered TEST that ends in a verdict, so each one is a question the viewer stays to see answered, and the next test is always teased.
- Series card after the cold open: `level` `kicker='TESTING CLAUDE'`, `title='UNTIL IT / FAILS'`, `sub='// EP nn · <your show>'`.
- Test cards: `level` `kicker='TEST 01'` …; test log HUD: `quest` `kicker='TEST LOG'` (tick on each verdict).
- Verdict stamps on the reveal frame: PASS (mint) · FAIL (red — only when it really failed) · NEXT EP (yellow, teases). Optional sub-line with the honest condition ("after a 0.90 loop").
- Hazard `tape` band (yellow, static chevrons): series name, section labels, "NEXT TEST · EP nn". Shorts: under the hook (y ≈ 365) for the first ~2.5 s — never at the bottom (collides with chest captions).
- CTAs are his own lines (comment "SKILL", "kitna time lagega", subscribe); editorial chips may point at them, never speak for him.
- Cold open = the episode's best payoff as a flash-forward, labelled with a tape ("TEST 04 · THE ONE THAT MADE ME DANCE"). End = NEXT TEST tease + endcard.
