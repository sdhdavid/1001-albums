"""Build tools/batches/201-250.json from the discovery output (tools/batches/201-250.discovered.json),
the Spotify ids below (found by web search) and the stories in tools/stories_201_250.py.  Durations are added
afterwards (fetch_durations.py + merge_durations.py), then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_201_250 import STORIES

SPOTIFY = {
 201:'24lX0YfUlQfqb2T2GioLji',202:'1CHUXwuge9A7L2KiA3vnR6',203:'69jyJl6Lyo80nQae0X312i',204:'2mlDvvSwZWVF6mjHt8aRPD',205:'4v9ZAufvuQKvTLcy21y6BM',
 206:'29f2cOueckYE8Nc1pkJjrU',207:'2v6ANhWhZBUKkg6pJJBs3B',208:'6P9BI0z8NrTBg3grSYiJPD',209:'2FHiXBmtRn9fuTRyRHWcnV',210:'40l8psHxHkph9yw5bcn2p3',
 211:'3NY5E1IrUP5xkyq41NZ9YC',212:'6RebvWkjRivaPoqxFAHxGF',213:'35w2w6W38bXCo4bG1akRe9',214:'29m6DinzdaD0OPqWKGyMdz',215:'0xzaemKucrJpYhyl7TltAk',
 216:'5NJHGcHNdLURknY2LfzjZg',217:'4X6gq5bgpGXcHINlFWzriM',218:'7IKUTIc9UWuVngyGPtqNHS',219:'5uvUlYLQpa3ErZ40kuoQ5K',220:'2OZbaW9tgO62ndm375lFZr',
 221:'17CT6ru3CyDXAi6xVaSUzg',222:'10jsW2NYd9blCrDITMh2zS',223:'55A2S482vOTTN5kgcMzTPJ',224:'5EyIDBAqhnlkAHqvPRwdbX',225:'66Y8VrfvHnwJSk2ahGOr32',
 226:'4VykjLwkyfKMZVLrJJVrYh',227:'16r4B64NuzQiI8sdY9CYO7',228:'5WGGkUyTDomzIAdj9Vz6v9',229:'1vz94WpXDVYIEGja8cjFNa',230:'3ywVzrwMQ3Kq43N9zBdBQm',
 231:'08ATX1GLcytmXFdeZKQso0',232:'4YYW1Q1okABRHpSj6LMtEO',233:'3mvdHEE56sgj1NtTnTF8qK',234:'1Qo7LnY9VsqcQ75YbO8JEs',235:'7zP0OZQPJjL4EDMlNbUEdL',
 236:'5t4FHrIAHI8nolSAOBRgPp',237:'3EfpOFKjotrMQTFTnxrXaB',238:'4Yw5uS8at8GkWmH2gZmLY0',239:'0vypdDHTQsoVmVu8OgXEly',240:'7ojNQckNp7Tj2BkLJCiiUL',
 241:'32NQ56VZDTXSH3SMv4XSGN',242:'0TDBkNvMV4M4VUaDtQit7i',243:'3iRW4cZOM90lX9Rtc2Qglh',244:'6DlSUW5gmq6Byc3osKDJ2p',245:'2l3QxNo4QubBNmVKxLeum0',
 246:'5PZjHIwD1BiwgYC4K8wV0u',247:'2ielHSukqq7jbVWHgcQGyr',248:'1IY4BdLApVlVa8xid34zJm',249:'252LyflX4wUeISSzgL392F',250:'5SqbMEyAt8332ISGiLX0St',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {223: 1, 225: 1, 241: 2}
RENAME = {'The Clap (Live)': 'The Clap', 'Starship Trooper: A. Life Seeker, B. Disillusion, C. Würm': 'Starship Trooper',
          "I've Seen All Good People: A. Your Move, B. All Good People": "I've Seen All Good People", '32-02': '32-20', 'Bang a Gong (Get It On)': 'Get It On', 'Freddie\'s Dead (Theme from "Superfly")': "Freddie's Dead",
          'Tarkus: I. Eruption / II. Stones of Years / III. Iconoclast / IV. Mass / V. Manticore / VI. Battlefield / VII. Aquatarkus': 'Tarkus'}
KEEP_FIRST = {223: 7, 227: 12}   # drop bonus tracks / outtakes after the original album
DROP = {}         # songs added on later editions, not on the original LP
# Albums the automatic search got wrong, filled in by hand.
MANUAL = {
 # no track list was found (the catalog title is in brackets); the band's official album playlist
 224: {'youtubePlaylist': 'PLMmd10177iHuglVcy9blANFopTddKtSV7',
       'names': ['Black Dog', 'Rock and Roll', 'The Battle of Evermore', 'Stairway to Heaven', 'Misty Mountain Hop', 'Four Sticks', 'Going to California', 'When the Levee Breaks'],
       'durations': ['4:55', '3:40', '5:52', '8:02', '4:38', '4:44', '3:31', '7:07']},
 # the track list found belonged to a later expanded edition; the LP has three pieces
 249: {'youtubePlaylist': 'PLbIN9DHtOfK-uFl66kKxIw90fuRzPqxG6',
       'names': ['Close to the Edge', 'And You and I', 'Siberian Khatru'], 'durations': ['18:43', '10:09', '8:57']},
 # no playlist of this album was found; one full-album video with four chapters
 232: {'fullAlbumVideo': '20UbO62UJUg', 'names': ["Let's Start", "Black Man's Cry", 'Ye Ye De Smell', 'Egbe Mi O (Carry Me I Want to Die)'],
       'starts': [0, 467, 1165, 1962], 'durations': ['7:47', '11:38', '13:17', '12:40']},
}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/201-250.discovered.json'))
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
json.dump(out, open('tools/batches/201-250.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
