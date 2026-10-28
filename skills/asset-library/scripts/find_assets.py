"""Search the asset sources that have open APIs and print results with licences.

No keys needed for most sources. Results are search hits only: nothing is
downloaded. Download the ones the user approves with fetch_asset.py.

  python -I find_assets.py sound "swoosh"               # Mixkit + Freesound CC0 (add --deep for Openverse, Commons, Archive)
      Mixkit wants a category slug: whoosh, swoosh, transition, click, interface, notification, cartoon,
      crowd, applause, laugh, impact, explosion, game, glitch, tech, magic, horror, ambience
  python -I find_assets.py memesound "vadivelu"         # Myinstants, Tamil Soundboard, Voicy (own channels only) + CC0 look-alikes
  python -I find_assets.py music "corporate"            # Mixkit (ads OK), NCS, Incompetech, ccMixter, Openverse music
  python -I find_assets.py image "chennai street" --commercial
  python -I find_assets.py video "highway" --ad-safe    # Mixkit, NASA, Commons, Archive (+ Pexels/Pixabay with keys)
  python -I find_assets.py meme "drake"                 # Imgflip top-100 meme templates
  python -I find_assets.py icon "rocket"                # Iconify (200k+ open icons, licence per set)
  python -I find_assets.py hdri "night city"            # Poly Haven (CC0)
  python -I find_assets.py texture "wood"               # ambientCG + Poly Haven (CC0)
  python -I find_assets.py model "chair"                # Poly Haven models (CC0)
  python -I find_assets.py font "" --subset tamil       # Google Fonts families with Tamil
  python -I find_assets.py song "kalyani" --country IN  # iTunes + Deezer: identify a song, 30 s preview for beat timing only

Use --source to pick one source (e.g. --source commons), -n for result count,
--json for machine-readable output, --resolve to also look up direct file URLs
where that needs a second request (NASA, Internet Archive).

Optional keys (environment variables): FREESOUND_TOKEN, PIXABAY_KEY, PEXELS_KEY.
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")
WIKI_UA = "asset-library-skill/1.0 (Claude Code; personal video editing)"


def get_json(url, headers=None, tries=3, timeout=25):
    last = None
    for i in range(tries):
        try:
            h = {"User-Agent": UA, "Accept": "application/json"}
            h.update(headers or {})
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
            raw = raw.lstrip()
            if raw.startswith(")]}'"):
                raw = raw[4:]
            return json.loads(raw)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url.split('?')[0]}: {last}")


def q(s):
    return urllib.parse.quote(s)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def row(source, title, licence, page, file="", author="", extra=""):
    return {"source": source, "title": title, "licence": licence, "author": author,
            "page": page, "file": file, "extra": extra, "licence_url": licence_url(source, licence)}


# Licence pages to pass to fetch_asset.py --licence-url (checked 28 Oct 2026; Pixabay and
# Pexels block scripts but open in a browser).
LICENCE_URLS = {
    "mixkit": "https://mixkit.co/license/",
    "incompetech": "https://creativecommons.org/licenses/by/4.0/",
    "ncs": "https://ncs.io/usage-policy",
    "polyhaven": "https://polyhaven.com/license",
    "ambientcg": "https://docs.ambientcg.com/license/",
    "gfonts": "https://openfontlicense.org/",
    "nasa": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
    "pixabay": "https://pixabay.com/service/license-summary/",
    "pexels": "https://www.pexels.com/license/",
}
CC_URLS = {"CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
           "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
           "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/"}


def licence_url(source, licence):
    if source in LICENCE_URLS:
        return LICENCE_URLS[source]
    lic = (licence or "").upper().replace("CC0 1.0", "CC0").strip()
    return CC_URLS.get(lic, "")


# ---------------------------------------------------------------- sources

def openverse(kind, query, n, commercial, extra_params=""):
    # Openverse is slow from here (~60 s a call, image search often 504s) and caps anonymous use
    # at 20/min and 200/day. Sources run in parallel, so the others answer meanwhile.
    url = f"https://api.openverse.org/v1/{kind}/?q={q(query)}&page_size={min(n, 20)}{extra_params}"
    if commercial:
        # license_type=commercial still lets "no derivatives" through; putting a sound under
        # video is a derivative, so list the licences that allow both instead.
        url += "&license=cc0,pdm,by"
    out = []
    for r in get_json(url, tries=1, timeout=90).get("results", []):
        lic = f"{r.get('license', '').upper()} {r.get('license_version') or ''}".strip()
        extra = ""
        if r.get("duration"):
            extra = f"{r['duration'] / 1000:.1f} s"
        elif r.get("width"):
            extra = f"{r['width']}x{r['height']}"
        extra += f" via {r.get('source') or r.get('provider')}"
        out.append(row("openverse", r.get("title") or "", lic, r.get("foreign_landing_url", ""),
                       r.get("url", ""), r.get("creator") or "", extra.strip()))
    return out


def freesound(query, n, commercial):
    token = os.environ.get("FREESOUND_TOKEN")
    if not token:
        return []
    flt = '&filter=license:"Creative Commons 0"' if commercial else ""
    url = (f"https://freesound.org/apiv2/search/text/?query={q(query)}&page_size={min(n, 30)}"
           f"&fields=id,name,license,username,previews,duration,url{flt}&token={token}")
    out = []
    for r in get_json(url).get("results", []):
        prev = (r.get("previews") or {}).get("preview-hq-mp3", "")
        out.append(row("freesound", r["name"], r["license"].rsplit("/", 2)[-2] if "/" in r["license"] else r["license"],
                       r["url"], prev, r["username"], f"{r.get('duration', 0):.1f} s (hq preview mp3)"))
    return out


def get_text(url, headers=None, timeout=30, tries=3):
    h = {"User-Agent": UA}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            # Freesound answers 429 when several searches run at once; wait and retry.
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


# An opening tag's attributes, allowing ">" inside quoted values (NCS puts HTML in data-artist).
TAG_ATTRS = r"""{}((?:[^>"']|"[^"]*"|'[^']*')*)>"""


def attr(block, name):
    m = re.search(name + r'="([^"]*)"', block)
    return html.unescape(m.group(1)) if m else ""


def freesound_web(query, n):
    """No token: the search page lists CC0 results with hq-able preview mp3s."""
    url = ("https://freesound.org/search/?q=" + urllib.parse.quote_plus(query)
           + "&f=" + q('license:"Creative Commons 0"'))
    page = get_text(url)
    out = []
    for block in re.findall(TAG_ATTRS.format('<div\\s+class="bw-player"'), page)[:n]:
        sid, user = attr(block, "data-sound-id"), attr(block, "data-username")
        mp3 = attr(block, "data-mp3").replace("-lq.mp3", "-hq.mp3")
        dur = attr(block, "data-duration")
        out.append(row("freesound", attr(block, "data-title"), "CC0", f"https://freesound.org/people/{user}/sounds/{sid}/",
                       mp3, user, f"{float(dur or 0):.1f} s (hq preview mp3; original WAV needs login)"))
    return out


def slugify(query):
    return re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")


def mixkit_audio_cards(page, n, file_pattern):
    """Audio-player cards on a Mixkit list page: (title, item id) in page order."""
    out = []
    for m in re.finditer(r'data-audio-player-item-id-value="(\d+)"', page):
        if len(out) >= n:
            break
        sid = m.group(1)
        t = re.search(r'item-grid-card__title[^>]*>\s*([^<]+)', page[m.end():m.end() + 4000])
        out.append((html.unescape(t.group(1).strip()) if t else f"Mixkit {sid}", file_pattern.format(id=sid)))
    return out


def mixkit(query, n):
    """Mixkit SFX: no credit, OK for online ads. Query is a category/tag slug (whoosh, swoosh, click, crowd...)."""
    url = f"https://mixkit.co/free-sound-effects/{slugify(query)}/"
    cards = mixkit_audio_cards(get_text(url), n, "https://assets.mixkit.co/active_storage/sfx/{id}/{id}.wav")
    return [row("mixkit", t, "Mixkit Sound Effects Free License (no credit, ads OK)", url, f, "Mixkit", "full WAV")
            for t, f in cards]


def mixkit_video(query, n):
    """Mixkit stock video (Mixkit Video Free License: no credit; some clips are 'Restricted', check the page)."""
    url = f"https://mixkit.co/free-stock-video/{slugify(query)}/"
    page = get_text(url)
    out, seen = [], set()
    for m in re.finditer(r'<img src="https://assets\.mixkit\.co/videos/(\d+)/\1-thumb[^"]*"[^>]*alt="([^"]*)"', page):
        vid, title = m.group(1), html.unescape(m.group(2)).rstrip(".")
        if vid in seen:
            continue
        seen.add(vid)
        out.append(row("mixkit", title, "Mixkit Video Free License (no credit; check the clip page for 'Restricted')", url,
                       f"https://assets.mixkit.co/videos/{vid}/{vid}-720.mp4", "Mixkit",
                       "720p; older clips also have -1080/-2160 (newer ones 403); mostly 16:9, crop for 9:16"))
        if len(out) >= n:
            break
    return out


def mixkit_music(query, n):
    """Mixkit Stock Music Free License: no credit, online ads allowed (not TV/radio broadcast).
    Most words redirect from /tag/<slug>/ to a mood, genre or /discover/ page; both layouts are handled."""
    slug = slugify(query)
    page = get_text(f"https://mixkit.co/free-stock-music/tag/{slug}/")
    out = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.S):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for node in (data.get("@graph", [data]) if isinstance(data, dict) else data):
            for it in (node.get("itemListElement") or []) if isinstance(node, dict) else []:
                if it.get("@type") == "MusicRecording" and len(out) < n:
                    dur = re.findall(r"(\d+)M(\d+)S", it.get("duration", ""))
                    out.append(row("mixkit", it.get("name", ""), "Mixkit Stock Music Free License (no credit, online ads OK)",
                                   f"https://mixkit.co/free-stock-music/tag/{slug}/", it.get("url", ""),
                                   it.get("byArtist", ""), f"{it.get('genre', '')}, {dur[0][0]}:{dur[0][1]}" if dur else it.get("genre", "")))
    if not out:  # mood/genre/discover pages have player cards instead of a JSON-LD list
        out = [row("mixkit", t, "Mixkit Stock Music Free License (no credit, online ads OK)",
                   f"https://mixkit.co/free-stock-music/tag/{slug}/", f, "Mixkit", "")
               for t, f in mixkit_audio_cards(page, n, "https://assets.mixkit.co/music/{id}/{id}.mp3")]
    return out


def ncs(query, n):
    page = get_text("https://ncs.io/music-search?q=" + urllib.parse.quote_plus(query) + "&genre=&mood=")
    out = []
    for block in re.findall(TAG_ATTRS.format('<a class="player-play"'), page)[:n]:
        out.append(row("ncs", attr(block, "data-track"), "NCS: free on own channels with the NCS credit block; brands/client ads need NCS permission",
                       "https://ncs.io/music-search?q=" + urllib.parse.quote_plus(query), attr(block, "data-url"),
                       attr(block, "data-artistraw"), attr(block, "data-genre")))
    return out


_PIECES = []


def incompetech(query, n):
    if not _PIECES:
        _PIECES.extend(get_json("https://incompetech.com/music/royalty-free/pieces.json", timeout=40))
    words = query.lower().split()
    hits = [p for p in _PIECES if all(w in " ".join(str(p.get(k) or "") for k in
                                                        ("title", "feel", "instruments", "description")).lower() for w in words)]
    hits.sort(key=lambda p: p.get("uploaded") or "", reverse=True)
    return [row("incompetech", p["title"], "CC BY 4.0 (credit Kevin MacLeod; see licence cheat sheet)",
                "https://incompetech.com/music/royalty-free/music.html",
                "https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + q(p["filename"]), "Kevin MacLeod",
                f"{p.get('length', '')}, {p.get('bpm', '?')} bpm, {p.get('feel', '')}")
            for p in hits[:n]]


def ccmixter(query, n):
    tag = re.sub(r"[^a-z0-9_]+", "_", query.lower()).strip("_") or "instrumental"
    data = get_json(f"https://ccmixter.org/api/query?f=json&tags={q(tag)}&lic=by&limit={n}&sort=rank")
    out = []
    for x in data if isinstance(data, list) else []:
        files = [f.get("download_url", "") for f in x.get("files", []) if f.get("download_url", "").endswith(".mp3")]
        bpm = (x.get("upload_extra") or {}).get("bpm", "")
        out.append(row("ccmixter", x.get("upload_name", ""), x.get("license_name", "CC BY"), x.get("file_page_url", ""),
                       files[0] if files else "", x.get("user_name", ""),
                       f"bpm {bpm}; download needs --referer {x.get('file_page_url', '')}"))
    return out


MEME_NOTE = "film/TV/creator clip: own channels only, never client ads"


def myinstants(query, n):
    data = get_json("https://www.myinstants.com/api/v1/instants/?format=json&name=" + q(query))
    return [row("myinstants", r.get("name", ""), MEME_NOTE, f"https://www.myinstants.com/en/instant/{r.get('slug', '')}/",
                r.get("sound", ""), "", "") for r in data.get("results", [])[:n]]


def tamilsoundboard(query, n):
    data = get_json(f"https://tamilsoundboard.com/api/v1/clips?q={q(query)}&per_page={min(n, 50)}")
    out = []
    for c in data.get("data", [])[:n]:
        actor = (c.get("actor") or {}).get("name", "")
        out.append(row("tamilsoundboard", c.get("title", ""), MEME_NOTE, "https://tamilsoundboard.com/",
                       f"https://tamilsoundboard.com/api/v1/clips/{c['id']}/stream", actor,
                       f"{(c.get('duration_ms') or 0) / 1000:.1f} s; {(c.get('transcription_tanglish') or '')[:50]}"))
    return out


def voicy(query, n):
    data = get_json("https://server.voicy.network/api/clips?search=" + q(query))
    return [row("voicy", c.get("name", ""), MEME_NOTE, "https://www.voicy.network/",
                "https://images.voicy.network" + c.get("source", ""), "", "")
            for c in (data.get("data") or [])[:n]]


def commons(query, n, media):
    ftype = {"image": "bitmap", "video": "video", "audio": "audio"}[media]
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
           f"&gsrsearch={q(query + ' filetype:' + ftype)}&gsrnamespace=6&gsrlimit={min(n, 30)}"
           "&prop=imageinfo&iiprop=url|size|extmetadata&iiextmetadatafilter=LicenseShortName|Artist")
    data = get_json(url, headers={"User-Agent": WIKI_UA})
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "?")
        file_url = ii.get("url", "").split("?")[0]
        size = f"{ii.get('width', '?')}x{ii.get('height', '?')}, {ii.get('size', 0) / 1e6:.1f} MB"
        out.append(row("commons", p["title"].replace("File:", ""), lic, ii.get("descriptionurl", ""),
                       file_url, strip_tags(md.get("Artist", {}).get("value", ""))[:40], size))
    return out


