"""Build tools/batches/251-300.json from the discovery output (tools/batches/251-300.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_251_300.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_251_300 import STORIES

SPOTIFY = {
 251:'7qfqgYcxCsLhu2xIRWKOdD', 252:'5risYG7klZCSLMNxB9dZhf', 253:'3fRCOoTbBsOITBWlCRCJQr', 254:'1dfvcFHSox0YKcPMxDrLIs', 255:'3PResMqFgQYBfzTnqTKwQw',
 256:'427BvOYZQRjTHODnreiZCo', 257:'5lL8N073N1d9ENpzM9Wtj5', 258:'6w4b41IacQMT1aFAldWRrh', 259:'51B7LbLWgYLKBVSpkan8Z7', 260:'7z7EJWzMiPb5NJ21okOIm7',
 261:'5mwOo1zikswhmfHvtqVSXg', 262:'49aoIKVNuO1PqayL3MiVde', 263:'4KjUgJn22cmBRQC0AHcjI3', 264:'0zKjnOsXxs63unPR6TWoHq', 265:'4Et98HH5UoYzwUH5583YE7',
 266:'4wbwwDANGlQcthuk83yIzD', 267:'4UZmpGH8kpAgyZ2yqQ8sP9', 268:'58eMx3QrTkiRmGGbSz2XL0', 269:'0xO9kRgdKZ3wzqrzJhM3sE', 270:'2GtOiYDDdU4jK2Q6uQnSr4',
 271:'35d7tjTi1UQq0cMfc0MWLg', 272:'10gbq3XvTrtUSplDoTtsOb', 273:'1z6Lu9ygvU5pNC8Y05AW31', 274:'6665FNrYGRuUGpbLpeoq7n', 275:'3smWSxwUr0dBref9OeUBnA',
 276:'3WkD4YxRCzgXG2MJF9yDpk', 277:'71UWDaWXrkE2diNsEJIukp', 278:'4iaDgkP0M6ahEHrBynAFei', 279:'2tSRe2rkdJvZWMOIZpu6lk', 280:'1oIICL75sMuInkEhX8jj3b',
 281:'1aBpWwhrZi3WEfKLAFFMMB', 282:'6gKMWnGptVs6yT2MgCxw29', 283:'6ou63QavbhaQvDTQ3BCkPv', 284:'5fmIolILp5NAtNYiRPjhzA', 285:'0CICGYdI3hXBqD6USYwWd5',
 286:'0a3YQpBnRzJzNktOjb6Dum', 287:'3vpVWxOR2W611w9lgAxWET', 288:'5WupqgR68HfuHt3BMJtgun', 289:'1oOpgDzHt6wl7kHbFFPzEc', 290:'4cxbRPxtGQgyNSCTtxoaSZ',
 291:'4LH4d3cOWNNsVw41Gqt2kv', 292:'5jgI8Eminx9MmLBontDWq8', 293:'0DOXzXXIHrYOxUvyCsucfX', 294:'257oomaawruFknt5wYCPDh', 295:'02kIg5Ft9nvOa1KTWlAZCI',
 296:'70vRcyvFfGc3rwaETxzjHC', 297:'2XDnCy6lPW0LefkmhvzkKN', 298:'0WIKGN8kf8xjnZzp9WoRfi', 299:'7brYayd20fiMrCiVwlidRI', 300:'74jn28Kr29iyh8eZXSvnwi',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
RENAME = {}
KEEP_FIRST = {}   # drop bonus tracks / outtakes after the original album
DROP = {}         # songs added on later editions, not on the original LP
# Albums the automatic search got wrong, filled in by hand.
MANUAL = {}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/251-300.discovered.json'))
out = []
for n in sorted(int(k) for k in disc):
    r = disc[str(n)]
    if n in MANUAL and 'fullAlbumVideo' in MANUAL[n]:
        m = MANUAL[n]; tracks = [[name, m['fullAlbumVideo'], None, t] for name, t in zip(m['names'], m['starts'])]
        extra = {'fullAlbumVideo': True}
    else:
        extra = None
    yt = (r.get('youtube') or [{'positions': []}])[PLAYLIST_CHOICE.get(n, 0)]
    names = [clean(t) for t in r.get('tracks', [])]
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
    rec['durations'] = durs if not extra else MANUAL[n]['durations']
    rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/251-300.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
