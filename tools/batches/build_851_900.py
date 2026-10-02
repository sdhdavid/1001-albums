"""Build tools/batches/851-900.json from the discovery output (tools/batches/851-900.discovered.json, which
also gives the track lengths, plus the second pass in 851-900.fix.discovered.json), the Spotify ids below (found by
web search, unverified) and the stories in tools/stories_851_900.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_851_900 import STORIES

SPOTIFY = {
 851:'31Sx9uz9KqlvmX07Pvp0wN', 852:'6qoD3WaEeRFUTIjQLPsSjy', 853:'020brgMKGgdPSYjcVNypql', 854:'185DHT5SvszXRrezx3lOjt', 855:'2wa0kOg4mJ94Iw17Gcv4IL',
 856:'5bmpvyP7UGqB4VuXmrJUMy', 857:'2okCg9scHue9GNELoB8U9g', 858:'56YzQ0dhmRMDryZsrjdHun', 859:'1cYRtXjzkEueYaYTU8R2EX', 860:'3lZOXiJrpeRDYNcAyD4HHR',
 861:'3wkvpbuSilxLfiHLtpnfvo', 862:'0yTmT1i6yHb5EVyJOmIwGw', 863:'4Vuni3hdPd5F1BxorpVijs', 864:'5dbW25KDJWBkv2gtaQdmxJ', 865:'0rK8K0z9sYhEhCW51v9jrp',
 866:'3iC6dJobZulVXp0F4Bojig', 867:'65TxXNf79y6E7zBpAdVMZZ', 868:'6cuNyrSmRjBeekioLdLkvI', 869:'1BZoqf8Zje5nGdwZhOjAtD', 870:'2KE8WCHtD8qnAxXeIzNEId',
 871:'5SHOMidOm0N4RpgulqwPoY', 872:'7p5mnxLTjbvs4kInkK8za9', 873:'0PSTqZ8cInMb1Wr68Uqdwp', 874:'5dmYtZVJ1bG9RyrZBRrkOA', 875:'2qw8luUB90qWpcgJzdAhsn',
 876:'0gsiszk6JWYwAyGvaTTud4', 877:'4PQFrVyQ6xWGjbq5kkVVaX', 878:'7nFlAxnXMrQRpM1R80pKQm', 879:'1vWnB0hYmluskQuzxwo25a', 880:'74HTGmkjvbilVJjTCsneXD',
 881:'0BOGd3GkLblP0N9koqXtmd', 882:'3Mz9d3xD0Hx3IaiCUiO4gt', 883:'34ZFTOIWAIdgm9iBbIIMxG', 884:'0K5FvRzJl6iTKikI9tMdAB', 885:'2T6sux5guHBhtL9AgDrTDQ',
 886:'5lOFvOWAdy9G6p44noRILU', 887:'6lijTrmA0yAucg4Axbj1up', 888:'41qn4oxd4WFgz4JSBI9Ips', 889:'4emdFI4WR6qBPNBbJzhivv', 890:'1ZFjvEN3C2J1Q1xVhu2YaC',
 891:'2Hck40QRPTqSQp7lsMrAku', 892:'7MmEaGmGItbs5MATihlFuS', 893:'0dSSZGzoukzrFBnG07J45i', 894:'1pAakXNiYkGzS7gRzxGyHn', 895:'3WNxdumkSMGMJRhEgK80qx',
 896:'7HcHPb1P9mubh0vyDdawAv', 897:'4WxHlSD6QmOXiJRB3inkah', 898:'0waCN9Dzq28sIxCSVYwPHO', 899:'6G9fHYDCoyEErUkHrFYfs4', 900:'0fLhefnjlIV3pGNF9Wo8CD',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
LENGTHS_FROM_PLAYLIST = {}
RENAME = {'My Gift to You / Earache My Eye': 'My Gift to You', 'Cop Shoot Cop...': 'Cop Shoot Cop', 'Baby Girl Window (Hidden Track "Hello Sir")': 'Baby Girl Window',
          'Cupids Trick': "Cupid's Trick", '2:45 Am': '2:45 AM', 'Suite‐Pee': 'Suite-Pee', 'Peep‐Hole': 'Peep-Hole', 'Sweet‐Lovin’ Man': 'Sweet-Lovin’ Man'}
KEEP_FIRST = {855: 13}   # #855: the 13-track single-disc album (as on Spotify)
DROP = {873: [5, 10, 12], 876: list(range(12))}   # #873 bonus tracks; #876 the twelve short silent tracks before the album
POSITION = {}
SPLIT = {}
BY_PLAYLIST = set()
SKIP = set()
DURATIONS = {}
NO_SPOTIFY = set()
MANUAL = {}
VIDEOS = {}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*\(with [^)]*\)', '', s)
    s = re.sub(r'\s*\[with [^\]]*\]', '', s)
    s = re.sub(r'\s*[\(\[]feat\.[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/851-900.discovered.json'))
try: disc.update(json.load(open('tools/batches/851-900.fix.discovered.json')))   # second pass for a few albums
except FileNotFoundError: pass
out = []
for n in sorted(int(k) for k in disc if int(k) not in SKIP):
    r = disc[str(n)]
    if n in MANUAL and 'fullAlbumVideo' in MANUAL[n]:
        m = MANUAL[n]; tracks = [[name, m['fullAlbumVideo'], None, t] for name, t in zip(m['names'], m['starts'])]
        extra = {'fullAlbumVideo': True}
    else:
        extra = None
    yt = (r.get('youtube') or [{'positions': []}])[PLAYLIST_CHOICE.get(n, 0)]
    names = [clean(t) for t in r.get('tracks', [])]
    pos = yt.get('positions', []); durs = list(r.get('durations') or [None] * len(names))
    if n in LENGTHS_FROM_PLAYLIST:
        secs = r['youtube'][LENGTHS_FROM_PLAYLIST[n]]['durations']
        durs = [f'{secs[p] // 60}:{secs[p] % 60:02d}' for p in pos]
    if n in MANUAL and not extra:
        yt = {'id': MANUAL[n]['youtubePlaylist']}; names = MANUAL[n]['names']; pos = list(range(len(names))); durs = MANUAL[n]['durations']
    pos = list(pos)
    for i, p in POSITION.get(n, {}).items(): pos[i] = p
    if n in DURATIONS: durs = list(DURATIONS[n])
    keep = KEEP_FIRST.get(n, len(names))
    names, pos, durs = names[:keep], pos[:keep], durs[:keep]
    names = [x for i, x in enumerate(names) if i not in DROP.get(n, ())]
    pos = [x for i, x in enumerate(pos) if i not in DROP.get(n, ())]
    durs = [x for i, x in enumerate(durs) if i not in DROP.get(n, ())]
    if n in BY_PLAYLIST:
        order = sorted(range(len(names)), key=lambda i: pos[i])
        names, pos, durs = [names[i] for i in order], [pos[i] for i in order], [durs[i] for i in order]
    seen = {}
    for i, x in enumerate(names):   # the same piece twice (a reprise): keep both, name the second
        if x in seen: names[i] = x + ' (Reprise)'
        seen[x] = 1
    used = {p for p in pos if p >= 0}; spare = max(used | {len(names)}) + 1
    fixed = []
    for i, p in enumerate(pos):
        if p < 0:   # song not found in the playlist: keep positions unique (the site re-matches by title at run time)
            p = i if i not in used else spare
            if p == spare: spare += 1
            used.add(p)
        fixed.append(p)
    if n in SPLIT:
        i, parts = SPLIT[n]
        names[i:i + 1] = [x[0] for x in parts]; fixed[i:i + 1] = [x[1] for x in parts]; durs[i:i + 1] = [x[2] for x in parts]
    if not extra: tracks = [[name, None, p] for name, p in zip(names, fixed)]
    if n in VIDEOS: tracks = [[name, vid] for name, vid, _ in VIDEOS[n]]; durs = [d for _, _, d in VIDEOS[n]]
    st = STORIES[n]; tnames = [t[0] for t in tracks]
    picks = [list(p) for p in st['picks']]
    lookup = {norm(t): t for t in tnames}
    for p in picks:
        assert norm(p[0]) in lookup, (n, p[0], tnames)
        p[0] = lookup[norm(p[0])]   # use the track's exact spelling
    focus = sorted({tnames.index(name) for name, _ in picks})
    if not SPOTIFY[n] and n not in NO_SPOTIFY: print('no Spotify id yet', n); continue
    rec = {'n': n, 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus, 'story': st['story'], 'picks': picks}
    if n in NO_SPOTIFY: del rec['spotifyAlbum']; rec['noSpotify'] = True
    else: assert len(SPOTIFY[n]) == 22
    rec['durations'] = durs if not extra else MANUAL[n]['durations']
    if n not in VIDEOS: rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/851-900.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
