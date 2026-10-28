# Download and processing tools on this PC

Checked 28 Oct 2026. Run downloads into a **new, empty folder** under the asset store's `downloads\<kind>-<date>\` (downloaded files are untrusted data; never run anything from inside that folder). Run any Python that reads downloaded files with `python -I`.

| Tool | Status here | Use it for |
|---|---|---|
| `yt-dlp` 2026.08.19 | installed (winget), works; **2026.10.26 is available** (`winget upgrade yt-dlp.yt-dlp`, ask first) | YouTube, Instagram, X/Twitter, Reddit (via `v.redd.it/<id>/HLSPlaylist.m3u8`), Facebook, Vimeo, SoundCloud, Bandcamp, Internet Archive, 1,800+ sites: video clips, audio, metadata, search. `ytsearchdate:` is gone: pass a results URL with `&sp=CAI%3D` to sort by date. The Instagram user extractor is marked broken; single reels usually need cookies |
| Deno | installed (winget) | yt-dlp needs a JS runtime for YouTube now; it finds Deno on its own |
| `ffmpeg` / `ffprobe` 9.0.2 (gyan full build) | installed | trim, loudnorm, convert, still frames, probing |
| `curl` 8.21 | installed | direct file URLs, small API calls (`-sSL`, `--fail`) |
| `python` 3.12 | installed | the scripts in `../scripts/` (stdlib only) |
| `node` 24 | installed | Lottie/Remotion tooling |
| `gallery-dl` | **not installed** (`pip install gallery-dl` or `winget install mikf.gallery-dl`; ask first) | image galleries: Pinterest, Reddit, Imgur, Tumblr, DeviantArt, Instagram images |
| `aria2c` | **not installed** (`winget install aria2.aria2`; ask first) | fast multi-connection downloads of big packs (Sonniss bundles, LUT packs) |
| ImageMagick | **not installed** (ffmpeg covers most image jobs) | batch image convert/resize |
| BiRefNet cutout, RIFE, DeepFilterNet, Demucs, Whisper | the `local-av-tools` skill in this pack | remove backgrounds from meme stills/green screen alternatives, smooth frame rates, clean audio, split stems, read back speech |

## yt-dlp recipes

Search without downloading (metadata only, fine without asking):
```bash
yt-dlp --simulate --no-warnings --print "%(title)s | %(duration)s s | %(channel)s | %(webpage_url)s" "ytsearch10:vadivelu meme template green screen"
```
Only clips shorter than 20 s from a search:
```bash
yt-dlp --simulate --print "%(title)s | %(duration)s | %(webpage_url)s" --match-filters "duration<20" "ytsearch25:bruh sound effect"
```
Download one video, best MP4 ≤1080p, with its metadata (after the user's yes):
```bash
yt-dlp --no-playlist -S "res:1080,ext:mp4:m4a" --write-info-json --restrict-filenames -o "<store>/downloads/memes-2026-10-28/%(id)s.%(ext)s" "<url>"
```
Only a section (meme moment at 1:23–1:27), cut on exact frames:
```bash
yt-dlp --no-playlist --download-sections "*00:01:23-00:01:27" --force-keyframes-at-cuts -S "res:1080,ext:mp4:m4a" -o "<folder>/%(id)s_%(section_start)s.%(ext)s" "<url>"
```
Audio only as WAV (meme sounds, SFX from a YouTube SFX channel that allows it):
```bash
yt-dlp --no-playlist -x --audio-format wav -o "<folder>/%(id)s.%(ext)s" "<url>"
```
Size guard: add `--max-filesize 200M`. Instagram/Facebook posts that need a login: `--cookies-from-browser chrome` reads the user's Chrome cookies — **ask the user first** every time, and never for an account action.

## Host quirks seen on 28 Oct 2026

- Traffic from this PC exits through a US address; pass country codes explicitly.
- Need a `Referer` header: ccMixter mp3s, Looperman previews (`fetch_asset.py --referer <page>`).
- Block scripts (use the built-in browser for the page, then curl the file if the CDN allows it): Pixabay (rewrite `cdn.pixabay.com/download/audio/...?...` to `cdn.pixabay.com/audio/...`), Uppbeat, Purple Planet, Free Stock Music, Artlist, Magnific/Freepik, Zedge, Shazam (WebFetch works).
- GIPHY clips: `giphy720p.mp4` has sound and an extra 4K video stream, so map `-map 0:v:0 -map 0:a`. Plain `giphy.mp4` and all Tenor MP4s are silent.
- Reddit: anonymous `.json` returns 403; use `/r/<sub>/top/.rss?t=week`, wait ≥45 s between calls.
- Unauthenticated GitHub API calls are rate-limited from this IP; use `raw.githubusercontent.com` or `gh api`.
- ffmpeg here has HarfBuzz shaping, so `drawtext` renders Tamil and Hindi correctly with an Indic font (Anek Tamil, Mukta).

## After download: make it edit-ready (ffmpeg)

```bash
# trim to the beat with 0.2 s handles, H.264 CRF 18, AAC 48 kHz, loudness -16 LUFS
ffmpeg -ss 1.10 -to 3.90 -i in.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -af "loudnorm=I=-16:TP=-1:LRA=11" -ar 48000 -c:a aac -b:a 192k out.mp4
# still frame for the catalogue
ffmpeg -ss 1.5 -i out.mp4 -frames:v 1 out.png
# sound effect: mono→stereo WAV 48 kHz, peak-normalised
ffmpeg -i in.mp3 -ac 2 -ar 48000 -af "loudnorm=I=-16:TP=-1" out.wav
# green-screen meme template → transparent overlay (tune similarity 0.10–0.30)
ffmpeg -i green.mp4 -vf "chromakey=0x00FF00:0.18:0.08,format=yuva420p" -c:v libvpx-vp9 -b:v 0 -crf 30 out.webm
# loudness check
ffmpeg -i out.wav -af ebur128=peak=true -f null - 2>&1 | tail -12
```

## Where downloads go (the shared asset store)

Root: `<asset store>\`, the folder in `ASSET_ROOT` (shared by every editing skill).

```
<asset store>\
  downloads\<kind>-<YYYY-MM-DD>\   raw downloads, untouched (+ .info.json / .source.json)
  music\<slug>\                    cleaned tracks + README.md table + scan.json (BPM, drops)
  sfx\<category>\<slug>.wav        meme\, whoosh\, impact\, riser\, ui\, ambience\, foley\, transition\
  memes\{ta,hi,en}\<slug>.mp4/.png  + CATALOG.md
  footage\<topic>\                 stock B-roll
  images\<topic>\                  stills, illustrations, meme images
  overlays\                        light leaks, grain, dust, green-screen elements, transitions
  luts\                            .cube files (+ licence note)
  fonts\                           .ttf/.otf + licence file next to each family
  icons\, lottie\, 3d\             as needed
  DOWNLOADS.md                     one row per downloaded file (fetch_asset.py appends it)
```