def nasa(query, n, media, resolve):
    url = f"https://images-api.nasa.gov/search?q={q(query)}&media_type={media}&page_size={max(n, 1)}"
    out = []
    for it in get_json(url).get("collection", {}).get("items", [])[:n]:
        d = it["data"][0]
        nid = d["nasa_id"]
        file_url = it.get("href", "")
        if resolve:
            try:
                files = get_json(it["href"])
                pref = ["~orig.mp4", "~large.mp4", "~medium.mp4", "~orig.jpg", "~large.jpg", "~orig.mp3", "~orig.wav"]
                file_url = next((f for p in pref for f in files if f.endswith(p)), files[0] if files else "")
            except RuntimeError:
                pass
        out.append(row("nasa", d.get("title", nid), "public domain (NASA; no endorsement, no logos)",
                       f"https://images.nasa.gov/details/{q(nid)}", file_url, d.get("center", ""),
                       d.get("date_created", "")[:10]))
    return out


def archive(query, n, media, resolve, commercial=False):
    mt = {"video": "movies", "audio": "audio", "image": "image"}[media]
    # Archive's query parser chokes on slashes, so ask for "has a licence" and filter here.
    lic_q = " AND licenseurl:[* TO *]" if commercial else ""
    url = ("https://archive.org/advancedsearch.php?q="
           + q(f"(title:({query}) OR subject:({query})) AND mediatype:{mt}{lic_q}")
           + "&fl[]=identifier&fl[]=title&fl[]=licenseurl&fl[]=creator&sort[]=" + q("downloads desc")
           + "&rows=" + str(n * 5 if commercial else n) + "&output=json")
    docs = get_json(url).get("response", {}).get("docs", [])
    if commercial:
        ok = re.compile(r"publicdomain|/zero/|/licenses/by/|/licenses/by-sa/")
        docs = [d for d in docs if ok.search(d.get("licenseurl", ""))][:n]
    out = []
    for d in docs:
        ident = d["identifier"]
        if d.get("licenseurl"):
            lic = d["licenseurl"] + " (set by the uploader: check it is really theirs)"
        else:
            lic = "no licence stated (assume copyrighted)"
        file_url = ""
        if resolve:
            try:
                meta = get_json(f"https://archive.org/metadata/{ident}")
                exts = {"video": (".mp4", ".mpeg4", ".ogv"), "audio": (".mp3", ".wav", ".flac", ".ogg"),
                        "image": (".jpg", ".png")}[media]
                f = next((f for f in meta.get("files", []) if f.get("name", "").lower().endswith(exts)), None)
                if f:
                    file_url = f"https://archive.org/download/{ident}/{q(f['name'])}"
            except RuntimeError:
                pass
        creator = d.get("creator", "")
        out.append(row("archive", d.get("title", ident) if isinstance(d.get("title"), str) else ident, lic,
                       f"https://archive.org/details/{ident}", file_url,
                       creator if isinstance(creator, str) else ", ".join(creator)))
    return out


