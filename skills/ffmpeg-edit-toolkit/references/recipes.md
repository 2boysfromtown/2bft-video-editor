# ffmpeg recipes (tested on ffmpeg 9.0.2)

Replace `in.mp4`, `out.mp4` and the numbers. Times are seconds. Every graph below was executed and its output checked (durations, frame comparison, level measurement) unless marked "idea".

## Inspect and measure

```
ffprobe -v error -show_entries format=duration:stream=codec_type,codec_name,width,height,r_frame_rate -of compact in.mp4
ffmpeg -hide_banner -nostats -i in.mp4 -vn -af "silencedetect=noise=-35dB:d=0.4" -f null -
ffmpeg -hide_banner -i in.mp4 -af volumedetect -f null -
ffmpeg -hide_banner -i in.mp4 -af "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null -
ffmpeg -ss 12 -i in.mp4 -frames:v 1 frame.png
```

`volumedetect` gives mean/max volume; `loudnorm ... print_format=json` prints `input_i` (integrated loudness). Frame grabs are how to "look" at a result.

## Trim and join

```
# fast, keyframe-snapped, no re-encode (rough only)
ffmpeg -ss 2 -to 6 -i in.mp4 -c copy out.mp4
# frame-accurate (re-encodes)
ffmpeg -i in.mp4 -ss 2 -to 6 -c:v libx264 -pix_fmt yuv420p -c:a aac out.mp4
# join clips that share codec, size and frame rate
#   list.txt:  file 'a.mp4'  (one line per clip)
ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4
# audio for transcription
ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 audio.wav
```

## Cut list (keep these ranges, drop the rest)

Keep 0-5, 8-12.4 and 20-31 as hard cuts:

```
ffmpeg -i in.mp4 -filter_complex "[0:v]trim=0:5,setpts=PTS-STARTPTS[v0];[0:a]atrim=0:5,asetpts=PTS-STARTPTS[a0];[0:v]trim=8:12.4,setpts=PTS-STARTPTS[v1];[0:a]atrim=8:12.4,asetpts=PTS-STARTPTS[a1];[0:v]trim=20:31,setpts=PTS-STARTPTS[v2];[0:a]atrim=20:31,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac cut.mp4
```

For many segments generate the graph in code and pass it with `-/filter_complex graph.txt` (see `scripts/remove_silence.py`, which does exactly this).

## Dead air / automatic jump cuts

```
python -I scripts/remove_silence.py in.mp4 out.mp4 --dry-run
python -I scripts/remove_silence.py in.mp4 out.mp4 --min-silence 0.5 --pad 0.1
```

Check afterwards: the transcript of `out.mp4` should still read naturally, and no word should start or end abruptly.

## Punch-in zoom (emphasis on an important line)

Zoom 15% from 3.0 s to 5.0 s with 0.25 s ramps. Source 1280x720; use your own width for `1280` and your own size in `crop`:

```
ffmpeg -i in.mp4 -vf "scale=w='trunc(1280*(1+0.15*clip((t-3)/0.25,0,1)*(1-clip((t-5)/0.25,0,1)))/2)*2':h=-2:eval=frame,crop=1280:720" -c:v libx264 -pix_fmt yuv420p -c:a copy out.mp4
```

Verified: frame at 4 s is clearly zoomed (SSIM 0.58 vs the unzoomed frame), and by 7 s it is identical again (SSIM 0.99999). Keep zooms to 5-15%; a few percent is enough for "listen up".

## Speed ramp, slow motion, fast forward

```
# normal 0-2s, 4x for source 2-10s, normal 10-12s
ffmpeg -i in.mp4 -filter_complex "[0:v]trim=0:2,setpts=PTS-STARTPTS[v0];[0:v]trim=2:10,setpts=(PTS-STARTPTS)/4[v1];[0:v]trim=10:12,setpts=PTS-STARTPTS[v2];[0:a]atrim=0:2,asetpts=PTS-STARTPTS[a0];[0:a]atrim=2:10,asetpts=PTS-STARTPTS,atempo=4[a1];[0:a]atrim=10:12,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac ramp.mp4
# whole clip 2x
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/2[v];[0:a]atempo=2[a]" -map "[v]" -map "[a]" out.mp4
# 50% slow motion (shoot 60 fps if you plan this; 30 fps slowed looks choppy)
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/0.5[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" out.mp4
```

