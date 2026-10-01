"""Find track lists, lengths and YouTube playlists for a range of albums.

Usage: python3 tools/discover.py FIRST LAST OUT.json   (or: '56,63,74' 0 OUT.json for a list)     (runs in GitHub Actions: "Discover albums")

For each catalog entry N in FIRST..LAST (skipping albums already on the site):
  * track list + lengths from the original-looking iTunes edition (median lengths across editions via fetch_durations helpers)
  * YouTube playlist candidates (yt-dlp search), each scored by how many of the album's songs it contains;
    the best playlist gives every song's position in it ("tracks": [[name, null, index], ...]).
Output is a review file: pick, check the scores, then turn it into a batch for add_albums.py.
"""
import json, re, sys, urllib.parse
sys.argv, args = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, 'tools')
import importlib.util
# reuse the lookup helpers without running fetch_durations' main script
src = open('tools/fetch_durations.py').read().split("sys.path.insert(0, 'tools'); import store")[0]
ns = {}; exec(compile(src, 'fetch_durations_helpers', 'exec'), ns)
get, sim, norm, clock, editions, assign = (ns[k] for k in ('get', 'sim', 'norm', 'clock', 'editions', 'assign'))
import yt_dlp, store

wanted = [int(x) for x in args[0].split(',')] if ',' in args[0] or args[1] == '0' else list(range(int(args[0]), int(args[1]) + 1))
out_path = args[2]
# Titles the automatic clean-up gets wrong: n -> (artist, title) to search for.
OVERRIDE = {74: ('The Yardbirds', 'Roger the Engineer'), 63: ('The Byrds', 'Fifth Dimension'),
            251: ('Hugh Masekela', 'Home Is Where the Music Is'), 270: ('Lynyrd Skynyrd', 'Pronounced Leh-Nerd Skin-Nerd'),
            314: ('Richard & Linda Thompson', 'I Want to See the Bright Lights Tonight'), 315: ('Gil Scott-Heron', 'Winter in America'),
            326: ('Brian Eno', 'Another Green World'), 328: ('Neu!', "Neu! '75"), 339: ('R. D. Burman', 'Shalimar (Original Motion Picture Soundtrack)'),
            304: ('Stevie Wonder', "Fulfillingness' First Finale"), 307: ('Van Morrison', "It's Too Late to Stop Now"),
            340: ('Neil Young', "Tonight's the Night"), 346: ('Earth, Wind & Fire', "That's the Way of the World"),
            347: ('Curtis Mayfield', "There's No Place Like America Today"), 330: ('Keith Jarrett', 'The Koln Concert'),
            357: ('Jorge Ben', 'Africa Brasil'), 360: ('Parliament', 'Mothership Connection'), 364: ('Fela Kuti', 'Zombie'),
            369: ('Kraftwerk', 'Trans-Europe Express'), 381: ('Talking Heads', 'Talking Heads 77'), 383: ('David Bowie', 'Heroes'),
            392: ('Ian Dury', 'New Boots and Panties'), 393: ('Sex Pistols', 'Never Mind the Bollocks'),
            395: ('Kraftwerk', 'The Man-Machine'), 397: ('Elis Regina', 'Elis 1980'), 361: ('Penguin Cafe Orchestra', 'Music from the Penguin Cafe'),
            403: ('The Adverts', 'Crossing the Red Sea with the Adverts'), 405: ('The Residents', 'Duck Stab Buster & Glen'),
            406: ('Public Image Ltd', 'Public Image First Issue'), 410: ('Throbbing Gristle', 'D.o.A. The Third and Final Report'),
            415: ('Willie Colon', 'Siembra'), 417: ('Devo', 'Q: Are We Not Men? A: We Are Devo!'), 423: ('X-Ray Spex', 'Germfree Adolescents'),
            424: ('Brian Eno', 'Ambient 1 Music for Airports'), 429: ('Germs', 'GI'), 430: ('The B-52s', 'The B-52s'),
            445: ('Cheap Trick', 'Cheap Trick at Budokan'), 448: ('Public Image Ltd', 'Metal Box'), 404: ('Big Star', 'Third'),
            452: ('The Specials', 'The Specials'), 458: ('Peter Gabriel', 'Peter Gabriel 3 Melt'), 480: ("The Go-Go's", 'Beauty and the Beat'),
            481: ('Motorhead', "No Sleep 'til Hammersmith"), 482: ('Soft Cell', 'Non-Stop Erotic Cabaret'),
            483: ('Orchestral Manoeuvres in the Dark', 'Architecture & Morality'), 484: ('Brian Eno & David Byrne', 'My Life in the Bush of Ghosts'),
            462: ('Motorhead', 'Ace of Spades'), 477: ('Einsturzende Neubauten', 'Kollaps'), 497: ('Grandmaster Flash', 'The Message'),
            500: ("Dexys Midnight Runners", 'Too-Rye-Ay'), 498: ('Elvis Costello', 'Imperial Bedroom'),
            501: ('Simple Minds', 'New Gold Dream'), 532: ('Run-DMC', 'Run-D.M.C.'), 548: ('a-ha', 'Hunting High and Low'),
            544: ("Youssou N'Dour", 'Immigres'), 539: ('The Style Council', 'Cafe Bleu'), 546: ('The Fall', "This Nation's Saving Grace"),
            526: ('Eurythmics', 'Sweet Dreams (Are Made of This)'), 537: ('Prince', 'Purple Rain'), 547: ('Abdullah Ibrahim', 'Water from an Ancient Well'),
            552: ('Mekons', 'Fear and Whiskey'), 555: ('The Pogues', 'Rum Sodomy and the Lash'), 560: ('New Order', 'Low-Life'),
            562: ('Dexys Midnight Runners', "Don't Stand Me Down"), 565: ('Afrika Bambaataa', 'Planet Rock The Album'),
            572: ('Megadeth', "Peace Sells But Who's Buying"), 578: ('Run-DMC', 'Raising Hell'), 586: ('Dinosaur Jr', "You're Living All Over Me"),
            587: ('Dolly Parton', 'Trio'), 590: ('Prince', 'Sign o the Times'), 595: ('Husker Du', 'Warehouse Songs and Stories'),
            597: ('Astor Piazzolla', 'The New Tango'), 564: ('Elvis Costello', 'Blood & Chocolate'),
            609: ("Terence Trent D'Arby", 'Introducing the Hardline'), 610: ('The Pogues', 'If I Should Fall from Grace with God'),
            611: ('Leonard Cohen', "I'm Your Man"), 612: ('The Waterboys', "Fisherman's Blues"), 616: ('Mudhoney', 'Superfuzz Bigmuff'), 619: ('The Go-Betweens', '16 Lovers Lane'),
            622: ('My Bloody Valentine', "Isn't Anything"), 624: ('Metallica', 'And Justice for All'), 626: ('Dagmar Krause', 'Tank Battles'), 629: ('Morrissey', 'Viva Hate'),
            631: ('The Sugarcubes', "Life's Too Good"), 633: ("Jane's Addiction", "Nothing's Shocking"), 640: ('Queen Latifah', 'All Hail the Queen'),
            642: ('fIREHOSE', 'fROMOHIO'), 643: ('Beastie Boys', "Paul's Boutique"), 644: ('The Young Gods', "L'eau rouge"), 645: ('John Zorn', 'Spy vs Spy'),
            648: ('Baaba Maal', 'Djam Leelii'), 601: ('Ladysmith Black Mambazo', 'Shaka Zulu'),
            651: ('808 State', '90'), 652: ('Coldcut', "What's That Noise"), 658: ('Soul II Soul', 'Club Classics Vol. One'), 659: ('De La Soul', '3 Feet High and Rising'),
            660: ('Janet Jackson', 'Rhythm Nation 1814'), 661: ('Jungle Brothers', 'Done by the Forces of Nature'), 662: ('N.W.A', 'Straight Outta Compton'),
            664: ('The Shamen', 'En-Tact'), 666: ("The La's", "The La's"), 671: ('Digital Underground', 'Sex Packets'), 673: ('Happy Mondays', "Pills 'n' Thrills and Bellyaches"),
            674: ('George Michael', 'Listen Without Prejudice Vol. 1'), 675: ('Neil Young', 'Ragged Glory'), 676: ('Ice Cube', "AmeriKKKa's Most Wanted"),
            677: ("Jane's Addiction", 'Ritual de lo Habitual'), 678: ('LL Cool J', 'Mama Said Knock You Out'), 680: ("Sinead O'Connor", "I Do Not Want What I Haven't Got"),
            681: ('A Tribe Called Quest', "People's Instinctive Travels and the Paths of Rhythm"), 690: ('MC Solaar', 'Qui seme le vent recolte le tempo'),
            691: ('Jah Wobble', 'Rising Above Bedlam'), 693: ('Ice-T', 'O.G. Original Gangster'), 695: ('Public Enemy', 'Apocalypse 91'), 684: ('My Bloody Valentine', 'Loveless')}
