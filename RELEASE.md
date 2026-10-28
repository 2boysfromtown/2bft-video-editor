v0.3.0: sound, music and clean-up tools join the 2BFT Video Editor pack.

New skills
- `asset-library`: about 400 checked sources for SFX, meme sounds, royalty-free and Indian music, trending songs, memes, stock footage, LUTs, fonts and icons, each with licence, credit rule and client-ad safety. Scripts to search (`find_assets.py`), check what is trending in India and globally (`trending.py`, 30 charts in about 13 s) and download with the licence recorded (`fetch_asset.py`).
- `local-av-tools`: offline noise removal (DeepFilterNet, 30 s in 2 s), stems (Demucs v4), karaoke (BS-RoFormer), shot detection (TransNetV2), face, pose and hand tracking (MediaPipe), speaker diarization (pyannote), smooth and slow motion (RIFE / FILM) and background removal (BiRefNet). Plus a guide to DaVinci Resolve's official MCP and free add-ons.

Updated
- `2bft-video-editor`, `edit-video`, `editor-os`, `video-sound-and-music`, `video-editing-craft` and `comedy-editing-timing` now point to the new tools.

Earlier (v0.2.0): face-tracked `reframe.py` (100 % face hit rate on our 20 s webcam test; 5 s of 1080p to a 1080x1920 Short in 5.7 s on CPU), `quest-lab-editor` and the claude-cuts editing skills.

Install: `npx skills add 2boysfromtown/2bft-video-editor --global --agent claude-code`
