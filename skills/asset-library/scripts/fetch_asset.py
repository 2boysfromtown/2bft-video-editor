"""Download one asset into the shared asset store and record where it came from.

Every file gets a <file>.source.json sidecar (source page, file URL, licence,
credit line, author, job, size, sha256, date) and a row in <root>/DOWNLOADS.md,
so credits and licences are never lost.

Only run this after the user has said yes to the download (name, source,
licence, size).

Direct file URL (mp3/wav/mp4/png/zip/cube/ttf...):
  python -I fetch_asset.py URL --kind sfx --name whoosh_soft \
      --page https://pixabay.com/sound-effects/... --licence "Pixabay Content License" \
      --licence-url https://pixabay.com/service/license-summary/ --credit none --job ep04

Video page through yt-dlp (YouTube, Instagram, Reddit, X, Vimeo...):
  python -I fetch_asset.py "https://www.youtube.com/watch?v=..." --ytdlp --section 00:01:23-00:01:27 \
      --kind meme --name ta_vada_pochey --licence "copyrighted film clip (user-approved meme use)" --job ep04

Add --audio to keep only audio (wav). Add --dry-run to see what would happen.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

DEFAULT_ROOT = os.environ.get("ASSET_ROOT", "assets")  # set ASSET_ROOT to keep one store for every project
KINDS = ["sfx", "music", "meme", "gif", "footage", "images", "overlays", "luts",
         "fonts", "icons", "lottie", "3d", "other"]
# find_assets.py's kind names, so a result can be passed straight through.
KIND_ALIASES = {"sound": "sfx", "memesound": "sfx", "song": "music", "video": "footage", "image": "images",
                "font": "fonts", "icon": "icons", "hdri": "3d", "texture": "3d", "model": "3d", "lut": "luts"}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")


def slugify(text):
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip()).strip("._")
    return text[:80] or "asset"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ext_from(url, content_type):
    path_ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
    if 1 < len(path_ext) <= 6:
        return path_ext
    ct = (content_type or "").split(";")[0].strip().lower()
    table = {"audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
             "audio/ogg": ".ogg", "audio/flac": ".flac", "video/mp4": ".mp4",
             "video/webm": ".webm", "image/png": ".png", "image/jpeg": ".jpg",
             "image/gif": ".gif", "image/webp": ".webp", "image/svg+xml": ".svg",
             "application/json": ".json", "application/zip": ".zip",
             "font/ttf": ".ttf", "font/otf": ".otf", "font/woff2": ".woff2"}
    return table.get(ct, ".bin")


def download_direct(url, folder, name, max_mb, referer):
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        length = resp.headers.get("Content-Length")
        if length and int(length) > max_mb * 1024 * 1024:
            sys.exit(f"Refusing: {int(length) / 1e6:.2f} MB is over --max-mb {max_mb}")
        ext = ext_from(resp.geturl(), resp.headers.get("Content-Type"))
        out = os.path.join(folder, name + ext)
        n = 0
        with open(out + ".part", "wb") as f:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                n += len(chunk)
                if n > max_mb * 1024 * 1024:
                    f.close()
                    os.remove(out + ".part")
                    sys.exit(f"Refusing: download passed --max-mb {max_mb}")
                f.write(chunk)
    os.replace(out + ".part", out)
    return out


def _media_files(folder, stem):
    return sorted(f for f in os.listdir(folder)
                  if f.startswith(stem + ".") and not f.endswith((".json", ".part", ".ytdl")))


def _ytdlp(url, folder, stem, section, audio, max_mb):
    cmd = ["yt-dlp", "--no-playlist", "--no-warnings", "--restrict-filenames",
           "--write-info-json", "--max-filesize", f"{max_mb}M",
           "-o", os.path.join(folder, stem + ".%(ext)s")]
    if section:
        cmd += ["--download-sections", "*" + section, "--force-keyframes-at-cuts"]
    if audio:
        cmd += ["-x", "--audio-format", "wav"]
    else:
        cmd += ["-S", "res:1080,ext:mp4:m4a", "--remux-video", "mp4"]
    cmd.append(url)
    print("running:", " ".join(cmd))
    return subprocess.run(cmd).returncode == 0 and bool(_media_files(folder, stem))


def _seconds(t):
    secs = 0.0
    for part in t.split(":"):
        secs = secs * 60 + float(part)
    return secs


def download_ytdlp(url, folder, name, section, audio, max_mb):
    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp is not on PATH")
    if _ytdlp(url, folder, name, section, audio, max_mb):
        return os.path.join(folder, _media_files(folder, name)[0])
    if not section:
        sys.exit("yt-dlp failed (see its output above)")
    # Some hosts can't serve part of a file. Fetch the whole clip (still under
    # --max-mb), then cut the section locally.
    print("section download failed; downloading the whole clip and trimming locally")
    for f in os.listdir(folder):
        if f.startswith(name + ".") and f.endswith((".part", ".ytdl")):
            os.remove(os.path.join(folder, f))
    full = name + "_full"
    if not _ytdlp(url, folder, full, None, audio, max_mb):
        sys.exit("yt-dlp failed (see its output above)")
    src = os.path.join(folder, _media_files(folder, full)[0])
    start, end = (_seconds(x) for x in section.split("-", 1))
    out = os.path.join(folder, name + (".wav" if audio else ".mp4"))
    codec = (["-c:a", "pcm_s16le", "-ar", "48000"] if audio else
             ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", src,
                    "-t", f"{end - start:.3f}", *codec, out], check=True)
    return out


def probe_size(url, ytdlp, section, referer):
    """Size to show the user before they say yes (HEAD for files, yt-dlp metadata for video pages)."""
    try:
        if ytdlp:
            res = subprocess.run(["yt-dlp", "--no-playlist", "--no-warnings", "--simulate", "--print",
                                  "%(duration)s|%(filesize,filesize_approx)s", url],
                                 capture_output=True, text=True, timeout=90)
            dur, size = (res.stdout.strip().splitlines() or ["|"])[-1].split("|")
            size_mb = f"{int(float(size)) / 1e6:.1f} MB for the whole video" if size not in ("", "NA") else "unknown"
            return f"video {dur} s, {size_mb}" + (f"; only {section} will be kept" if section else "")
        headers = {"User-Agent": UA}
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            length = r.headers.get("Content-Length")
            return f"{int(length) / 1e6:.2f} MB" if length else "unknown (no Content-Length)"
    except Exception as e:  # size is a courtesy; never block the dry run
        return f"unknown ({str(e)[:80]})"


def append_log(root, row):
    log = os.path.join(root, "DOWNLOADS.md")
    new = not os.path.exists(log)
    with open(log, "a", encoding="utf-8") as f:
        if new:
            f.write("# Asset downloads (one row per file; sidecar .source.json has full details)\n\n")
            f.write("| date | kind | file | licence | credit | source | job | size |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
        f.write("| {date} | {kind} | `{rel}` | {licence} | {credit} | {page} | {job} | {size} |\n".format(**row))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--kind", required=True, choices=KINDS + sorted(KIND_ALIASES),
                    help="what it is; find_assets.py kind names work too (video, image, font, sound, ...)")
    ap.add_argument("--name", help="slug for the file (default: from URL)")
    ap.add_argument("--page", default="", help="human page the asset came from")
    ap.add_argument("--licence", required=True, help='e.g. "CC0", "CC BY 4.0", "Pixabay Content License"')
    ap.add_argument("--licence-url", default="")
    ap.add_argument("--credit", default="none", help='exact credit line to paste, or "none"')
    ap.add_argument("--author", default="")
    ap.add_argument("--job", default="", help="project this was downloaded for")
    ap.add_argument("--note", default="", help="badges/caveats: Content ID registered, editorial, NC...")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--dest", help="subfolder under root (default downloads/<kind>-<date>)")
    ap.add_argument("--ytdlp", action="store_true", help="treat URL as a video page and use yt-dlp")
    ap.add_argument("--section", help="yt-dlp only: start-end, e.g. 00:01:23-00:01:27")
    ap.add_argument("--audio", action="store_true", help="yt-dlp only: keep audio as wav")
    ap.add_argument("--referer", help="Referer header for hosts that need one")
    ap.add_argument("--max-mb", type=float, default=300)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    a.kind = KIND_ALIASES.get(a.kind, a.kind)
    today = dt.date.today().isoformat()
    name = slugify(a.name or os.path.splitext(os.path.basename(urllib.parse.urlparse(a.url).path))[0] or a.kind)
    # Match the store's existing folder names (downloads\memes-2026-10-28, music-..., sfx-...).
    folder_kind = {"meme": "memes", "gif": "gifs"}.get(a.kind, a.kind)
    folder = os.path.join(a.root, a.dest or os.path.join("downloads", f"{folder_kind}-{today}"))
    if a.dry_run:
        print(json.dumps({"would_download": a.url, "into": folder, "name": name,
                          "mode": "yt-dlp" if a.ytdlp else "direct", "licence": a.licence,
                          "size": probe_size(a.url, a.ytdlp, a.section, a.referer)}, indent=2))
        return
    os.makedirs(folder, exist_ok=True)
    out = (download_ytdlp(a.url, folder, name, a.section, a.audio, a.max_mb) if a.ytdlp
           else download_direct(a.url, folder, name, a.max_mb, a.referer))
    size = os.path.getsize(out)
    meta = {
        "file": out, "kind": a.kind, "downloaded": dt.datetime.now().isoformat(timespec="seconds"),
        "file_url": a.url, "source_page": a.page or a.url, "licence": a.licence,
        "licence_url": a.licence_url, "credit": a.credit, "author": a.author,
        "job": a.job, "note": a.note, "bytes": size, "sha256": sha256(out),
        "section": a.section or "",
    }
    with open(out + ".source.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    rel = os.path.relpath(out, a.root)
    append_log(a.root, {"date": today, "kind": a.kind, "rel": rel.replace("|", "/"),
                        "licence": a.licence + (f" ({a.note})" if a.note else ""),
                        "credit": "none" if a.credit in ("", "none") else "yes",
                        "page": a.page or a.url, "job": a.job or "-",
                        "size": f"{size / 1e6:.2f} MB" if size > 1e6 else f"{size / 1e3:.0f} KB"})
    print(json.dumps({"saved": out, "bytes": size, "sidecar": out + ".source.json"}, indent=2))


if __name__ == "__main__":
    main()