# Extra words for the YouTube search when the plain query finds the wrong playlists (live versions, other albums).
YT_QUERY = {275: 'Hawkwind Space Ritual 1973 full album', 284: 'Herbie Hancock Head Hunters 1973 full album Chameleon',
            297: 'Iggy and the Stooges Raw Power 1973 full album',
            307: 'Van Morrison Its Too Late to Stop Now 1974 live album', 339: 'Shalimar 1978 R D Burman soundtrack songs',
            301: 'Bad Company 1974 debut album full', 348: 'Tom Petty and the Heartbreakers 1976 debut album full',
            352: 'Boston 1976 debut album full', 358: 'Joan Armatrading 1976 album full', 363: 'Ramones 1976 debut album full',
            376: 'The Clash 1977 debut album UK full', 381: 'Talking Heads 77 full album', 385: 'Suicide 1977 debut album full Alan Vega',
            387: 'Peter Gabriel 1 Car 1977 full album', 399: 'The Only Ones 1978 debut album full', 397: 'Elis Regina Elis 1980 album',
            383: 'David Bowie Heroes 1977 full album',
            414: 'Van Halen 1978 debut album full', 416: 'The Cars 1978 debut album full', 418: 'Dire Straits 1978 debut album full',
            430: 'The B-52s 1979 debut album full', 437: 'The Undertones 1979 debut album full', 429: 'Germs GI 1979 full album',
            404: 'Big Star Third Sister Lovers full album', 406: 'Public Image Ltd First Issue 1978 full album', 431: 'Holger Czukay Movies 1979 full album',
            433: 'The Fall Live at the Witch Trials full album',
            452: 'The Specials 1979 debut album full', 458: 'Peter Gabriel 3 Melt 1980 full album', 463: 'Killing Joke 1980 debut album full',
            468: 'Iron Maiden 1980 debut album full', 476: 'Pretenders 1980 debut album full', 492: 'Tom Tom Club 1981 debut album full',
            481: 'Motorhead No Sleep til Hammersmith 1981 live album full', 486: 'X Wild Gift 1981 full album', 465: 'Circle Jerks Group Sex 1980 full album',
            514: 'Violent Femmes 1983 debut album full', 532: 'Run DMC 1984 debut album full', 536: 'Van Halen 1984 album full',
            538: 'The Replacements Let It Be 1984 full album', 509: 'Venom Black Metal 1982 full album', 539: 'The Style Council Cafe Bleu 1984 full album',
            544: "Youssou N'Dour Immigres 1984 album", 547: 'Abdullah Ibrahim Water from an Ancient Well album', 529: 'Meat Puppets II 1984 full album',
            554: 'Suzanne Vega 1985 debut album full', 576: 'Throwing Muses 1986 debut album full', 552: 'Mekons Fear and Whiskey 1985 full album',
            587: 'Dolly Parton Linda Ronstadt Emmylou Harris Trio 1987 full album', 597: 'Astor Piazzolla Gary Burton The New Tango 1987',
            604: 'Sonic Youth Sister 1987 full album', 605: 'The Triffids Calenture 1987 full album', 621: 'Tracy Chapman 1988 debut album full',
            625: 'Dinosaur Jr Bug 1988 full album', 628: 'American Music Club California 1988 album', 646: 'The Stone Roses 1989 debut album full',
            616: 'Mudhoney Superfuzz Bigmuff 1988 EP', 626: 'Dagmar Krause Tank Battles Hanns Eisler', 648: 'Baaba Maal Mansour Seck Djam Leelii',
            645: 'John Zorn Spy vs Spy Ornette Coleman', 644: 'The Young Gods L eau rouge 1989', 609: 'Terence Trent DArby Introducing the Hardline 1987 full album',
            610: 'The Pogues If I Should Fall from Grace with God 1988 full album', 641: 'Spacemen 3 Playing with Fire 1989 full album',
            651: '808 State 90 1989 album', 653: 'Barry Adamson Moss Side Story 1989 album', 666: "The La's 1990 debut album full", 687: 'Cypress Hill 1991 debut album full',
            683: 'Ride Nowhere 1990 full album', 686: 'Crowded House Woodface 1991 full album', 688: 'Julian Cope Peggy Suicide 1991 full album',
            689: 'Gang Starr Step in the Arena 1991 full album', 699: 'Sepultura Arise 1991 full album', 700: 'Slint Spiderland 1991 full album', 657: 'Fugazi Repeater 1990 full album'}