def pixabay(query, n, media):
    key = os.environ.get("PIXABAY_KEY")
    if not key:
        return []
    base = "https://pixabay.com/api/videos/" if media == "video" else "https://pixabay.com/api/"
    data = get_json(f"{base}?key={key}&q={q(query)}&per_page={max(3, min(n, 50))}&safesearch=true")
    out = []
    for h in data.get("hits", []):
        if media == "video":
            v = h["videos"].get("large") or h["videos"].get("medium") or {}
            f, extra = v.get("url", ""), f"{v.get('width')}x{v.get('height')}, {h.get('duration')} s"
        else:
            f, extra = h.get("largeImageURL", ""), f"{h.get('imageWidth')}x{h.get('imageHeight')}"
        out.append(row("pixabay", h.get("tags", ""), "Pixabay Content License (no credit)",
                       h.get("pageURL", ""), f, h.get("user", ""), extra))
    return out


def pexels(query, n, media):
    key = os.environ.get("PEXELS_KEY")
    if not key:
        return []
    if media == "video":
        data = get_json(f"https://api.pexels.com/videos/search?query={q(query)}&per_page={min(n, 40)}",
                        headers={"Authorization": key})
        out = []
        for v in data.get("videos", []):
            files = sorted(v.get("video_files", []), key=lambda f: (f.get("height") or 0), reverse=True)
            best = next((f for f in files if (f.get("height") or 0) <= 2160), files[0] if files else {})
            out.append(row("pexels", v.get("url", "").rstrip("/").rsplit("/", 1)[-1], "Pexels License (no credit)",
                           v.get("url", ""), best.get("link", ""), (v.get("user") or {}).get("name", ""),
                           f"{best.get('width')}x{best.get('height')}, {v.get('duration')} s"))
        return out
    data = get_json(f"https://api.pexels.com/v1/search?query={q(query)}&per_page={min(n, 80)}",
                    headers={"Authorization": key})
    return [row("pexels", p.get("alt", ""), "Pexels License (no credit)", p.get("url", ""),
                p["src"]["original"], p.get("photographer", ""), f"{p['width']}x{p['height']}")
            for p in data.get("photos", [])]


