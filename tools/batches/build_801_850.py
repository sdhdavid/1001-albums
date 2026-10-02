"""Build tools/batches/801-850.json from the discovery output (tools/batches/801-850.discovered.json, which
also gives the track lengths, plus the second pass in 801-850.fix.discovered.json), the Spotify ids below (found by
web search, unverified) and the stories in tools/stories_801_850.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_801_850 import STORIES

SPOTIFY = {
 801:'3ly9T2L4pqTZijFgQssd3x', 802:'4kY6z5DSnmAihvm3F1ePlK', 803:'3DWfRADPpuK3AHHGZNJvUO', 804:'2u30gztZTylY4RG7IvfXs8', 805:'0MbeekWXeO9BFjImhNH5gf',
 806:'09AwlP99cHfKVNKv4FC8VW', 807:'0YW9Qke0AfzNVISsPQ7KoF', 808:'4E9neQ6TnlFxMaLoboETua', 809:'1UuXxohFdBe53FTv780i2Z', 810:'0GAqyZFjgaz6V5ozTS0dfW',
 811:'2EvCXuFV2Oduqo3cVqeU5W', 812:'6uhxuvVd4JL0EgtTFU99He', 813:'1Pus5h1qGedCn4CtOuPVtp', 814:'5OHv40uxVjNFuilXYmuAo5', 815:'7ssmEk3nxZq0EGOdGz1kAu',
 816:'7sqwuxORaCogFGgygafdSt', 817:'0txgYRjymfL0U28aTEK6Qk', 818:'5gVBXH8MT6zfdRkjp7qT18', 819:'6QuWvE0Txi12KMUyFeH4HI', 820:'5JjnPCfpp6redrkKpXZAs8',
 821:'4WoTkbpby1GTx3VvDMhDui', 822:'4U0j2a6r5avOlqkeYHY6i5', 823:'6wMq2h9GZ1MEbKr1tvPkJj', 824:'5Z1qbz6SLdQnWiVMEJ5MNK', 825:'1fi3IyodfojWTth7DhDQ6d',
 826:'459tNoDnuv0bL9ue9pENVz', 827:'4EMI48u2Fn6srocaXjuAcJ', 828:'', 829:'7KCxqRRNQfefktipLBoM16', 830:'0smEDe5xqBnofkwdLu8wo7',
 831:'0YI7QPNUGq8NTB6Nd8nWfd', 832:'1WLs1iVHFL0wboZpeZ0bFf', 833:'4z6F5s3RVaOsekuaegbLfD', 834:'6Zj0LtkX3xTnaNwO1Bia3Z', 835:'7dBI2sWcBJjU45v1tzsVxc',
 836:'3VyHgnHE4cp7YuU7skzuJ2', 837:'6dVIqQ8qmQ5GBnJ9shOYGE', 838:'6CBOvGgpmCOUz42VseThUf', 839:'6UkdyvPElK6JDkyeRClbI2', 840:'0FjHy5dCyVROqDUl6f2VTK',
 841:'6VSh1xjvCqEbUa07zZGGl6', 842:'4DF5ISpGZrFODkX3v8jgT5', 843:'0HEoXFTgPHGvczXdz9Ty5S', 844:'3fygVW5xqNoaGc95ClKFkc', 845:'2qivROlvQ8BcUKTaCA7dL2',
 846:'4g0dGimxnz4S2pvMknYjEx', 847:'4ij84pOJd9kY2uNdT2dOH1', 848:'4QSAiYWpavbk2vAYrxIKuO', 849:'5AXE8k2GdeTl05f0pKkNDN', 850:'5uRdvUR7xCnHmUW8n64n9y',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
LENGTHS_FROM_PLAYLIST = {}
RENAME = {'Mis‐Shapes': 'Mis-Shapes', 'Fu‐Gee‐La': 'Fu-Gee-La', "Essex Dogs (Includes 'Interlude')": 'Essex Dogs', 'Olv 26': 'OLV 26',
          'Monstre Sacre': 'Monstre Sacré', 'Achieved In the Valley In the Dolls': 'Achieved in the Valley of Dolls',
          'F.E.E.L.I.N.G.C.A.L.L.E.D.L.O.V.E': 'F.E.E.L.I.N.G.C.A.L.L.E.D.L.O.V.E.'}
KEEP_FIRST = {826: 9, 832: 16, 833: 13}   # bonus remixes / hidden tracks cut
DROP = {}
POSITION = {}
SPLIT = {}
BY_PLAYLIST = set()
SKIP = set()
DURATIONS = {}
NO_SPOTIFY = {828}   # #828 Logical Progression (a label compilation) is not on Spotify
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

disc = json.load(open('tools/batches/801-850.discovered.json'))
try: disc.update(json.load(open('tools/batches/801-850.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/801-850.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
