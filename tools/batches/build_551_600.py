"""Build tools/batches/551-600.json from the discovery output (tools/batches/551-600.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_551_600.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_551_600 import STORIES

SPOTIFY = {
 551:'0Vfz3nzrhiy2JBVmjeKQCP', 552:'1a0E0UI4Qf86gjgF8Jfzs3', 553:'39ug65qdY5NvkiK2UjYqVe', 554:'5cboZA5AxA9fc6F1gp818q', 555:'5uy9pvgfvVAlZnegK6fPLU',
 556:'5BWl0bB1q0TqyFmkBEupZy', 557:'0lQpEZbn64sAOvI8tGayQe', 558:'5bbb7E51zaDCuD85uLyFkK', 559:'0PnzJO3D4i85ALVJPaDpru', 560:'0fn2SPJjYECJG3BNvNOd9f',
 561:'5SP47w4PiPjqLsbPzKbxXT', 562:'4STlruvvwisFADIjNE3Jau', 563:'19aNtdJs4pkuYDWYDEAGUf', 564:'35V5TZ6drqYeYOoXY1Mp0i', 565:'03MEgGTQq5Vlgz9RsKd6CY',
 566:'11oR0ZuqB3ucZwb5TGbZxb', 567:'1bKbnWJHS0AiikWAxM94eE', 568:'2tK5echafDK5obMXduEvKq', 569:'6xBLmLS1bD7n8Cb9yBpMX3', 570:'0jMxhxH5JW3aUdVoeRKjWl',
 571:'1Xtzjp8COFI0V82CLiHvia', 572:'4PqSk2iBHnsYQK0ecXjS9k', 573:'0kBfgEilUFCMIQY5IOjG4t', 574:'5Bf5U1Zw9gsJh6bWaM2VY2', 575:'279yIkDusPSYNWUMiZGIsE',
 576:'5V2UTN2mkQkn5GnoVkmIUI', 577:'4WoQ94qzwQj28n3nlSOVLB', 578:'0PanG8trSzqFIX7pZmCVFG', 579:'3FVsJiQMI7dp0RfTBdWtMW', 580:'3bEnaGjQRqfoqNkAQtO1Uy',
 581:'6xw5oNhHoLltpXCFONNnqs', 582:'15Ob3oBedxes2SqsrQbVuY', 583:'38PSQu2ndRIMJSoZwho17z', 584:'0sozfhkNTSDCVxhicblcsq', 585:'5vZVl8vM576VyIrksnvAph',
 586:'7LpjAJON4CNX6PmY9SICs3', 587:'1uPjtjcaOwsxwLO7DzwQh2', 588:'1ja2qzCrh6bZykcojbZs82', 589:'1Sl9IDnFbR4c5nQnwFn0GV', 590:'1XsXHctYSQNyAd9BANCk2B',
 591:'2Ah76CkWPKnhhuwQT8DcHQ', 592:'2ybu0EJFA2jgoOFy64LKf0', 593:'5Wcb09PdAwHCKGAwBvnK04', 594:'4imgqeBHbJPcoU57twdgTk', 595:'1By3l3EcAlNZXJvSOHFJ98',
 596:'0YaG8TgKhZGxqEqMC913FY', 597:'4C0wWqAGX8EegAkSQJXjtu', 598:'7jfexk2w5aDI25njkN0UGg', 599:'5JKFiC2WVi9HtvJEm8CUB8', 600:'7KLJM2KoVkWIaOpLzfyGHh',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
# #553: iTunes has no lengths, so they come from the hand-picked playlist (seconds)
LENGTHS_FROM_PLAYLIST = {553: 2}
RENAME = {'Psycho Cupid - Danceband On the Edge of Time': 'Psycho Cupid', 'Marlene On the Wall': 'Marlene on the Wall', 'The Sick Bed of Cuchulainn': 'The Sick Bed of Cúchulainn',
          'Wood Beez': 'Wood Beez (Pray Like Aretha Franklin)', 'Fight for Your Right': '(You Gotta) Fight for Your Right (To Party!)', 'Honey Are You Straight Or Are You Blind': 'Honey, Are You Straight or Are You Blind?',
          'The Last Of The True Believers': 'The Last of the True Believers', 'Love At The Five & Dime': 'Love at the Five and Dime', 'More Than A Whisper': 'More Than a Whisper',
          'Banks Of The Pontchartrain': 'Banks of the Pontchartrain', "Lookin' For The Time (Workin' Girl)": "Lookin' for the Time (Workin' Girl)", 'One Of These Days': 'One of These Days',
          "Love's Found A Shoulder": "Love's Found a Shoulder", 'Fly By Night': 'Fly by Night', 'The Wing & The Wheel': 'The Wing and the Wheel', 'SludgeFeast': 'Sludgefeast',
          'I Want Your Sex, Pts. 1 & 2': 'I Want Your Sex (Parts 1 & 2)', 'La Muerta del Angel': 'La Muerte del Angel', 'Reminisce': 'Reminisce (Part Two)', 'Cables (live)': 'Cables',
          'Back of Love': 'The Back of Love', 'Rene and Georgette Magritte with Their Dog After the War': 'René and Georgette Magritte with Their Dog After the War', "Sucker M.C.'s (Krush-Groove 1)": "Sucker M.C.'s", 'Hollis Crew (Krush-Groove 2)': 'Hollis Crew', 'Weight - Lifting Lulu': 'Weight-Lifting Lulu', 'Smash It Up (Pts. 1 & 2)': 'Smash It Up (Parts 1 & 2)', 'Another Brick In the Wall, Pt. 1': 'Another Brick in the Wall, Part 1', 'Another Brick In the Wall, Pt. 2': 'Another Brick in the Wall, Part 2', 'Another Brick In the Wall, Pt. 3': 'Another Brick in the Wall, Part 3', 'Love Like Anthrax': 'Anthrax', 'Tubular Bells, Pt. I': 'Tubular Bells, Part One', 'Tubular Bells, Pt. II': 'Tubular Bells, Part Two',
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
KEEP_FIRST = {586: 9, 594: 9}   # bonus tracks cut (#586 Just Like Heaven, #594 A Last Request, CD only)
DROP = {557: [5], 579: [14]}   # not on the original UK LP: #557 How Soon Is Now?, #579 Dear God
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
BY_PLAYLIST = {584}   # #584: original LP order (In Your Eyes on side two), not the 2002 order   # albums with no fixed track order: follow the playlist
SKIP = set()   # albums to hold back (none)
# Albums the automatic search got wrong, filled in by hand.
MANUAL = {}
# Albums with no full playlist on YouTube: one video per song (n -> [(name, videoId, length)]), found by web search.
VIDEOS = {}

def clean(s):
    s = re.sub(r'\s*\(including [^)]*\)', '', s)
    s = re.sub(r'\s*\(with [^)]*\)', '', s)
    s = re.sub(r'\s*[\(\[]feat\.[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s*[\(\[][^)\]]*(remaster|mono|stereo|version|edit|mix|bonus|single|live|\b(19|20)\d\d\b)[^)\]]*[\)\]]', '', s, flags=re.I)
    s = re.sub(r'\s+-\s+(\d{4}\s+)?(remaster|mono|stereo|single|live).*$', '', s, flags=re.I)
    s = s.strip()
    return RENAME.get(s, s)

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

disc = json.load(open('tools/batches/551-600.discovered.json'))
try: disc.update(json.load(open('tools/batches/551-600.fix.discovered.json')))   # second pass for a few albums
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
    if not SPOTIFY[n]: print('no Spotify id yet', n); continue
    assert len(SPOTIFY[n]) == 22
    rec = {'n': n, 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus, 'story': st['story'], 'picks': picks}
    rec['durations'] = durs if not extra else MANUAL[n]['durations']
    if n not in VIDEOS: rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/551-600.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