def imgflip(query, n):
    memes = get_json("https://api.imgflip.com/get_memes")["data"]["memes"]
    words = query.lower().split()
    hits = [m for m in memes if all(w in m["name"].lower() for w in words)] if words else memes
    return [row("imgflip", m["name"], "meme template (copyrighted image; meme use only, not client ads)",
                f"https://imgflip.com/memetemplate/{m['id']}", m["url"], "",
                f"{m['width']}x{m['height']}, {m['box_count']} text boxes")
            for m in hits[:n]]


_ICON_SETS = {}


def iconify(query, n):
    data = get_json(f"https://api.iconify.design/search?query={q(query)}&limit={max(32, n)}")
    icons = data.get("icons", [])[:n]
    prefixes = sorted({i.split(":")[0] for i in icons} - set(_ICON_SETS))
    if prefixes:
        _ICON_SETS.update(get_json("https://api.iconify.design/collections?prefixes=" + ",".join(prefixes)))
    out = []
    for i in icons:
        pre, name = i.split(":", 1)
        info = _ICON_SETS.get(pre, {})
        lic = (info.get("license") or {}).get("title", "?")
        out.append(row("iconify", i, lic, f"https://icon-sets.iconify.design/{pre}/{name}/",
                       f"https://api.iconify.design/{pre}/{name}.svg", (info.get("author") or {}).get("name", ""),
                       info.get("name", "")))
    return out


