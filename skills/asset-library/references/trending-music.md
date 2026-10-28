# Trending music: where to look on every platform, and how Claude reads it

Every source below was fetched live on **28 Oct 2026 (IST)** with curl, Python urllib, WebFetch or the built-in browser. Each entry records what came back. India comes first, then global. The skill script `scripts/trending.py` reads **30 of these sources with no key, login or JS** (29 answer; Shazam is a canary that always fails in scripts) and prints one combined table plus an "India picks" summary.

**Verified 28 Oct 2026.** Re-run `scripts/trending.py --list` and fix any source that prints FAILED; update the row here when a site changes.

**Read this first: three facts that change how to use the charts**
1. **This machine's traffic leaves through a US address.** The YouTube visitorData decodes to `US`, Shazam answers from a Fastly Newark (EWR) cache, and Deezer's default chart is US-flavoured. So **always pass the country explicitly** (`in`, `IN`, `india`). Never trust a "default/auto" region.
2. **Spotify retired its Viral 50 charts in May 2026.** The Viral 50 Global playlist `37i9dQZEVXbLiRSasKsNU9` now returns 404 from the embed. Use **Viral Hits** (editorial) and **Trending Now India** instead.
3. **YouTube's old Trending page is gone.** `youtube.com/feed/trending` now redirects to `charts.youtube.com/charts/TrendingVideos`. **YouTube Charts publishes a real "Top Shorts songs" chart for India (daily + weekly)**. It is the best public proxy for short-form audio in India, and it reads with no key.

---

## 1. YouTube (start here for Shorts and Reels audio)

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it (endpoint/method) | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| **YouTube Charts – Top Shorts songs** | https://charts.youtube.com/charts/TopShortsSongs/in/daily | Songs ranked by **number of Shorts created with them**, daily + weekly, per country + global | **India yes**. Also has Hindi/Bhojpuri tracks | None | Internal JSON: `POST https://charts.youtube.com/youtubei/v1/browse?alt=json` with body `{"context":{"client":{"clientName":"WEB_MUSIC_ANALYTICS","clientVersion":"2.0","hl":"en","gl":"IN"}},"browseId":"FEmusic_analytics_charts_home","query":"perspective=CHART_DETAILS&chart_params_country_code=in&chart_params_chart_type=SHORTS_TRACKS_BY_USAGE&chart_params_period_type=DAILY"}` → `contents.sectionListRenderer.contents[0].musicAnalyticsSectionRenderer.content.trackTypes[0].trackViews[]` | **200, 184 KB JSON, no key.** Daily (to 26 Oct): 1 PASSO BEM SOLTO (Slowed), ATLXS · 2 Parvati, Sadhu Tiwari · 3 BAILA LENTO, sma$her. Weekly (to 22 Oct) #3 Meri Maa Ke Barabar Koi Nahi, Jubin Nautiyal | **The single best public short-form audio signal for India.** Use `WEEKLY` for stable picks and `global` for the world chart. The HTML page itself is a JS app |
| YouTube Charts – Top songs India (weekly) | https://charts.youtube.com/charts/TopSongs/in/weekly | Songs by views across all YouTube (incl. Shorts/UGC), weekly | India yes | None | Same POST, `chart_type=TRACKS&period_type=WEEKLY` | 200, 371 KB. 1 KALYANI (Remix), ARJN/KDS/FIFTY4/Shreya Ghoshal (32.98 M views) · 2 Yeshanagula · 3 Ala Bolelo, Anirudh | Each row carries `chartEntryMetadata` (position, previous position, weeks on chart, % change) plus songwriters |
| **YouTube Charts – language charts (Tamil, Hindi, etc.)** | https://charts.youtube.com/ (pick India → language) | Top music videos **by language of performance**, weekly | **Tamil (`ta`), Hindi (`hi`)**, Telugu, Punjabi, Bhojpuri, Haryanvi (`bgc`), "international" | None | Same POST, `chart_type=VIDEOS_LOP&period_type=WEEKLY&chart_params_chart_attribute=ta` (plain language code; `language:ta` returns 400) | 200. Tamil: 1 Radhimaa (Think Indie), Asma Teji/Sai Abhyankkar · 2 Veezha Veera · 3 Pavazha Malli, Sai Abhyankkar/Shruti Haasan. Hindi: 1 Casa Tupka Anthemo, Yo Yo Honey Singh | **The best Tamil-specific video chart that reads without a key** |
| YouTube Charts – Trending music videos / Top videos daily | https://charts.youtube.com/charts/TrendingVideos/in | Rolling "trending now" music videos; also daily top videos | India yes | None | Same POST, `chart_type=TRENDING_VIDEOS` (no period) or `chart_type=VIDEOS&period_type=DAILY` | 200. Trending: 1 Yeshanagula · 2 Veezha Veera (Hindi) · 3 Ramayana: Mangal Rang. Daily videos: 1 Glimpse of DSP Inbaraj (Sony Music South, 4.16 M) | `availableChartsInfo` in every response lists all chart types and their latest dates. India also has a weekly **podcast** chart |
| kworb – YouTube India weekly | https://kworb.net/youtube/insights/in.html | Mirror of YouTube's weekly India song chart, with view counts | India yes | None | Static HTML table; regex `<tr>`/`<td>`; date = first `YYYY/MM/DD` | 200, 25.7 KB. Date 2026/10/22. 1 ARJN – KALYANI (Remix) 32,981,818 · 2 Singer Prabha – Yeshanagula · 3 Anirudh – Ala Bolelo | Fallback if the innertube call ever breaks |
| kworb – Music videos trending in India | https://kworb.net/youtube/trending/in.html | YouTube trending music videos, India | India yes | None | Static HTML table | 200, 21.6 KB. 1 Glimpse of DSP Inbaraj (Respectaa) · 2 Hushaaru 2 teaser · 3 FREE FIRE INDIA IS HERE! | Mixes in non-music teasers. Filter them out |
| YouTube Data API `videos?chart=mostPopular` | https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=IN&videoCategoryId=10 | Most popular videos by region/category | India yes | **API key required** | — | **403** "Method doesn't allow unregistered callers" | Skip it. Charts innertube gives more for free |
| ppc.land weekly Shorts chart write-ups | https://ppc.land/ (e.g. /shorts-decides-the-charts-now-and-this-weeks-data-proves-it/) | Commentary on YouTube **global** weekly Shorts + songs charts | Global (Indian tracks appear) | None | HTML (Ghost CMS); WebFetch | Tag page 200. **The newest chart post found is from about March 2026**, so the series looks stale | Background reading only. Go to the chart itself |
| YouTube Shorts in-app sound picker | YouTube app → + → Short → "Add sound" → Trending / Top tabs. Or tap a sound on any Short → "Use this sound" | What is trending for **your** account/region right now | India (by phone location) | App login | **Claude cannot read it.** Ask the user for a screenshot | n/a | Ground truth for Shorts. The sound must be added in-app (see licensing) |

