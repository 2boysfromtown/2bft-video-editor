# Licence cheat sheet (read before any download)

Plain-language rules for deciding whether an asset can go into a given deliverable. Licence pages change: when a source's row in another reference file says "verified", that is the date it was last checked; re-check the licence page if it is older than ~3 months or the asset is going into a paid client ad.

## 1. What each licence word means

| Label | Can use in my videos? | Credit? | Paid client ads? | Can edit/remix? | Watch out |
|---|---|---|---|---|---|
| **CC0 / Public domain** | yes | no (nice to give) | yes | yes | Someone may still have uploaded a copyrighted file and wrongly marked it CC0 (common on Freesound, Openverse, Wikimedia). Check the uploader looks like the real creator. |
| **CC BY** | yes | **yes**: title, author, source link, licence link | **avoid**: allowed only if the credit can appear where viewers see it, which a paid ad almost never allows | yes | Credit goes in the YouTube description / Reel caption or pinned comment. Keep it in `CREDITS`. |
| **CC BY-SA** | yes | yes | yes, but adapted versions must carry the same licence | yes | Fine for fonts/emoji (OpenMoji); avoid for music you'd remix into a client deliverable. |
| **CC BY-NC** (any NC) | only non-commercial | yes | **no** | depends | "Non-commercial" includes monetised YouTube and anything promoting a business. Treat NC as "personal tests only". |
| **CC BY-ND** | only unchanged | yes | depends | **no** | Trimming/remixing music counts as a change. Usually skip. |
| **Royalty-free (site licence)** | per site terms | per site | per site | usually | Read the site's own licence: Pixabay, Mixkit, Pexels, Uppbeat, etc. each have a different list of forbidden uses (e.g. no reselling the file as-is, no use in trademarks/logos). |
| **"Free for creators" (NCS, StreamBeats)** | yes for the user's own channels | NCS: yes; StreamBeats: no | **ask first / no** | NCS: no remixing beyond the edit; StreamBeats: use as-is | Brands promoting their own products are a different case (NCS asks brands to contact them). |
| **Content ID registered** | usable, but YouTube may put a claim on the video | per site | risky | — | A claim can take the ad revenue or, on Shorts 60 s–3 min, block the Short worldwide. Keep the licence certificate; prefer non-registered tracks for Shorts. |
| **Copyrighted (film/TV clips, commercial songs)** | only by the user's explicit choice, short, unmonetised | — | **never** | — | Meme clips and trending songs fall here. See §3 and §4. |
| **Editorial use only** | news/commentary only | — | **no** | — | Common on stock sites for photos with logos, events or recognisable people. |

## 2. Per deliverable

- **Paid client ads (any brand):** the test is **commercial use + no credit + no share-alike**. That means CC0 or public domain; site licences that grant exactly that (Mixkit, Pexels, Pixabay tracks without the "Content ID Registered" or "AI generated" badge, Coverr, Unsplash); OFL, Apache or MIT fonts and icons; the user's own recordings; generated assets with commercial terms; or paid pro licences at the right tier (Epidemic Pro, Artlist, Envato, Purple Planet Standard). Not CC BY (no room for the credit), not BY-SA, no NC, no NCS without permission, no meme clips, no trending commercial songs in the file. `find_assets.py --ad-safe` applies this filter. Re-open the licence page of each item used, and keep every licence certificate in the job's `CREDITS`.
- **What the licence doesn't cover in an ad:** recognisable people (need a model release), brand logos, number plates and trademarks in shot, landmarks that imply an endorsement. Look at frames of every clip before it goes in an ad (a contact sheet at 1 frame per second is enough): a Hyundai badge on a steering wheel in a car-delivery ad is a real problem even when the footage licence is clean.
- **YouTube long-form (2BFT, Let Nav Live):** CC0, CC BY with credit, site-licence royalty-free, NCS (with the credit block), YouTube Audio Library. Content-ID-registered tracks only if the user accepts a possible claim. Commercial songs → Content ID claims (blocked, monetised for the owner, or tracked): never bake them into the master.
- **YouTube Shorts uploaded as a file:** under 60 s a claim behaves like long-form; **60 s – 3 min with any active claim = blocked worldwide**. Songs added from the Shorts in-app library are licensed for the clip length the app allows. Audio Library tracks are never claimed.
- **Instagram Reels:** trending songs are added **in-app** (Creator account). Business accounts only get the Meta Sound Collection. Songs embedded in an uploaded file get muted or blocked. So export a **`_clean`** version (voice + SFX, no music, or a licensed bed) for the user to add the trending track in the app, and name the song + where it should start in the notes.
- **Personal / test / internal:** anything goes for a preview, but say what would have to be swapped before publishing.

