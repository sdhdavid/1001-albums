"""Build tools/batches/151-200.json from the discovery output (tools/batches/151-200.discovered.json),
the Spotify ids below (found by web search) and the stories in tools/stories_151_200.py.  Durations are added
afterwards (fetch_durations.py + merge_durations.py), then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_151_200 import STORIES

SPOTIFY = {
 151:'7ETjltUjIuYreYFUokclBh',152:'1Yb6NXSBoFedGL1qhXyO4K',153:'7d9IZA5hVMlRqkRszYt66r',154:'1J8QW9qsMLx3staWaHpQmU',155:'4vXFiaDS8zuEl5bOUbW53x',
 156:'58MQ0PLijVHePUonQlK76Y',157:'0kT4F2mSpvTk3stwiaEStp',158:'6tCPiWGLQCg8UzceiH008f',159:'7iwS1r6JHYJe9xpPjzmWqD',160:'20CYfxjKvqXkCXBhAgOE39',
 161:'4DjSI3qiOKsUlZo4NsgYFq',162:'7isYifHXAT7wbuxbJziBG3',163:'76q2Ubo0vZIJxCqS0I1msH',164:'71rxIr6MJYUzDG9ge6Jq3J',165:'1b3JDPGdB107sY2fpOna7Z',
 166:'0Oz9XlZ1Af2o1MgOLrgIIs',167:'1Lzi2p6CUH156zbJTcOjNX',168:'2pTyJZOTqFYn2UPP30zZNl',169:'1P0cFYs8P7bCzfyDwgBJjz',170:'7uU2qrFZQSdQacicLXMnaJ',
 171:'3MANoCcmaHWeXSuWiO3iVo',172:'7sIFcFS96iFIdzLuETglbq',173:'0WYYrC9My9rYWigac003hw',174:'5w2X5ZmdE4u0XGkOU7BiLG',175:'6rvGaPLmW7Ciq6UgmK9TGF',
 176:'3Q0zkOZEOC855ErOOJ1AdO',177:'3X6rUtZhuPvWLYcczx8CDa',178:'4ZLy3U2q17Yjw7jkjXPJQj',179:'6AFLOkpJjFF652jevcSOZX',180:'1CsuCA05y9r7ftG9bGGtWV',
 181:'2nkFniR6DseqFJLhxXV01T',182:'0DFYbYCcHCEJPcN1hODG6K',183:'5bHkK1X4WEOzNvRhehvOcb',184:'132qAo1cDiEJdA3fv4xyNK',185:'5EVlXlHbRQI8ybuNt4ArXI',
 186:'6P5QHz4XtxOmS5EuiGIPut',187:'3llL1qaL2RvtyQAthAuRFS',188:'5PfnCqRbdfIDMb1x3MPQam',189:'7rqgm1BnAZ8I4d6hukpkdg',190:'04FfqGvZJ9oUBGRVrq2FE5',
 191:'24R9CyPLFa0CJrSZ9whlT3',192:'1jVqTEHG1Fq8xZKcTnNAL7',193:'111J9nxmdhyHSLNHeAL1jO',194:'2ZFCR4pxXNKfPFUzzMw8X1',195:'4tgndY02xcHEIrs9M6MzjS',
 196:'0JwHz5SSvpYWuuCNbtYZoV',197:'44VxbAytHpVi3Rq8hRhild',198:'2TjodugH6rA5ZHPsWVErmw',199:'5qhXaVIC5BdE4a5Kq1FMZG',200:'2NEQ5Q4sBbUHVVx3Wf8TEZ',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
RENAME = {"Intro / Ramblin' Rose": "Ramblin' Rose", 'Intro No. 2 / Kick Out the Jams': 'Kick Out the Jams', 'Tall / Rocket Reducer No. 62': 'Rocket Reducer No. 62',
          'Bird On a Wire': 'Bird on the Wire', "The Old Man's Back Again (Dedicated To the Neo-Stalinist Regime)": "The Old Man's Back Again",
          "War Pigs / Luke's Wall": 'War Pigs', 'Jack the Stripper / Fairies Wear Boots': 'Fairies Wear Boots'}
KEEP_FIRST = {172: 12}   # drop bonus tracks / outtakes after the original album
DROP = {192: {0, 1, 2, 3, 6, 7, 8, 9}}   # Live at Leeds: the six songs of the original LP only
# Albums the automatic search got wrong, filled in by hand.
MANUAL = {
 # the track list found was the US edition with medley titles; the playlist follows the UK LP song by song
 178: {'youtubePlaylist': 'PLo2VF3ux4qcZtVqa2p5ICdOAyDZOPyUDp',
       'names': ['Black Sabbath', 'The Wizard', 'Behind the Wall of Sleep', 'N.I.B.', 'Evil Woman', 'Sleeping Village', 'The Warning'],
       'durations': ['6:20', '4:24', '3:37', '6:05', '3:25', '3:46', '10:32']},
}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/151-200.discovered.json'))
out = []
for n in sorted(int(k) for k in disc):
    r = disc[str(n)]
    if n in MANUAL and 'fullAlbumVideo' in MANUAL[n]:
        m = MANUAL[n]; tracks = [[name, m['fullAlbumVideo'], None, t] for name, t in zip(m['names'], m['starts'])]
        extra = {'fullAlbumVideo': True}
    else:
        extra = None
    yt = r['youtube'][PLAYLIST_CHOICE.get(n, 0)]
    names = [clean(t) for t in r['tracks']]
    pos = yt['positions']; durs = list(r.get('durations') or [None] * len(names))
    if n in MANUAL and not extra:
        yt = {'id': MANUAL[n]['youtubePlaylist']}; names = MANUAL[n]['names']; pos = list(range(len(names))); durs = MANUAL[n]['durations']
    keep = KEEP_FIRST.get(n, len(names))
    names, pos, durs = names[:keep], pos[:keep], durs[:keep]
    names = [x for i, x in enumerate(names) if i not in DROP.get(n, ())]
    pos = [x for i, x in enumerate(pos) if i not in DROP.get(n, ())]
    durs = [x for i, x in enumerate(durs) if i not in DROP.get(n, ())]
    seen = {}
    for i, x in enumerate(names):   # the same song twice (e.g. an encore): keep both, name the second
        if x in seen: names[i] = x + ' (Encore)'
        seen[x] = 1
    used = {p for p in pos if p >= 0}; spare = max(used | {len(names)}) + 1
    fixed = []
    for i, p in enumerate(pos):
        if p < 0:   # song not found in the playlist: keep positions unique (the site re-matches by title at run time)
            p = i if i not in used else spare
            if p == spare: spare += 1
            used.add(p)
        fixed.append(p)
    if not extra: tracks = [[name, None, p] for name, p in zip(names, fixed)]
    st = STORIES[n]; tnames = [t[0] for t in tracks]
    picks = [list(p) for p in st['picks']]
    lookup = {norm(t): t for t in tnames}
    for p in picks:
        assert norm(p[0]) in lookup, (n, p[0], tnames)
        p[0] = lookup[norm(p[0])]   # use the track's exact spelling
    focus = sorted({tnames.index(name) for name, _ in picks})
    assert len(SPOTIFY[n]) == 22
    rec = {'n': n, 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus, 'story': st['story'], 'picks': picks}
    if not extra: rec['durations'] = durs
    rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/151-200.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
