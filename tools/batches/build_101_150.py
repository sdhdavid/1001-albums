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
PLAYLIST_CHOICE = {}
RENAME = {}
KEEP_FIRST = {}   # drop bonus tracks / duplicates after the original album

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
    yt = r['youtube'][PLAYLIST_CHOICE.get(n, 0)]
    names = [clean(t) for t in r['tracks']]
    pos = yt['positions']
    keep = KEEP_FIRST.get(n, len(names))
    names, pos = names[:keep], pos[:keep]
    used = {p for p in pos if p >= 0}; spare = max(used | {len(names)}) + 1
    fixed = []
    for i, p in enumerate(pos):
        if p < 0:   # song not found in the playlist: keep positions unique (the site re-matches by title at run time)
            p = i if i not in used else spare
            if p == spare: spare += 1
            used.add(p)
        fixed.append(p)
    tracks = [[name, None, p] for name, p in zip(names, fixed)]
    st = STORIES[n]; tnames = [t[0] for t in tracks]
    picks = [list(p) for p in st['picks']]
    lookup = {norm(t): t for t in tnames}
    for p in picks:
        assert norm(p[0]) in lookup, (n, p[0], tnames)
        p[0] = lookup[norm(p[0])]   # use the track's exact spelling
    focus = sorted({tnames.index(name) for name, _ in picks})
    assert len(SPOTIFY[n]) == 22
    out.append({'n': n, 'youtubePlaylist': yt['id'], 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus,
                'story': st['story'], 'picks': picks})
json.dump(out, open('tools/batches/101-150.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
