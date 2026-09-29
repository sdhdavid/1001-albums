"""Build tools/batches/101-150.json from the discovery output (tools/batches/101-150.discovered.json),
the Spotify ids below (found by web search) and the stories in tools/stories_101_150.py.  Durations are added
afterwards (fetch_durations.py + merge_durations.py), then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_101_150 import STORIES

SPOTIFY = {
 101:'2HDvpJuWTI97BnZbJOxBzj',102:'32fTx9DYJWjenQSMoI22Dq',103:'1fmGwfVnsdYtMWiOuvM5YT',104:'0HHmJpwOXXRJu9HI9iQiEO',105:'3uFZf8rykoHo7XMIQVYW6r',
 106:'5WndWfzGwCkHzAbQXVkg2V',107:'7oS7E5bFMzE8PXTZQKW0ge',108:'17PJF8shZv36RJQeqmHPYe',109:'168tPkaBJZKYxSrWDo4n1h',110:'2zYEcirgirihBtUr9ninD6',
 111:'4aSIyoC7BdDebquu0WgcFK',112:'0RBkIFbQy91qv8Tqja20og',113:'5z090LQztiqh13wYspQvKQ',114:'2Aiv0ThDpFa7lqHphR6MN5',115:'4TJIdlY9hGSSTO1kUs1neh',
 116:'533zqKatpy90jse2K5IaiQ',117:'6TYqjNcnBvFGtWCjiZFZug',118:'3dAjO3dyUP7edWoE1OeB7b',119:'5UI2X5VAmgu9xrlXDd5U7B',120:'2rogKfOpmCFuqNhtGKf2dX',
 121:'328gsq5mObioXj2TcD8AED',122:'1yBoaVrgcup2hX2DCYUajs',123:'4L1Qw49gKwFuQwQovBxsKI',124:'5IIB3xh53eRBpkkktSFQbc',125:'3bzgbgiytguTDnwzflAZr2',
 126:'13HI0VjkdnlqpyZXBYUHqs',127:'0ky5kdvfPxSmSpj03hpSAE',128:'1rRm5wc5lBtycx5xlY3848',129:'3idXLXoZDLQyxAHF97yguf',130:'4bGsY4hGvqBf9XrAzA1gZ2',
 131:'7K6JtyaSSVr7HidQsCHun0',132:'4pG3bKkbmReDt5QTDn3JDz',133:'02XyFDfvHfIwtqOC3o0PcK',134:'0L8n5dW0KfoNnLuYfyOFPg',135:'70Yl2w1p00whfnC7fj94ox',
 136:'4dgAnIHFpnFdSBqpRZheHq',137:'7F76o5x7W6dgfmgcVDeBH0',138:'6vUWpE8qciYHOhf7mgaGny',139:'5hWCiqRJKipJ2PWWUPntNp',140:'6VWKy5o2OcdeWa7yolazjU',
 141:'6bYqwLMVRQzwPQweVzCiry',142:'5N6DllSsuia7LnQUZ5UGuX',143:'0ETFjACtuP2ADo6LFhL6HN',144:'5cT7ee1sy2oEbFalP4asS4',145:'0Hs3BomCdwIWRhgT57x22T',
 146:'2IpGpYgkYYT1LtlynzSy58',147:'6C22QvOc4ombgUjY1M1ASN',148:'4l4u9e9jSbotSXNjYfOugy',149:'7IpcJbVxLLEfW0KXB7ndE2',150:'14UrtAcLym4a6f7IgXVGjF',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {115: 1, 127: 2, 133: 1}
RENAME = {}
KEEP_FIRST = {124: 13, 127: 11, 133: 11}   # drop bonus tracks / outtakes after the original album
DROP = {115: {1, 12, 16}}          # songs added on later editions, not on the original LP
# Albums the automatic search got wrong, filled in by hand (playlists found with a web search).
MANUAL = {
 # the search matched the 1969 album of the same name; this is the 1968 one
 129: {'youtubePlaylist': 'PLowQCq3Ss89jc16dgqj9Fxg9ryvgDChZf',
       'names': ['Tropicália', 'Clarice', 'No Dia Que Eu Vim-me Embora', 'Alegria, Alegria', 'Onde Andarás', 'Anunciação',
                 'Superbacana', 'Paisagem Útil', 'Clara', 'Soy Loco por Ti, América', 'Ave Maria', 'Eles']},
 # no playlist matched; this is the official YouTube Music album playlist
 111: {'youtubePlaylist': 'OLAK5uy_lnp_8yMyoUXE7yezOQkr546yLXO20oltk',
       'names': ['An Introduction to Indian Music', 'Dadra', 'Maru-Bihag', 'Bhimpalasi', 'Sindhi-Bhairavi']},
 # the playlists split the two long pieces unevenly; one full-album video with two chapters instead
 145: {'fullAlbumVideo': 'AKaZv7mwqQU', 'names': ['Shhh / Peaceful', 'In a Silent Way / It’s About That Time'], 'starts': [0, 1080]},
}

def clean(s):
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/101-150.discovered.json'))
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
    pos = yt['positions']
    if n in MANUAL and not extra:
        yt = {'id': MANUAL[n]['youtubePlaylist']}; names = MANUAL[n]['names']; pos = list(range(len(names)))
    keep = KEEP_FIRST.get(n, len(names))
    names, pos = names[:keep], pos[:keep]
    names = [x for i, x in enumerate(names) if i not in DROP.get(n, ())]
    pos = [x for i, x in enumerate(pos) if i not in DROP.get(n, ())]
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
    rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/101-150.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
