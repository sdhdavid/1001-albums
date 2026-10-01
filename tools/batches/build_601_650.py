"""Build tools/batches/601-650.json from the discovery output (tools/batches/601-650.discovered.json, which
also gives the track lengths), the Spotify ids below (found by web search, unverified) and the stories in
tools/stories_601_650.py.  Then add_albums.py writes the albums."""
import json, re, sys
sys.path.insert(0, 'tools')
from stories_601_650 import STORIES

SPOTIFY = {
 601:'6BqoNCQsupSaLBkl8u1uME', 602:'1TBNjPts9k7Z0Pq6qYsdhQ', 603:'6udwOJKxsNiLZAkcvjjnvb', 604:'0apKBDnFXYmhlMYfXt5zCB', 605:'5wTBP2faMYL8VfGJ6Ax3oy',
 606:'3Us57CjssWnHjTUIXBuIeH', 607:'5UVU0ftzd3onHzP7rs6EpI', 608:'5vBZRYu2GLA65nfxBvG1a7', 609:'0nw38yniBfbluS93FdYcbE', 610:'4V92Puney9WxGPecKtLG4L',
 611:'0iahfkN4PwmphXcQezpTRg', 612:'1niTZlsM14tECBG5PDAdZc', 613:'4aAhYU0IplW3AKbduPspJx', 614:'4zhqDQd41cAkGg7EJVezvx', 615:'0Itv01cUzRusmyNcEgEmOA',
 616:'5w4gJSJS1LaSJ5DgaC6Cl8', 617:'7rfKAiPs9ToZP9zEJDBqBH', 618:'63bl9diz0qWk5OOxb71zda', 619:'2jodAR4BsYntuyZn55ZrHB', 620:'566tD6a3xWL6MKLWkw8ERz',
 621:'6hmmX5UP4rIvOpGSaPerV8', 622:'3mnv6nzZV5AQhDG7OUsLdo', 623:'2l7RPWC3E6eStJJLBsUeCI', 624:'69oeRoYEpSsNPGVuYRxfoB', 625:'3qyW9uFZskhChIgwyrIh0i',
 626:'', 627:'6PmH3vQpsBfkQdnDr4AzLs', 628:'4CgweKiwA0yckiVbG6eUJI', 629:'4k4khFDw8jRzRnRynxgACP', 630:'5z8bPdGFiJx56cqsHTvWM9',
 631:'4HI70D2jFAAVJXKY9LAlpg', 632:'1NZ8YBYnruBPeKLuvTBARx', 633:'3LppC6RopLS9eWrceGYN8i', 634:'08lBERPbNkl9wCLHnJXXvm', 635:'6JOUA8k5wGLvppurfYDS6y',
 636:'70Vuh3jYUMO8LLP5BaqZMb', 637:'3FjlnBZ4PGmGrtyKw0H8ka', 638:'7b7yM2bhyOEjcFQRF6dRSV', 639:'48AGkmM7iO4jrELRnNZGPV', 640:'6Agl4DVuihiDPuxuN1L8Jv',
 641:'0Ju8YUtJB0RMw8NZXgXe6n', 642:'5SUqb3XY2BmvfAFLTjnBs0', 643:'4DfmPm17Nz6a60BlEpGGKU', 644:'5G6akYvygKGToUIB863YqU', 645:'4A10zgDO51IMdrLVfUnhh8',
 646:'0um9FI6BLBldL5POP4D4Cw', 647:'2AyJzvREOnlnYhaBzF1Kxp', 648:'3fI60xJqLkfhnbAf907JsS', 649:'1dr9h8cfIfIWp1Z57pbr3Z', 650:'6DZNOsLXIU2zOQfQDwDpIS',
}

# Which discovered playlist to use when it is not the top-scoring one (index into rec['youtube']).
PLAYLIST_CHOICE = {641: 2}   # #641: the playlist that holds the whole LP
# #553: iTunes has no lengths, so they come from the hand-picked playlist (seconds)
LENGTHS_FROM_PLAYLIST = {}
RENAME = {'Leben Heißt Leben': 'Leben heißt Leben', 'Geburt Einer Nation': 'Geburt einer Nation', 'Open Letter (To a Landord)': 'Open Letter (To a Landlord)',
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
KEEP_FIRST = {606: 10, 640: 12, 641: 9, 646: 11, 649: 10}   # bonus tracks cut (CD bonus / remixes / Fools Gold / deluxe)
DROP = {614: [0]}   # #614 I Don't Want to Talk About It, added on later editions
POSITION = {}     # playlist positions the title matching missed
# One discovered track that is two songs in the playlist: n -> (index, [(name, position, length), ...])
SPLIT = {}
BY_PLAYLIST = {616}   # #616: the original EP order
SKIP = set()
NO_SPOTIFY = {626}   # #626 Tank Battles is not on Spotify: YouTube only
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

disc = json.load(open('tools/batches/601-650.discovered.json'))
try: disc.update(json.load(open('tools/batches/601-650.fix.discovered.json')))   # second pass for a few albums
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
    if not SPOTIFY[n] and n not in NO_SPOTIFY: print('no Spotify id yet', n); continue
    rec = {'n': n, 'spotifyAlbum': SPOTIFY[n], 'tracks': tracks, 'focus': focus, 'story': st['story'], 'picks': picks}
    if n in NO_SPOTIFY: del rec['spotifyAlbum']; rec['noSpotify'] = True
    else: assert len(SPOTIFY[n]) == 22
    rec['durations'] = durs if not extra else MANUAL[n]['durations']
    if n not in VIDEOS: rec.update(extra or {'youtubePlaylist': yt['id']})
    out.append(rec)
json.dump(out, open('tools/batches/601-650.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'albums')
