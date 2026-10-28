#!/usr/bin/env python3
"""trending.py - pull "what's trending right now" from every no-key, no-JS music source.

Stdlib only (urllib, json, re, html, concurrent.futures). India first, then global.
Run:   python -I trending.py                       # top 10 from every source + "hot in India" summary
       python -I trending.py --lang ta             # Tamil charts + Shorts India (also: hi, en, shorts, india)
       python -I trending.py --top 5 --only yt_shorts_in_daily,sp_hot_tamil
       python -I trending.py --md plan/trending.md # dated markdown list to paste into the edit plan
       python -I trending.py --json out.json       # also save rows as JSON
       python -I trending.py --list                # list source keys and presets

Every source is wrapped in its own try/except with a timeout, so one broken site
never stops the rest; failures are printed as "FAILED: <reason>".
Tested 28 Oct 2026. Endpoints are unofficial where noted - if one breaks, read
the matching row in ../references/trending-music.md for the browser/WebFetch fallback.
Charts say what is trending; they never grant a licence (see the licence cheat sheet).
"""
import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
TIMEOUT = 20
IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------- helpers
def fetch(url, data=None, headers=None, timeout=TIMEOUT):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def fetch_json(url, **kw):
    return json.loads(fetch(url, **kw))


def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def html_rows(page):
    """Yield the <td> cell texts of every table row that has <td> cells."""
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if cells:
            yield cells


def split_artist_title(s):
    a, sep, t = s.partition(" - ")
    return (t, a) if sep else (s, "")


# ---------------------------------------------------------------- Apple / iTunes
def apple_rss(cc):
    def run(n):
        d = fetch_json(f"https://rss.marketingtools.apple.com/api/v2/{cc}/music/most-played/{max(n, 10)}/songs.json")
        f = d["feed"]
        return f.get("updated", ""), [(r["name"], r["artistName"]) for r in f["results"][:n]]
    return run


def itunes_genre(cc, genre):
    def run(n):
        g = f"/genre={genre}" if genre else ""
        d = fetch_json(f"https://itunes.apple.com/{cc}/rss/topsongs/limit={max(n, 10)}{g}/json")
        f = d["feed"]
        rows = [(e["im:name"]["label"], e["im:artist"]["label"]) for e in f.get("entry", [])[:n]]
        return f.get("updated", {}).get("label", ""), rows
    return run


# ---------------------------------------------------------------- Deezer
def deezer_global(n):
    d = fetch_json(f"https://api.deezer.com/chart/0/tracks?limit={n}")
    return "live", [(t["title"], t["artist"]["name"]) for t in d["data"][:n]]


# ---------------------------------------------------------------- kworb (static HTML)
def kworb(path):
    def run(n):
        page = fetch("https://kworb.net/" + path)
        m = re.search(r"\d{4}/\d{2}/\d{2}", page)
        rows = []
        for cells in html_rows(page):
            if len(cells) < 3 or not cells[0].isdigit():
                continue
            rows.append(split_artist_title(cells[2]))
            if len(rows) >= n:
                break
        return (m.group(0) if m else "see page"), rows
    return run