def polyhaven(query, n, kind):
    t = {"hdri": "hdris", "texture": "textures", "model": "models"}[kind]
    assets = get_json(f"https://api.polyhaven.com/assets?t={t}")
    words = query.lower().split()

    def score(a):
        hay = " ".join([a.get("name", "")] + a.get("tags", []) + a.get("categories", [])).lower()
        return sum(w in hay for w in words)

    ranked = sorted(assets.items(), key=lambda kv: (-score(kv[1]), -kv[1].get("download_count", 0)))
    if words:
        ranked = [kv for kv in ranked if score(kv[1]) > 0]
    out = []
    for aid, a in ranked[:n]:
        out.append(row("polyhaven", a.get("name", aid), "CC0", f"https://polyhaven.com/a/{aid}",
                       f"https://api.polyhaven.com/files/{aid}  (pick resolution/format)", ", ".join(a.get("authors", {})),
                       ", ".join(a.get("categories", [])[:4])))
    return out


def ambientcg(query, n):
    data = get_json(f"https://ambientcg.com/api/v2/full_json?q={q(query)}&type=Material&limit={n}&include=downloadData")
    out = []
    for a in data.get("foundAssets", []):
        dls = a.get("downloadFolders", {}).get("default", {}).get("downloadFiletypeCategories", {}).get("zip", {}).get("downloads", [])
        pick = next((d for d in dls if d.get("attribute") == "2K-JPG"), dls[0] if dls else {})
        out.append(row("ambientcg", a.get("displayName", a["assetId"]), "CC0", a.get("shortLink", ""),
                       pick.get("fullDownloadPath", ""), "ambientCG",
                       f"{pick.get('attribute', '')} {pick.get('size', 0) / 1e6:.0f} MB"))
    return out