## 2. Spotify

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| charts.spotify.com (country daily/weekly) | https://charts.spotify.com/charts/view/regional-in-daily/latest | Top 200 India/global, daily + weekly, cities, genres | India yes | **Login required** for chart detail | Built-in browser + user's Spotify login only. The auth API `charts-spotify-com-service.spotify.com/auth/v0/charts/regional-in-daily/latest` returns **401** | HTML is a 12 KB Next.js shell. In the built-in browser the page redirected to `/home` with a "Log in" button | Use kworb or the playlist embeds instead |
| Spotify Charts public API | https://charts-spotify-com-service.spotify.com/public/v0/charts | **Global weekly** top 50 songs, albums, artists only | Global only | None | GET JSON → `chartEntryViewResponses[]` (alias `REGIONAL_GLOBAL_WEEKLY`) | 200, 84 KB. Week ending 2026-10-22: 1 Housewife, Tate McRae · 2 BbY WOW, KAROL G · 3 Nicole Kidman, ADÉLA | `?country=IN` and `/regional-in-daily` variants → 404 |
| **kworb – Spotify India daily / weekly** | https://kworb.net/spotify/country/in_daily.html · https://kworb.net/spotify/country/in_weekly.html | Spotify India Top 200, daily and weekly, with streams, days on chart and peak | **India yes** | None | Static HTML table; cell[2] = "Artist - Title (w/ feat)" | 200, 97.7 KB. Date 2026/10/26: 1 Hamza Malik – Alfaaz (w/ Zain Zohaib) · 2 Banjaare – Barsaat (w/ Roni) · 3 Anuv Jain – Arz Kiya Hai (Coke Studio Bharat) | Updated daily, about 1–2 days behind. Also `in_daily_totals.html` and `in_weekly_totals.html` |
| kworb – Spotify Global daily | https://kworb.net/spotify/country/global_daily.html | Global Top 200 daily, with streams | Global | None | Static HTML | 200, 89.6 KB. 2026/10/26: 1 Tate McRae – Housewife (7,222,738) · 2 KAROL G – BbY WOW · 3 ADÉLA – Nicole Kidman | `/spotify/` index lists every country |
| **Spotify playlist embeds (no auth)** | `https://open.spotify.com/embed/playlist/<id>` | The live tracklist of any public playlist | Yes, via the playlist chosen | None | GET HTML → `<script id="__NEXT_DATA__">` JSON → `props.pageProps.state.data.entity.trackList[]` (`title`, `subtitle` = artists, with `\xa0` separators) | 200, 83 KB. Works for all IDs below. A dead ID returns `pageProps.status: 404` | **Verified playlist IDs:** Top 50 India `37i9dQZEVXbLZ52XmnySJg` (1 Alfaaz · 2 Barsaat · 3 Arz Kiya Hai) · Top Songs India weekly `37i9dQZEVXbMWDif5SCBJq` · **Hot Hits Tamil `37i9dQZF1DX1i3hvzHpcQV`** (1 Muthumani (Dorothy), Ilaiyaraaja · 2 One Name, Anirudh) · **Hot Hits Hindi `37i9dQZF1DX0XUfTFmNBRM`** (1 Tera Mera Rishta (New Version) · 2 Gehra Hua) · **Trending Now India `37i9dQZF1DXbVhgADFy3im`** (75 tracks: 1 Jaiye Sajana · 2 Bairan) · Bollywood Central `37i9dQZF1DWXtlo6ENS92N` · Indie India `37i9dQZF1DX5q67ZpWyRrZ` · Top 50 Global `37i9dQZEVXbMDoHDwVN2tF` · Top Songs Global `37i9dQZEVXbNG2KDcFcKOF` · Today's Top Hits `37i9dQZF1DXcBWIGoYBM5M` · Viral Hits `37i9dQZF1DX2L0iB23Enbq` |
| Spotify Viral 50 India / Global | (was `37i9dQZEVXbLiRSasKsNU9` for global) | — | — | — | — | Embed **404 "Page not found"** | **Discontinued May 2026** (RouteNote, PiunikaWeb and HipHop-n-More reports). Use Viral Hits / Trending Now India |
| Soundcharts – Spotify India (public page) | https://soundcharts.com/en/charts/spotify/india | Spotify India **weekly** chart mirror | India yes | Free page; full data is paid | Server-rendered HTML; rank/title/artist lines after "Week of …" | 200, 192 KB. Week of 22 Oct 2026: 1 Barsaat · 2 Alfaaz · 3 Arz Kiya Hai · 4 Radhimaa (Think Indie) | Backup mirror. `/en/charts/youtube/india` also exists |

