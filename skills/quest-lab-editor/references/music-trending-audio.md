# Music and trending audio — rights, the pack, and fresh research every time

## Rule 1: research trends fresh before every edit
Trends move weekly. Before each job, search (WebSearch, standard first, extended if thin) and write a dated list into the project's `EDIT-PLAN.md`:
- India: YouTube India weekly chart (Soundcharts / kworb), Spotify India daily (kworb), Billboard India; Tamil charts when the audience is Tamil.
- Global Shorts: the YouTube Shorts songs chart (ppc.land posts it weekly), TikTok Creative Center.
- Instagram formats: Later, Buffer, Hootsuite, CreatorDB, Social Media Today "trending audio this week" posts — note which are **not available to business accounts**.
- Note the date of every source; say so when data is older than ~3 weeks or thin (there is no official India Reels chart).
Downloads of any audio only after the user's explicit yes (file name, source, size).

## Rule 2: what can be embedded
- **YouTube long-form with a commercial song** → Content ID: block, monetise for the owner, or track. Creator Music is US-only and closed to new licences since 10 Aug 2026. Never bake commercial songs into the master.
- **YouTube Short uploaded as a file** → < 60 s normal Content ID; **60 s–3 min with any active claim = blocked worldwide**. Songs added in-app can run up to 90 s (some 60/30). One partner track halves the Short's revenue share; Audio Library tracks are never claimed.
- **Instagram Reel** → add trending songs **in-app** (Creator account; Business accounts only get the Meta Sound Collection). Embedded commercial songs get muted/blocked; repeat violations can remove a page. Downloads of a Reel lose licensed audio.
- **Third-party audio in the stream** (other creators' videos, songs he played, e.g. Seedhe Maut "Red") must be muted or cut in every deliverable.
- So: export the master with voice + SFX + a **licensed bed**, and also a **`_clean` version without music** for adding the trending song in-app. Each Short's notes name the trending song and where it should sit.

## Rule 3: licence terms of the sources we use
- **NoCopyrightSounds (NCS)**: free for independent creators on YouTube/Twitch, monetisation allowed, credit block in the description. Brands promoting their own products must contact NCS first — fine for a creator channel; ask before using NCS in an ad for your own product.
- **Kevin MacLeod (incompetech)**: CC BY 4.0, credit required.
- **StreamBeats (Harris Heller)**: free, no credit, use tracks as-is (no remix/speed-up).
- **Pixabay Music**: free, no credit, but avoid tracks with the "Content ID Registered" badge (or keep the licence certificate for disputes).
- **YouTube Audio Library**: safest default for YouTube; CC tracks need credit.
- SFX: Pixabay (no credit), Mixkit (no credit), Freesound CC0 only, Sonniss GDC bundles (no attribution; no AI training). Meme dialogue clips are copyrighted — recreate with his own voice.

## Your music pack — `music/<slug>/`
No music ships with this skill. Build your own pack from tracks you have the rights to (the sources above, or music you made), one folder per track, and write the folder path on one line in `<skill>/music_pack_path.txt`. Keep a table like this in the pack's README so every plan can pick by job:

| slug | track | licence | use | scan (bpm ≈, drops) |
|---|---|---|---|---|
| `<slug>` | `<artist — title>` | `<NCS / CC BY 4.0 / own>` | `<cold open / fails / reveal / talking bed / outro>` | `<from music_scan.py>` |

Run `engine/tools/music_scan.py music music/scan.json` after adding tracks (BPM estimates can be double/half; check by ear).

### Credit lines
Paste the exact credit line each licence asks for into the description of every video that uses the track (NCS gives one per release; CC BY 4.0 needs title, author, licence and link).

## Trend snapshot (write a fresh one per job)
Write the date, the platform, the song or format, why it fits this footage, and where it would sit, into `EDIT-PLAN.md`. Mark anything older than about three weeks as stale. Commercial songs from the snapshot go into the posting notes for in-app use only, never into the master.
