"""Build tools/batches/51-100.json from the discovery output (tools/batches/51-100.discovered.json),
the Spotify ids below and the stories in tools/stories_51_100.py.  Durations are added afterwards
(fetch_durations.py + merge_durations.py), then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_51_100 import STORIES

SPOTIFY = {51:'2P0TLZSGxpDmYdp16bI4hv',52:'1xPtXzS5yCbDAqC7pxRCaF',54:'7njGz7ZeDXL6cH3VnflcQ2',55:'50o7kf2wLwVmOTVYJOTplm',56:'3nB9DKUlU5REI0SBYyh8yG',
 57:'0pkrqPjeq9K5KD0hFqAKNa',58:'6YabPKtZAjxwyWbuO9p4ZD',59:'05XrdYLJKZgLnYUgWPyQ23',60:'3PRoXYsngSwjEQWR5PsHWR',61:'2CNEkSE8TADXRT2AzcEt1b',
 62:'7wpo5k9gqXQHfxISH1jatO',63:'3dfPMayEO2G87wzXPMEvmb',64:'4NP1rhnsPdYpnyJP0p0k0L',65:'0YEmNXaNDq03tfgFmG4MOj',66:'1SbqioSVe6TgXudiKMKEaB',
 67:'6zK7GV2JCqLknAdTeIhooB',68:'3CFeJ5Kb9dNPaxCrdC1Dv7',69:'6qfS5de8GAy1G5tk7tyiof',70:'72qrnM4yUNMDDlWiqKc8iY',71:'1sh32o99zA04PJIUJUpEj7',
 72:'1EPEx0lzGPCal0YRTJV66u',73:'3W45Tazulh4zb48uL1RV8H',74:'6d6y86rdCfkh5EeA23iIAp',75:'2EYVXfypcucR62WMKJl6Mr',76:'1nd8Xz8Zh7tZv5EdLbg5nF',
 77:'6O62Cqi0YqOytEbFmeLyjU',78:'6QaVfG1pHYl1z15ZxkvVDW',79:'1PdqT2EZfFkWTsN18x1SZk',80:'7hez8jibf36E66GHpFkWz7',81:'5MTUjDTUWFuyhWW7oRqqmi',
 82:'47inaDdXEosHHrQc2nT7aK',83:'0DFhGsFKG7G58cke33GlAh',84:'6evLFi930oxXqMhKRmGMaX',85:'1XBC1NVZsxOvZFwG5stJ8o',86:'3AyMAtsTeETJh8zKjYDQLm',
 87:'6myt0Ez6hGJIPQeZKgY8um',88:'6fRqzJT070Kp9RWlSXmKcY',89:'2Se4ZylF9NkFGD92yv1aZC',90:'01Zc1xVpVQFnVKBc0SMMBO',91:'2QkDDVLuh025znjaxvTfAY',
 92:'0LYpJGx3fHoTmKOtKuMWtQ',93:'1jWmEhn3ggaL6isoyLfwBn',94:'2RAkj374WmU09Pt06H0hcQ',95:'1KdQnV7aijYNQB9KOpZNYy',96:'6lPb7Eoon6QPbscWbMsk6a',
 97:'1klQV0Z1x2oXmcCb7IvUZt',98:'2ULhVPvdhT7RREnqRWM06G',99:'3sWVVl0RzliQSiN5OTRGlM',100:'7rSZXXHHvIhF4yUFdaOCy9'}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {85: 1}
RENAME = {"Change Gonna Come": "A Change Is Gonna Come", "Rael 1": "Rael"}
KEEP_FIRST = {68: 12, 90: 13}   # drop bonus tracks / duplicates after the original album

def clean(s):
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/51-100.discovered.json'))
out = []
for n in sorted(int(k) for k in disc):
    r = disc[str(n)]
    yt = r['youtube'][PLAYLIST_CHOICE.get(n, 0)]
    names = [clean(t) for t in r['tracks']]
    pos = yt['positions']
    keep = KEEP_FIRST.get(n, len(names))
    names, pos = names[:keep], pos[:keep]
    tracks = [[name, None, (p if p >= 0 else i)] for i, (name, p) in enumerate(zip(names, pos))]
    st = STORIES[n]; tnames = [t[0] for t in tracks]
    picks = [list(p) for p in st['picks']]
    lookup = {norm(t): t for t in tnames}
    for p in picks:
        assert norm(p[0]) in lookup, (n, p[0], tnames)
        p[0] = lookup[norm(p[0])]   # use the track's exact spelling
    focus = sorted({tnames.index(name) for name, _ in picks})
    assert len(SPOTIFY[n]) == 22
    out.append({'n': n, 'youtubePlaylist': yt['id'], 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus,
                'story': st['story'], 'picks': picks, 'genres_from': 'tools/genres.py'})
    for k in ('genres_from',): out[-1].pop(k)
json.dump(out, open('tools/batches/51-100.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
