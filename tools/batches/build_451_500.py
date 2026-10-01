"""Build tools/batches/451-500.json from the discovery output (tools/batches/451-500.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_451_500.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_451_500 import STORIES

SPOTIFY = {
 451:'6wHjdKs7VVPVcqaHRzwqJt', 452:'7kHtInr7Es2tPk5QJO6y6c', 453:'3rCtKLmTi3yf2kRbolwWaV', 454:'5iawHcgRuKL5HMRbigdvWC', 455:'6mUdeDZCsExyJLMdAfDuwh',
 456:'6S9rbimtTmC0v6UBWqSpay', 457:'6tg1dxmyylhE7oFXcnK0P6', 458:'53nMBxHhUEpd11QWaNf2tq', 459:'3icMmcNKFULWPSodX8jDEb', 460:'2KWHRfKSRpgsxNGIl2nQva',
 461:'44aVVevMGKS4q6nWXbELpP', 462:'58Uj0mEB9TJcYcRFvj5rBX', 463:'3IPjvl1nQ20Xaq9MUT4SCl', 464:'5bqtZRbUZUxUps8mrO9tGY', 465:'0Z8yFLZUW9Xlh1MZr26HVd',
 466:'1JvXxLsm0PxlGH4LXzqMGq', 467:'4kT3ewGWBRAOlocyVp03bm', 468:'3DNeMApEMCo4IDXNMYnlFi', 469:'22Etsne83iSDw5anZLbxMH', 470:'43SBfe6XWr2AkSLLqphSqJ',
 471:None, 472:'0rfNBDAG7tzO4Sw5mO3xJE', 473:'6u9JszNMhfmzpwwUr7DHy5', 474:'3xz9b9m7yn3WxYxrBVNnNy', 475:'2sdeUV587HpFaDmr7eyO5r',
 476:'28Eu96aUziJU9iemBomWRs', 477:'5ESlb1RVMYfhixc1x8JRts', 478:'5OEum65e1HMGX51Ifu51Wb', 479:'37SbrHnaAE21bYdSnMSoaL', 480:'1L4HE00En7eNK74voVZums',
 481:'3iWhyQjMh52eSqFdLUfj5j', 482:'5GqXU5mjDRXWZMuSLqGKHq', 483:'4yPDBhXVhGYMaDsHA8POjQ', 484:'33aOaSSSamZAHI0y9gZ0qW', 485:'34aFnrFRBlErcbU6moRZR3',
 486:'6a3a1We83O9GOK6S4EyqiP', 487:'19m9G8cS0IbK7TBe3Sfvrw', 488:'3ls7tE9D2SIvjTmRuEtsQY', 489:'14LxwpAPXrY2RrfZoiAIZu', 490:'378ahhobt690RQEsyD8DaK',
 491:'7wJTATARITosmqhrbHUm7k', 492:'5WKUL88usO5Y8cfbh2EQdu', 493:'4tYzvNBYBh3vFbLdFMplWT', 494:'2VaiKCk6DvqMfPeFNcykeR', 495:'1vkql5n4Vb9j5XG3yxOU66',
 496:'34MHuXONazzgSxI0cThpAg', 497:'4dEczweFPXeLMMVD1zIdi7', 498:None, 499:'5O5mnof890aQ1Wn42H5pCW', 500:'0QNluXFRHFyRVDiBHXmstK',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {481: 1}   # #481: the playlist in album order
RENAME = {'Weight - Lifting Lulu': 'Weight-Lifting Lulu', 'Smash It Up (Pts. 1 & 2)': 'Smash It Up (Parts 1 & 2)', 'Another Brick In the Wall, Pt. 1': 'Another Brick in the Wall, Part 1', 'Another Brick In the Wall, Pt. 2': 'Another Brick in the Wall, Part 2', 'Another Brick In the Wall, Pt. 3': 'Another Brick in the Wall, Part 3', 'Love Like Anthrax': 'Anthrax', 'Tubular Bells, Pt. I': 'Tubular Bells, Part One', 'Tubular Bells, Pt. II': 'Tubular Bells, Part Two',
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
          'Köln, January 24, 1975, Pt. II B': 'Part IIb', 'Köln, January 24, 1975, Pt. II C': 'Part IIc', 'H₂Ogate Blues': 'H2Ogate Blues',
          'She Is Like Heroin to Me': "She's Like Heroin to Me", 'Abstieg and Zerfall': 'Abstieg & Zerfall', 'Schmerzen hören': 'Hören mit Schmerzen',
          'Jet`m': "Jet'm", 'California über alles': 'California Über Alles', 'I was a Teenage Werewolf': 'I Was a Teenage Werewolf',
          'Rock On the Moon': 'Rock on the Moon', 'Steh Auf Berlin': 'Steh auf Berlin', 'Draussen Ist Feindlich': 'Draußen ist feindlich', 'The Queen of Eyes': 'Queen of Eyes', 'Kick in the Eye 2': 'Kick in the Eye', 'Of Lillies and Remains': 'Of Lilies and Remains'}
KEEP_FIRST = {453: 12, 456: 13, 477: 13, 480: 11, 490: 10, 497: 7}   # bonus tracks cut (#453 the UK LP)
DROP = {452: [12]}         # songs added on later editions, not on the original LP (#452 Gangsters, US edition)
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
BY_PLAYLIST = set()   # albums with no fixed track order: follow the playlist
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

disc = json.load(open('tools/batches/451-500.discovered.json'))
try: disc.update(json.load(open('tools/batches/451-500.fix.discovered.json')))   # second pass for a few albums
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
    if n in MANUAL and not extra:
        yt = {'id': MANUAL[n]['youtubePlaylist']}; names = MANUAL[n]['names']; pos = list(range(len(names))); durs = MANUAL[n]['durations']
    pos = list(pos)
    for i, p in POSITION.get(n, {}).items(): pos[i] = p
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
    st = STORIES[n]; tnames = [t[0] for t in tracks]
    picks = [list(p) for p in st['picks']]
    lookup = {norm(t): t for t in tnames}
    for p in picks:
        assert norm(p[0]) in lookup, (n, p[0], tnames)
        p[0] = lookup[norm(p[0])]   # use the track's exact spelling
    focus = sorted({tnames.index(name) for name, _ in picks})
    if not SPOTIFY[n]: print('no Spotify id yet', n); continue
    assert len(SPOTIFY[n]) == 22
    rec = {'n': n, 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus, 'story': st['story'], 'picks': picks}
    rec['durations'] = durs if not extra else MANUAL[n]['durations']
    rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/451-500.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
