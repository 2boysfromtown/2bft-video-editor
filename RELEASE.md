First release of the 2BFT Video Editor skill pack for Claude Code.

- `reframe.py`: face-tracked reframe to 9:16 / 4:5 / 1:1 with smooth, camera-operator motion. 100 % face hit rate on our 20 s webcam test; 5 s of 1080p to a 1080x1920 Short in 5.7 s on CPU.
- `quest-lab-editor`: our stream-to-video engine (face-following webcam crops, energy shake, captions, SFX, music, QC).
- `editor-os` plus the claude-cuts editing skills, in one install.

Install: `npx skills add 2boysfromtown/2bft-video-editor --global --agent claude-code`
