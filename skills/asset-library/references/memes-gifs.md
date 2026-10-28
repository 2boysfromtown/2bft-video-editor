# Memes, meme templates, reaction clips, GIFs, stickers and green-screen memes

Where Claude finds and downloads real meme clips (video + sound), meme stills, GIFs, stickers and emoji for Tamil (Kollywood), Hindi (Bollywood/TV) and English/global edits. Every row was checked live on **28 Oct 2026** from the user's PC (its traffic exits through a US address, so region-locked results can differ from what the user sees) with curl, yt-dlp 2026.08.19, ffprobe or WebFetch. No accounts were created and no keys were used. Language codes: ta = Tamil, hi = Hindi/Hinglish, en = English, global = no language.

**Check your existing library first:** `<asset store>\memes\CATALOG.md` and `<asset store>\sfx\meme\`, if you keep them (meme clips trimmed and loudness-matched, with stills). Download new ones with `scripts/fetch_asset.py --ytdlp --section ...` so the source is recorded.

> **Rights in one line.** Almost every film/TV meme clip, still and "no copyright" YouTube template here is owned by a studio or channel, whatever the uploader claims. Use them only in the user's own non-monetised or at-risk videos, by their choice. **Never in client ads.** The open emoji sets (Noto, Fluent, Twemoji, OpenMoji) and Lottie animations are the only items here that are actually licensed for reuse. See [Copyright reality](#copyright-reality-india--youtube--instagram).

**Contents:** [1 Video templates & green screen](#1-video-meme-templates--green-screen) · [2 Image templates](#2-image-meme-templates-stills-captionable) · [3 GIF/sticker platforms](#3-gif--sticker-platforms) · [4 Communities](#4-communities--trend-pages-find-whats-funny-right-now) · [5 Emoji & stickers](#5-emoji--sticker-sets-properly-licensed-safe-for-client-work-with-credit) · [6 Origin lookup](#6-context--origin-lookup-what-the-meme-means-where-it-came-from) · [Dead/hijacked domains](#dead-or-hijacked-do-not-use) · [Best picks](#best-picks) · [Fetch recipes](#fetch-recipes-all-run-on-28-oct-2026-output-trimmed) · Quick search: `scripts/find_assets.py meme "<name>"` (Imgflip) and `memesound "<line>"` (meme audio).

---

## 1. Video meme templates & green screen

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| YouTube search (all template channels) | youtube.com | The largest pool of meme clips: green-screen templates, "meme template" cuts and 100-clip compilations | ta/hi/en | The film studio owns them. "No copyright" in a title means nothing | Free, no login (occasional bot check) | `yt-dlp --flat-playlist --print "%(title)s \| %(channel)s \| %(duration)s \| %(url)s" "ytsearch10:<query>"`, then `--download-sections` to trim (see recipes) | yt-dlp search plus a 3 s section download that came out as 1920x1080 h264+aac | `ytsearchdate` no longer exists in yt-dlp 2026.08. Use a results URL instead. One video returned "Please sign in" (bot check). Retry later, or use `--cookies-from-browser` only if the user says yes |
| **Tamilan Movie Clips** (YT) | youtube.com/@TamilanMovieClips | Numbered "Tamil Movie Clips Templates / Memes Template N" compilations, 60–90 s each | ta | Studio-owned film cuts | Free | yt-dlp (trim individual gags with `--download-sections`) | yt-dlp: 2.21K subs, **latest upload 27 Oct 2026** | The most active Tamil template channel found |
| **Tamil Meme Templates** (YT) | youtube.com/@tamilmemetemplates5937 | Single-gag templates (Santhanam, Singamuthu, Vijay, Vadivelu), 10–20 s | ta | Studio-owned | Free | yt-dlp | yt-dlp: 1.34K subs, latest 9 Jul 2026 | Clean one-line clips, good for punch-ins |
| **Template Memer** (YT) | youtube.com/@TemplateMemer | Vadivelu/Goundamani green-screen and plain templates, plus a "Top Viral Indian Meme Templates" playlist | ta/hi | Studio-owned | Free | yt-dlp | yt-dlp: 8.35K subs, latest long upload Jul 2021 (archive still up) | A big back catalogue, e.g. "Kuthi paaru da" green screen `o6RY1ICzWyY`, which was used in the tests |
| **Pachai Niramae** (YT) | youtube.com/@pachainiramae8757 | Vadivelu comedy on **green screen** (Bomb Pakkiri, Mara Tamilan…), 5–15 s | ta | Studio-owned | Free | yt-dlp, then chroma key in ffmpeg | yt-dlp: 1.09K subs, latest Mar 2022 | Dormant but useful keyed clips |
| TAMIL TEMPLATES (YT) | youtube.com/@tamiltemplates1922 | Short Tamil green-screen and Shorts templates (Goundamani "dei sapudu da", Thookudurai) | ta | Studio-owned | Free | yt-dlp | yt-dlp: 753 subs, latest May 2025 | |
| RA1. Hub (YT) | youtube.com/@Ra1.Hub143 | Weekly "Tamil New Meme Templates" ~5-min packs (trend snapshots) | ta | Studio-owned | Free | yt-dlp with `--download-sections` | yt-dlp: 1.57K subs, latest Mar 2025 | Good for seeing which Tamil templates were trending |
| Timepass Templates (YT) | youtube.com/@timepasstemplates5104 | Tamil meme template compilations | ta | Studio-owned | Free | yt-dlp | yt-dlp: 1.32K subs, latest May 2025 | |
| **Streak Series** (YT) | youtube.com/@StreakSeries | "Top 40+ Indian memes for video editing" compilations (Hindi/gaming) | hi | Studio-owned | Free | yt-dlp, trimming each meme | yt-dlp: 35.3K subs, latest May 2025 | The biggest Hindi compilation channel found |
| Palamu Gyan (YT) | youtube.com/@AsmitKumar-m9p9e | "100+ Memes, Popular Meme Clips for Video Editing 2026" | hi | Studio-owned | Free | yt-dlp | yt-dlp: 987 subs, latest 14 Oct 2026 | Fresh 2026 Hindi packs |
| SY Finance Services (YT) | youtube.com/channel/UCTBA3O6A-m9_CJ_JTq3GiWA | "Top 50 Popular Hindi Meme Templates" and Rajpal Yadav packs | hi | Studio-owned | Free | yt-dlp | yt-dlp search result (stats not pulled) | |
| Meme template videos (YT) | youtube.com/@memetemplatevideos8771 | Single Hindi TV/film lines, e.g. CID "kuch toh gadbad hai" | hi | Studio-owned (Sony for CID) | Free | yt-dlp | yt-dlp: 1.42K subs, latest Nov 2025 | |
| No Copyright Memes #CreativeCommon (YT) | youtube.com/@nocopyrightmemescreativeco1668 | Hindi meme cuts (Paresh Rawal "Are Deva…") | hi | Claims "Creative Commons", but the uploader doesn't own the film, so **treat as all rights reserved** | Free | yt-dlp | yt-dlp: 1.5K subs, latest Dec 2025 | A YouTube CC licence label is only valid if the uploader owns the rights |
| **Green Screens by CreatorSet** (YT) | youtube.com/@CreatorSetGreenScreens | Clean English pop-culture **green-screen** memes (Homelander, IShowSpeed…) | en | Studio/creator-owned | Free | yt-dlp, then chroma key | yt-dlp: **334K subs**, latest May 2025 | High-quality keys |
| Yadro Green Screen (YT) | youtube.com/@yadrogreenscreen | Global green-screen memes (laughing dog, Legend Reggie…) | en/global | Mixed | Free | yt-dlp | yt-dlp: 189K subs, latest Jun 2025 | |
| Demonal (YT) | youtube.com/@Demonal | "100 green screen memes", "500+ meme SFX" packs (10-min compilations) | en | Mixed. "No copyright" label is unreliable | Free | yt-dlp `--download-sections` per meme | yt-dlp: 711K subs, latest Jan 2026 | Use as a menu, then trim |
| **Green Screen Memes** site + channel | greenscreenmemes.com · youtube.com/@greenscreenmem | **5,000+ green-screen meme MP4s**, new ones daily, plus sound library and Top 100 | en/global (12 "indian" hits) | Site terms: free for editing, credit appreciated, **no redistribution of unmodified files**. The underlying clips are still third-party | Free HD direct MP4 (4K via Patreon) | `curl` the page, grep `media.greenscreenmemes.com/YYYY/MM/<name>.mp4`. Search with `/?s=indian` | HEAD `aura-farmer.mp4` gave 200 video/mp4 8.6 MB. The channel uploaded on 27 Oct 2026 | **The best direct-download green-screen library** (no YouTube re-encode). No Bollywood or Tamil hits |
| **MemesTube** | memestube.com | Hindi/Bollywood/TV meme clips (Jethalal, Hera Pheri, Nawazuddin…) as **MP4 + separate MP3 + JPG**, plus a "green screen" section | hi (some en) | Site is an independent project (Rahul Mourya). Clips are studio-owned. It has a DMCA page | Free, no login | Page `/<slug>-meme-download` holds `https://media.memestube.com/meme/<slug>-video-meme-download.mp4`. Audio: `...-audio-meme-download.mp3` | HEAD mp4 gave 200 4.49 MB and mp3 gave 200 106 KB. Sections: `/section/{bollywood-memes,hindi-memes,indian-memes,meme-templates,no-copyright-memes,viral-memes}` | **The best Hindi direct source.** Don't confuse it with **memestube.in**, a different, near-empty WordPress clone |
| Kapwing video meme templates | kapwing.com/templates/memes/video | 309 English video meme templates (Moo Deng, The Office, green-screen cat…) | en | Kapwing ToS. Clips are third-party | Editing needs a sign-in | Browse only. Find the clip name and get the source from YouTube or greenscreenmemes | curl 200 / WebFetch | Claude can't sign in, so use it as an idea list |
| Imgflip GIF templates | imgflip.com/gif-templates | Short GIF "video templates" | en/global | User uploads | Free view | Open the template page and grep `i.imgflip.com/<id>.mp4/.gif` | curl 200 | Silent |
| GIPHY **Clips** (GIFs with sound) | giphy.com/clips | Official short clips **with audio**, incl. Indian stars (Hrithik Roshan channel), Sun Pictures (`sunpictures`), TVF (`theviralfever`) | hi/ta/en | Rights-holder uploads, licensed for sharing through GIPHY only, **not for re-editing** | Free view | From the clip page HTML grep `media.giphy.com/media/<id>/giphy720p.mp4` (or `giphy1080p.mp4`). These carry **AAC audio**, while plain `giphy.mp4` is silent | ffprobe on clip `RjiqioskznA1JjAbTc` found h264 1280x720 + **aac** audio, 3.5 s | The file has a second 4K video stream, so map `-map 0:v:0 -map 0:a` |
| CapCut templates | capcut.com/explore/tamil-template | Tamil/Hindi "trend" templates | ta/hi | CapCut ToS | **The app has been banned in India since 2020**. Web pages still load (200) | Reference only | curl 200 | Not a clip source |
| invideo meme templates | invideo.io/templates/meme-videos/ | Editable meme video templates | en | Commercial use only on a paid plan, per their FAQ | Sign-in | Reference only | curl 200 (redirect) | |

