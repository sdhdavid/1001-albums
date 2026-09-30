"""Build tools/batches/401-450.json from the discovery output (tools/batches/401-450.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_401_450.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_401_450 import STORIES

SPOTIFY = {
 401:'5b533EfxPpiYtk0MmilEJO', 402:'4hIp9tRsRa562HTFSlzUKX', 403:'7Lwhf0KIxKSRnwyrQqhp7H', 404:'5spnOKcCnsfRsIBtRrRqGV', 405:'0PEMxmj2m6pLKoqYR0WtzW',
 406:'3WcKYFYncNK0oKBOcurAE1', 407:'57l34nudIa2wEI2q3zdTVo', 408:'4KT6G8fj8EEIfsyr75hbgc', 409:'0QLGc9YYoHIKpnprRURTdm', 410:'5Mbw7VLJdYGYbwWBUbPPgi',
 411:'5XgLc3jXWJOXrg1YnbsdxZ', 412:'39jsLMRmrTpfdq2vE4TCUe', 413:'09IXN25ZAfR272CVFcdeqh', 414:'7DdEbYFPKTZ8KB4z6L4UnQ', 415:'7wOJ9RTQr05ytqROWtTPzy',
 416:'4tJPWT4r4FSKwy784Qs1Fq', 417:'1u2Qni8cVRptDTaA00fmBC', 418:'4dKdxly4ji1vfl7sEYuqBe', 419:'4DJC1f7Fb0yX86qlw9aqsF', 420:'1iVf41qWHZsAk9DwY43WnV',
 421:'5Sdzd5jW8HGJH7bINTZovR', 422:'0YvlThJzVtCMqTpwPMxAkI', 423:'7nZ0F572fluFD4tQCFf3z7', 424:'063f8Ej8rLVTz9KkjQKEMa', 425:'3uMr78kOScjc6eLHMYcVl4',
 426:'10v912xgTZbjAtYfyKWJCS', 427:'4GSidaoqyGNwaG5mNKmuLT', 428:'56GUb1eplzyqk2gcy9dviI', 429:'1dwzhoYlTd5ZgPygszllwo', 430:'3eXETk1esvZPRluDCWH3GN',
 431:'5giL5FOmVBQo9DBDcH1MS3', 432:'5fMAuIxI96lqdSPqUGwlXd', 433:'6lf5L8JM1TomSM6mfjZ9I5', 434:'4OLsnJQPTX0S6lODXw1MqC', 435:'5Dgqy4bBg09Rdw7CQM545s',
 436:'1UFBJkKiBe3Lzjr307UhuU', 437:'5tXec5CMljyjidi4lHNptm', 438:'6FCzvataOZh68j8OKzOt9a', 439:'0QOBJYviordwqHAgv5g9m3', 440:'3H0cWLh4X4x5TB8TTkE3LE',
 441:'4iNtNt45SY3Ieb5FR8qt3Q', 442:'3ZAHIjLdPoEmHGMCHtoMpq', 443:'2QqocFdpBkxOBLcIRo6UuJ', 444:'1UMvR1rwj9EzLnbj4L6Zoy', 445:'0f6TFLr9pkfCfbK4ChYiYi',
 446:'6b6FYoisWvkLKxF2JDjm1j', 447:'5Dbax7G8SWrP9xyzkOvy2F', 448:'7HoqZkuUQEE12tl0ByOSsh', 449:'2ZytN2cY4Zjrr9ukb2rqTP', 450:'1lvAASyHZrOQ04lowYjWEC',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
RENAME = {'Tubular Bells, Pt. I': 'Tubular Bells, Part One', 'Tubular Bells, Pt. II': 'Tubular Bells, Part Two',
          'That Lady, Parts 1 & 2': 'That Lady', 'Speak to Me / Breathe in the Air': 'Speak to Me / Breathe',
          'Rock and Roll P***y': 'Rock and Roll Pussy', 'Cars and Girls': '(I Live for) Cars and Girls',
          'Shine On You Crazy Diamond, Pts. 1-5': 'Shine On You Crazy Diamond (Parts I-V)',
          'Shine On You Crazy Diamond, Pts. 6-9': 'Shine On You Crazy Diamond (Parts VI-IX)', 'Xl-30': 'XL-30', 'Alife': 'Alifie', 'Sai dessa': 'Sai Dessa', '2112: Overture / The Temples Of Syrinx / Discovery / Presentation / Oracle / Soliloquy / Grand Finale': '2112',
          'Ponta de Lanca Africano': 'Ponta de Lança Africano (Umbabarauma)', 'Oxygène, Pt. 1': 'Oxygène, Pt. I', 'Oxygène, Pt. 2': 'Oxygène, Pt. II',
          'Oxygène, Pt. 3': 'Oxygène, Pt. III', 'Oxygène, Pt. 4': 'Oxygène, Pt. IV', 'Oxygène, Pt. 5': 'Oxygène, Pt. V', 'Oxygène, Pt. 6': 'Oxygène, Pt. VI',
          'The Blues Had a Baby and They Named It Rock and Roll (#2)': 'The Blues Had a Baby and They Named It Rock and Roll',
          'Down in the Sewer: (a) Falling / (b) Down in the Sewer / (c) Trying to Get Out Again / (d) Rats Rally': 'Down in the Sewer',
          'I Want to Be Loved': 'I Want to Be Loved', 'Modern Dance': 'The Modern Dance', 'Nova estação': 'Nova Estação', 'O medo de amar é o medo de ser livre': 'O Medo de Amar É o Medo de Ser Livre',
          'Aprendendo a jogar': 'Aprendendo a Jogar', 'Só Deus é quem sabe': 'Só Deus É Quem Sabe', 'O trem azul': 'O Trem Azul',
          'Vento de maio (Música Incidental: Um Girassol Da Cor Do Seu Cabelo)': 'Vento de Maio', 'Calcanhar de Aquilles': 'Calcanhar de Aquiles', 'Köln, January 24, 1975, Pt. I': 'Part I', 'Köln, January 24, 1975, Pt. II A': 'Part IIa',
          'Köln, January 24, 1975, Pt. II B': 'Part IIb', 'Köln, January 24, 1975, Pt. II C': 'Part IIc', 'H₂Ogate Blues': 'H2Ogate Blues'}
KEEP_FIRST = {}
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

disc = json.load(open('tools/batches/401-450.discovered.json'))
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
json.dump(out, open('tools/batches/401-450.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
