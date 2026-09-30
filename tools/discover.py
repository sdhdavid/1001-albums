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
            251: ('Hugh Masekela', 'Home Is Where the Music Is'), 270: ('Lynyrd Skynyrd', 'Pronounced Leh-Nerd Skin-Nerd'),
            314: ('Richard & Linda Thompson', 'I Want to See the Bright Lights Tonight'), 315: ('Gil Scott-Heron', 'Winter in America'),
            326: ('Brian Eno', 'Another Green World'), 328: ('Neu!', "Neu! '75"), 339: ('R. D. Burman', 'Shalimar (Original Motion Picture Soundtrack)'),
            304: ('Stevie Wonder', "Fulfillingness' First Finale"), 307: ('Van Morrison', "It's Too Late to Stop Now"),
            340: ('Neil Young', "Tonight's the Night"), 346: ('Earth, Wind & Fire', "That's the Way of the World"),
            347: ('Curtis Mayfield', "There's No Place Like America Today"), 330: ('Keith Jarrett', 'The Koln Concert'),
            357: ('Jorge Ben', 'Africa Brasil'), 360: ('Parliament', 'Mothership Connection'), 364: ('Fela Kuti', 'Zombie'),
            369: ('Kraftwerk', 'Trans-Europe Express'), 381: ('Talking Heads', 'Talking Heads 77'), 383: ('David Bowie', 'Heroes'),
            392: ('Ian Dury', 'New Boots and Panties'), 393: ('Sex Pistols', 'Never Mind the Bollocks'),
            395: ('Kraftwerk', 'The Man-Machine'), 397: ('Elis Regina', 'Elis 1980'), 361: ('Penguin Cafe Orchestra', 'Music from the Penguin Cafe'),
            403: ('The Adverts', 'Crossing the Red Sea with the Adverts'), 405: ('The Residents', 'Duck Stab Buster & Glen'),
            406: ('Public Image Ltd', 'Public Image First Issue'), 410: ('Throbbing Gristle', 'D.o.A. The Third and Final Report'),
            415: ('Willie Colon', 'Siembra'), 417: ('Devo', 'Q: Are We Not Men? A: We Are Devo!'), 423: ('X-Ray Spex', 'Germfree Adolescents'),
            424: ('Brian Eno', 'Ambient 1 Music for Airports'), 429: ('Germs', 'GI'), 430: ('The B-52s', 'The B-52s'),
            445: ('Cheap Trick', 'Cheap Trick at Budokan'), 448: ('Public Image Ltd', 'Metal Box'), 404: ('Big Star', 'Third')}
# Extra words for the YouTube search when the plain query finds the wrong playlists (live versions, other albums).
YT_QUERY = {275: 'Hawkwind Space Ritual 1973 full album', 284: 'Herbie Hancock Head Hunters 1973 full album Chameleon',
            297: 'Iggy and the Stooges Raw Power 1973 full album',
            307: 'Van Morrison Its Too Late to Stop Now 1974 live album', 339: 'Shalimar 1978 R D Burman soundtrack songs',
            301: 'Bad Company 1974 debut album full', 348: 'Tom Petty and the Heartbreakers 1976 debut album full',
            352: 'Boston 1976 debut album full', 358: 'Joan Armatrading 1976 album full', 363: 'Ramones 1976 debut album full',
            376: 'The Clash 1977 debut album UK full', 381: 'Talking Heads 77 full album', 385: 'Suicide 1977 debut album full Alan Vega',
            387: 'Peter Gabriel 1 Car 1977 full album', 399: 'The Only Ones 1978 debut album full', 397: 'Elis Regina Elis 1980 album',
            383: 'David Bowie Heroes 1977 full album',
            414: 'Van Halen 1978 debut album full', 416: 'The Cars 1978 debut album full', 418: 'Dire Straits 1978 debut album full',
            430: 'The B-52s 1979 debut album full', 437: 'The Undertones 1979 debut album full', 429: 'Germs GI 1979 full album',
            404: 'Big Star Third Sister Lovers full album', 406: 'Public Image Ltd First Issue 1978 full album', 431: 'Holger Czukay Movies 1979 full album',
            433: 'The Fall Live at the Witch Trials full album'}
