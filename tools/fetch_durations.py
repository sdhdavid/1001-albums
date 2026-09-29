"""Look up a length for every track in dist/pilot.json.

Runs where the public catalogs are reachable (GitHub Actions). Collects
several editions from the iTunes Search API and MusicBrainz, matches songs
by normalized title and takes the median length per song. Prints a JSON map {album number: ["m:ss" or null, ...]} between
markers so the result can be read from the job log.
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
from difflib import SequenceMatcher

UA = {'User-Agent': '1001-albums-site/1.0 (https://github.com/sdhdavid/1001-albums)'}

def get(url, pause=0.0):
    time.sleep(pause)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print('  retry', attempt, url[:90], e, file=sys.stderr); time.sleep(3 + attempt * 3)
    return None

def norm(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'")).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\((?:.*?(?:remaster|mono|stereo|live|version|mix|edit|take|bonus).*?)\)|\[.*?\]', ' ', s)
    s = re.sub(r' - .*?(remaster|mono|stereo|live|version|mix|edit).*$', ' ', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return 0
    if a == b: return 1
    if a in b or b in a: return .92
    return SequenceMatcher(None, a, b).ratio()

def clock(ms):
    s = round(ms / 1000); return f'{s // 60}:{s % 60:02d}'

def assign(names, cands):
    """cands: list of (title, ms). Greedy best-first match, threshold .8; returns ms per name."""
    pairs = sorted(((sim(n, t), i, j) for i, n in enumerate(names) for j, (t, _) in enumerate(cands)), reverse=True)
    out, used_i, used_j = [None] * len(names), set(), set()
    for score, i, j in pairs:
        if score < .8: break
        if i in used_i or j in used_j or not cands[j][1]: continue
        out[i] = cands[j][1]; used_i.add(i); used_j.add(j)
    return out

def editions(artist, title):
    """Yield track lists (title, ms) from several editions in both catalogs."""
    q = urllib.parse.quote(f'{artist} {title}')
    res = get(f'https://itunes.apple.com/search?term={q}&entity=album&limit=15&country=US', .4) or {}
    for c in [c for c in res.get('results', []) if sim(c.get('collectionName', ''), title) >= .75][:8]:
        tracks = get(f"https://itunes.apple.com/lookup?id={c['collectionId']}&entity=song&country=US", .4) or {}
        yield [(t.get('trackName', ''), t.get('trackTimeMillis')) for t in tracks.get('results', []) if t.get('wrapperType') == 'track']
    q = urllib.parse.quote(f'release:"{title}" AND artist:"{artist}"')
    res = get(f'https://musicbrainz.org/ws/2/release?query={q}&fmt=json&limit=15', 1.1) or {}
    for rel in [r for r in res.get('releases', []) if sim(r.get('title', ''), title) >= .75][:8]:
        data = get(f"https://musicbrainz.org/ws/2/release/{rel['id']}?inc=recordings&fmt=json", 1.1) or {}
        yield [(t.get('title', ''), t.get('length')) for m in data.get('media', []) for t in m.get('tracks', [])]

def lengths(artist, title, names):
    """Median length per song across every edition found, so one live take or single edit can't skew it."""
    seen = [[] for _ in names]
    for cands in editions(artist, title):
        for i, ms in enumerate(assign(names, cands)):
            if ms: seen[i].append(ms)
    return [clock(sorted(v)[len(v) // 2]) if v else None for v in seen], [len(v) for v in seen]

pilot = json.load(open('dist/pilot.json'))
catalog = {str(a['n']): a for a in json.load(open('dist/albums.json'))}
result = {}
for n, album in pilot.items():
    meta = catalog[n]; names = [t[0] for t in album['tracks']]
    artist = re.split(r' \+ | featuring |/| and Her| & His', meta['artist'])[0].strip()
    title = re.sub(r'[“”"]', '', meta['title'])
    got, votes = lengths(artist, title, names)
    result[n] = got
    print(f'{n:>3} {sum(x is not None for x in got):>2}/{len(names)} {meta["artist"]} — {meta["title"]}', file=sys.stderr)
    for name, d, v in zip(names, got, votes):
        if d is None or v < 2: print(f'      {v} editions: {name} {d}', file=sys.stderr)
print('===DURATIONS-BEGIN===')
print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))
print('===DURATIONS-END===')