# ---------------------------------------------------------------- YouTube Charts (innertube, no key)
def yt_chart(country, chart_type, period=None, attribute=None):
    def run(n):
        q = (f"perspective=CHART_DETAILS&chart_params_country_code={country}"
             f"&chart_params_chart_type={chart_type}")
        if period:
            q += f"&chart_params_period_type={period}"
        if attribute:
            q += f"&chart_params_chart_attribute={attribute}"
        body = {"context": {"client": {"clientName": "WEB_MUSIC_ANALYTICS", "clientVersion": "2.0",
                                       "hl": "en", "gl": "IN", "theme": "MUSIC"},
                            "capabilities": {}, "request": {"internalExperimentFlags": []}},
                "browseId": "FEmusic_analytics_charts_home", "query": q}
        d = json.loads(fetch("https://charts.youtube.com/youtubei/v1/browse?alt=json",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Origin": "https://charts.youtube.com",
                                      "Referer": "https://charts.youtube.com/"}))
        c = d["contents"]["sectionListRenderer"]["contents"][0]["musicAnalyticsSectionRenderer"]["content"]
        date = ""
        for a in c["perspectiveMetadata"].get("availableChartsInfo", []):
            if a.get("chartType") == "CHART_TYPE_" + chart_type and (
                    not period or a.get("chartPeriodType") == "CHART_PERIOD_TYPE_" + period) and (
                    not attribute or a.get("chartAttribute", {}).get("language") == attribute) and (
                    a.get("latestEndDate")):
                date = ("day" if period == "DAILY" else "week") + " ending " + a.get("latestEndDate", "")
        entries = []
        for k, v in c.items():
            if isinstance(v, list):
                for block in v:
                    for lst in block.values():
                        if isinstance(lst, list):
                            entries.extend(lst)
        rows = [(e.get("name") or e.get("title") or "?",
                 ", ".join(a.get("name", "") for a in e.get("artists", [])[:3]))
                for e in entries[:n]]
        return date or ("now (rolling)" if not period else "latest"), rows
    return run


# ---------------------------------------------------------------- Spotify (no login)
def spotify_embed(playlist_id):
    def run(n):
        page = fetch(f"https://open.spotify.com/embed/playlist/{playlist_id}")
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
        ent = json.loads(m.group(1))["props"]["pageProps"]["state"]["data"]["entity"]
        rows = [(clean(t["title"]), clean(t["subtitle"])) for t in ent["trackList"][:n]]
        return "live playlist: " + ent.get("name", ""), rows
    return run


def spotify_public_global(n):
    d = fetch_json("https://charts-spotify-com-service.spotify.com/public/v0/charts")
    for c in d["chartEntryViewResponses"]:
        if c["displayChart"]["chartMetadata"]["alias"] == "REGIONAL_GLOBAL_WEEKLY":
            rows = [(e["trackMetadata"]["trackName"],
                     ", ".join(a["name"] for a in e["trackMetadata"]["artists"][:3]))
                    for e in c["entries"][:n]]
            return "week ending " + c["displayChart"]["date"], rows
    raise RuntimeError("REGIONAL_GLOBAL_WEEKLY not in response")


# ---------------------------------------------------------------- JioSaavn (unofficial web API)
def jiosaavn_playlist(token):
    def run(n):
        url = ("https://www.jiosaavn.com/api.php?__call=webapi.get&api_version=4&_format=json"
               f"&_marker=0&ctx=web6dot0&type=playlist&p=1&n={max(n, 10)}&token={urllib.parse.quote(token)}")
        d = fetch_json(url)
        rows = []
        for s in d.get("list", [])[:n]:
            arts = s.get("more_info", {}).get("artistMap", {}).get("primary_artists", [])
            rows.append((clean(s.get("title")), ", ".join(a["name"] for a in arts[:3]) or clean(s.get("subtitle"))))
        lu = d.get("more_info", {}).get("last_updated")
        date = datetime.fromtimestamp(int(lu), IST).strftime("updated %Y-%m-%d %H:%M IST") if lu else "live"
        return f"{clean(d.get('title'))} ({date})", rows
    return run


# ---------------------------------------------------------------- Gaana (server-rendered ld+json)
def gaana_playlist(slug):
    def run(n):
        page = fetch("https://gaana.com/playlist/" + slug)
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
            try:
                d = json.loads(m)
            except ValueError:
                continue
            for x in d if isinstance(d, list) else [d]:
                if x.get("@type") == "MusicPlaylist":
                    rows = [(t.get("name", ""), (t.get("byArtist") or {}).get("name", "").replace(",", ", "))
                            for t in x.get("track", [])[:n]]
                    return "live playlist: " + x.get("name", ""), rows
        raise RuntimeError("no MusicPlaylist ld+json found")
    return run


