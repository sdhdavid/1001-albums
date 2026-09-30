"""Find track lists, lengths and YouTube playlists for a range of albums.

Usage: python3 tools/discover.py FIRST LAST OUT.json   (or: '56,63,74' 0 OUT.json for a list)     (runs in GitHub Actions: "Discover albums")

For each catalog entry N in FIRST..LAST (skipping albums already on the site):
  * track list + lengths from the original-looking iTunes edition (median lengths across editions via fetch_durations helpers)
  * YouTube playlist candidates (yt-dlp search), each scored by how many of the album's songs it contains;
    the best playlist gives every song's position in it ("tracks": [[name, null, index], ...]).
Output is a review file: pick, check the scores, then turn it into a batch for add_albums.py.
"""
import json, re, sys, urllib.parse
sys.argv, args = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, 'tools')
import importlib.util
# reuse the lookup helpers without running fetch_durations' main script
src = open('tools/fetch_durations.py').read().split("sys.path.insert(0, 'tools'); import store")[0]
ns = {}; exec(compile(src, 'fetch_durations_helpers', 'exec'), ns)
get, sim, norm, clock, editions, assign = (ns[k] for k in ('get', 'sim', 'norm', 'clock', 'editions', 'assign'))
import yt_dlp, store

wanted = [int(x) for x in args[0].split(',')] if ',' in args[0] or args[1] == '0' else list(range(int(args[0]), int(args[1]) + 1))
out_path = args[2]
# Titles the automatic clean-up gets wrong: n -> (artist, title) to search for.
OVERRIDE = {74: ('The Yardbirds', 'Roger the Engineer'), 63: ('The Byrds', 'Fifth Dimension'),
            251: ('Hugh Masekela', 'Home Is Where the Music Is'), 270: ('Lynyrd Skynyrd', 'Pronounced Leh-Nerd Skin-Nerd')}
# Extra words for the YouTube search when the plain query finds the wrong playlists (live versions, other albums).
YT_QUERY = {275: 'Hawkwind Space Ritual 1973 full album', 284: 'Herbie Hancock Head Hunters 1973 full album Chameleon',
            297: 'Iggy and the Stooges Raw Power 1973 full album'}
# Candidates found by hand (web search): extra playlists to score, and full-album videos whose chapters are read.
EXTRA_PLAYLISTS = {275: ['OLAK5uy_lFFPjJvqQDLVRR8HA3an2aZZUIH_s4ogk', 'OLAK5uy_kCFLJeEuBQmuXIHWYQxX-zjcXtceZe8UY', 'PLycVTiaj8OI_vlOI_Hhs7lHuTeAAf57c5'],
                   284: ['OLAK5uy_nvlpZLPE7acPh4D5k2lvtdFCe68yEIqV4', 'OLAK5uy_m789U0dt-J4aLVd7p-dXJxSfDliep-NT0', 'PLm4I8tP6UbWayMmspp9ucpplfT2twORSe', 'PLLpV5usM_H_YUpR35cBBP4fwXrSQOH-qZ']}
VIDEOS = {}  # video pages need a signed-in browser from GitHub Actions, so chapters can't be read there
catalog = {a['n']: a for a in store.catalog()}
have = set(store.numbers())
BAD = re.compile(r'deluxe|anniversary|expanded|sessions|collector|super|box|live|bonus|mono|stereo|demo|remix', re.I)

def pick_edition(artist, title):
    eds = list(editions(artist, title))
    eds = [e for e in eds if len(e) >= 4]
    if not eds: return None, []
    counts = [len(e) for e in eds]
    # most common track count = the original album (deluxe editions are longer)
    common = max(set(counts), key=lambda c: (counts.count(c), -c))
    best = next(e for e in eds if len(e) == common)
    return best, counts

def simple(s): return norm(re.sub(r'\(.*?\)|\[.*?\]|- .*$', '', s))

ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist', 'skip_download': True, 'ignoreerrors': True, 'socket_timeout': 30})

def yt_candidates(artist, title, n=None):
    q = urllib.parse.quote(YT_QUERY.get(n) or f'{artist} {title} album')
    info = ydl.extract_info(f'https://www.youtube.com/results?search_query={q}&sp=EgIQAw%253D%253D', download=False) or {}
    return [(e.get('id'), e.get('title')) for e in info.get('entries', []) if e and e.get('id') and str(e['id']).startswith(('PL', 'OLAK'))][:6]

def variants(t):
    t = t or ''
    out = [t, re.sub(r'^\s*\d+[\.\)\-]?\s*', '', t)]
    if ' - ' in t: out.append(t.split(' - ', 1)[1])
    return [simple(v) for v in out if simple(v)]

def score(names, entries):
    titles = [variants(t) for t in entries]
    pos, used = [], set()
    for n in names:
        best, bj = 0, -1
        for j, t in enumerate(titles):
            if j in used: continue
            s = max((sim(simple(n), v) for v in t), default=0)
            if s > best: best, bj = s, j
        if best >= .8: used.add(bj); pos.append(bj)
        else: pos.append(-1)
    return pos

result = {}
for n in wanted:
    if n in have or n not in catalog: continue
    meta = catalog[n]; artist = re.split(r' \+ | featuring |/| and Her| & His', meta['artist'])[0].strip(); title = re.sub(r'[“”"]', '', meta['title'])
    title = re.sub(r'\s*\(.*?\)\s*$', '', title)
    artist, title = OVERRIDE.get(n, (artist, title))
    edition, counts = pick_edition(artist, title)
    rec = {'n': n, 'artist': meta['artist'], 'title': meta['title'], 'editionSizes': counts}
    if edition:
        names = [t for t, _ in edition]
        rec['tracks'] = names; rec['durations'] = [clock(ms) if ms else None for _, ms in edition]
        best = []
        for pid, ptitle in yt_candidates(artist, title, n) + [(p, 'hand-picked') for p in EXTRA_PLAYLISTS.get(n, [])]:
            info = ydl.extract_info(f'https://www.youtube.com/playlist?list={pid}', download=False) or {}
            ents = [e.get('title') for e in info.get('entries', []) if e]
            pos = score(names, ents)
            found = sum(p >= 0 for p in pos)
            best.append({'id': pid, 'title': ptitle, 'size': len(ents), 'found': found, 'positions': pos, 'entries': ents if ptitle == 'hand-picked' else None})
        best.sort(key=lambda b: (b['found'] - abs(b['size'] - len(names)) * .5, b['id'].startswith('OLAK')), reverse=True)
        rec['youtube'] = best[:3] + [b for b in best[3:] if b['title'] == 'hand-picked']
        vids = []
        for vid in VIDEOS.get(n, []):
            v = ydl.extract_info(f'https://www.youtube.com/watch?v={vid}', download=False) or {}
            vids.append({'id': vid, 'title': v.get('title'), 'duration': v.get('duration'), 'channel': v.get('channel'),
                         'chapters': [[c.get('title'), int(c.get('start_time') or 0)] for c in v.get('chapters') or []],
                         'description': (v.get('description') or '')[:3000]})
        if vids: rec['videos'] = vids
    result[n] = rec
    print(n, meta['title'], '| editions', counts, '| best', (rec.get('youtube') or [{}])[0].get('id'), (rec.get('youtube') or [{}])[0].get('found'), flush=True)
    json.dump(result, open(out_path, 'w'), ensure_ascii=False, indent=1)
