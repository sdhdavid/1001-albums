"""Build tools/batches/952-1001.json, the last batch, from the discovery output (tools/batches/952-1001.discovered.json,
run before the White Album was inserted, so its keys were moved up by one; it also gives the track lengths), the second
pass in 952-1001.fix.discovered.json (which also has #134, the White Album), the Spotify ids below (found by web
search, unverified) and the stories in tools/stories_952_1001.py and tools/stories_134.py.  Then add_albums.py writes
the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_952_1001 import STORIES
from stories_134 import STORIES as WHITE
STORIES.update(WHITE)

SPOTIFY = {
 134:'1klALx0u4AavZNEvC4LrTL', 952:'5Ua1WwH7wtVGxp9N3AWgow', 953:'4HihJAJjF6hSVoh318zLu9', 954:'1LY17BAs6sqh3EZeLXQvfZ', 955:'25vTmWaczSrAsoe3bBjgjx',
 956:'2USigX9DhGuAini71XZEEK', 957:'1kLGYdCm5cLFjF5NXv0INo', 958:'69Wr9DvWfIJRTi5NUGeVTn', 959:'6QPkyl04rXwTGlGlcYaRoW', 960:'1eAyvj2rLzEfgTCzOP93qc',
 961:'6dO1bXWSqKofUUsgygq0bb', 962:'5mzoI3VH0ZWk1pLFR6RoYy', 963:'2rWBGF3pKx8Jla9VYMQ8Xc', 964:'1SohYJmnNVgYDD1KadV5An', 965:'6VUdJVyGk3k9vMgHzZ43SW',
 966:'6D9urpsOWWKtYvF6PaorGE', 967:'4YTIXKkNoBKiGK8lzexYCS', 968:'6RCKpPBWCh9WSchJHH2gmC', 969:'3fHFalxlzXF44vupfXJd0R', 970:'51aULewn2y20Ud0MIQONRg',
 971:'1UsmQ3bpJTyK6ygoOOjG1r', 972:'2PiSkRUZWhvID1Cf3ppls4', 973:'0CA2EVHhRPR5VPV78KZw89', 974:'4DsHBZ9Cw8D5cE2gmjoaXu', 975:'4oOhV44kug5ZR6crjk7tqS',
 976:'0n1CrR5kCz5aAUH565cLDu', 977:'4mXL7oTIbIqAJPTQOBEQXb', 978:'1OBctVHKbHrQ2t5oCeHNtN', 979:'2wdHHEDHe9dw71xVl1EgJZ', 980:'4Uc6YCjpfyjj02rZfg2EUv',
 981:'63Eji2cNg0vH9sYqxg5iHI', 982:'0aGwrXjKIfAMlj1vBYLtnR', 983:'2s6AIr1sL5P0NAFzqd0zsW', 984:'0Dn05ZrhYlqEXIfbdkNqQS', 985:'0vi5ePiEHrGZJF7QhnDW2z',
 986:'4MwR8zCF5m9JH8t3LcHqas', 987:'3lDca6e9MuyFAhoaR6GjlW', 988:'5pgaVcKREhdQ3OI7ZvP9tv', 989:'', 990:'3ff2p3LnR6V7m6BinwhNaQ',
 991:'0wdleLMeNmGUHChsmx9svt', 992:'76XQSGpf3sPBgnAX0iVEr1', 993:'', 994:'365ETCJBUmEWroc4UGBS1u', 995:'5lHKuIClr94hUV3xP1joHm',
 996:'0FLs42SkAlPHa6Y6YwVne4', 997:'6SODLjPAWEhIlsb9Ewt7ez', 998:'7eJbM7ZdGAFPLQfW53hllZ', 999:'0fsIwO8qESz53BkTMjBSd3', 1000:'3ZJhEfoNRh684uuv9VG9EC',
 1001:'3rHeq4F5wnaLBjNtuz7Yvh',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {963: 2, 979: 1}   # #963 the 13-track UK album; #979 the original 14 tracks in order
LENGTHS_FROM_PLAYLIST = {}
RAW = {'Work It (feat. 50 Cent) [Remix]': 'Work It (Remix)'}   # names fixed before clean()
RENAME = {'Quattro - World Drifts in': 'Quattro (World Drifts In)', 'Holy Roller Novocaine / Talihina Sky': 'Holy Roller Novocaine',
          'Modern Romance / Poor Song': 'Modern Romance', 'Galang / M.I.A.': 'Galang', 'Intro / Stronger Than Me': 'Stronger Than Me',
          'Who Is It (Carry My Joy On the Left, Carry My Pain On the Right)': 'Who Is It'}
KEEP_FIRST = {963: 13, 979: 14}   # deluxe / US bonus tracks cut
DROP = {957: {14, 15, 17}}   # #957 the silent tracks before the hidden song
POSITION = {957: {2: 2}, 981: {4: 4}}
SPLIT = {}
BY_PLAYLIST = set()
SKIP = set()
DURATIONS = {}
NO_SPOTIFY = set()
MANUAL = {}
VIDEOS = {}

def clean(s):
    if s in RAW: return RAW[s]
    s = re.sub(r' = [^\x00-\x7f].*$', '', s)   # #962 Japanese titles after the English ones
    s = re.sub(r'\.? \([^)]*\.\)$', '', s).rstrip('.') if re.search(r'\.\)$', s) else s   # #962 '2 + 2 = 5 (The Lukewarm.)'
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*\(with [^)]*\)', '', s)
    s = re.sub(r'\s*\[with [^\]]*\]', '', s)
    s = re.sub(r'\s*[\(\[]feat\.[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/952-1001.discovered.json'))
try: disc.update(json.load(open('tools/batches/952-1001.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/952-1001.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