def gfonts(query, n, subset):
    data = get_json("https://fonts.google.com/metadata/fonts")
    fams = data["familyMetadataList"]
    if subset:
        fams = [f for f in fams if subset in f.get("subsets", [])]
    if query:
        fams = [f for f in fams if query.lower() in f["family"].lower()]
    fams.sort(key=lambda f: f.get("popularity", 9999))
    out = []
    for f in fams[:n]:
        fam = f["family"]
        out.append(row("gfonts", fam, "OFL/Apache (check LICENSE in the family folder)",
                       f"https://fonts.google.com/specimen/{fam.replace(' ', '+')}",
                       f"https://github.com/google/fonts/tree/main/ofl/{re.sub(r'[^a-z0-9]', '', fam.lower())}",
                       f.get("designers", [""])[0] if f.get("designers") else "",
                       f"{f.get('category', '')}; {', '.join(s for s in f.get('subsets', []) if s != 'menu')}"))
    return out


def itunes(query, n, country):
    data = get_json(f"https://itunes.apple.com/search?term={q(query)}&entity=song&country={country}&limit={n}")
    return [row("itunes", f"{r.get('trackName')} - {r.get('artistName')}",
                "commercial song: preview for beat timing only; add in-app",
                r.get("trackViewUrl", ""), r.get("previewUrl", ""), r.get("artistName", ""),
                f"{(r.get('trackTimeMillis') or 0) / 1000:.0f} s, {r.get('primaryGenreName', '')}")
            for r in data.get("results", [])]


