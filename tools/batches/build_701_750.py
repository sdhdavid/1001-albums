"""Build tools/batches/701-750.json from the discovery output (tools/batches/701-750.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_701_750.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_701_750 import STORIES

SPOTIFY = {
 701:'5n52kyQKeUZs5ObZJejLQd', 702:'0pXHFRsNFwGmFv9zlNOoKC', 703:'5mAPk4qeNqVLtNydaWbWlf', 704:'0n5DeW2klYVOI1FnZz94d8', 705:'4M6vPZ4hQdOeH07D0JO2JQ',
 706:'', 707:'7o14zVcXSRk7clV6QCEdOD', 708:'5ZVnbpiFllDz7NkVOWb6WG', 709:'4QrhfVaznhrAPlM5xCKBPh', 710:'7uexJzLIjd4r6asSts0jWT',
 711:'0m3Xt8jqX3rCxX9mSfRRYN', 712:'2VyjjlQ1CxXwAqzVOWhggl', 713:'6pFFRqFbkh3XDBBuiFZqye', 714:'304ku3JS6QsFz75Jae9VKW', 715:'1FJ9XKn6aTTigSG5GTQaXZ',
 716:'1XHEQqyatYvfK5cEJfkPeK', 717:'2V5rhszUpCudPcb01zevOt', 718:'53mCB0cuaEBjsqokPSDhbw', 719:'5iLfT6G0VLP4WHUZTAYuEF', 720:'0Ge5MTUh5sUHmg61KWwYTQ',
 721:'4haSyDMB9N6R9BHBO6flMe', 722:'5blxyZRgkA735vO40p56MA', 723:'3vZQVeesxkzSRPtVLsrXKn', 724:'3NRQnGdFznbXtP8u2O4VKB', 725:'',
 726:'1pFUGy3ABpLRRE3oNMPbDb', 727:'71HM1CMYWeZzws8pyiEn46', 728:'1a3nQN9odOQ2Mr7ygYzI9I', 729:'2VNui22dikp6XEMdK8j8Xs', 730:'05wEDivrJlju67zESWvwDe',
 731:'3Y3yhP0knjINnXoYQoNb7S', 732:'2i7LOk6ywjKsc7uPzidTve', 733:'2cGYoviw1c8njoL5uN2nVg', 734:'16RbYsL8rkGIn02qZx6t2o', 735:'3kWHxGw4R5azuMU2FYxLfK',
 736:'', 737:'3DRlG4ezNna6WCi3uPGcDL', 738:'2GWIHTDjZJ3H5Cu6qooJhT', 739:'6c1xyQiasQXWYtKy70Vm8q', 740:'2l9jfB5bOcsR9VSbYbnSuE',
 741:'0IeANhddQskfJOk3UxzfB6', 742:'0pF9a14D0GUZoYGoFM90Ji', 743:'6isi41U6Wdh0JBglB26rKX', 744:'2fDJpBJhtloxzUENHlU9JB', 745:'',
 746:'244V9tFZNQ9tuN0cKNLQT5', 747:'3y4o8DtTqCFEFcJrI87nqu', 748:'0ujpvwNskNwgU6nb2krDZS', 749:'4ORsCg1x8p80RfW0vXA35N', 750:'',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {}
# #553: iTunes has no lengths, so they come from the hand-picked playlist (seconds)
LENGTHS_FROM_PLAYLIST = {}
RENAME = {'Release / Master/Slave': 'Release', 'Leben Heißt Leben': 'Leben heißt Leben', 'Geburt Einer Nation': 'Geburt einer Nation', 'Open Letter (To a Landord)': 'Open Letter (To a Landlord)',
          "Honky Tonk Angels' Medley: In the Evening (When the Sun Goes Down) / You Nearly Lose Your Mind / Blues Stay Away from Me": "Honky Tonk Angels' Medley",
          'Buenos Noches From a Lonely Room (She Wore Red Dresses)': 'Buenas Noches from a Lonely Room (She Wore Red Dresses)', 'Pig’s in Zen': 'Pigs in Zen',
          'Bye Bye Bad Man': 'Bye Bye Badman', 'Trilogy: a) The Wonder / B) Hyperstation / Z) Eliminator Jr.': 'Trilogy',
          'Psycho Cupid - Danceband On the Edge of Time': 'Psycho Cupid', 'Marlene On the Wall': 'Marlene on the Wall', 'The Sick Bed of Cuchulainn': 'The Sick Bed of Cúchulainn',
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
KEEP_FIRST = {}   # bonus tracks cut
DROP = {}   # songs not on the original LP
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
BY_PLAYLIST = set()
SKIP = set()
# Track lengths given by hand when discovery found none (#697 Ten, original CD)
DURATIONS = {}   # track lengths given by hand when discovery found none
NO_SPOTIFY = set()
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

disc = json.load(open('tools/batches/701-750.discovered.json'))
try: disc.update(json.load(open('tools/batches/701-750.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/701-750.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
