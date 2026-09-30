"""Build tools/batches/351-400.json from the discovery output (tools/batches/351-400.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_351_400.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_351_400 import STORIES

SPOTIFY = {
 351:'3Z0qQc09rmk4JYtIaxEx2J', 352:'2QLp07RO6anZHmtcKTEvSC', 353:'1yW5dI0y4ckpC2646nakvc', 354:'1V6a99EbTTIegOhWoPxYI9', 355:'2oPeCzPDtjkm2Ux5r7edAb',
 356:'6qMn1rdskwDEk58j0teEgJ', 357:'4g9wGKoKnABAV40zFgvquR', 358:'3BsE4yVwIOxM38hDnzrMlx', 359:'4ldiyfqRvKiIasHHuDftuP', 360:'7qqcE5xC5YISPxoC4Q302Z',
 361:'372smdctC8hNczUfZG8phL', 362:'6qF91BDNaJY4PI0mSwYv8L', 363:'7u31R0chlCbztAqHlEEQM6', 364:'2zZ7ZXZABoDDxJS1ZxfKMI', 365:'7aXRSPsEDgXGxFGY235DYz',
 366:'6YUCc2RiXcEKS9ibuZxjt0', 367:'1SJZWjxsSbKvSycxDfnwcN', 368:'6lU1MDxi3TqhKnYNQm555u', 369:'0HHRIVjvBcnTepfeRVgS2f', 370:'3IILMjMMnoN2sKzgesX8KV',
 371:'2mBbV0Ad6B4ydHMZlzAY7S', 372:'3usnShwygMXVZB4IV5dwnU', 373:'2M9F2yYsUvqiBPwUGeNvn1', 374:'2xk6vjune34Ym0oUumMeaC', 375:'2h6cfDyixzatw4bKFshozy',
 376:'7LAgu2DG7DfVTUT9LJZ9KY', 377:'2de6LD7eOW8zrlorbS28na', 378:'5Zxv8bCtxjz11jjypNdkEa', 379:'2XypKUg8tyn0ZRxxJwrxnP', 380:'78WlsSQKrX4suYf909Fcrm',
 381:'0r7o2FeARRr23EZ0TJ0a8S', 382:'1bt6q2SruMsBtcerNVtpZB', 383:'4I5zzKYd2SKDgZ9DRf5LVk', 384:'55d1108rwedIaZkwpQB2v6', 385:'46kw5FsFdJhNRL8wfHM9Bp',
 386:'7vCU9jvSESwQNQr6SB9JyS', 387:'5YIrWYj4msO7JMCPj5jr2M', 388:'630o1rKTDsLeIPreOY1jqP', 389:'6mvI80w5r78niBmwtu7RF9', 390:'1aucGNKimhgARC7iO2xLt2',
 391:'2jnV6ytZOmt71iEC5xHEYz', 392:'0yLDsFkaUbkT2EZFL13HTi', 393:'6ggO3YVhyonYuFWUPBRyIv', 394:'3zGgLRMaApg4t8GUhG9X8W', 395:'3eyz60xEK5dGEeZF1JJSi9',
 396:'4M6s2jbhKWEcOdXZ8WiHts', 397:'3NOxICud3CE6svBnR9WqC7', 398:'64CW8fAAWtgoVkbQ1MyWrS', 399:'4MNYrqeS506fw5RqInQzXP', 400:'0mUFefHSr0Ovi9vNcUGppt',
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
KEEP_FIRST = {354: 10, 390: 12, 397: 9, 399: 10}   # bonus tracks cut; #390: UK LP (no Watching the Detectives)
DROP = {}         # songs added on later editions, not on the original LP
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
SKIP = {364, 376, 400}   # waiting for hand-found playlists / UK track lists
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

disc = json.load(open('tools/batches/351-400.discovered.json'))
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
json.dump(out, open('tools/batches/351-400.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
