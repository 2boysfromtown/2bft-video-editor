# DaVinci Resolve with Claude Code

When an edit needs a real timeline (a client wants the project file, or a colourist takes over), hand it to DaVinci Resolve. Everything below was set up and tested on Resolve Studio 21.1.1 on Windows 11 in October 2026.

## Connect Claude to Resolve (official MCP)

Resolve 21.1 ships Blackmagic's own MCP server, `ResolveMCP.exe`, in the Resolve install folder. Its manifest says it needs Resolve Studio.

```bash
claude mcp add davinci-resolve -- "<Resolve folder>/ResolveMCP.exe"
```

It gives Claude 14 tools: `launch_resolve`, `get_resolve_status`, scripting API search and docs, `run_script` (sandboxed Python with `resolve` and `project` ready to use), `run_script_unsafe` (file system and ffmpeg), and DCTL and LUT management including `generate_lut`.

What we learned:
- Start Resolve yourself and wait until it has fully loaded. `launch_resolve` gives up after 60 seconds, and Resolve can take two minutes to open when the PC is short on memory.
- The MCP tools appear in new Claude sessions only.
- If Resolve hangs while creating a project, it is usually low system memory: close other heavy apps.
- Logs: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\logs\` (`ResolveDebug.txt`, `mcp.log`).

## A useful way to split the work

1. Do the measuring in this pack: transcript (`transcribe-local`), pause list (`quest-lab-editor/engine/tools/pauses.py`), face track (`reframe.py --track-json`), cleaned audio (`denoise.py`), stems (`stems.py`), cutouts (`cutout.py --as mov`).
2. Have Claude build the timeline in Resolve with `run_script`: import media, place clips from the cut list, add markers at hooks and SFX points, set the project to 1080x1920 for Shorts.
3. The human does the parts that need eyes and ears in Resolve: timing feel, colour, the final mix.

## Free add-ons worth installing

| Add-on | What it adds | Where |
|---|---|---|
| AutoSubs | Whisper subtitles straight onto the Resolve timeline, with styled captions | https://github.com/tmoroney/auto-subs (Workspace > Scripts > AutoSubs) |
| Reactor | The community package manager for Fusion tools inside Resolve | https://gitlab.com/WeSuckLess/Reactor |
| ReaPlugs | Free VST effects (EQ, compressor, gate) usable in Fairlight | https://www.reaper.fm/reaplugs/ |

Reactor atoms we found useful for social edits: CapCut-style captions, camera shake (ml_Twitch), glitch tools, glow, lens flares, heat distortion, echo, ReGrain, HUD elements, audio waveform, skin correction. Check each atom's licence before using it in client work.

If Reactor's catalogue fails to download (GitLab rate limits), clone its repository and point `Reactor.cfg` at the local folder with `Protocol = "FileSystem"`. Reactor may rewrite the cfg when its window closes, so check it again afterwards.