# Candidates found by hand (web search): extra playlists to score, and full-album videos whose chapters are read.
EXTRA_PLAYLISTS = {275: ['OLAK5uy_lFFPjJvqQDLVRR8HA3an2aZZUIH_s4ogk', 'OLAK5uy_kCFLJeEuBQmuXIHWYQxX-zjcXtceZe8UY', 'PLycVTiaj8OI_vlOI_Hhs7lHuTeAAf57c5'],
                   284: ['OLAK5uy_nvlpZLPE7acPh4D5k2lvtdFCe68yEIqV4', 'OLAK5uy_m789U0dt-J4aLVd7p-dXJxSfDliep-NT0', 'PLm4I8tP6UbWayMmspp9ucpplfT2twORSe', 'PLLpV5usM_H_YUpR35cBBP4fwXrSQOH-qZ'],
                   310: ['OLAK5uy_lhwiy3qPEpBwBTOpyy-KK8Pmcn7x9fI2k', 'OLAK5uy_m0wBxaewH-lbo6eGyZQUbE-fzlUeug7fM', 'PL4wwexJLSb3mF35yaNEVCZiX68Lb9FnEm'],
                   330: ['PLlziogY0fk9phBIR0pGySlfV92DebcKrc', 'PLfdMKJMGPPtwRzlKi6bCI1_mSv0cJkm4r', 'PL8SFNbbOmAYMsaQSCbbv5oC4aY5o_4t6s', 'PL0766CFA4CBD669D6'],
                   339: ['OLAK5uy_kzduVKq3Un4mx4ssOCWgbvq5AMRBvvNv4', 'OLAK5uy_nrjFfBfmaNOYAL09VgoinGl5IW59qFw2U', 'PLw61iWYSKReevacFkh4SlEafze-k8qXn0'],
                   364: ['OLAK5uy_kz-CwckiMEJh2jW1jU0-j0e9mi4vXxGPY', 'PL4ZqKOqeg4cVrjNjVVfB8UU36iO4enFVJ'],
                   376: ['PLHTo__bpnlYX4wXCfUXsk8atvR0zpbpPN'], 400: ['PLNPGM2D7aODeIwtlLA51o7d-DAkqffyrb'],
                   404: ['OLAK5uy_nEfRmzliYZ8KP0g2PRBjmQdJ6kPSuU86g', 'PLEvr99j7ruPzc3YXLXOnxQGVMw4iWAA6c', 'PLOJWuc3CN303QT7RnWuruRLJJxEnf6TUu', 'PLJvYa4hB_Ul-5gdY9UcBDXNbuLGhQKim_'],
                   406: ['OLAK5uy_m2PSh2Vw6s0PdINtbPCyv81N5nMX3yNac', 'OLAK5uy_l8aOiSeHdlBuY6Uiiz2__J280s7Yh8o6k', 'PLw31gx_Af1g-uYdvOjGTI3T1WieKas-51'],
                   431: ['OLAK5uy_niijN27zTnrqADCiWObap5-AK22HsC7qI', 'PLDCQnAwuT7e-oi-BQrVV8o5DrCiOVKZV1'],
                   441: ['PLOJWuc3CN301YxZG_I_ZniHGfb4tl7vug', 'PLo2aaBamFnLTj8Ad0ymIx81CavqxNcjnB', 'PLmna7oCNK2MmgBrbPZPciNsXxAMQEjUao'],
                   458: ['OLAK5uy_l6J0IYQQ9zTbh_teJb7GYlx9T1nUKIyro', 'PL4mbw3LEmSEmMXVWZsY6J3fuIEWYB_fs9', 'PLEvwWAEnoCLlNVdGVLAWGHmMhAAwOey_W'],
                   463: ['PLG9675Na1SXZs7yvrbLkdTsoZH4bUmJjx', 'PL2j_Wb5pKu_2V16IOI--3s_F2XV__gW38'],
                   465: ['PLreQ0V6eABfILf1X0KFOA7bVzfFcUsPaI'],
                   476: ['PLahyulnypeEyK9PA4r6QoeDzA1nJ4wgG7', 'PLBokfEObLPHAU9IejPCwVkJs0E-Y8mkhc', 'OLAK5uy_n58mJ_2quIcm6sKFTWa90TEedpuAqj3x8'],
                   499: ['OLAK5uy_kojS0C3l6gUvDaGXWmRH8_lYvIyfvVk_M', 'PLE6gHCwAovfDEU0bQ2mOWKTa9Gj6bSQ63', 'PLfimnwaZdumh8CA9TGQuYLwYLMePx5SbQ'],
                   570: ['PLuFrIncMdIQzSOBw9mJg_jhMO8zp4DoHC'], 553: ['PLVxakxoWul5UcH8THGanJuzSyIorJfVQr', 'PLF56F94BE1CDFF4DD']}
