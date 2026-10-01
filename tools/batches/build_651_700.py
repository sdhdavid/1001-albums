"""Build tools/batches/651-700.json from the discovery output (tools/batches/651-700.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_651_700.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_651_700 import STORIES

SPOTIFY = {
 651:'1Wn9vV02wDeOvMJkaXfQJM', 652:'', 653:'1ZoXYdLYSn8brqkCILrJiH', 654:'4VWobt8JHr24Gq2qUZK7DB', 655:'0DQyTVcDhK9wm0f6RaErWO',
 656:'6wxpS5o0ty5CLqyH5fIRln', 657:'3ZnF1cPxlqB48RyLiecDnv', 658:'3n9Se2ErW2i2XQDES0o4Ya', 659:'34LxHI9x14qXUOS8AWRrYD', 660:'4OD3LU6001esAtFshDX46M',
 661:'5FCNQAQLw46CKYbv0n2H6V', 662:'0Y7qkJVZ06tS2GUCDptzyW', 663:'5lEphbceIgaK1XxWeSrC9E', 664:'4jpHKPCfCxyj8CiDEgjrpT', 665:'4sTAgYLZy5zwqR3kT1g0oh',
 666:'7rgHWQp1VqbhBjENV6ys8l', 667:'6QU6itggAYKtzjKOMqz8Ch', 668:'0HT8cy9nQThb3jKPwdGiLb', 669:'60cRh5MCFNOrFeQykKnDej', 670:'4e6ML9RBhDyyKTaTwbiRZv',
 671:'1qUuOtsaAWlD6D83AebzD0', 672:'3QKOefqeoWmK67Fv6ToyJa', 673:'0Gu0z7Agm0kSDhpX55dttF', 674:'4lGS8HxU3NYaQxfU0wx2r1', 675:'4YHIfZ986IFFp7OiO9D9Qt',
 676:'3AI5kAUjgNtZBwFRi6opDc', 677:'7acrrQejzV4ybWWTM8TmPf', 678:'6dfYmbgWeJCgqJhnR4TfKb', 679:'0QNPblZ1LIHTKja8pvHauW', 680:'0fV9DAddjwNZcmCP1Q8b01',
 681:'4Qt1ZvWZ3DoKDimDMesZd5', 682:'4G1YVElmzCn3QkVFQyuxkt', 683:'2Psn9p8O8w5MMoqAuM0PIU', 684:'0Nm5h20xUZB56nA7U2p6eN', 685:'2guirTSEqLizK7j9i1MTTZ',
 686:'1QSoW668F9DVj8Rk9azF7h', 687:'4tQSV1ZGpwlo3dBiTRuKvM', 688:'7GJ2y2we8EjzdgavH2Jt3S', 689:'05wcY4zcfSawCyoutTTxda', 690:'5hM61fBUA5OIMJUUuMrzyH',
 691:'2TXvjVOhfNjAYpRpODqmVb', 692:'1DCI2yWmV4UI7Aga71yx9B', 693:'08Bjvwbg1cFsFfXSdhG23I', 694:'4HJavRkzA8bYyGt7ireR4J', 695:'2OUT5225hEywJ5sKeOWvs1',
 696:'1p12OAWwudgMqfMzjMvl2a', 697:'39BXqF0ttK6P3Jx3BGjMP6', 698:'7e0mEjhM8D2x8E5c9H1oY3', 699:'0wZ4ANTdGJarksyTOD1cyl', 700:'2NnkLRaeX33d1Mn8ZLgTo8',
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
DROP = {652: [12]}   # #652: Stop This Crazy Thing listed twice
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
BY_PLAYLIST = set()
SKIP = set()
# Track lengths given by hand when discovery found none (#697 Ten, original CD)
DURATIONS = {697: ['3:51', '4:53', '5:40', '3:20', '5:43', '5:18', '2:41', '3:30', '4:58', '4:18', '9:05']}
NO_SPOTIFY = {652}   # #652 What's That Noise? is not on Spotify: YouTube only
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

disc = json.load(open('tools/batches/651-700.discovered.json'))
try: disc.update(json.load(open('tools/batches/651-700.fix.discovered.json')))   # second pass for a few albums
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
json.dump(out, open('tools/batches/651-700.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