# ---------------------------------------------------------------- Billboard (server-rendered HTML)
def billboard(chart):
    def run(n):
        page = fetch(f"https://www.billboard.com/charts/{chart}/")
        wk = re.search(r"Week of ([A-Z][a-z]+ \d+, \d{4})", page)
        rows = re.findall(r'<li class="o-chart-results-list__item[^"]*">\s*<h3 id="title-of-a-story"[^>]*>'
                          r'(.*?)</h3>\s*<span[^>]*>(.*?)</span>', page, re.S)
        return ("week of " + wk.group(1)) if wk else "", [(clean(a), clean(b)) for a, b in rows[:n]]
    return run


# ---------------------------------------------------------------- Genius (public JSON, no key)
def genius_day(n):
    d = fetch_json(f"https://genius.com/api/songs/chart?time_period=day&chart_genre=all&per_page={n}&page=1")
    rows = [(i["item"]["title"], i["item"]["artist_names"]) for i in d["response"]["chart_items"][:n]]
    return "last 24h (lyrics page views, global)", rows


# ---------------------------------------------------------------- Shazam (blocked to scripts; kept as a canary)
def shazam_in(n):
    try:
        fetch("https://www.shazam.com/charts/top-200/india")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} - Shazam blocks scripted requests; use WebFetch "
                           "on https://www.shazam.com/charts/top-200/india") from None
    raise RuntimeError("page loaded but is JS-rendered; use WebFetch instead")


# ---------------------------------------------------------------- Google Trends (culture, not music)
def google_trends_in(n):
    page = fetch("https://trends.google.com/trending/rss?geo=IN")
    items = re.findall(r"<item>(.*?)</item>", page, re.S)
    rows = []
    for it in items[:n]:
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        tr = re.search(r"<ht:approx_traffic>(.*?)</ht:approx_traffic>", it)
        rows.append((clean(t.group(1)) if t else "?", (tr.group(1) + " searches") if tr else ""))
    return "trending searches India, last ~24h", rows