# Spotify album ids to check (the embed page lists the album's tracks), when web search found several albums with one name.
SPOTIFY_CHECK = {397: ['3NOxICud3CE6svBnR9WqC7', '4huMvebKxtKXAm51LCfOoC', '67UdOjU4vLZx8yoHgXkNes', '21XmM8dZGAfwUXTnAPqxdC'], 471: ['22mcOt74IVtCeR5hoIfveO', '2fgQN85UzwZMRIBTs06FjX', '3zeDrhkNv8872fC7CsOCpI', '4xrUp1M9XmKHFzRRyXIx71', '53fzZMZ3ENBY0BpLFOMy9p', '6GjMcck9c4i6cQo194xKl6', '7lCEnPYYkUuvnkrCbA6RCa', '7lGDjzmvAcNl6kEtn1rTaJ', '7qLJ8bzny3tynTPW2U2Anv'], 498: ['0LSWSMW0LVJX3fmSgDnk2A', '0rhmwOflgYrPntNuEe8chN', '1aucGNKimhgARC7iO2xLt2', '1pK8MLyjgvt8pNVkQCBnSg', '27qrMWYugzTnAvn2mtZdcx', '2B6i9ZY0NF8UkESEIL0taZ', '2srC8Ls3xXdRUH3n7jvHQD', '4HWzj6tf8nXvH7GzXAl1ld', '5h4pJfrTGROIhFJpTHa1Cu', '65Al3RSB7zeQeYcinysMxJ', '6A4MecoyRjnDtYeAZ7JGQf', '6Iyeo7CPHen8QEW4x31TpI', '6zwFIyWKbdHi9mwrQcrEY1']}
# Spotify track ids (found by web search) whose album id is wanted, when no album page turned up in search.
SPOTIFY_TRACKS = {652: ['6rvinglzwGWPaO9N9nnHeR', '1F5QCrmxZ18xN9jkOI94aU', '3w9fto7To0gKvUzYWxthP8'], 690: ['0JYiIbdztz6KjiJt9OXfYS', '55u4IiABkTGzBfs2iXwhbo'], 691: ['1sffL3V01zHOByMZxAMCfD', '1kZJYvBOXRBA6zgB5vocqY']}
# Track lists given by hand (n -> names) when the automatic edition is the wrong album: the iTunes edition that matches
# them best gives the lengths, and the playlists are scored against these names.
WANT = {458: ['Intruder', 'No Self Control', 'Start', "I Don't Remember", 'Family Snapshot', 'And Through the Wire',
              'Games Without Frontiers', 'Not One of Us', 'Lead a Normal Life', 'Biko'],
        473: ['Ha Ha I\'m Drowning', 'Sleeping Gas', 'Treason', 'Second Head', 'Poppies in the Field', 'Went Crazy',
              'Brave Boys Keep Their Promises', 'Bouncing Babies', 'Books', 'Thief of Baghdad', 'When I Dream'],
        492: ['Wordy Rappinghood', 'Genius of Love', 'Tom Tom Theme', "L'Éléphant", 'As Above, So Below', 'Lorelei', 'On, On, On, On...', 'Booming and Zooming'],
        476: ['Precious', 'The Phone Call', 'Up the Neck', 'Tattooed Love Boys', 'Space Invader', 'The Wait', 'Stop Your Sobbing',
              'Kid', 'Private Life', 'Brass in Pocket', 'Lovers of Today', 'Mystery Achievement'],
        509: ['Black Metal', 'To Hell and Back', 'Buried Alive', 'Raise the Dead', "Teacher's Pet", 'Leave Me in Hell', 'Sacrifice',
              "Heaven's on Fire", 'Countess Bathory', "Don't Burn the Witch", 'At War with Satan'],
        463: ['Requiem', 'Wardance', "Tomorrow's World", 'Bloodsport', 'The Wait', 'Complications', 'S.O. 36', 'Primitive'],
        609: ['If You All Get to Heaven', 'If You Let Me Stay', 'Wishing Well', "I'll Never Turn My Back on You (Father's Words)", 'Dance Little Sister',
              'Seven More Days', "Let's Go Forward", 'Rain', 'Sign Your Name', 'As Yet Untitled', "Who's Loving You"],
        610: ['If I Should Fall from Grace with God', 'Turkish Song of the Damned', 'Bottle of Smoke', 'Fairytale of New York', 'Metropolis',
              'Thousands Are Sailing', 'Fiesta', 'Medley: The Recruiting Sergeant / The Rocky Road to Dublin / The Galway Races',
              'Streets of Sorrow / Birmingham Six', 'Lullaby of London', 'Sit Down by the Fire', 'The Broad Majestic Shannon', 'Worms'],
        641: ['Honey', 'Come Down Softly to My Soul', 'How Does It Feel?', 'I Believe It', 'Revolution', 'Let Me Down Gently',
              'So Hot (Wash Away All of My Tears)', 'Suicide', 'Lord Can You Hear Me?']}