def deezer(query, n):
    data = get_json(f"https://api.deezer.com/search?q={q(query)}&limit={n}")
    return [row("deezer", f"{r.get('title')} - {r.get('artist', {}).get('name')}",
                "commercial song: preview for beat timing only; add in-app",
                r.get("link", ""), r.get("preview", ""), r.get("artist", {}).get("name", ""),
                f"{r.get('duration')} s, rank {r.get('rank')}")
            for r in data.get("data", [])]


# ---------------------------------------------------------------- routing

# --commercial: commercial use and editing allowed (credit may be needed; own monetised channels).
# --ad-safe:    also no credit and no share-alike, as a paid client ad needs. Uploader-set licences
#               (Internet Archive) are never ad-safe because they are often wrong.
NOT_COMMERCIAL = re.compile(r"\bNC\b|BY-NC|NON-?COMMERCIAL|\bND\b|BY-ND|NO ?DERIV|own channels|beat timing|"
                            r"copyrighted|not client|meme use|NCS:", re.I)
AD_SAFE = re.compile(r"\bCC0\b|PUBLIC ?DOMAIN|\bPDM\b|Mixkit|Pixabay|Pexels|\bOFL\b|OPEN ?FONT|APACHE|\bMIT\b|\bISC\b", re.I)


def licence_ok(licence, ad_safe):
    if NOT_COMMERCIAL.search(licence or ""):
        return False
    if ad_safe:
        return bool(AD_SAFE.search(licence)) and "uploader" not in licence and not re.search(r"\bSA\b|BY-SA|\bBY\b", licence, re.I)
    return True