# ---------------------------------------------------------------- registry (India first)
SOURCES = [
    # key, label, function
    ("yt_shorts_in_daily", "YouTube Charts - Top Shorts songs India (daily, by # of Shorts made)", yt_chart("in", "SHORTS_TRACKS_BY_USAGE", "DAILY")),
    ("yt_shorts_in_weekly", "YouTube Charts - Top Shorts songs India (weekly)", yt_chart("in", "SHORTS_TRACKS_BY_USAGE", "WEEKLY")),
    ("yt_songs_in", "YouTube Charts - Top songs India (weekly)", yt_chart("in", "TRACKS", "WEEKLY")),
    ("yt_tamil", "YouTube Charts - Tamil-language top videos India (weekly)", yt_chart("in", "VIDEOS_LOP", "WEEKLY", "ta")),
    ("yt_hindi", "YouTube Charts - Hindi-language top videos India (weekly)", yt_chart("in", "VIDEOS_LOP", "WEEKLY", "hi")),
    ("yt_trending_in", "YouTube Charts - Trending music videos India (now)", yt_chart("in", "TRENDING_VIDEOS")),
    ("kworb_sp_in", "kworb - Spotify India daily", kworb("spotify/country/in_daily.html")),
    ("kworb_yt_in", "kworb - YouTube India weekly", kworb("youtube/insights/in.html")),
    ("sp_top50_in", "Spotify playlist - Top 50 India (daily)", spotify_embed("37i9dQZEVXbLZ52XmnySJg")),
    ("sp_hot_tamil", "Spotify playlist - Hot Hits Tamil (editorial)", spotify_embed("37i9dQZF1DX1i3hvzHpcQV")),
    ("sp_hot_hindi", "Spotify playlist - Hot Hits Hindi (editorial)", spotify_embed("37i9dQZF1DX0XUfTFmNBRM")),
    ("sp_trending_in", "Spotify playlist - Trending Now India (editorial)", spotify_embed("37i9dQZF1DXbVhgADFy3im")),
    ("apple_in", "Apple Music - Top songs India (daily)", apple_rss("in")),
    ("itunes_tamil", "iTunes Store - Top Tamil songs India (sales)", itunes_genre("in", 1264)),
    ("itunes_bollywood", "iTunes Store - Top Bollywood songs India (sales)", itunes_genre("in", 1263)),
    ("jiosaavn_trending", "JioSaavn - Trending Today", jiosaavn_playlist("I3kvhipIy73uCJW60TJk1Q__")),
    ("jiosaavn_top50", "JioSaavn - India Superhits Top 50", jiosaavn_playlist("VuJUPQ9ch77bB,U5Yp5iAA__")),
    ("jiosaavn_tamil", "JioSaavn - Tamil: India Superhits Top 50", jiosaavn_playlist("Dq3pWn1coqesud-ETNX4vg__")),
    ("gaana_tamil", "Gaana - Tamil Top 50", gaana_playlist("gaana-dj-tamil-top-50-2")),
    ("billboard_india", "Billboard - India Songs (weekly)", billboard("india-songs-hotw")),
    ("shazam_in", "Shazam - India Top 200 (canary: expected to fail in scripts)", shazam_in),
    # ---- global
    ("yt_shorts_global", "YouTube Charts - Top Shorts songs Global (weekly)", yt_chart("global", "SHORTS_TRACKS_BY_USAGE", "WEEKLY")),
    ("kworb_sp_global", "kworb - Spotify Global daily", kworb("spotify/country/global_daily.html")),
    ("sp_global_weekly", "Spotify Charts public API - Global weekly", spotify_public_global),
    ("sp_viral_hits", "Spotify playlist - Viral Hits (editorial; Viral 50 charts ended May 2026)", spotify_embed("37i9dQZF1DX2L0iB23Enbq")),
    ("apple_us", "Apple Music - Top songs US (daily)", apple_rss("us")),
    ("deezer_global", "Deezer API - Global chart", deezer_global),
    ("billboard_global200", "Billboard - Global 200 (weekly)", billboard("billboard-global-200")),
    ("genius_day", "Genius - top songs by lyric views (24h)", genius_day),
    ("gtrends_in", "Google Trends - trending searches India (RSS, all topics)", google_trends_in),
]


PRESETS = {
    "shorts": ["yt_shorts_in_daily", "yt_shorts_in_weekly", "yt_shorts_global"],
    "ta": ["yt_shorts_in_daily", "yt_shorts_in_weekly", "yt_tamil", "sp_hot_tamil", "itunes_tamil",
           "jiosaavn_tamil", "gaana_tamil", "apple_in"],
    "hi": ["yt_shorts_in_daily", "yt_shorts_in_weekly", "yt_hindi", "sp_hot_hindi", "sp_trending_in",
           "itunes_bollywood", "jiosaavn_top50", "kworb_sp_in", "sp_top50_in", "billboard_india"],
    "en": ["yt_shorts_global", "kworb_sp_global", "sp_global_weekly", "sp_viral_hits", "apple_us",
           "billboard_global200", "deezer_global", "genius_day"],
}
PRESETS["india"] = [k for k, _, _ in SOURCES[:SOURCES.index(next(s for s in SOURCES if s[0] == "shazam_in"))]]
INDIA_KEYS = set(PRESETS["india"])
SHORTS_KEYS = {"yt_shorts_in_daily", "yt_shorts_in_weekly", "yt_shorts_global"}