## 3. Apple Music / iTunes

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| **Apple Marketing Tools RSS v2 – Top songs** | https://rss.marketingtools.apple.com/api/v2/in/music/most-played/100/songs.json (also `/us/`) | Apple Music daily top songs per storefront (also `albums.json`, `music-videos.json`) | **India yes. Tamil dominates it right now** | None | GET JSON → `feed.results[]` (`name`, `artistName`, `genres`, `url`); `feed.updated` | IN 200 (100 rows), updated 27 Oct 21:20 UTC: 1 Ashke, Karan Aujla & MXRCI · 2 Veezha Veera (Tamil), Sai Abhyankkar · 3 One Sun One Moon (Jailer 2), Anirudh. US: 1 Housewife · 2 Choosin' Texas · 3 BbY WOW | The old host `rss.applemarketingtools.com` **301-redirects** here (the first try timed out), so call the new host directly. `new-releases` returned 404 |
| **iTunes legacy RSS by genre (Tamil/Bollywood)** | https://itunes.apple.com/in/rss/topsongs/limit=25/genre=1264/json | iTunes Store **sales** chart per genre | **Tamil = 1264**, Bollywood = 1263, Indian = 1262, Telugu = 1265, Regional Indian = 1266, Devotional = 1267 | None | GET JSON → `feed.entry[]` (`im:name.label`, `im:artist.label`); `feed.updated.label` | 200. Tamil: 1 Roddy Theme (Jailer 2) · 2 Jailer 2 Theme · 3 One Sun One Moon. Bollywood: 1 Hriday Mein Jinke Sitaram · 2 Mangal Rang (Ramayana) · 3 Jaiye Sajana | Purchases, not streams. Still a good "what's hot in Tamil this week" pulse |
| kworb – Apple Music India / iTunes India | https://kworb.net/charts/apple_s/in.html · https://kworb.net/charts/itunes/in.html | Apple Music and iTunes India daily, with movement | India yes | None | Static HTML table | 200 / 200. Apple: 2 Veezha Veera (+1) · 3 One Sun One Moon (−1) · 4 One Name. iTunes: 2 Roddy Theme (+112) · 3 RAYE – WHERE IS MY HUSBAND! | Shows rank change (+/−). Index at https://kworb.net/charts/ |

## 4. Shazam (early "people are asking what this song is" signal)

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| Shazam Top 200 India | https://www.shazam.com/charts/top-200/india | Most-Shazamed songs this week | India yes | None | **WebFetch only.** curl/urllib → **405 "Not allowed" (Varnish error 54113)**; the built-in browser got the **same 405** on this network. Do not try header tricks | WebFetch worked, though the text came back partial: #1 Alfaaz, Hamza Malik & Zain Zohaib (Ashke also visible) | All old JSON endpoints (`/shazam/v3/...ip-country-chart-IN`, `/services/charts/csv/...`) also return 405 here. Should work in the user's own browser |
| Shazam Discovery India | https://www.shazam.com/charts/discovery/india | "Artists on the move and their trending tracks this week" | India yes | None | WebFetch | WebFetch OK: 1 BbY WOW · 2 Aadame (From "Disco") · 3 Chalray Chalray Waal · 4 Tum Se Tum Tak, Niyam · 5 Filam | **The best early signal of what is rising.** Also exists: `/charts/viral/india` |
| Shazam city charts | https://www.shazam.com/charts/top-50/india/<city> | City top 50 | **Only Bengaluru, Delhi and Mumbai. No Chennai** | None | WebFetch | `/top-50/india/chennai` falls back to the India chart | For Tamil, use the YouTube `ta` chart, Hot Hits Tamil and iTunes 1264 instead |
| Soundcharts – Shazam | https://soundcharts.com/en/charts/shazam/global | Shazam global mirror | Global only | Free page | Server-rendered HTML | 200, week of 27 Oct. Rows look like long-tail catalogue (Calm Down, Water) | Not useful for India |

