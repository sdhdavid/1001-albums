"""Build tools/batches/901-950.json from the discovery output (tools/batches/901-950.discovered.json, which
also gives the track lengths, plus the second pass in 901-950.fix.discovered.json), the Spotify ids below (found by
web search, unverified) and the stories in tools/stories_901_950.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_901_950 import STORIES

SPOTIFY = {
 901:'7LKQtdC6uWxqLzSbDonFij', 902:'33nyNThvBKPzS4NGdnWACf', 903:'2E1q8eohZZ1BUQ7Bq5WUIY', 904:'7hmZCaBzp6mVrelxW6Ckrn', 905:'0Z4pW2hvnmlTLWSGEozZ5n',
 906:'6Vp1b0Xsv8dbpBZfvkWSZG', 907:'', 908:'3hGM52SddRWwI4yatyZYmb', 909:'6GjwtEZcfenmOf6l18N7T7', 910:'7a5U0GPoAvT3gvEY66FRuN',
 911:'6PFPjumGRpZnBzqnDci6qJ', 912:'7DC0pE943VR5tAKIvQXHts', 913:'7y0QwysyQgSf9fyBFr6Q3x', 914:'0hBWhJEmVyNPG2Jq71CJXz', 915:'1BROiAW4CtstJEwqMds6Pu',
 916:'', 917:'5Vdh9NszWNh82xuzTBdNHO', 918:'1uWyROzREJNyGbLNvgABzm', 919:'', 920:'6t7956yu5zYf5A829XRiHC',
 921:'7Ce9F1Eof9r7u9tr702H5C', 922:'', 923:'1JgEmaIjznPkIEnzd4pxou', 924:'', 925:'',
 926:'3GBnNRYsxBfEeMSMmTpJ25', 927:'2tm3Ht61kqqRZtIYsBjxEj', 928:'6eIhOXRKIOXa71UBX7WIv5', 929:'3nyA5CLiEDw7jWJ8W4Vu4J', 930:'10cCtAAEpW4JAARBL4AvRH',
 931:'4LboNEcWQGTpRj9m5AxAod', 932:'1tYlx93ShW1M8TiAVDJSKc', 933:'2HcjLD0ButtKsQYqzoyOx9', 934:'2yNaksHgeMQM9Quse463b5', 935:'55FP2ypQcghszSqylyBRbp',
 936:'4j0BDfrtgQeMLA4RaSCch4', 937:'7rIhZOxiuEieQylkZt50TN', 938:'5ElnMKBlg21XKlqAynLH9x', 939:'54I5tDCMjnNVWSENHg8EDH', 940:'4WOZU9evfEO7eI6ICsoGN0',
 941:'2hR5HQzHdxgAiAjyvGqSI3', 942:'6g6WBTqT5gE4fAcwRljpjc', 943:'0f0nGqpgiu4z6wg0Mrcs8L', 944:'0rPtXOMN42nsLDiShvGamv', 945:'4hF66CtQgAPU6LzedAQi4V',
 946:'3zyTnmQF1J9B9z7excfhIa', 947:'3ul9GmXlTkmRMh3OciXxFR', 948:'0RHX9XECH8IVI3LNgWDpmQ', 949:'', 950:'2SuUATTRN6HEIrCTGH9Xes',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
LENGTHS_FROM_PLAYLIST = {}
RENAME = {"Sincere (Re-Cue'd)": 'Sincere', 'Re‐Hash': 'Re-Hash', '19‒2000': '19-2000', 'Ágaetis Byrjun': 'Ágætis byrjun', 'AMY': 'Amy',
          'Outro (Limp Bizkit/Chocolate Starfish And The Hot Dog Flavored Water)': 'Outro'}
KEEP_FIRST = {931: 17}   # #931 remix bonus tracks cut
DROP = {}
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

disc = json.load(open('tools/batches/901-950.discovered.json'))
try: disc.update(json.load(open('tools/batches/901-950.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/901-950.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