VIDEOS = {}  # video pages need a signed-in browser from GitHub Actions, so chapters can't be read there
catalog = {a['n']: a for a in store.catalog()}
have = set(store.numbers())
BAD = re.compile(r'deluxe|anniversary|expanded|sessions|collector|super|box|live|bonus|mono|stereo|demo|remix', re.I)

def pick_edition(artist, title):
    eds = list(editions(artist, title))
    eds = [e for e in eds if len(e) >= 4]
    if not eds: return None, []
    counts = [len(e) for e in eds]
    # most common track count = the original album (deluxe editions are longer)
    common = max(set(counts), key=lambda c: (counts.count(c), -c))
    best = next(e for e in eds if len(e) == common)
    return best, counts

def simple(s): return norm(re.sub(r'\(.*?\)|\[.*?\]|- .*$', '', s))

ydl = yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': 'in_playlist', 'skip_download': True, 'ignoreerrors': True, 'socket_timeout': 30})

def yt_candidates(artist, title, n=None):
    q = urllib.parse.quote(YT_QUERY.get(n) or f'{artist} {title} album')
    info = ydl.extract_info(f'https://www.youtube.com/results?search_query={q}&sp=EgIQAw%253D%253D', download=False) or {}
    return [(e.get('id'), e.get('title')) for e in info.get('entries', []) if e and e.get('id') and str(e['id']).startswith(('PL', 'OLAK'))][:6]