## 5. Instagram Reels (no public chart: use trackers, then confirm in-app)

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| Instagram Professional Dashboard → **Trending audio** | IG app → profile → Professional dashboard → Tips and resources / Reels trends → Trending audio | About the top 50 sounds used on Reels over the last ~3 days, with an ↗ (rising) arrow | Account's region (India if the phone is in India) | Professional (creator/business) account, app only | **Claude cannot read it.** Ask the user for a screenshot | n/a | Guides say it is US-first and rolling out. Some say all public accounts got it from Mar 2026 (unverified). **Business accounts see a reduced, licensed-for-business catalogue** |
| Reels audio picker ↗ arrow / audio page | Reels camera → Audio → Trending. Or tap the sound name on any Reel | Rising sounds (↗) and the number of Reels using a sound | India | App login | Screenshot from the user | n/a | The audio page's "N reels" count is the best freshness check. "Audio unavailable" on a business account means it is not licensed for business use |
| Edits app → Inspiration tab | Meta's Edits app (iOS/Android) | Reels that use trending sounds; "Use audio" button | India | App login | Screenshot | n/a | Free Meta editor with the full licensed library for the account type |
| @creators on Instagram / creators.instagram.com | https://www.instagram.com/creators/ · https://creators.instagram.com/ | Meta's own trend reports (periodic, not a chart) | Occasionally India editions (e.g. a 2022 India Reels trend report) | Web is JS/login | creators.instagram.com → **400** to curl; instagram.com/creators returns a 504 KB JS shell | n/a | Low frequency. Use as context only |
| **Later – "Instagram Reels Trends (Updated Weekly)"** | https://later.com/blog/instagram-reels-trends/ | Weekly hand-picked trending Reels audio and formats | US/global | None | Server-rendered HTML; `dateModified` in ld+json; WebFetch for the list | 200, 1.1 MB. **dateModified 2026-10-23** | The most consistent weekly tracker. Tags business-friendly "original audio" |
| **SocialPilot – "Trending Audio This Week"** | https://www.socialpilot.co/blog/instagram-reels-trends | Weekly list, plus a "**Trending Sounds Available for Business Accounts This Week**" section | Global | None | HTML h2/h3 headings | 200. Heading "Oct 12 – 25, 2026": 1 Hello October, Sugar Lime Blue · 2 My October, The Folks · 6 STORM II, GENER8ION | **Useful for business/client accounts** because of the business-safe list |
| **CreatorDB – Trending Instagram Audio This Week** | https://creatordb.app/free-tools/trending-instagram-audio/ | Weekly ranked "Heat" score that blends 7 trend reports, Reel counts and Spotify/Apple US chart heat | US-centric | None | Server-rendered HTML table | 200. "October 21, 2026": 01 Patient Zero, Taylor Swift (Heat 95, Rising, 53K reels) · 02 Nicole Kidman, ADÉLA (78, Peaking) · 03 We Fell in Love in October, girl in red | Has Rising/Peaking/Returning labels, which help with timing |
| Buffer – "13 Trending Sounds on Instagram in October 2026" | https://buffer.com/resources/trending-audio-instagram/ | Monthly list | Global | None | HTML h3 "1. Title" | 200. 1 What You Waiting For? · 2 Last Train to London · 3 Upside Down … 13 Nicole Kidman | Monthly, so slower |
| Dash Social – Trending Reels songs | https://www.dashsocial.com/blog/trending-instagram-reels-songs | Monthly, with Reel counts | Global | None | HTML h3 | 200. Oct 2026: Patient Zero (189K Reels) · Nicole Kidman (328K) · Autumn Colors, LuLuMusic (86K) | |
| **ZOPE Digital – Hindi Reels songs (India)** | https://zopedigital.in/instagram-trending-songs | Weekly top 10 **Hindi** Reels songs, built from the Spotify India daily chart | **India / Hindi** | None | Server-rendered HTML | 200. "Last updated: 24 October 2026": 1 Barsaat · 2 Arz Kiya Hai · 3 Alfaaz · 4 Khat · 5 Bairan | The only dated India-specific Reels list found. It is a Spotify proxy, not Reels data |
| SocialBee – trending Instagram songs this week | https://socialbee.com/blog/trending-instagram-songs-this-week/ | Weekly list (search shows "Oct 21, 2026") | Global | None | **403 to curl (Cloudflare)** → WebFetch or the built-in browser | 403 | |
| TechnoSports (India) weekly Reels trend roundups | https://technosports.co.in/ (search "Trending Dance & Song Challenges This Week") | Weekly India Reels/dance trends | **India; mentions Tamil** | None | WebSearch for the newest post, then WebFetch | Newest found: "Oct 2–9, 2026 … Tamil Beats Rule Reels" (≈3 weeks old) | Irregular. Treat as a hint |
| Social Samosa / afaqs! | https://www.socialsamosa.com · https://www.afaqs.com | Indian social-media news (trend stories, Meta India reports) | India | None | WebSearch `site:socialsamosa.com reels trending audio` | Social Samosa search page 200 (nothing parseable); **afaqs 403 Cloudflare** | News, not charts |
| Hootsuite Reels trends | (old URL blog.hootsuite.com/instagram-reels-trends/) | — | — | — | — | **404** (moved) | Skip it |

## 6. TikTok (banned in India, but it shows what reaches Reels 1–3 weeks later)

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| TikTok Creative Center (now "TikTok One Creative Suite") | https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en | Was: popular/breakout songs by region, 7/30/120 days | **No India** (TikTok is banned there). US/UK/etc. | **Songs now need login** | Built-in browser only. curl gets a 21 KB JS shell. API `ads.tiktok.com/creative_radar_api/v1/popular_trend/sound/rank_list` → `{"code":40101,"msg":"no permission"}` | In the browser it redirected to `/creative/creativeCenter/trends/hashtag?region=US`. Logged out it shows **only Hashtag (top 3) and Video tabs; `/trends/song` redirects back to hashtags** | The free songs chart is effectively gone for logged-out users |
| tokchart.com | https://tokchart.com/ | TikTok songs ranked by new UGC videos in 24h | Global | Free top 5; the rest is paid | Server-rendered HTML; parse text lines after "Number #" | 200. Title "Top trending songs on TikTok today 27 October 2026": 1 Housewife, Tate McRae (+35K UGC/24h) · 2 πρωτότυπος ήχος – harrison.saltzman · 3 Zany Emote Fortnite | The "will trend tomorrow" list is paywalled |
| Buffer – trending TikTok songs (monthly) | https://buffer.com/resources/trending-songs-tiktok/ | Monthly list | Global | None | HTML h3 | 200. "October 2026": 1 Ramalama (Bang Bang) · 2 original sound – Nileyna Garcia | |
| Soundcharts – TikTok charts | https://soundcharts.com/en/charts/tiktok/worldwide | TikTok weekly by country (72 countries, **not India**) | No India | Free page | Server-rendered HTML | 200, week of 27 Oct: 1 we fell in love in october, girl in red (108K) · 2 Faded, Alan Walker · 3 Set Fire to the Rain | Neighbour markets (Bangladesh, Pakistan, Gulf) are a proxy for desi sounds |

