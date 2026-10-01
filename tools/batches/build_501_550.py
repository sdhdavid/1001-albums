"""Build tools/batches/501-550.json from the discovery output (tools/batches/501-550.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_501_550.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_501_550 import STORIES

SPOTIFY = {
 501:'1m8ybrw0umxg8FbBC3pH7K', 502:'0VTxtFfoBxHDMFjDuVLmTh', 503:'5cOS6szqlcoqmiSoVTqqe8', 504:'27EpLLPy10aNZ1VfXioW2x', 505:'59dmyw7CgPluQ6PlTmn7ik',
 506:'0kyKdRPKFDn8cATzWkFAsO', 507:'1x6guHfwvOGsIQgRK5v5p1', 508:'1JfIRGXDOQFlP1OGWzmvL5', 509:'5tcHEZse8nH7FiSVcriInN', 510:'6yskFQZNlLYhkchAxELHi6',
 511:'25SKfbYtNpdoWI2z3mOhUI', 512:'6UXvg5jZjihUbG7OvhWLHb', 513:'0vndiSM8xxlb8CQFOMMO9h', 514:'2G9onFLGqlMJd1ThYf0vIB', 515:None,
 516:'5wRCRA0W8B6oYJbbKwtH8M', 517:'4Mw9Gcu1LT7JaipXdwrq1Q', 518:'1BsN7LvFmxvfUaaUj5Bskr', 519:'51hrKjSvIX69tl1g13R0hI', 520:'2UrSPDjccATKgu4CIxu8IV',
 521:'57ILJ0HfN2VCtFSUCa1Ull', 522:'1FvdZ1oizXwF9bxogujoF0', 523:'4qs8dBF1Avnt97zEMU9nxp', 524:None, 525:'4KW6YVbF8E3kexYcl0k4IK',
 526:'4RMZ9x6tYqO2R5ioa0zAPw', 527:'4EG6O0FseOD53hZ4B2CosR', 528:'7yDxJXFPl88Dt9kBo0dDD6', 529:'5JFZRr2UTCkcuT5LSXSbJ9', 530:'51NPMfa9QfxsYtqzcB2VfY',
 531:'6shkK6FfpYBwBWwXMm4dsm', 532:None, 533:'1yypMM9PUTFVLAgLn3GJ29', 534:'7pBPB9vwqCMLKNmUCK4k62', 535:'0w3NDo617KZktU7gtIdxTR',
 536:'2g39bJJlAVqLkCiwvlcM95', 537:'2umoqwMrmjBBPeaqgYu6J9', 538:'2sOLW5TSgXiLZBacdHxO6m', 539:'6tF9nPl6x7ACsKZ8alL1he', 540:'0grIG45v0JWy5N46z4As0B',
 541:'43jEYhOEU6eWL51lk4l3M7', 542:'5viZ5HyYtV0wafK7DoXmgF', 543:'2RtAWChS6XRsqiz28hpB1Q', 544:'5bRDrsAfi4j65Zbf3LQE6E', 545:'47VqWjxJe2AiTIIeyeWlPX',
 546:'2QcPIOpOR2sxOqKVXODAhx', 547:'5EQkSknw8twG8oiukc55la', 548:'1ER3B6zev5JEAaqhnyyfbf', 549:'7y7459SFZReE5Wec4hejv5', 550:'15J400U0rEpgE64UQgtvLs',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
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
KEEP_FIRST = {}   # bonus tracks cut
DROP = {}         # songs added on later editions, not on the original LP
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

disc = json.load(open('tools/batches/501-550.discovered.json'))
try: disc.update(json.load(open('tools/batches/501-550.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/501-550.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