def variants(t):
    t = t or ''
    out = [t, re.sub(r'^\s*\d+[\.\)\-]?\s*', '', t)]
    if ' - ' in t: out.append(t.split(' - ', 1)[1])
    return [simple(v) for v in out if simple(v)]

def score(names, entries):
    titles = [variants(t) for t in entries]
    pos, used = [], set()
    for n in names:
        best, bj = 0, -1
        for j, t in enumerate(titles):
            if j in used: continue
            s = max((sim(simple(n), v) for v in t), default=0)
            if s > best: best, bj = s, j
        if best >= .8: used.add(bj); pos.append(bj)
        else: pos.append(-1)
    return pos

result = {}
for n in wanted:
    if n in have or n not in catalog: continue
    meta = catalog[n]; artist = re.split(r' \+ | featuring |/| and Her| & His', meta['artist'])[0].strip(); title = re.sub(r'[“”"]', '', meta['title'])
    title = re.sub(r'\s*\(.*?\)\s*$', '', title)
    artist, title = OVERRIDE.get(n, (artist, title))
    edition, counts = pick_edition(artist, title)
    if n in WANT:   # names given by hand: lengths from the best-matching edition
        eds = list(editions(artist, title)); counts = [len(e) for e in eds]
        best_ed = max(eds, key=lambda e: sum(any(sim(simple(w), simple(t)) >= .8 for t, _ in e) for w in WANT[n]), default=[])
        def length(w):
            m = max(best_ed, key=lambda x: sim(simple(w), simple(x[0])), default=None)
            return m[1] if m and sim(simple(w), simple(m[0])) >= .8 else None
        edition = [(w, length(w)) for w in WANT[n]]
    rec = {'n': n, 'artist': meta['artist'], 'title': meta['title'], 'editionSizes': counts}
    if edition:
        names = [t for t, _ in edition]
        rec['tracks'] = names; rec['durations'] = [clock(ms) if ms else None for _, ms in edition]
        best = []
        for pid, ptitle in yt_candidates(artist, title, n) + [(p, 'hand-picked') for p in EXTRA_PLAYLISTS.get(n, [])]:
            info = ydl.extract_info(f'https://www.youtube.com/playlist?list={pid}', download=False) or {}
            ents = [e.get('title') for e in info.get('entries', []) if e]
            pos = score(names, ents)
            found = sum(p >= 0 for p in pos)
            best.append({'id': pid, 'title': ptitle, 'size': len(ents), 'found': found, 'positions': pos, 'entries': ents if ptitle == 'hand-picked' else None,
                         'durations': [e.get('duration') for e in info.get('entries', []) if e] if ptitle == 'hand-picked' else None})
        best.sort(key=lambda b: (b['found'] - abs(b['size'] - len(names)) * .5, b['id'].startswith('OLAK')), reverse=True)
        rec['youtube'] = best[:3] + [b for b in best[3:] if b['title'] == 'hand-picked']
        vids = []
        for vid in VIDEOS.get(n, []):
            v = ydl.extract_info(f'https://www.youtube.com/watch?v={vid}', download=False) or {}
            vids.append({'id': vid, 'title': v.get('title'), 'duration': v.get('duration'), 'channel': v.get('channel'),
                         'chapters': [[c.get('title'), int(c.get('start_time') or 0)] for c in v.get('chapters') or []],
                         'description': (v.get('description') or '')[:3000]})
        if vids: rec['videos'] = vids
    elif EXTRA_PLAYLISTS.get(n):
        rec['youtube'] = []
        for pid in EXTRA_PLAYLISTS[n]:
            info = ydl.extract_info(f'https://www.youtube.com/playlist?list={pid}', download=False) or {}
            ents = [e for e in info.get('entries', []) if e]
            rec['youtube'].append({'id': pid, 'title': 'hand-picked', 'size': len(ents), 'entries': [e.get('title') for e in ents],
                                   'durations': [e.get('duration') for e in ents]})
    for sid in SPOTIFY_CHECK.get(n, []):
        try:
            import urllib.request as ur
            page = ur.urlopen(ur.Request(f'https://open.spotify.com/embed/album/{sid}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
            rec.setdefault('spotifyCheck', {})[sid] = re.findall(r'"name":"([^"]{1,80})"', page)[:25] + re.findall(r'"releaseDate":\{"isoString":"([^"]+)"', page)[:1]
        except Exception as e:
            rec.setdefault('spotifyCheck', {})[sid] = [str(e)]
    for tid in SPOTIFY_TRACKS.get(n, []):
        try:
            import urllib.request as ur
            page = ''.join(ur.urlopen(ur.Request(f'https://open.spotify.com/{kind}/track/{tid}'.replace('//track', '/track'), headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
                           for kind in ('', 'embed'))
            rec.setdefault('spotifyTracks', {})[tid] = sorted(set(re.findall(r'spotify:album:([A-Za-z0-9]{22})', page) + re.findall(r'/album/([A-Za-z0-9]{22})', page) + re.findall(r'album%3A([A-Za-z0-9]{22})', page)))
            # name each candidate album (its embed page starts with the album name)
            for aid in rec['spotifyTracks'][tid]:
                if aid in rec.setdefault('spotifyNames', {}): continue
                try:
                    apage = ur.urlopen(ur.Request(f'https://open.spotify.com/embed/album/{aid}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
                    rec['spotifyNames'][aid] = (re.findall(r'"name":"([^"]{1,80})"', apage) or [''])[0]
                except Exception as e:
                    rec['spotifyNames'][aid] = str(e)
        except Exception as e:
            rec.setdefault('spotifyTracks', {})[tid] = [str(e)]
    result[n] = rec
    print(n, meta['title'], '| editions', counts, '| best', (rec.get('youtube') or [{}])[0].get('id'), (rec.get('youtube') or [{}])[0].get('found'), flush=True)
    json.dump(result, open(out_path, 'w'), ensure_ascii=False, indent=1)