## 7. Indian streaming services and Indian charts

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| **JioSaavn charts list** | `https://www.jiosaavn.com/api.php?__call=content.getCharts&api_version=4&_format=json&_marker=0&ctx=web6dot0` | The chart playlists for the language cookie | **Hindi by default; add cookie `L=tamil` for Tamil charts** | None (unofficial API) | GET JSON list (`id`, `title`, `perma_url`) | 200. Default: Hindi: India Superhits Top 50 · India Superhits Top 50 · Trending Today … With `L=tamil`: **Tamil: India Superhits Top 50** (id 1134651042), Most Searched Songs – Tamil | Unofficial. It could change without notice |
| **JioSaavn playlist contents** | `...&__call=webapi.get&type=playlist&p=1&n=50&token=<token>` | Tracks of a chart playlist | Yes | None | JSON → `list[]` (`title`, `more_info.artistMap.primary_artists`, `language`, `year`); `more_info.last_updated` (epoch) | 200. **Trending Today** (token `I3kvhipIy73uCJW60TJk1Q__`, updated 27 Oct 18:00 IST): 1 Chann (Udta Teer), Sachin-Jigar/Arijit · 2 Hanuman Chalisa… **India Superhits Top 50** (`VuJUPQ9ch77bB,U5Yp5iAA__`): 1 Casa Tupka Anthemo · 2 Yeshanagula · 3 Gehra Hua. **Tamil Top 50** (`Dq3pWn1coqesud-ETNX4vg__`): 1 One Sun One Moon · 2 One Name · 3 Ala Bolelo | `playlist.getDetails&listid=<id>` also works. Hindi Top 50 token is `zlJfJYVuyjpxWb5,FqsjKg__` |
| JioSaavn `content.getTrending` | `...&__call=content.getTrending&entity_type=song&entity_language=tamil` | "Trending" songs/albums per language | Tamil/Hindi | None | JSON list | 200, but **stale/evergreen**: Tamil gave Kannadi Poove, Arabic Kuthu, Ordinary Person (Leo). Hindi gave Akhiyaan Gulaab, Ram Siya Ram | **Do not use it for "now"**. Use the playlists above |
| **Gaana – Top charts + language Top 50s** | https://gaana.com/charts/top-songs/weekly · https://gaana.com/playlist/gaana-dj-tamil-top-50-2 · https://gaana.com/playlist/gaana-dj-hindi-top-50-1 | Weekly top songs; language Top 50 playlists (Tamil, Hindi, Telugu, Punjabi, Bhojpuri, Haryanvi) | **India; Tamil and Hindi yes** | None | Server-rendered HTML. Playlist pages carry **ld+json `MusicPlaylist.track[]`** (`name`, `byArtist.name`, `inLanguage`); the charts page gives `/song/<slug>` links in order | 200. Tamil Top 50 (ld+json has 22 tracks): 1 Raavana Mavandaa (Jana Nayagan), Anirudh · 2 Thalapathy Kacheri · 3 Pattampoochi. Charts weekly order: casa-tupka-anthemo, gehra-hua, parvati | No public JSON API needed. `gaana.com/songs` = "Trending Songs" |
| Wynk Music | https://wynk.in/music | — | — | — | — | 200 but a stub (261 chars of text, footer "Hellotunes") | **Shut down.** Airtel announced the closure on 27 Aug 2024 and moved users to Apple Music; the app closed around Dec 2024. Ignore it |
| Amazon Music India | https://music.amazon.in/popular/songs | Popular songs India | India | None to view | **Built-in browser only** (8 KB JS shell, no data in HTML) | 200, empty shell | Soundcharts only mirrors Amazon "worldwide". Low priority |
| Hungama Music | https://www.hungama.com/music/top-charts/ | Top charts | India | — | JS shell (319 chars of text) | 200, no chart data | Low relevance now. Skip |
| Audiomack | https://audiomack.com/ | Trending/top songs | Minor India presence | API needs OAuth | `api.audiomack.com/v1/music/trending` → **401**; `/trending-now` and `/songs/week` → 404 page | Not usable without the browser | Low priority (Africa/US hip-hop) |
| **Billboard India Songs** | https://www.billboard.com/charts/india-songs-hotw/ | Weekly top 25 India (streams + downloads, Luminate) | India yes | None | Server-rendered HTML; regex `<li class="o-chart-results-list__item…"><h3 id="title-of-a-story">TITLE</h3><span>ARTIST</span>`; "Week of …" | 200, 1.38 MB. Week of 31 Oct 2026: 1 Barsaat, Banjaare & Roni · 2 Alfaaz · 3 Kalyani, ARJN/KDS/FIFTY4/RONN | Good weekly cross-check |
| IMI (Indian Music Industry) charts | https://indianmi.org/charts/ → https://www.imicharts.com/ | **International** (non-Indian) Top 20 singles in India, weekly | India market, but only foreign songs | None | Server-rendered HTML (WordPress) | 200. **The latest shown is the week ending 17 Aug 2026 (Week 33)**, so it is about 10 weeks stale | Not useful for Indian trends |
| Radio Mirchi Top 20 | https://www.radiomirchi.com/more/mirchi-top-20/ | (was a weekly Bollywood countdown) | Hindi | — | — | 200 but **redirects to mirchi.in/stories** (news) | The chart page is gone |
| Tamil-specific roll-up | — | — | **Tamil** | — | Use: YouTube `VIDEOS_LOP` + `ta`; Spotify Hot Hits Tamil; iTunes genre 1264; JioSaavn Tamil Top 50 (cookie `L=tamil`); Gaana Tamil Top 50; Apple Music IN (currently Tamil-heavy) | All tested OK (above) | No standalone Tamil chart site worth scraping. These six cover it |
| 12notez – Trending Songs India | https://12notez.in/trending-songs/india | Monthly India trending | India | — | **403 Cloudflare** | 403 | Search snippets show it mirrors Spotify India |