# Charts that copy each other count once (kworb mirrors YouTube and Spotify; daily and weekly
# Shorts are one signal), so "seen on 3 charts" means three independent signals.
FAMILY = {
    "yt_shorts_in_daily": "YT Shorts India", "yt_shorts_in_weekly": "YT Shorts India",
    "yt_songs_in": "YT songs India", "kworb_yt_in": "YT songs India",
    "yt_tamil": "YT Tamil", "yt_hindi": "YT Hindi", "yt_trending_in": "YT trending India",
    "kworb_sp_in": "Spotify India", "sp_top50_in": "Spotify India",
    "sp_hot_tamil": "Spotify Hot Hits Tamil", "sp_hot_hindi": "Spotify Hot Hits Hindi",
    "sp_trending_in": "Spotify Trending Now India", "apple_in": "Apple Music India",
    "itunes_tamil": "iTunes Tamil", "itunes_bollywood": "iTunes Bollywood",
    "jiosaavn_trending": "JioSaavn trending", "jiosaavn_top50": "JioSaavn Top 50",
    "jiosaavn_tamil": "JioSaavn Tamil", "gaana_tamil": "Gaana Tamil", "billboard_india": "Billboard India",
}
SHORTS_FAMILY = "YT Shorts India"


def norm_title(t):
    """Loose key for matching one song across charts, tolerant of spelling variants
    ("Veezha Veera" / "Veezh Veeraa"): each Latin word keeps its first letter plus its consonants."""
    t = t.lower()
    t = re.sub(r"\(.*?\)|\[.*?\]|\|.*$|- (new version|remix|slowed|sped up).*$", "", t)
    t = re.sub(r"\b(from|feat|ft|with|w/)\b.*$", "", t)
    words = re.sub(r"[^a-z0-9ऀ-෿]+", " ", t).split()
    out = []
    for w in words:
        if w.isascii() and len(w) > 2:
            w = w[0] + re.sub(r"[aeiouy]", "", w[1:])
            w = re.sub(r"(.)\1+", r"\1", w)
        out.append(w)
    return " ".join(out)


def hot_summary(results, per_group=8):
    """Songs on several independent India charts, plus everything on the India Shorts chart
    (the closest public signal to Reels audio), most useful first."""
    seen = {}
    for key, label, date, rows, err in results:
        if err or key not in FAMILY:
            continue
        for rank, (title, artist) in enumerate(rows, 1):
            k = norm_title(title)
            if not k:
                continue
            e = seen.setdefault(k, {"title": title, "artist": artist, "sources": [], "families": [],
                                    "best": rank, "shorts_rank": None})
            if key not in e["sources"]:
                e["sources"].append(key)
            if FAMILY[key] not in e["families"]:
                e["families"].append(FAMILY[key])
            e["best"] = min(e["best"], rank)
            if FAMILY[key] == SHORTS_FAMILY:
                e["shorts_rank"] = rank if e["shorts_rank"] is None else min(e["shorts_rank"], rank)
    def group(e):
        v = verdict(e)
        return next((i for i, p in enumerate(("HOT", "rising", "popular")) if v.startswith(p)), 3)

    keep = [e for e in seen.values() if e["shorts_rank"] is not None or len(e["families"]) >= 2]
    keep.sort(key=lambda e: (group(e), e["shorts_rank"] or 99, -len(e["families"]), e["best"]))
    out, counts = [], {}
    for e in keep:  # every HOT song, then up to per_group of each other kind
        g = group(e)
        if g == 0 or counts.get(g, 0) < per_group:
            out.append(e)
            counts[g] = counts.get(g, 0) + 1
    return out


def verdict(e):
    shorts = SHORTS_FAMILY in e["families"]
    others = len([f for f in e["families"] if f != SHORTS_FAMILY])
    if shorts and others >= 2:
        return f"HOT (Shorts #{e['shorts_rank']} + {others} other charts)"
    if shorts:
        return f"rising on Shorts (#{e['shorts_rank']}; few streaming charts yet)"
    if len(e["families"]) >= 3:
        return "popular on streaming (not on the Shorts chart; may not be a Reels sound)"
    return "on 2 charts"


