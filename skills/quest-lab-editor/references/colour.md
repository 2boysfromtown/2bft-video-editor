# Colour — grade the webcam only, normalise what you insert

Merged 27 Oct 2026 (sources at the end). The QUEST LAB look comes from the graphics (blue dot grid, stickers, ink). The footage only needs to look *correct*: true skin, clean whites on the screen share, consistent from shot to shot.

## 1. Classify before you touch anything
- **Screen recordings: little or no grading.** A skin-friendly warm grade turns white web pages yellow and makes code harder to read. The engine already applies a tiny global lift to every pane (contrast ×1.06, saturation ×1.06, brightness 1.01); leave the screen at that.
- **Webcam: grade separately.** Set `cam_grade` in the plan (or once in `source.json` for a whole stream). Only webcam panes and face bubbles get it:
  ```python
  PLAN = dict(..., cam_grade=dict(contrast=1.03, bright=1.02, grade='saturate(0.95) hue-rotate(-3deg)'))
  ```
  `contrast` and `bright` multiply the engine's defaults; `grade` is any CSS canvas filter string (`saturate()`, `hue-rotate()`, `sepia()`, `brightness()`, `contrast()`). With no `cam_grade` nothing changes. Tested 27 Oct on S09 stills: background, captions and hook are untouched.
- **Inserted media** (phone clips, Google Flow renders, other episodes, Leela): normalise first (§4), then judge.

## 2. Measure, don't eyeball
Grab 3 webcam frames in different moments (`tools/grab.py`, crop the cam rect) and measure the luma percentiles:
- exposure from the **median** (aim ~110–140 of 255 on the face);
- contrast from the **10th–90th spread**;
- blacks lifted if the darkest 1 % sits above ~8; whites pulled if the brightest 1 % sits below ~245;
- colour cast measured separately in shadows, mids and highlights (mean R/G/B in each third).
Our host's webcam (25 Oct stream) already reads warm/red on skin under the room light — the correction usually goes **toward neutral** (slightly less saturation, a few degrees of hue toward yellow-green), never warmer.

## 3. Correction order and the skin gate
1. White balance / cast (`hue-rotate`, or `colortemperature` in ffmpeg for manual work).
2. Tint.
3. Exposure (`bright` within ±0.06; prefer midtone lifts over raising blacks).
4. Saturation / vibrance (protect skin: small steps).
5. Contrast or curves last (curves need anchor points at both ends or they blow out).
**Skin gate** on 2–3 frames: average skin hue moves < 6° and saturation < 25 % from the ungraded frame → pass. Otherwise halve the strength and re-check; if it still fails, the white balance is wrong — go back to step 1. Before choosing a look, render a small still menu (each candidate on 2 differently lit frames) and let the user pick.

## 4. Normalise inserted clips before they meet the edit
Probe every inserted file: `ffprobe -show_entries stream=pix_fmt,color_range,color_space,color_transfer,color_primaries`.
- Full range (`yuvj420p`, `color_range=pc`) → convert to limited (tv) range; BT.601 → BT.709. Mismatches show as crushed or lifted blacks (QC codes BLACKS-CRUSHED / BLACKS-LIFTED).
- HDR phone clips (HLG `arib-std-b67` or PQ `smpte2084`) → tone-map to SDR BT.709 *before* use, or colours wash out. Example: `zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`.
- Keep intermediates high quality: three chained CRF-23 encodes measurably lose quality (≈ 91 → 82 VMAF in one test). The engine reads source frames as q2 JPEGs and encodes once — keep it that way.

## 5. Delivery
The engine encodes BT.709, TV range, yuv420p and tags it. Blue gradients and the vignette can band at streaming bitrates — the film-grain layer already masks this; don't remove it. Judge the grade in a real player on a phone, not only in a PNG.

## Sources (ideas re-derived; licences checked 27 Oct 2026)
louisedesadeleer/color-correct (no licence — ideas only, no values copied) — classify layers, measure percentiles, fixed order, skin gate, look menu · erichowens/some_claude_skills video-processing-editing (MIT) — colour-space normalisation, HDR tone-map, generation loss · MovieLabs QC vocabulary — BLACKS-LIFTED / CRUSHED, BANDING.