## 8. Global and aggregate charts

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| Billboard Hot 100 / Global 200 | https://www.billboard.com/charts/hot-100/ · https://www.billboard.com/charts/billboard-global-200/ | US weekly / world weekly | Global (Indian songs appear on the Global 200 sometimes) | None | Same regex as Billboard India | 200 (3.1 MB / 4.9 MB). Week of 31 Oct 2026. Hot 100: 1 Choosin' Texas · 2 Housewife · 3 Expectations. Global 200: 1 Housewife · 2 Expectations · 3 BbY WOW | |
| **Deezer API /chart** | https://api.deezer.com/chart/0/tracks?limit=50 | Deezer top tracks (`0` = all genres; other ids are genres, e.g. 116 = rap) | No India (Deezer is not big there) | **No key** | GET JSON → `data[]` (`position`, `title`, `artist.name`, `rank`) | 200, 105 KB: 1 Dracula (with JENNIE), Tame Impala · 2 Boston, STELLA LEFTY · 3 Choosin' Texas | Region follows the caller's IP (US here) |
| **kworb overview** | https://kworb.net/ (Spotify, YouTube, Apple, iTunes, radio, "pop" aggregate) | Mirrors of many official charts | India pages for Spotify, YouTube, Apple, iTunes | None | Static HTML | All pages tested 200 | The most reliable no-JS mirror. Be polite: one fetch per page per run |
| **Genius chart** | https://genius.com/api/songs/chart?time_period=day&chart_genre=all&per_page=10&page=1 | Songs by lyric-page views (day/week/month/all_time; genres: rap, pop, rb, rock, country) | Global, but Indian songs show up | **No key** for this endpoint | GET JSON → `response.chart_items[].item` (`title`, `artist_names`, `stats.pageviews`) | 200: 1 Alfaaz, Hamza Malik & Zain Zohaib (698K views) · 2 Nicole Kidman, ADÉLA · 3 Housewife | Genius's HTML homepage → 403. Use the API URL |
| Last.fm charts | https://www.last.fm/charts | Scrobble charts (daily/weekly) | Web chart is global; `?geo=India` is **ignored** | Web: none. API (`geo.gettoptracks`): **key required** (error 6) | curl → "Client Challenge" page. **The built-in browser passes it after ~4 s** | Browser: 1 expectations (feat. Chappell Roan), Olivia Rodrigo · 2 Nicole Kidman · 3 Housewife | Tiny Indian user base. Low value |
| Soundcharts | https://soundcharts.com/en/charts | Public mirrors: Spotify/YouTube (incl. India), Shazam, JioSaavn, Gaana, Amazon, TikTok, Melon, Anghami, Boomplay, airplay | Some India pages (Spotify/YouTube/airplay India) | Free pages; full data is paid | Server-rendered HTML ("Week of …" plus rank lines) | 200. JioSaavn page (week of 23 Oct): 1 Chann (Udta Teer) · 2 Main Ram (Ramayana) · 3 Tujh Mein Basi Meri Jaan | A handy single site of mirrors. Free views are truncated |
| Chartmetric | https://app.chartmetric.com/charts | Everything (incl. TikTok/IG/Shazam India) | Yes | **Paid account** | JS app (24 chars of text in HTML) | 200, empty shell | Only worth it if the user subscribes |
| Songstats | https://songstats.com/charts | Track analytics/charts | Yes | **Paid / login** | JS app (redirects to the homepage) | 200, empty shell | Same as above |
| Spotify Viral | — | — | — | — | — | Discontinued May 2026 (see §2) | Use the Viral Hits playlist |
| SoundCloud charts | https://soundcloud.com/charts/top | (was Top 50 / New & Hot) | — | — | — | **404**, JS-only site | SoundCloud charts are gone. Skip |
| Boomplay | https://www.boomplay.com/trending-songs | Trending songs | Africa-focused | None | Server-rendered HTML | 200, 306 KB | Not relevant for India |
| Anghami | https://play.anghami.com/chart/top-50 | MENA charts | No (Gulf diaspora only) | — | Chart URL **404**; Soundcharts has `/en/charts/anghami` | 404 | Only for Gulf-targeted client ads |
| **Melon (Korea)** | https://www.melon.com/chart/index.htm | Korean realtime/daily Top 100 | No (K-pop trends) | None | Server-rendered HTML; regex `div.ellipsis.rank01 a` (title) and `rank02 a` (artist) | 200, 466 KB, 100 rows: 1 NEON, A2O · 2 꿈꾸던 어른이 되었나요?, 머무르 · 3 퇴사할게여 (Narr. 기안84), SOYEON | K-pop crossovers (ILLIT and BTS are on Last.fm now) |

## 9. Meme and trend culture (for format and hook ideas, not songs)

| Source | URL | What it ranks | India/Tamil/Hindi? | Login/key? | How Claude reads it | Test result (28 Oct 2026) | Notes |
|---|---|---|---|---|---|---|---|
| Know Your Meme | https://knowyourmeme.com/ · https://knowyourmeme.com/memes/popular | Newsworthy and popular memes | Mostly global | None | Server-rendered HTML; links `/memes/<slug>` | Home 200: snicker-cat, black-cat-clapping, skull-cap-trend, dictator-mbappe … `/memes/trending` → **404** | Use the homepage "Newsworthy" section |
| **Google Trends – Trending now RSS** | https://trends.google.com/trending/rss?geo=IN | Rising searches in India, about the last 24 h (all topics) | **India; includes Hindi-script queries** | None | GET RSS/XML → `<item><title>`, `<ht:approx_traffic>`, `<pubDate>`, plus news links | 200, 10 items: ford trophy (100+) · thane news (200+) · सोना चांदी (1000+) | The full trending UI (category filter "Entertainment") needs JS, so use the built-in browser. Good for topical hooks (a match, a film release) |
| Exploding Topics | https://explodingtopics.com/ | Fast-growing topics (products, tech) | Global | Topic lists need login | Homepage server-rendered (Next.js); `/topics-this-month` → redirect to `/auth` | Home 200 (no music topics) | Not a music source. Skip for audio |