def run_one(item, n):
    key, label, fn = item
    try:
        date, rows = fn(n)
        return key, label, date, rows, None
    except Exception as e:  # noqa: BLE001 - per-source isolation is the point
        return key, label, "", [], f"{type(e).__name__}: {e}"[:200]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--top", type=int, default=10, help="rows per source (default 10)")
    ap.add_argument("--only", help="comma-separated source keys")
    ap.add_argument("--json", help="also write all rows to this JSON file")
    ap.add_argument("--list", action="store_true", help="list source keys and exit")
    ap.add_argument("--lang", choices=sorted(PRESETS), help="preset source group: ta, hi, en, shorts, india")
    ap.add_argument("--md", help="also write a dated markdown list (for the edit plan) to this file")
    a = ap.parse_args()
    if a.list:
        for k, label, _ in SOURCES:
            print(f"{k:22} {label}")
        print()
        for name, keys in PRESETS.items():
            print(f"--lang {name:7} {', '.join(keys)}")
        return
    wanted = set(a.only.split(",")) if a.only else set(PRESETS[a.lang]) if a.lang else None
    chosen = [s for s in SOURCES if wanted is None or s[0] in wanted]
    fetched = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda s: run_one(s, a.top), chosen))

    ok = 0
    out = []
    print(f"Trending probe - fetched {fetched} - top {a.top} per source\n")
    print(f"{'SOURCE':22} | {'#':>2} | {'TITLE':48} | ARTIST")
    print("-" * 110)
    for key, label, date, rows, err in results:
        print(f"## {label}  [{date or 'n/a'}]")
        if err:
            print(f"{key:22} | -- | FAILED: {err}")
        else:
            ok += 1
            for i, (t, ar) in enumerate(rows, 1):
                print(f"{key:22} | {i:>2} | {t[:48]:48} | {ar[:40]}")
                out.append({"source": key, "label": label, "chart_date": date, "rank": i,
                            "title": t, "artist": ar, "fetched": fetched})
        print()
    hot = hot_summary(results)
    if hot:
        print("== India picks: Shorts usage first, then songs on several independent charts (mirrors counted once)")
        for e in hot:
            print(f"  {e['title'][:44]:44} | {e['artist'][:28]:28} | {len(e['families'])} chart{'s' if len(e['families']) > 1 else ''} | {verdict(e)}")
        print()
    canary = " (Shazam is a canary that always fails in scripts)" if any(r[0] == "shazam_in" for r in results) else ""
    print(f"{ok}/{len(results)} sources OK - fetched {fetched}{canary}")
    print("Charts say nothing about tempo or mood: play the 30 s preview (find_assets.py song) or ask the user.")
    print("There is no public India Reels chart: YouTube Shorts India is the proxy; confirm on the user's phone.")
    print("Reminder: trending commercial songs are added in-app (Reels/Shorts), never baked into the master.")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            md = [f"# Trending music check - {fetched}", "",
                  "Charts tell us what is trending; they grant no licence. Commercial songs go on in-app only.", ""]
            if hot:
                md += ["## India picks (Shorts usage first; mirrors counted once)", "",
                       "| song | artist | independent charts | best rank | verdict |", "|---|---|---|---|---|"]
                md += [f"| {e['title']} | {e['artist']} | {', '.join(e['families'])} | {e['best']} | {verdict(e)} |"
                       for e in hot]
                md.append("")
            for key, label, date, rows, err in results:
                md += [f"## {label} ({date or 'n/a'})", ""]
                md += [f"FAILED: {err}"] if err else [f"{i}. {t} - {ar}" for i, (t, ar) in enumerate(rows, 1)]
                md.append("")
            f.write("\n".join(md))
        print("markdown written to", a.md)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("rows written to", a.json)


if __name__ == "__main__":
    main()
