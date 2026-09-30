"""Build tools/batches/301-350.json from the discovery output (tools/batches/301-350.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_301_350.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_301_350 import STORIES

SPOTIFY = {
 301:'6DaTfshdfMQiM00Yw1CG3J', 302:'70sCoSN0qV6U4AqJ1wJkY0', 303:'5EvsfavFbWpzcg3VNLQEOF', 304:'1kda4McF274Jl5x3aOAmPJ', 305:'73cxqemPE6sVoCkwRuPU6E',
 306:'7Fmf1203WvpvvFOlNlCs6m', 307:'7ycOIZnRNdpnAEaHXZwah4', 308:'2akjxkzFolkeV72Yyv5KrM', 309:'6Cg1pPfnfFXlR1qH2H6NDL', 310:'59RclwjkzMJTJZNxrfGdLC',
 311:'7KRXWeJYBkyUmwOFTayiQk', 312:'7KOmuu3cbJQEQYGt3XmLmY', 313:'649U8ZM3frAE5Hq90KRhy6', 314:'3vCMmrJEx8CBtW4Hh0ehdl', 315:'4QiT8a3MqN8CnB5HnJIVjH',
 316:'2mEAmmRoZrvhBh1Vic03fZ', 317:'3Y21G2WWUrhJM95rdIC9SS', 318:'3w5Hok05AFjCLy269xXM7e', 319:'4AB1Ni41i1YgE1snxb0b6r', 320:'0bHiuso3WXpchgSlfX48uY',
 321:'2OUYJtDV6EmLkVyoHSuGIp', 322:'4UY90kcO4N9ZPBl4xPLvvU', 323:'2fUrVWDYASjthLVsVH53zP', 324:'72t34rHQENHfAK5kDLZjuG', 325:'6UQujMGmR5MbFsML9amCuN',
 326:'6uoeezh45SYEb8lcT8gDTY', 327:'5okHa1nb4z8WAQK27Y8yo8', 328:'5WvkGu24ipDKjOFzlXsDIy', 329:'0ovKDDAHiTwg4AEjKdgdWo', 330:'0I8vpSE1bSmysN2PhmHoQg',
 331:'6As5aOEQjfxLIChIB3fQRD', 332:'4tfBE4zd8PUieuUNF0zd03', 333:'2YsfYi8B9pEuts9qwa3TSN', 334:'43YIoHKSrEw2GJsWmhZIpu', 335:'04TlWfr3EnQE47HyNTBnex',
 336:'6TkmkfaLuRjdXIdGGOCGj6', 337:'3gUlFM3azK6ZIkKz1zK7Nj', 338:'09kBh6SUZteTaTo7aNctUr', 339:'4JXen1DO7SmgTd0sEWLRJd', 340:'5FTx6W84UUU14n29QV4saY',
 341:'4WD4pslu83FF6oMa1e19mF', 342:'0OeuSeP8wp8n8OuTqYb61C', 343:'0bCAjiUamIFqKJsekOYuRw', 344:'7HVoV2lgVsmuiHsjbbUJB4', 345:'5aEtg4dxdBk4pj6SJ3hNsM',
 346:'7suiCSZwt82LY5lLcqVi81', 347:'6hP2HgGSn9yC0SrCwjaUOM', 348:'6TLTd0P2CUI0Q29AQ1LyFi', 349:'1gIgG7phTZ9QAKNnDtD1OX', 350:'0MWrKayUshRuT8maG4ZAOU',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
RENAME = {'Tubular Bells, Pt. I': 'Tubular Bells, Part One', 'Tubular Bells, Pt. II': 'Tubular Bells, Part Two',
          'That Lady, Parts 1 & 2': 'That Lady', 'Speak to Me / Breathe in the Air': 'Speak to Me / Breathe',
          'Rock and Roll P***y': 'Rock and Roll Pussy'}
KEEP_FIRST = {}   # drop bonus tracks / outtakes after the original album
DROP = {}         # songs added on later editions, not on the original LP
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
SKIP = set()   # albums to hold back (none)
# Albums the automatic search got wrong, filled in by hand.
MANUAL = {}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*[\(\[]feat\.[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/301-350.discovered.json'))
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
    pos = yt['positions']; durs = list(r.get('durations') or [None] * len(names))
    if n in MANUAL and not extra:
        yt = {'id': MANUAL[n]['youtubePlaylist']}; names = MANUAL[n]['names']; pos = list(range(len(names))); durs = MANUAL[n]['durations']
    pos = list(pos)
    for i, p in POSITION.get(n, {}).items(): pos[i] = p
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
    if n in SPLIT:
        i, parts = SPLIT[n]
        names[i:i + 1] = [x[0] for x in parts]; fixed[i:i + 1] = [x[1] for x in parts]; durs[i:i + 1] = [x[2] for x in parts]
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
json.dump(out, open('tools/batches/301-350.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