---

## Weekly trend-check routine (run before every edit, India first)

1. **Run the probe** (about 12 s):
   `python -I <skills>/asset-library/scripts/trending.py --top 15 --md <edit-folder>/trending_<date>.md` (add `--lang ta`, `hi`, `en` or `shorts` to narrow it; `--json` for rows).
   Note the chart dates printed in brackets. Spotify/kworb lag 1–2 days, and the YouTube weekly charts close on Thursdays.
2. **Short-form first:** read `yt_shorts_in_daily` and `yt_shorts_in_weekly`. These are the only public charts ranked by **how many short videos used the song**, the closest proxy for Reels audio in India. Then check `yt_shorts_global` for imports (Brazilian phonk, slowed edits) that are crossing into India.
3. **Language pass** (match the edit's language):
   - Tamil: `yt_tamil`, `sp_hot_tamil`, `itunes_tamil`, `jiosaavn_tamil`, `gaana_tamil`, `apple_in`.
   - Hindi/Hinglish: `yt_hindi`, `sp_hot_hindi`, `sp_trending_in`, `itunes_bollywood`, `jiosaavn_top50`, `kworb_sp_in`, plus a WebFetch of the ZOPE Hindi Reels list.
   - English/global: `kworb_sp_global`, `sp_global_weekly`, `apple_us`, `billboard_global200`.
4. **Rising signals:** WebFetch `shazam.com/charts/discovery/india` and `/charts/top-200/india` (not curl). Check `sp_trending_in` for editorial picks and `genius_day` for songs people are looking up.
5. **Reels trackers:** WebFetch Later (weekly; check `dateModified`), the SocialPilot weekly page (copy its **business-safe** list for client/brand accounts) and CreatorDB (Rising/Peaking labels). Then WebSearch "trending reels audio India this week" for TechnoSports and similar Indian roundups. Treat them as US-leaning unless they say India.
6. **TikTok lead indicator** (optional): the tokchart top 5 and Buffer's monthly TikTok list. Sounds that peak there often reach Reels 1–3 weeks later.
7. **Ground truth from the user's phone:** ask the user for a screenshot of IG Professional Dashboard → Trending audio (and the ↗ list in the Reels audio picker), plus the YouTube Shorts "Add sound → Trending" tab. These are the only views of what *their* account can actually use.
8. **Score and shortlist** (the script prints this summary as "Seen on several India charts" with a verdict per song): in ≥3 India sources including a Shorts chart = **hot/safe**. Only in Shorts/Shazam Discovery/Reels trackers = **rising, use now**. Only on streaming charts = **popular, but maybe not a Reels sound**. Pick 3–5 and write them, with the date, into the edit's notes.
9. **Check availability on the posting account:** search the exact sound in the IG audio library from the account that will post. If it is "unavailable" or missing on a business/brand account, switch to a Meta Sound Collection track, or to licensed BGM from the asset-library music section.
10. **Never download a trending track into the timeline** for the master. The edit gets a licensed or royalty-free bed (or silence or VO only), timed so the trending sound can be laid on top in-app.

## Licensing reminder (read before every edit)

- **Trending commercial songs go on Reels/Shorts in-app only.** Add them from Instagram's or YouTube Shorts' own audio picker at upload time. Platform licences cover only that in-app use. **Never bake a commercial song into an exported master** (the uploaded .mp4) for YouTube long-form, Reels, Shorts, or anything sent to a client. Baked-in tracks trigger Content ID / Rights Manager claims, muting, blocked regions, demonetisation or removal.
- **Business accounts only get the Meta Sound Collection** (Meta's royalty-free library) plus whatever Meta has cleared for business use. The full trending catalogue is for personal/creator accounts. Client brand accounts, and 2BFT if it is set as a business account, should plan on Sound Collection tracks or "original audio" flagged business-safe. Even those are not royalty-free for ads.
- **Boosted posts and paid ads cannot use licensed commercial music.** Meta will not let you boost a Reel with it, and YouTube ads with it get claimed. Client ads always use properly licensed or royalty-free music (stock libraries with a commercial licence, Meta Sound Collection inside Meta ads, the YouTube Audio Library for YouTube).
- **YouTube long-form:** commercial songs are almost always Content ID-claimed (revenue goes to the rights holder, or the video is blocked). Use the YouTube Audio Library or licensed music. Shorts can use songs from the Shorts sound picker. A Short that reuses a claimed song in a long-form video gets the claim there too.
- Charts tell you *what* is trending. They never grant a licence. Record which tracks were added in-app so later re-uploads do not accidentally bake them in.

---

## Sample output of `scripts/trending.py` (run 28 Oct 2026 03:09 IST, `--top 5`, trimmed to 3 rows)

```
Trending probe - fetched 2026-10-28 03:09 IST - top 5 per source
SOURCE                 |  # | TITLE                                            | ARTIST
## YouTube Charts - Top Shorts songs India (daily, by # of Shorts made)  [day ending 2026-10-26]
yt_shorts_in_daily     |  1 | PASSO BEM SOLTO (Slowed)                         | ATLXS
yt_shorts_in_daily     |  2 | Parvati                                          | Sadhu Tiwari
yt_shorts_in_daily     |  3 | BAILA LENTO                                      | sma$her, MC DA$ILVA
## YouTube Charts - Tamil-language top videos India (weekly)  [week ending 2026-10-22]
yt_tamil               |  1 | Radhimaa [From "Think Indie"]                    | Asma Teji, Sai Abhyankkar, Vivek
yt_tamil               |  2 | Veezha Veera (From "OM Chapter 1: Udhiram - The  | Ritesh G Rao, Sai Abhyankkar, Rahul
yt_tamil               |  3 | Pavazha Malli                                    | Sai Abhyankkar, Shruti Haasan
## YouTube Charts - Hindi-language top videos India (weekly)  [week ending 2026-10-22]
yt_hindi               |  1 | Casa Tupka Anthemo                               | Yo Yo Honey Singh
yt_hindi               |  3 | Parvati                                          | Sadhu Tiwari
## kworb - Spotify India daily  [2026/10/26]
kworb_sp_in            |  1 | Alfaaz (w/ Zain Zohaib)                          | Hamza Malik
kworb_sp_in            |  2 | Barsaat (w/ Roni)                                | Banjaare
kworb_sp_in            |  3 | Arz Kiya Hai | Coke Studio Bharat                | Anuv Jain
## Spotify playlist - Hot Hits Tamil (editorial)  [live playlist: Hot Hits Tamil]
sp_hot_tamil           |  1 | Muthumani (From "Dorothy")                       | Ilaiyaraaja, Shweta Mohan
sp_hot_tamil           |  2 | One Name                                         | Anirudh Ravichander, Super Subu
sp_hot_tamil           |  3 | Raga of Revenge                                  | Anirudh Ravichander
## Spotify playlist - Trending Now India (editorial)  [live playlist: Trending Now India]
sp_trending_in         |  1 | Jaiye Sajana                                     | Shashwat Sachdev, Jasmine Sandlas, Satin
sp_trending_in         |  2 | Bairan                                           | Banjaare
sp_trending_in         |  3 | KALYANI - Remix                                  | ARJN, KDS, FIFTY4, Shreya Ghoshal
## Apple Music - Top songs India (daily)  [Tue, 27 Oct 2026 21:39:44 +0000]
apple_in               |  1 | Ashke                                            | Karan Aujla & MXRCI
apple_in               |  2 | Veezha Veera (From "OM Chapter 1: Udhiram  - The | Sai Abhyankkar, Tippu & Arun Srinivasan
apple_in               |  3 | One Sun One Moon (From "Jailer 2")               | Anirudh Ravichander, Super Subu, M.S Krs
## iTunes Store - Top Tamil songs India (sales)  [2026-10-27T14:39:09-07:00]
itunes_tamil           |  1 | Roddy Theme (From "Jailer 2")                    | Anirudh Ravichander
itunes_tamil           |  2 | Jailer 2 Theme                                   | Anirudh Ravichander, M.S Krsna & Super S
## JioSaavn - Tamil: India Superhits Top 50  [Tamil: India Superhits Top 50 (updated 2026-10-23 10:10 IST)]
jiosaavn_tamil         |  1 | One Sun One Moon                                 | Anirudh Ravichander, Super Subu, M.S Krs
jiosaavn_tamil         |  2 | One Name                                         | Anirudh Ravichander, Super Subu
jiosaavn_tamil         |  3 | Ala Bolelo                                       | Anirudh Ravichander, Arunraja Kamaraj
## Gaana - Tamil Top 50  [live playlist: Tamil Top 50]
gaana_tamil            |  1 | Raavana Mavandaa (From Jana Nayagan)             | Anirudh Ravichander, Vivek
gaana_tamil            |  2 | Thalapathy Kacheri (From Jana Nayagan)           | Anirudh Ravichander, Vijay, Arivu
## Billboard - India Songs (weekly)  [week of October 31, 2026]
billboard_india        |  1 | Barsaat                                          | Banjaare & Roni
billboard_india        |  2 | Alfaaz                                           | Hamza Malik x Zain Zohaib
## Shazam - India Top 200 (canary: expected to fail in scripts)  [n/a]
shazam_in              | -- | FAILED: RuntimeError: HTTP 405 - Shazam blocks scripted requests; use WebFetch on https://www.shazam.com/charts/top-200/india
## YouTube Charts - Top Shorts songs Global (weekly)  [week ending 2026-10-22]
yt_shorts_global       |  1 | PASSO BEM SOLTO (Slowed)                         | ATLXS
yt_shorts_global       |  2 | Headlights (feat. KIDDO)                         | Alok, Alan Walker
## Spotify Charts public API - Global weekly  [week ending 2026-10-22]
sp_global_weekly       |  1 | Housewife                                        | Tate McRae
sp_global_weekly       |  2 | BbY WOW                                          | KAROL G, Judeline, rusowsky
## Deezer API - Global chart  [live]
deezer_global          |  1 | Dracula (with JENNIE)                            | Tame Impala
## Genius - top songs by lyric views (24h)  [last 24h (lyrics page views, global)]
genius_day             |  1 | Alfaaz                                           | Hamza Malik & Zain Zohaib
29/30 sources OK - fetched 2026-10-28 03:09 IST
```

Script keys (`--list`): yt_shorts_in_daily, yt_shorts_in_weekly, yt_songs_in, yt_tamil, yt_hindi, yt_trending_in, kworb_sp_in, kworb_yt_in, sp_top50_in, sp_hot_tamil, sp_hot_hindi, sp_trending_in, apple_in, itunes_tamil, itunes_bollywood, jiosaavn_trending, jiosaavn_top50, jiosaavn_tamil, gaana_tamil, billboard_india, shazam_in (canary), yt_shorts_global, kworb_sp_global, sp_global_weekly, sp_viral_hits, apple_us, deezer_global, billboard_global200, genius_day, gtrends_in.

**Fragility notes:** unofficial endpoints (YouTube Charts innertube, JioSaavn `api.php`, Spotify embed `__NEXT_DATA__`, Gaana ld+json) can change without notice. Each fails on its own in the script and prints `FAILED: …`. Fall back to the kworb mirror, WebFetch or the built-in browser listed in the table row.