### Quick picks by deliverable (checked 28 Oct 2026; details and caveats in each reference file)

| Deliverable | Music | SFX | Visuals |
|---|---|---|---|
| **Paid client ad, zero budget** | Mixkit Stock Music (online ads named in the licence), FreePD folders on the Internet Archive (CC0), own ACE-Step / Stable Audio 3 generations | Mixkit SFX, Freesound **CC0 only**, Kenney (CC0), Sonniss GDC bundles, Adobe Audition SFX zips | Pexels, Pixabay, Mixkit video, Coverr, Poly Haven, ambientCG, Google Fonts (OFL), Noto/Fluent emoji |
| **Paid client ad, small budget** | Purple Planet Standard ($8/track, same-day channel clearance), Jamendo Licensing (€29/track), Hoopr Business, Hoopr Smash (real Bollywood hits for brands) | Epidemic Sound Pro, Envato Elements (register the project) | Envato Elements, Storyblocks Business |
| **Own YouTube long-form** | YouTube Audio Library (never claimed on YouTube), the licensed pack, NCS (credit), Incompetech (credit), StreamBeats (as-is) | all of the above + Pixabay | + Wikimedia Commons with credit, NASA, Prelinger |
| **Own Shorts / Reels** | trending song added **in-app**; bed from the pack, Pixabay (no "Content ID Registered" badge), NCS | + meme boards (own channels only, by the user's choice) | + meme clips 1–3 s (own channels only) |

Never in client work: NC or ND licences, CC BY-SA (share-alike spreads to the whole video), NCS without NCS's permission, StreamBeats, YouTube Audio Library standard tracks outside YouTube, BBC Sound Effects (no social media), Uppbeat/Bensound free tiers, Suno free-plan songs, MusicGen/AudioGen/MMAudio outputs (non-commercial weights), meme clips or meme sounds, and commercial songs.

## 3. Meme clips (film, TV, viral videos)

- They are copyrighted. In India there is no broad "fair use"; the Copyright Act's "fair dealing" covers criticism, review and reporting, and a short meme quote in an educational video is a judgement call, not a guarantee.
- YouTube Content ID can match even 2–3 s of a film clip; most meme clips on YouTube are re-uploads, so the match is usually with the studio's reference file.
- Short real meme clips go only into the user's own non-monetised edits, and only if the user chooses to take that risk. Keep them 1–3 s, never more than a few per video, never in client ads, and say "possible Content ID claim" in the delivery notes.
- Safer alternatives, in order: (1) recreate the line in the user's own cloned voice (`my-voice`) over the still image; (2) the still frame + a generic SFX (vine boom, record scratch); (3) a code-drawn reaction (anime-episodes / video-asset-packs style).

## 4. Trending songs

- Use the trending list to **choose** and to **tell the user** what to add in-app. Do not download commercial songs to put in a master. Do not use spotdl/yt-dlp to rip charting songs for an upload.
- For timing an edit to a trending song, it is fine to use a 30 s preview (Apple/Deezer preview URLs) privately to find the beat, then deliver the `_clean` version with the song name and start time in the notes.

## 5. What to record for every downloaded asset

`scripts/fetch_asset.py` writes this automatically next to the file (`<file>.source.json`) and appends a row to the store's `DOWNLOADS.md`:
- source page URL and direct file URL
- licence label and licence URL, and whether credit is required
- the exact credit line to paste
- author/uploader
- date downloaded, size, sha256
- which job it was downloaded for

If the source page shows a badge like "Content ID registered", "Editorial", "Premium" or "Attribution required", put it in `--note`.

## 6. Credit line templates

- CC BY: `"<Title>" by <Author> (<source URL>) is licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)`
- Kevin MacLeod: `"<Title>" Kevin MacLeod (incompetech.com) / Licensed under Creative Commons: By Attribution 4.0 / https://creativecommons.org/licenses/by/4.0/`
- NCS: `Song: <Artist> - <Title> [NCS Release] / Music provided by NoCopyrightSounds / Free Download/Stream: <ncs.io link> / Watch: <YouTube link>`
- Freesound CC BY: `<sound name> by <username> -- <freesound URL> -- License: Attribution 4.0`
- Uppbeat free: use the credit code the site generates for that track (it whitelists the video).
- Pixabay / Mixkit / Pexels / Unsplash: no credit required; a thank-you line is optional.