Drop the audio (`-an`, remove the `[a]` parts) when the fast section should be silent or covered by music.

## J-cut and L-cut

Picture cuts from A (0-5 s) to B (source 8-12 s) at 5 s.

J-cut: B's sound starts 0.6 s before its picture. Needs B's audio from source 7.4 s, placed at 4.4 s:

```
ffmpeg -i in.mp4 -filter_complex "[0:v]trim=0:5,setpts=PTS-STARTPTS[va];[0:v]trim=8:12,setpts=PTS-STARTPTS[vb];[va][vb]concat=n=2:v=1:a=0[v];[0:a]atrim=0:5,asetpts=PTS-STARTPTS,afade=t=out:st=4.4:d=0.6[aa];[0:a]atrim=7.4:12,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,adelay=4400|4400[ab];[aa][ab]amix=inputs=2:normalize=0:duration=longest[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac jcut.mp4
```

L-cut: A's sound carries 0.6 s into B's picture (B's own sound enters at 5.6 s). Use it when B is a reaction or cutaway, not when B's own speaker is talking in sync:

```
ffmpeg -i in.mp4 -filter_complex "[0:v]trim=0:5,setpts=PTS-STARTPTS[va];[0:v]trim=8:12,setpts=PTS-STARTPTS[vb];[va][vb]concat=n=2:v=1:a=0[v];[0:a]atrim=0:5.6,asetpts=PTS-STARTPTS,afade=t=out:st=5.0:d=0.6[aa];[0:a]atrim=8.6:12,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.2,adelay=5600|5600[ab];[aa][ab]amix=inputs=2:normalize=0:duration=longest[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac lcut.mp4
```

Both need "handles": source footage before the picture in-point (J) or after the out-point (L). Without it, use ambience or music instead of the missing sound.

## Dissolve, fade

```
# 0.5 s cross-dissolve between two 4 s clips (picture and sound); offset = clip1 length - 0.5
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=3.5[v];[0:a][1:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac out.mp4
# fade to black over the last second of a 4 s clip
ffmpeg -i in.mp4 -vf "fade=t=out:st=3:d=1" -af "afade=t=out:st=3:d=1" out.mp4
```

Other `xfade` transitions (`wipeleft`, `slideleft`, `circleopen`, ...) exist; use them sparingly (see `video-editing-craft`).

## Graphic overlay and captions

```
# PNG with alpha fades in at 1 s and shows from 1 s to 3 s, bottom-left
ffmpeg -i in.mp4 -i lower.png -filter_complex "[1:v]fade=t=in:st=1:d=0.3:alpha=1[g];[0:v][g]overlay=x=60:y=H-h-60:enable='between(t,1,3)'[v]" -map "[v]" -map 0:a -c:v libx264 -pix_fmt yuv420p -c:a copy out.mp4
# burn in an .srt
ffmpeg -i in.mp4 -vf "subtitles=c.srt:force_style='FontSize=28,Outline=2,Alignment=2,MarginV=40'" -c:v libx264 -pix_fmt yuv420p -c:a copy out.mp4
```

For animated graphics and kinetic captions, build them in Remotion and overlay the render (see `motion-graphics-for-video`).

## Voice

Chain in the order recommended by the tutorials: remove rumble and hiss, light denoise, even out level, tame harsh S sounds, then protect against clipping.

```
ffmpeg -i in.wav -af "highpass=f=80,lowpass=f=14000,afftdn=nr=10:nf=-30,acompressor=threshold=-20dB:ratio=2:attack=5:release=80:makeup=3,deesser=i=0.4,alimiter=limit=0.89" voice.wav
```

Set the compressor threshold near the quieter parts of the voice (measure with `volumedetect`; the tutorial example used about -20 dB), ratio about 2:1. Keep denoise subtle; heavy denoise makes speech watery.

## Music under a voice

Carve a pocket for the voice in the music, then duck the music while the voice plays:

```
ffmpeg -i music.wav -i voice.wav -filter_complex "[0:a]equalizer=f=1800:width_type=q:width=0.8:g=-4[m];[1:a]asplit[sc][v];[m][sc]sidechaincompress=threshold=0.08:ratio=2.5:attack=30:release=600[bg];[bg][v]amix=inputs=2:normalize=0:duration=longest[o]" -map "[o]" mix.wav
```

Measured on a test tone, music ducked by: `threshold=0.1:ratio=2` about 4.6 dB, `threshold=0.08:ratio=2.5` about 6.6 dB, `threshold=0.05:ratio=3` about 10 dB, `threshold=0.03:ratio=8` about 16 dB (too deep, it pumps). Start at 0.08 / 2.5 and tune with `volumedetect`; results depend on the voice level.

Fade the music in and out and mix onto the video, ending at a loudness target:

```
ffmpeg -i in.mp4 -i music.wav -filter_complex "[1:a]equalizer=f=1800:width_type=q:width=0.8:g=-4,afade=t=in:st=0:d=1.5,afade=t=out:st=14.5:d=2[m];[0:a]asplit[sc][v];[m][sc]sidechaincompress=threshold=0.08:ratio=2.5:attack=30:release=600[bg];[bg][v]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k mixed.mp4
```

(`st=14.5` is the video length minus the fade; set it for your clip.)

## Music endings and transitions

```
# reverb-style tail on the final beat: trim, fade, echo, pad silence so the tail can ring out
ffmpeg -i music.wav -af "atrim=0:4,afade=t=out:st=3.5:d=0.5,aecho=0.8:0.9:60|120|240:0.5|0.35|0.2,apad=pad_dur=1.5" tail.wav
# reversed riser from the first 1.5 s of a track, to lead into a new section
ffmpeg -i music.wav -af "atrim=0:1.5,areverse,afade=t=in:st=0:d=1.5,volume=0.8" riser_rev.wav
```

`aecho` is an approximation of reverb. For a true room sound use a convolution reverb impulse response with `afir`, or a DAW.

## Sound effects

```
# place effects at 4.2 s and 9.0 s over a voice track
ffmpeg -i voice.wav -i whoosh.wav -i hit.wav -filter_complex "[1:a]adelay=4200|4200[w];[2:a]adelay=9000|9000[h];[0:a]aformat=channel_layouts=stereo[v];[v][w][h]amix=inputs=3:normalize=0:duration=first[o]" -map "[o]" sfx_placed.wav
# placeholders
python -I scripts/make_sfx.py whoosh whoosh.wav
python -I scripts/make_sfx.py riser riser.wav --dur 2.5
python -I scripts/make_sfx.py hit hit.wav
```

Place by the loudest point of the effect, not its start: delay = target time minus the time of the effect's peak. Layer a lower and a higher copy of a whoosh (`asetrate`/`atempo` or a different file) so it fills the spectrum.

## Pan a sound across the screen

Left at 0 s to right at 3 s, mono input to stereo output:

```
ffmpeg -i in.wav -t 3 -filter_complex "[0:a]asplit[a][b];[a]volume='clip(1-t/3,0,1)':eval=frame[l];[b]volume='clip(t/3,0,1)':eval=frame[r];[l][r]amerge=inputs=2[o]" -map "[o]" pan.wav
```

## Muffle through a wall or phone

```
ffmpeg -i in.wav -af "highpass=f=300,lowpass=f=3000" phone.wav     # small speaker (runs; judge by ear)
ffmpeg -i in.wav -af "lowpass=f=800,volume=0.6" wall.wav           # other side of a door (runs; judge by ear)
```

## Loudness and delivery

```
# one pass to about -14 LUFS integrated, -1.5 dBTP (common streaming target; check the platform's current guidance)
ffmpeg -i in.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 out.wav
# delivery encode, 16:9 or any size
ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -ar 48000 -movflags +faststart final.mp4
```

Always listen on more than one speaker (laptop, phone, headphones) before calling a mix finished; a measurement does not replace that, and an AI agent cannot do it. Say so in the report.
