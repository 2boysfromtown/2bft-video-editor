v0.3.1: the main editor now uses the sound and clean-up tools at every step of an edit.

Updated
- `2bft-video-editor`: the order of work now cleans a noisy recording before transcribing (`denoise.py`, or `stems.py --two` when music bleeds under the voice), checks this week's trending songs while planning Shorts and Reels, lists every outside asset per shot, shows one shortlist with licence, credit and size before any download, and copies every credit line into the delivery notes. A new row covers trending songs (Shorts India, Tamil, Hindi, Spotify, Apple, JioSaavn), and every `local-av-tools` command now shows the flags to use.
- `ffmpeg-edit-toolkit`: points to `asset-library` for the real sounds, music and meme clips that replace its placeholder whooshes and hits.

Earlier (v0.3.0): `asset-library` (about 400 checked sources for SFX, meme sounds, music, trending songs, memes, stock footage, LUTs, fonts and icons, each with licence and client-ad safety) and `local-av-tools` (offline noise removal, stems, karaoke, shot detection, face/pose/hand tracking, speaker labels, slow motion and background removal). (v0.2.0): face-tracked `reframe.py` (100 % face hit rate on our 20 s webcam test; 5 s of 1080p to a 1080x1920 Short in 5.7 s on CPU), `quest-lab-editor` and the claude-cuts editing skills.

Install: `npx skills add 2boysfromtown/2bft-video-editor --global --agent claude-code`