def run(kind, query, a):
    n, c = a.n, a.commercial or a.ad_safe
    fs = (lambda: freesound(query, n, c)) if os.environ.get("FREESOUND_TOKEN") else (lambda: freesound_web(query, n))
    plan = {
        "sound": [("mixkit", lambda: mixkit(query, n)), ("freesound", fs),
                  ("openverse", lambda: openverse("audio", query, n, c)), ("commons", lambda: commons(query, n, "audio")),
                  ("archive", lambda: archive(query, n, "audio", a.resolve, c))],
        "music": [("mixkit", lambda: mixkit_music(query, n)), ("ncs", lambda: ncs(query, n)),
                  ("incompetech", lambda: incompetech(query, n)), ("ccmixter", lambda: ccmixter(query, n)),
                  ("openverse", lambda: openverse("audio", query, n, c, "&category=music"))],
        "memesound": [("myinstants", lambda: myinstants(query, n)), ("tamilsoundboard", lambda: tamilsoundboard(query, n)),
                      ("voicy", lambda: voicy(query, n)), ("freesound", lambda: freesound_web(query, n))],
        "image": [("openverse", lambda: openverse("images", query, n, c)), ("commons", lambda: commons(query, n, "image")),
                  ("nasa", lambda: nasa(query, n, "image", a.resolve)), ("pixabay", lambda: pixabay(query, n, "image")),
                  ("pexels", lambda: pexels(query, n, "image"))],
        "video": [("mixkit", lambda: mixkit_video(query, n)),
                  ("nasa", lambda: nasa(query, n, "video", a.resolve)), ("commons", lambda: commons(query, n, "video")),
                  ("archive", lambda: archive(query, n, "video", a.resolve, c)), ("pixabay", lambda: pixabay(query, n, "video")),
                  ("pexels", lambda: pexels(query, n, "video"))],
        "meme": [("imgflip", lambda: imgflip(query, n))],
        "icon": [("iconify", lambda: iconify(query, n))],
        "hdri": [("polyhaven", lambda: polyhaven(query, n, "hdri"))],
        "texture": [("ambientcg", lambda: ambientcg(query, n)), ("polyhaven", lambda: polyhaven(query, n, "texture"))],
        "model": [("polyhaven", lambda: polyhaven(query, n, "model"))],
        "font": [("gfonts", lambda: gfonts(query, n, a.subset))],
        "song": [("itunes", lambda: itunes(query, n, a.country)), ("deezer", lambda: deezer(query, n))],
    }[kind]
    # Slow or noisy sources only join with --deep (or when asked for by --source): Openverse takes
    # ~60 s and often errors from here; Commons/Archive sound results are mostly off-topic.
    deep_only = {"sound": {"openverse", "commons", "archive"}, "music": {"openverse"}, "image": {"openverse"}}.get(kind, set())
    skipped = [name for name, _ in plan if name in deep_only and not a.deep and a.source != name]
    plan = [(name, fn) for name, fn in plan
            if (not a.source or name == a.source) and name not in skipped]

    def call(item):
        name, fn = item
        try:
            return name, fn(), None
        except Exception as e:  # one bad source must not hide the others
            return name, [], f"{name}: failed ({str(e)[:160]})"

    results, notes = [], []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for name, got, err in ex.map(call, plan):  # map keeps the plan's order
            if err:
                notes.append(err)
            elif not got and name in ("pixabay", "pexels"):
                notes.append(f"{name}: skipped (set {name.upper()}_KEY to include)")
            elif not got:
                notes.append(f"{name}: no results")
            results += got
    if skipped and not a.source:
        notes.append(f"not searched (slow or noisy; add --deep): {', '.join(skipped)}")
    if c:
        kept = [r for r in results if licence_ok(r["licence"], a.ad_safe)]
        if len(kept) < len(results):
            notes.append(f"dropped {len(results) - len(kept)} results whose licence fails "
                         f"{'--ad-safe (needs no credit, no share-alike, commercial use)' if a.ad_safe else '--commercial'}")
        results = kept
    return results, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["sound", "memesound", "music", "image", "video", "meme", "icon", "hdri", "texture",
                                     "model", "font", "song"])
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("-n", type=int, default=8, help="results per source")
    ap.add_argument("--source", help="only this source (mixkit, freesound, openverse, commons, archive, ncs, incompetech, ccmixter, myinstants, "
                                     "tamilsoundboard, voicy, nasa, pixabay, pexels, imgflip, iconify, polyhaven, "
                                     "ambientcg, gfonts, itunes, deezer)")
    ap.add_argument("--commercial", action="store_true",
                    help="only licences that allow commercial use and editing (credit may still be needed)")
    ap.add_argument("--ad-safe", action="store_true",
                    help="for paid client ads: commercial, no credit, no share-alike, no uploader-set licences")
    ap.add_argument("--resolve", action="store_true", help="look up direct file URLs that need a second request (NASA, archive)")
    ap.add_argument("--subset", help="fonts: script subset, e.g. tamil, devanagari")
    ap.add_argument("--country", default="IN", help="songs: iTunes store country")
    ap.add_argument("--deep", action="store_true", help="also ask the slow/noisy sources (Openverse ~60 s; Commons and Archive for sound)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results, notes = run(a.kind, a.query, a)
    if a.json:
        print(json.dumps({"results": results, "notes": notes}, ensure_ascii=False, indent=2))
        return
    for r in results:
        print(f"[{r['source']}] {r['title'][:70]}")
        print(f"    licence: {r['licence']}   by: {r['author'][:40]}   {r['extra']}")
        print(f"    page: {r['page']}")
        if r["file"]:
            print(f"    file: {r['file']}")
        if r["licence_url"]:
            print(f"    licence url: {r['licence_url']}")
    for nline in notes:
        print("note:", nline)
    print(f"{len(results)} results")


if __name__ == "__main__":
    main()