## 2. Image meme templates (stills, captionable)

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| **Imgflip API `get_memes`** | api.imgflip.com/get_memes | JSON of the **top 100** blank templates: `id, name, url, width, height, box_count, captions` | en/global | Templates are third-party images | **No key** for get_memes. `caption_image` and `search_memes` **need a username/password or API key** (verified error) | `curl -s https://api.imgflip.com/get_memes` | `success: True, 100 memes` | Claude must not sign in, so caption locally (ffmpeg/PIL) or via memegen.link |
| **Imgflip search (Indian user templates)** | imgflip.com/memesearch?q=vadivelu | Thousands of user-uploaded templates: "Vadivelu Thank you", "vadivelu sentiment", Hera Pheri, CID… | ta/hi/en | User uploads of film stills | Free | Grep `href="/meme/<id>/<slug>"`. **Blank image = `https://i.imgflip.com/<base36(id)>.jpg`** | `/meme/101731240/Vadivelu-Thank-you` gave base36 `1okgbs` and `i.imgflip.com/1okgbs.jpg` returned 200 image/jpeg | The base36 rule also matches the API (`181913649` → `30b1gx`) |
| **memegen.link API** | api.memegen.link | 210 classic templates, and it **renders captions server-side** to PNG/JPG/**GIF**. Custom backgrounds by URL | en (any text incl. Tamil/Hindi glyphs, font-dependent) | Code is open source. Template images are third-party | **No key** | `https://api.memegen.link/images/<id>/<top>/<bottom>.png` or `/images/custom/_/<text>.png?background=<img url>` | `drake/...png` 200 (500 KB), `.gif` 200, custom bg with an Imgflip Vadivelu still 200 | `_` = space, `~q` = ?, `~s` = / in text. Best keyless caption renderer |
| **Indian Meme Templates** | indianmemetemplates.com | Blank Bollywood/Indian still templates (Arjun Kapoor angry, "Kya Baat Hai Sir"…), plus an online meme maker | hi/en | © 2026 site. Images are film stills | Free | Page `/<slug>/` holds the image `/wp-content/uploads/<file>.{webp,jpg,png}` | curl 200, WebFetch | No Tamil. Images only, despite the "meme videos" title |
| Know Your Meme image galleries | knowyourmeme.com/memes/<slug>/photos | Original stills and variants per meme | global (some ta/hi entries) | Mixed | Free | On `/memes/<slug>/photos` grep `https://i.kym-cdn.com/photos/images/masonry/...` and swap `masonry` for `original`. The header image is `entries/icons/original/...` | Pray for Nesamani: `photos/images/original/001/497/734/9aa.png` 200 (1.28 MB), `entries/icons/original/000/029/878/pray.jpg` 200 | Best for "the original frame" |
| Supermeme.ai | supermeme.ai | AI meme generator (text → template + caption), GIF memes, Meme API + **MCP server** | en (+ others) | "Rights depend on the template". Free tier is watermarked | 10 free credits/mo, then paid. API needs a key | Not usable without signup | WebFetch 200 | Its MCP could plug into Claude if the user wants it |
| Mematic | mematic.com (mematic.net redirects) | Mobile meme-maker app with template library | en | App ToS | App | Not fetchable | curl 200 | Reference only |
| memes.com | memes.com | Now a meme-culture hub with templates by brand/industry, a Studio and an AI generator (memes.ai, memes.media) | en | ToS | Studio needs sign-in | Reference only | WebFetch 200 | No Indian focus |
| Makeameme / MemeCreator | makeameme.org · memecreator.org | Classic image meme generators | en | User content | Free | Reference | curl 200 (makeameme `/memes` is 404) | memegen.link is easier for Claude |
| Canva meme templates | canva.com/memes/templates/ | Designed meme layouts | en/global | Canva content licence (free and Pro elements) | Sign-in | Reference only | curl 200 | |
| Pinterest | pinterest.com/search/pins/?q=tamil%20meme%20template | Huge pile of re-posted Tamil/Hindi template stills | ta/hi/en | Re-posts with no clear owner | Login wall after a few pins | Browser only. Upscaling is often needed | curl 200 | Useful for discovery, low quality |

## 3. GIF / sticker platforms

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| **GIPHY (website)** | giphy.com/search/<q> | GIFs, stickers (transparent), clips with sound. Tamil hits exist (`sunpictures`, `viber` Vadivelu stickers) | ta/hi/en | GIPHY ToS: shareable through GIPHY. Rights stay with the uploader | Free, no key for pages | From search HTML grep `https://giphy.com/gifs/<slug>-<ID>`, then `https://media.giphy.com/media/<ID>/giphy.mp4` (silent loop), `giphy.gif`, `giphy.webp`, `200.mp4`, `source.gif` | HEAD on ID `8oRgog5T4Y9O`: giphy.mp4 200 349 KB, giphy.gif 878 KB, source.gif 1.3 MB, giphy.webp 350 KB | `source.mp4` gave 403 on clips. Use `giphy720p.mp4` |
| GIPHY API | developers.giphy.com | `api.giphy.com/v1/{gifs,stickers}/{search,trending}`, Clips, v2 emoji | global | Must show "Powered By GIPHY" | **Key required.** Free beta key = 100 calls/hr, 50 results per call. Production pricing is custom | Not usable (no signup). The website pattern above is enough | WebFetch of docs page | WhatsApp moved to GIPHY after Tenor died |
| **Tenor (website)** | tenor.com/search/<q>-gifs | Big library of **Vadivelu/Tamil reaction GIFs** ("podhum mudiyala", "loosu") and Hindi ones | ta/hi/en | Google ToS. Uploader-owned | Website alive, no key | Grep `https://media.tenor.com/<11-char ID><5-char format>/<slug>.<ext>` from the search HTML. Format codes: **AAAAC** gif full, **AAAAd** gif medium, **AAAAM** tinygif, **AAAPo** mp4, **AAAP1** tiny mp4, **AAAPs** webm, **AAAA1** webp | ID `0LezyXETODQ`: AAAPo mp4 439 KB, AAAAC gif 8.1 MB, AAAPs webm 187 KB all 200 | **All Tenor MP4s are silent.** One ID returned 404 for every variant (removed or blocked), so check each one |
| **Tenor API** | developers.google.com/tenor | — | — | — | **Dead.** Google stopped new keys in **Jan 2026**. API shut down **30 Jun 2026** (press: 9to5google, Shacknews). The page now shows a "Tenor API Service Discontinuation" notice | Don't use | WebFetch of docs page | Website still serves media |
| **KLIPY** | klipy.com | GIFs, stickers, **clips (movie/TV)**, memes, emoji. A Tenor replacement with a drop-in base URL `api.klipy.com` | global (Vadivelu hits exist) | KLIPY branding required | Website free. API needs a Partner Panel key (test key 100 calls/hr) | Website: grep `static*.klipy.com/ii/.../*.{mp4,webp}` | curl 200. Clip mp4 probed: 640x640, 5 s, **no audio** | New in 2026. "Migrate from Tenor" page |
| Gfycat | gfycat.com | — | — | — | **Dead** (shut down 1 Sep 2023) | — | curl: no connection (000) | Old gfycat links in Reddit posts are broken |
| Imgur | imgur.com | Reaction GIFs/videos (`.gifv` = mp4) | en/global | Uploader-owned | Site free. **API needs Client-ID** (401 verified) | `https://i.imgur.com/<id>.mp4`, or yt-dlp (Imgur extractor present) | curl 200, API 401 | |
| **9GAG** | 9gag.com | Video memes **with audio** (`hasAudio:1`), photos | en/global | Uploader-owned | Free, no key | `curl https://9gag.com/v1/group-posts/group/default/type/hot` and read `images.image460sv.url`, e.g. `https://img-9gag-fun.9cache.com/photo/<id>_460sv.mp4`. yt-dlp has a 9gag extractor | JSON 200 (40 KB). mp4 URLs listed | Good for global trending reaction clips |
| Memedroid | memedroid.com | User meme feed + generator | en | User content | Free | Browser (WebFetch 403. curl with a browser UA gives 200) | curl 200 | Low value for Indian content |
| GIPHY stickers | giphy.com/stickers | Transparent animated stickers (GIF/WebP with alpha) | global | GIPHY ToS | Free | Same media pattern: `giphy.webp` / `giphy.gif` keep alpha. **mp4 has no alpha** | Pattern verified on GIFs | For alpha in video use the webp or gif, or the Noto/Lottie emoji below |

## 4. Communities / trend pages (find what's funny right now)

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| **Reddit (all subs)** | reddit.com/r/<sub> | Trending meme posts, v.redd.it videos with audio | — | Uploader-owned | **Anonymous `.json` is blocked**: www/api gave 403 "blocked by network security", and old.reddit `.json` redirects to login. **RSS still works** but is rate-limited (429 at under ~30 s spacing) | `https://www.reddit.com/r/<sub>/top/.rss?t=week`. Grep `https://v.redd.it/<id>`, then `yt-dlp "https://v.redd.it/<id>/HLSPlaylist.m3u8"` (video+audio). yt-dlp on the post URL fails ("Account authentication is required") | RSS 200 (25 entries). The HLS playlist gave 720x1280 + audio | Space requests ≥45 s apart and send a custom User-Agent. `CMAF_480.mp4`/`CMAF_AUDIO_128.mp4` also return 206, while `DASH_*` is 403 |
| r/MemeTemplatesOfficial | reddit.com/r/MemeTemplatesOfficial | Clean, text-free templates (stills and video) | en/global | Mixed | RSS | As above | RSS 200, updated 27 Oct 2026 | |
| r/IndianDankMemes | reddit.com/r/IndianDankMemes | Hindi/Indian video memes (many v.redd.it) | hi/en | Mixed | RSS | As above | RSS 200, 25 entries, updated 27 Oct 2026 | |
| r/BollywoodMemes | reddit.com/r/BollywoodMemes | Bollywood stills/clips | hi | Mixed | RSS | As above | RSS 200, updated 27 Oct 2026 | |
| r/IndianMeyMeys | reddit.com/r/IndianMeyMeys | Indian memes | hi/en | Mixed | RSS | As above | RSS 200, updated 27 Oct 2026 | |
| r/TamilMemes | reddit.com/r/TamilMemes | Tamil memes | ta | Mixed | RSS | As above | RSS 200 (Tamil emoji titles) | Keep `python -I` and call `sys.stdout.reconfigure(encoding="utf-8")` in the script, otherwise Windows cp1252 crashes on emoji |
| r/Kollywood | reddit.com/r/Kollywood | Tamil cinema news, memes and clips | ta | Mixed | RSS | As above | RSS 200 | |
| r/kollywoodmemes | — | — | ta | — | **403 Forbidden** (private or banned) | — | RSS 403 | Skip |
| r/reactiongifs | reddit.com/r/reactiongifs | "MRW" reaction GIFs | en | Mixed | RSS | As above | RSS 200 | |
| r/dankinindia | reddit.com/r/dankinindia | Indian memes | hi/en | Mixed | RSS | As above | Only 429 (rate-limited, not confirmed alive) | Retry slowly |
| Instagram meme pages | instagram.com/<handle> (e.g. @vadivelumemes, Tamil Memes pages tracked by Qoruz) | The Tamil/Hindi meme scene, where trends start | ta/hi | Page-owned, mostly film clips | Login wall | yt-dlp has an Instagram extractor for single reels/posts, but **`instagram:user` is marked CURRENTLY BROKEN**. Single reels usually need cookies | Not tested (no public reel URL to hand) | Use for spotting trends, not as a download source. Cookies only if the user says yes |
| Telegram public channels | t.me/s/<channel> | Template packs posted as videos | ta/hi | Unknown | Public preview needs no login | `curl https://t.me/s/<channel>` and grep `cdn*.telesco.pe/file/...mp4?token=...`, or yt-dlp `telegram:embed` | Preview works (tested on a public channel: 20 posts and mp4 links). **No real Tamil/Hindi template channel found.** TGStat search returns 403 to bots | Ask the user for channel names he trusts |
| ShareChat / Moj | sharechat.com · mojapp.in | Indian-language short videos incl. Tamil/Hindi memes | ta/hi | Uploader-owned | Free | Browser only (no yt-dlp extractor) | curl 200 | For spotting trends |
| X / Twitter | x.com | Meme clips | all | Uploader-owned | Often needs login | `yt-dlp <tweet url>` (twitter extractor present) | Extractor listed, not tested | |

## 5. Emoji & sticker sets (properly licensed, safe for client work with credit)

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| **Noto Emoji 2D + new 3D** | github.com/googlefonts/noto-emoji | Full Unicode set as PNG 32/72/128/512 and SVG, **plus a new `3D/png/512` set** | global | **Images: Apache 2.0**. Fonts: OFL 1.1 | Free | `https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/512/emoji_u1f602.png` (or `3D/png/512/...`, `2D/svg/...svg`) | 2D png 200 (38 KB), 3D png 200 (295 KB), svg 200. Repo pushed 26 Oct 2026 | **The repo was restructured.** The old `png/512/` paths now return 404 |
| **Noto Animated Emoji** | googlefonts.github.io/noto-emoji-animation | Animated emoji as **Lottie JSON, GIF, WebP** (512 px) | global | **CC BY 4.0** (per Google's launch post and the packages that bundle it; the site itself doesn't print it). Credit Google | Free | `https://fonts.gstatic.com/s/e/notoemoji/latest/<codepoint>/{lottie.json,512.gif,512.webp}`. Index: `.../data/api.json` | 1f602: lottie.json 200 (59 KB), 512.gif 200 (1.2 MB), 512.webp 200 | Best animated reaction emoji. WebP/Lottie keep alpha |
| **Fluent Emoji** (Microsoft) | github.com/microsoft/fluentui-emoji | 3D PNG, Color/Flat/High-contrast SVG | global | **MIT** | Free | `https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/<Name>/3D/<name>_3d.png` | Face with tears of joy: 3D png 200 (44 KB), Color svg 200 | Folder names have spaces (`%20`) |
| **Twemoji** (jdecked fork) | github.com/jdecked/twemoji | 72x72 PNG + SVG | global | Graphics **CC BY 4.0**, code MIT | Free | `https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f602.svg` (or `72x72/1f602.png`) | Both 200 | Twitter dropped the original. This fork is maintained (pushed Jun 2026) |
| **OpenMoji** | openmoji.org · github.com/hfg-gmuend/openmoji | 4,000+ emoji incl. extras, colour/black SVG and 72/618 PNG | global | **CC BY-SA 4.0** (attribution + share-alike) | Free | `https://cdn.jsdelivr.net/npm/openmoji@17.0.0/color/svg/1F602.svg` (uppercase hex). PNG zips are in GitHub release **17.0.0** (23 Apr 2026) | svg 200. `618x618` PNG is **not** in the npm package (404) | Share-alike: avoid for client deliverables |
| LottieFiles free animations | lottiefiles.com/free-animations/emoji | Lottie emoji/sticker/reaction animations | global | **Lottie Simple License**: commercial use OK, attribution optional | Free. Some downloads need a login | Browser. Check each file's licence | curl 200, licence page read | |
| Flaticon stickers | flaticon.com/stickers | Static PNG/SVG stickers, some animated | global | Freepik licence: **free with attribution**, Premium without | Free/Premium, downloads may need login | Browser only | **403 to curl and WebFetch** (bot wall), not confirmed live | |
| Emojipedia | emojipedia.org | Every vendor's rendition + codepoints | global | Reference only (images © vendors) | Free | Use it to look up codepoints | curl 200 | |

## 6. Context / origin lookup (what the meme means, where it came from)

| Name | URL | What you get | Lang | Licence/rights | Access | How Claude fetches it | Verified (how) | Notes |
|---|---|---|---|---|---|---|---|---|
| **Know Your Meme** | knowyourmeme.com | Origin, spread, usage and original images. Indian entries exist: **Pray for Nesamani** (Vadivelu), **Hera Pheri (2000 film)** subculture, "Darwaza mat kholna…" | global/ta/hi | KYM content | Free | `https://knowyourmeme.com/search?q=<q>` and grep `href="/memes/..."`. WebFetch works | curl 200 on `/memes/pray-for-nesamani` and `/memes/subcultures/hera-pheri-2000-film` | No entry found for CID "kuch toh gadbad hai" |
| Imgflip meme pages | imgflip.com/meme/<id>/<slug> | How a template is captioned in practice (view counts) | ta/hi/en | User content | Free | curl | Verified for Vadivelu | |
| Wikipedia | en.wikipedia.org/wiki/Pray_for_Nesamani | Background for big Indian meme moments | en | CC BY-SA text | Free | WebFetch | curl 200 | |
| Film Companion / news | filmcompanion.in (e.g. "Vadivelu, the man from the meme") | Context on Tamil meme culture | en | Editorial | Free | WebFetch | Search result | |
| **Myinstants** (meme sound buttons, cross-ref) | myinstants.com/en/search/?name=<q> | One-line **meme audio** mp3s: Vadivelu ("nee yaaru", "theriyaama modhiten", "adampudikiriye"), CID ("aree cid"), Phir Hera Pheri | ta/hi/en | User uploads of film audio, **unlicensed** | Free, no key | Grep `/media/sounds/<file>.mp3`, then download `https://www.myinstants.com/media/sounds/<file>.mp3` | "vadivelu" 200 (6+ sounds), "tamil" 36 sounds, "cid" 4+. mp3 HEAD 200 audio/mpeg 22 KB | Search with no results returns **404** (e.g. "goundamani"). Overlaps with the sounds category |
| Other sound boards (cross-ref) | memes.co.in/sound-buttons · 101soundboards.com · voicy.network · memesoundboard.org | Meme sound buttons | mixed | Unlicensed user uploads | Free | Browser/curl | All 200 | Belongs to the sounds category. Listed here only for meme audio |

### Dead or hijacked: do not use
| Domain | Status (28 Oct 2026) |
|---|---|
| gfycat.com | Dead (no connection). Shut down 2023 |
| Tenor API (tenor.googleapis.com) | Shut down 30 Jun 2026 (no new keys since Jan 2026). Website still works |
| memetemplates.in | **Hijacked: now a betting/casino site** |
| tamilmemes.in / tamilmemes.com | Parked / for sale |
| memeshappen.com | Dead (no connection) |
| msoid.icmbio.gov.br/templates/... | SEO spam on a hijacked Brazilian government host that ranks for "Tamil/Vadivelu meme template". Never download from it |
| memestube.in | Near-empty clone. The real one is memestube.com |

---

## Best picks

**Tamil (ta)**
1. **YouTube via yt-dlp**: Tamilan Movie Clips (active 27 Oct 2026), Tamil Meme Templates, Template Memer, Pachai Niramae (Vadivelu green screen). Search with `ytsearch10:"<actor> <dialogue> meme template"` and trim with `--download-sections`.
2. **Tenor website** for silent Vadivelu reaction GIFs/MP4s (AAAPo mp4 pattern).
3. **Imgflip memesearch** for Vadivelu/Goundamani stills, then the blank image from base36(id), captioned locally or with memegen.link `custom` background.
4. **Myinstants** for the one-line Vadivelu audio sting.
5. **r/TamilMemes + r/Kollywood RSS** to see what's current.

**Hindi (hi)**
1. **MemesTube** (memestube.com): direct MP4 + MP3 per meme, no login. Jethalal, Hera Pheri, Nawazuddin, 3 Idiots.
2. **YouTube**: Streak Series (35K), Palamu Gyan (2026 packs), Meme template videos (CID), SY Finance Services top-50.
3. **GIPHY Clips** with audio (`giphy720p.mp4`) from official Indian channels (Hrithik Roshan, TVF).
4. **Myinstants** (CID, Hera Pheri sounds) and **indianmemetemplates.com** stills.
5. **r/IndianDankMemes / r/BollywoodMemes RSS**, then v.redd.it HLS.

**English / global (en)**
1. **greenscreenmemes.com**: 5,000+ direct green-screen MP4s, updated daily.
2. **Imgflip `get_memes`** (top 100, no key) + **memegen.link** for keyless captioned PNG/GIF.
3. **Green Screens by CreatorSet** (334K), Yadro (189K), Demonal (711K packs) on YouTube.
4. **GIPHY website** media patterns, **9GAG JSON** (mp4 with audio).
5. **Know Your Meme** for origin and correct usage.

**Reactions that are actually licensed:** Noto Animated Emoji (Lottie/GIF/WebP, CC BY 4.0), Noto 3D PNG (Apache 2.0), Fluent 3D (MIT).

---

## Fetch recipes (all run on 28 Oct 2026; output trimmed)

Run these in the Bash tool (Git Bash). Put downloads in their own new folder, e.g. `mkdir -p "$SCRATCH/memes/<job>" && cd` there.

### 1. YouTube meme search: metadata only
```bash
export PYTHONIOENCODING=utf-8
yt-dlp --flat-playlist --print "%(title).70s | %(channel)s | %(duration)s | %(url)s" "ytsearch8:vadivelu meme template green screen"
```
```
vadivelu green screen video background | TOP 1 YT TAMIL | 45 | https://www.youtube.com/watch?v=NtJiEopws28
BOMB PAKKIRI | VADIVELU COMEDY GREEN SCREEN | Pachai Niramae | 15 | https://www.youtube.com/watch?v=j3S9MNhK5Nw
Kuthi paaru da yen koduku vadivelu comedy Green screen video Meme Temp | Template Memer | 8 | https://www.youtube.com/watch?v=o6RY1ICzWyY
```
`--simulate --print "%(title)s | %(duration)s s | %(resolution)s | %(webpage_url)s" "ytsearch3:..."` also works and adds the resolution (`1920x1080`, `1440x1080`…). `ytsearchdate` is **gone** in 2026.08. To sort by date, pass a results URL: `"https://www.youtube.com/results?search_query=tamil+meme+template&sp=CAI%3D"`.

### 2. Channel health check (subs + latest upload)
```bash
yt-dlp --skip-download --playlist-items 1 --print "%(channel)s | subs=%(channel_follower_count)s | latest=%(upload_date)s" "https://www.youtube.com/channel/UCF0dTNfFwcgbNU4JEQvho-g/videos"
```
```
Tamilan Movie Clips | subs=2210 | latest=20261027
```

### 3. Download only the gag (trimmed, frame-accurate, video + sound)
```bash
yt-dlp -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b" \
  --download-sections "*00:00:01-00:00:04" --force-keyframes-at-cuts \
  --merge-output-format mp4 -o "%(id)s_cut.%(ext)s" "https://www.youtube.com/watch?v=o6RY1ICzWyY"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact o6RY1ICzWyY_cut.mp4
```
```
stream|codec_name=h264|width=1920|height=1080
stream|codec_name=aac
format|duration=3.000000          (602 KB)
```
Several gags from one compilation: repeat `--download-sections "*1:02-1:05" --download-sections "*3:40-3:44"` and add `-o "%(id)s_%(section_start)s.%(ext)s"`.

### 4. Meme audio sting only
```bash
yt-dlp -x --audio-format mp3 --download-sections "*1-3" -o "%(id)s_sfx.%(ext)s" "https://www.youtube.com/watch?v=o6RY1ICzWyY"
```
```
[ExtractAudio] Destination: o6RY1ICzWyY_sfx.mp3   -> mp3, duration=2.0135
```

### 5. Key out a green-screen meme over the edit (tested; clean result)
```bash
# sample the key colour first (corner pixel)
ffmpeg -v error -ss 1 -i o6RY1ICzWyY_cut.mp4 -frames:v 1 -vf "crop=40:40:0:0,scale=1:1" -f rawvideo -pix_fmt rgb24 - | od -An -tu1
#   0 255   0   -> pure green, so key 0x00FF00
ffmpeg -y -i BACKGROUND.mp4 -i o6RY1ICzWyY_cut.mp4 -filter_complex \
 "[1:v]scale=1080:-2,chromakey=0x00FF00:0.15:0.05,despill=type=green[fg];[0:v][fg]overlay=(W-w)/2:(H-h)/2:shortest=1[v]" \
 -map "[v]" -map "1:a?" -c:v libx264 -pix_fmt yuv420p -c:a aac keyed.mp4
```
The test over a solid 1080x1920 background gave clean edges on both Vadivelu-scene characters.

### 6. Imgflip: top 100 templates (no key) and any template's blank image
```bash
curl -s https://api.imgflip.com/get_memes | python -c "import json,sys;d=json.load(sys.stdin);print(d['success'],len(d['data']['memes']));print(d['data']['memes'][0])"
```
```
True 100
{"id": "181913649", "name": "Drake Hotline Bling", "url": "https://i.imgflip.com/30b1gx.jpg", "width": 1200, "height": 1200, "box_count": 2, "captions": 1579250}
```
```bash
# Indian templates: search page, then base36(id) gives the blank image
curl -s -A "Mozilla/5.0" "https://imgflip.com/memesearch?q=vadivelu" | grep -o 'href="/meme/[^"]*"' | sort -u | head
#  href="/meme/101731240/Vadivelu-Thank-you"   href="/meme/127745157/vadivelu-sentiment" ...
python -c "n=101731240;s='0123456789abcdefghijklmnopqrstuvwxyz';r=''
while n: n,m=divmod(n,36); r=s[m]+r
print('https://i.imgflip.com/'+r+'.jpg')"
#  https://i.imgflip.com/1okgbs.jpg   -> HTTP 200 image/jpeg 47 KB
```
`caption_image` / `search_memes` reply `"An API key or a username and password are required"`. Don't sign in. Use recipe 7.

### 7. memegen.link: keyless captioned meme (PNG or GIF), any background
```bash
curl -s -o drake.png "https://api.memegen.link/images/drake/manual_editing/claude_editing.png"      # 200, 500 KB
curl -s -o drake.gif "https://api.memegen.link/images/drake/manual_editing/claude_editing.gif"      # 200 image/gif
curl -s -o vadi.png  "https://api.memegen.link/images/custom/_/naan_ready_neenga_ready_ah.png?background=https://i.imgflip.com/1okgbs.jpg"  # 200
curl -s https://api.memegen.link/templates | python -c "import json,sys;print(len(json.load(sys.stdin)))"   # 210
```

### 8. MemesTube (Hindi): page → MP4 + MP3
```bash
curl -s -A "Mozilla/5.0" https://memestube.com/section/hindi-memes | grep -o 'href="/[^"]*-meme-download"' | sort -u | head
curl -s -A "Mozilla/5.0" https://memestube.com/jethalal-arey-band-kar-band-kar-meme-download | grep -o 'https://media.memestube.com/meme/[^"]*\.mp4'
#  https://media.memestube.com/meme/jethalal-arey-band-kar-band-kar-video-meme-download.mp4   (200 video/mp4 4.49 MB)
#  audio twin: ...-audio-meme-download.mp3                                                    (200 audio/mpeg 106 KB)
```

### 9. greenscreenmemes.com: direct green-screen MP4s
```bash
curl -s -A "Mozilla/5.0" "https://greenscreenmemes.com/?s=indian" | grep -o 'https://media.greenscreenmemes.com/[^"]*\.mp4' | sort -u
#  .../Annoying-indian-chicken-meme-Green-Screen.mp4  .../Indian-man-dancing-Green-Screen.mp4  (12 hits)
curl -sI https://media.greenscreenmemes.com/2026/10/aura-farmer.mp4   # 200 video/mp4 8,621,724 bytes
```

### 10. Tenor website (API is dead): silent reaction MP4/GIF
```bash
curl -s -A "Mozilla/5.0" "https://tenor.com/search/vadivelu-gifs" | grep -o 'https://media.tenor.com/[^"\\ ]*\.\(mp4\|gif\|webp\)' | sort -u | head
#  https://media.tenor.com/0LezyXETODQAAAP1/funny-comedy.mp4   (tiny mp4)
# swap the 5-char code after the 11-char ID:
#  AAAPo = mp4 (439 KB)  AAAAC = full gif (8.1 MB)  AAAAd = medium gif  AAAAM = tinygif  AAAPs = webm  AAAA1 = webp
curl -s -o reaction.mp4 "https://media.tenor.com/0LezyXETODQAAAPo/funny-comedy.mp4"
```

### 11. GIPHY website (no key): GIF loop or clip with sound
```bash
curl -s -A "Mozilla/5.0" https://giphy.com/search/bollywood-clips | grep -o 'https://giphy.com/clips/[^"\\]*' | sort -u | head -3
#  https://giphy.com/clips/HrithikRoshan-not-funny-hrithik-roshan-its-RjiqioskznA1JjAbTc
ID=RjiqioskznA1JjAbTc
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height -of compact "https://media.giphy.com/media/$ID/giphy720p.mp4"
#  stream|codec_name=h264|codec_type=video|width=1280|height=720
#  stream|codec_name=h264|codec_type=video|width=3840|height=2160     <- extra stream: use -map 0:v:0
#  stream|codec_name=aac|codec_type=audio                              <- clips HAVE sound
ffmpeg -i "https://media.giphy.com/media/$ID/giphy720p.mp4" -map 0:v:0 -map 0:a -c copy clip.mp4
# plain GIF IDs: https://media.giphy.com/media/<ID>/giphy.mp4 (silent), giphy.gif, giphy.webp, source.gif
```

### 12. Reddit without auth: RSS, then v.redd.it HLS (video + audio)
```bash
curl -s -A "windows:asset-library:v0.1" "https://www.reddit.com/r/IndianDankMemes/top/.rss?t=week" -o feed.xml   # 200 atom, 25 entries
grep -o 'https://v.redd.it/[a-z0-9]*' feed.xml | sort -u | head
#  https://v.redd.it/1zpigz6j2kxh1
yt-dlp -o "%(id)s.%(ext)s" "https://v.redd.it/1zpigz6j2kxh1/HLSPlaylist.m3u8"
#  simulate: HLSPlaylist | 108 s | 720x1280 + audio_0
```
`https://www.reddit.com/r/<sub>/top.json` returns **403 "You've been blocked by network security"**, and yt-dlp on the post URL fails with "Account authentication is required". Wait ≥45 s between RSS calls (429 otherwise).

### 13. 9GAG hot feed (JSON, mp4 with audio)
```bash
curl -s -A "Mozilla/5.0" "https://9gag.com/v1/group-posts/group/default/type/hot" | python -c "
import json,sys;d=json.load(sys.stdin)
for p in d['data']['posts'][:5]:
  sv=p.get('images',{}).get('image460sv',{}); print(p['type'],p['title'][:40],'|',sv.get('url'),'| audio:',sv.get('hasAudio'))"
#  Animated Imma head out and do the dishes now | https://img-9gag-fun.9cache.com/photo/aQg6r08_460sv.mp4 | audio: 1
```

### 14. Myinstants: one-line meme audio
```bash
curl -s -A "Mozilla/5.0" "https://www.myinstants.com/en/search/?name=vadivelu" | grep -o "/media/sounds/[^'\"]*\.mp3" | sort -u
#  /media/sounds/vadivelu-nee-yaaru.mp3  /media/sounds/vadivelu-theriyaama-modhiten.mp3 ...
curl -s -o nee-yaaru.mp3 "https://www.myinstants.com/media/sounds/vadivelu-nee-yaaru.mp3"   # 200 audio/mpeg
```

### 15. Licensed reaction emoji (direct URLs)
```bash
curl -s -o joy_3d.png   https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/512/emoji_u1f602.png      # Apache 2.0, 295 KB
curl -s -o joy.json     https://fonts.gstatic.com/s/e/notoemoji/latest/1f602/lottie.json                               # CC BY 4.0 Lottie
curl -s -o joy.webp     https://fonts.gstatic.com/s/e/notoemoji/latest/1f602/512.webp                                  # animated, alpha
curl -s -o joy_fluent.png "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/Face%20with%20tears%20of%20joy/3D/face_with_tears_of_joy_3d.png"  # MIT
curl -s -o joy_tw.svg   https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f602.svg                         # CC BY 4.0
curl -s -o joy_om.svg   https://cdn.jsdelivr.net/npm/openmoji@17.0.0/color/svg/1F602.svg                                # CC BY-SA 4.0
```

### 16. Telegram public channel preview (no login)
```bash
curl -s -A "Mozilla/5.0" "https://t.me/s/<channel>" | grep -o 'https://cdn[0-9]*\.telesco\.pe/file/[^"]*\.mp4[^"]*'
```
Tested on a public channel: 20 posts and tokenised mp4 links. Ask the user for trusted template channel names.

### 17. Know Your Meme: origin + original-size frames
```bash
curl -s -A "Mozilla/5.0" "https://knowyourmeme.com/memes/pray-for-nesamani/photos" | grep -o 'https://i.kym-cdn.com/photos/images/masonry/[^"]*' | sed 's#/masonry/#/original/#' | head -3
#  https://i.kym-cdn.com/photos/images/original/001/497/734/9aa.png   -> 200 image/png 1.28 MB
```

---

## Copyright reality (India + YouTube + Instagram)

- **India has no broad "fair use".** The Copyright Act 1957 protects the film and its soundtrack separately. Section 52(1)(a) "fair dealing" covers private use, criticism/review and reporting, and courts weigh purpose and amount. A 2–4 s reaction clip inside commentary is a grey area, not a safe harbour, and there is no explicit meme or parody exception.
- **Content ID catches short clips.** Sun TV/Sun NXT, Saregama, T-Series, Shemaroo, Goldmines, Sony and others fingerprint their films and shows (audio especially). A match usually means a **claim** (ad money goes to them, or the video is blocked in some regions), not a strike. Strikes come from manual takedowns, and 3 strikes ends the channel. **YouTube Help: a Short longer than 1 minute with any active Content ID claim is blocked worldwide**, whatever the claim's policy.
- **Monetisation is a separate risk.** YPP's reused/inauthentic-content rules demonetise channels built on other people's clips. Memes used as seasoning inside original educational content are the normal low-risk pattern. Instagram/Facebook Rights Manager can mute the audio or limit a reel.
- **"No copyright", "Creative Commons" and "free download" labels on template channels and sites are worthless** unless the uploader owns the film. GIPHY/Tenor/KLIPY terms let you share through their apps, not re-edit into monetised videos. **Client ads: never use any of these clips or stills.**
- **Safer pattern for the user's own videos:** keep the clip ≤2–3 s, put it inside their commentary, transform it (zoom/punch-in, captions), and avoid the film's music bed. If a claim lands, swap the clip or trim it in YouTube Studio's "Remove claimed content".

**Safer alternatives (when monetised or for clients)**
1. **Recreate the line in the user's own voice** (or their own cloned voice) over a still or their own reaction shot. That is their performance, with no film audio to fingerprint.
2. **Meme still + own SFX**: a KYM/Imgflip frame for 1 s with a licensed whoosh or record-scratch, instead of the clip's audio. Stills are rarely Content-ID matched, though still copyrighted.
3. **Act it out**: the user (or a 2BFT anime character) imitates the gesture or line. Parody of a well-known line is common and far lower risk.
4. **Licensed reactions**: Noto Animated / Noto 3D / Fluent 3D emoji, LottieFiles (Lottie Simple License), and the user's own sticker pack.
5. For client ads, only licensed stock or newly shot/recreated material.