# Candidates found by hand (web search): extra playlists to score, and full-album videos whose chapters are read.
EXTRA_PLAYLISTS = {275: ['OLAK5uy_lFFPjJvqQDLVRR8HA3an2aZZUIH_s4ogk', 'OLAK5uy_kCFLJeEuBQmuXIHWYQxX-zjcXtceZe8UY', 'PLycVTiaj8OI_vlOI_Hhs7lHuTeAAf57c5'],
                   284: ['OLAK5uy_nvlpZLPE7acPh4D5k2lvtdFCe68yEIqV4', 'OLAK5uy_m789U0dt-J4aLVd7p-dXJxSfDliep-NT0', 'PLm4I8tP6UbWayMmspp9ucpplfT2twORSe', 'PLLpV5usM_H_YUpR35cBBP4fwXrSQOH-qZ'],
                   310: ['OLAK5uy_lhwiy3qPEpBwBTOpyy-KK8Pmcn7x9fI2k', 'OLAK5uy_m0wBxaewH-lbo6eGyZQUbE-fzlUeug7fM', 'PL4wwexJLSb3mF35yaNEVCZiX68Lb9FnEm'],
                   330: ['PLlziogY0fk9phBIR0pGySlfV92DebcKrc', 'PLfdMKJMGPPtwRzlKi6bCI1_mSv0cJkm4r', 'PL8SFNbbOmAYMsaQSCbbv5oC4aY5o_4t6s', 'PL0766CFA4CBD669D6'],
                   339: ['OLAK5uy_kzduVKq3Un4mx4ssOCWgbvq5AMRBvvNv4', 'OLAK5uy_nrjFfBfmaNOYAL09VgoinGl5IW59qFw2U', 'PLw61iWYSKReevacFkh4SlEafze-k8qXn0'],
                   364: ['OLAK5uy_kz-CwckiMEJh2jW1jU0-j0e9mi4vXxGPY', 'PL4ZqKOqeg4cVrjNjVVfB8UU36iO4enFVJ'],
                   376: ['PLHTo__bpnlYX4wXCfUXsk8atvR0zpbpPN'], 400: ['PLNPGM2D7aODeIwtlLA51o7d-DAkqffyrb'],
                   404: ['OLAK5uy_nEfRmzliYZ8KP0g2PRBjmQdJ6kPSuU86g', 'PLEvr99j7ruPzc3YXLXOnxQGVMw4iWAA6c', 'PLOJWuc3CN303QT7RnWuruRLJJxEnf6TUu', 'PLJvYa4hB_Ul-5gdY9UcBDXNbuLGhQKim_'],
                   406: ['OLAK5uy_m2PSh2Vw6s0PdINtbPCyv81N5nMX3yNac', 'OLAK5uy_l8aOiSeHdlBuY6Uiiz2__J280s7Yh8o6k', 'PLw31gx_Af1g-uYdvOjGTI3T1WieKas-51'],
                   431: ['OLAK5uy_niijN27zTnrqADCiWObap5-AK22HsC7qI', 'PLDCQnAwuT7e-oi-BQrVV8o5DrCiOVKZV1'],
                   441: ['PLOJWuc3CN301YxZG_I_ZniHGfb4tl7vug', 'PLo2aaBamFnLTj8Ad0ymIx81CavqxNcjnB', 'PLmna7oCNK2MmgBrbPZPciNsXxAMQEjUao']}
# Spotify album ids to check (the embed page lists the album's tracks), when web search found several albums with one name.
SPOTIFY_CHECK = {397: ['3NOxICud3CE6svBnR9WqC7', '4huMvebKxtKXAm51LCfOoC', '67UdOjU4vLZx8yoHgXkNes', '21XmM8dZGAfwUXTnAPqxdC']}
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
    elif EXTRA_PLAYLISTS.get(n):
        rec['youtube'] = []
        for pid in EXTRA_PLAYLISTS[n]:
            info = ydl.extract_info(f'https://www.youtube.com/playlist?list={pid}', download=False) or {}
            ents = [e for e in info.get('entries', []) if e]
            rec['youtube'].append({'id': pid, 'title': 'hand-picked', 'size': len(ents), 'entries': [e.get('title') for e in ents],
                                   'durations': [e.get('duration') for e in ents]})
    for sid in SPOTIFY_CHECK.get(n, []):
        try:
            import urllib.request as ur
            page = ur.urlopen(ur.Request(f'https://open.spotify.com/embed/album/{sid}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
            rec.setdefault('spotifyCheck', {})[sid] = re.findall(r'"name":"([^"]{1,80})"', page)[:25] + re.findall(r'"releaseDate":\{"isoString":"([^"]+)"', page)[:1]
        except Exception as e:
            rec.setdefault('spotifyCheck', {})[sid] = [str(e)]
    result[n] = rec
    print(n, meta['title'], '| editions', counts, '| best', (rec.get('youtube') or [{}])[0].get('id'), (rec.get('youtube') or [{}])[0].get('found'), flush=True)
    json.dump(result, open(out_path, 'w'), ensure_ascii=False, indent=1)
