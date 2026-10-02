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
            252: ('Hugh Masekela', 'Home Is Where the Music Is'), 271: ('Lynyrd Skynyrd', 'Pronounced Leh-Nerd Skin-Nerd'),
            315: ('Richard & Linda Thompson', 'I Want to See the Bright Lights Tonight'), 316: ('Gil Scott-Heron', 'Winter in America'),
            327: ('Brian Eno', 'Another Green World'), 329: ('Neu!', "Neu! '75"), 340: ('R. D. Burman', 'Shalimar (Original Motion Picture Soundtrack)'),
            305: ('Stevie Wonder', "Fulfillingness' First Finale"), 308: ('Van Morrison', "It's Too Late to Stop Now"),
            341: ('Neil Young', "Tonight's the Night"), 347: ('Earth, Wind & Fire', "That's the Way of the World"),
            348: ('Curtis Mayfield', "There's No Place Like America Today"), 331: ('Keith Jarrett', 'The Koln Concert'),
            358: ('Jorge Ben', 'Africa Brasil'), 361: ('Parliament', 'Mothership Connection'), 365: ('Fela Kuti', 'Zombie'),
            370: ('Kraftwerk', 'Trans-Europe Express'), 382: ('Talking Heads', 'Talking Heads 77'), 384: ('David Bowie', 'Heroes'),
            393: ('Ian Dury', 'New Boots and Panties'), 394: ('Sex Pistols', 'Never Mind the Bollocks'),
            396: ('Kraftwerk', 'The Man-Machine'), 398: ('Elis Regina', 'Elis 1980'), 362: ('Penguin Cafe Orchestra', 'Music from the Penguin Cafe'),
            404: ('The Adverts', 'Crossing the Red Sea with the Adverts'), 406: ('The Residents', 'Duck Stab Buster & Glen'),
            407: ('Public Image Ltd', 'Public Image First Issue'), 411: ('Throbbing Gristle', 'D.o.A. The Third and Final Report'),
            416: ('Willie Colon', 'Siembra'), 418: ('Devo', 'Q: Are We Not Men? A: We Are Devo!'), 424: ('X-Ray Spex', 'Germfree Adolescents'),
            425: ('Brian Eno', 'Ambient 1 Music for Airports'), 430: ('Germs', 'GI'), 431: ('The B-52s', 'The B-52s'),
            446: ('Cheap Trick', 'Cheap Trick at Budokan'), 449: ('Public Image Ltd', 'Metal Box'), 405: ('Big Star', 'Third'),
            453: ('The Specials', 'The Specials'), 459: ('Peter Gabriel', 'Peter Gabriel 3 Melt'), 481: ("The Go-Go's", 'Beauty and the Beat'),
            482: ('Motorhead', "No Sleep 'til Hammersmith"), 483: ('Soft Cell', 'Non-Stop Erotic Cabaret'),
            484: ('Orchestral Manoeuvres in the Dark', 'Architecture & Morality'), 485: ('Brian Eno & David Byrne', 'My Life in the Bush of Ghosts'),
            463: ('Motorhead', 'Ace of Spades'), 478: ('Einsturzende Neubauten', 'Kollaps'), 498: ('Grandmaster Flash', 'The Message'),
            501: ("Dexys Midnight Runners", 'Too-Rye-Ay'), 499: ('Elvis Costello', 'Imperial Bedroom'),
            502: ('Simple Minds', 'New Gold Dream'), 533: ('Run-DMC', 'Run-D.M.C.'), 549: ('a-ha', 'Hunting High and Low'),
            545: ("Youssou N'Dour", 'Immigres'), 540: ('The Style Council', 'Cafe Bleu'), 547: ('The Fall', "This Nation's Saving Grace"),
            527: ('Eurythmics', 'Sweet Dreams (Are Made of This)'), 538: ('Prince', 'Purple Rain'), 548: ('Abdullah Ibrahim', 'Water from an Ancient Well'),
            553: ('Mekons', 'Fear and Whiskey'), 556: ('The Pogues', 'Rum Sodomy and the Lash'), 561: ('New Order', 'Low-Life'),
            563: ('Dexys Midnight Runners', "Don't Stand Me Down"), 566: ('Afrika Bambaataa', 'Planet Rock The Album'),
            573: ('Megadeth', "Peace Sells But Who's Buying"), 579: ('Run-DMC', 'Raising Hell'), 587: ('Dinosaur Jr', "You're Living All Over Me"),
            588: ('Dolly Parton', 'Trio'), 591: ('Prince', 'Sign o the Times'), 596: ('Husker Du', 'Warehouse Songs and Stories'),
            598: ('Astor Piazzolla', 'The New Tango'), 565: ('Elvis Costello', 'Blood & Chocolate'),
            610: ("Terence Trent D'Arby", 'Introducing the Hardline'), 611: ('The Pogues', 'If I Should Fall from Grace with God'),
            612: ('Leonard Cohen', "I'm Your Man"), 613: ('The Waterboys', "Fisherman's Blues"), 617: ('Mudhoney', 'Superfuzz Bigmuff'), 620: ('The Go-Betweens', '16 Lovers Lane'),
            623: ('My Bloody Valentine', "Isn't Anything"), 625: ('Metallica', 'And Justice for All'), 627: ('Dagmar Krause', 'Tank Battles'), 630: ('Morrissey', 'Viva Hate'),
            632: ('The Sugarcubes', "Life's Too Good"), 634: ("Jane's Addiction", "Nothing's Shocking"), 641: ('Queen Latifah', 'All Hail the Queen'),
            643: ('fIREHOSE', 'fROMOHIO'), 644: ('Beastie Boys', "Paul's Boutique"), 645: ('The Young Gods', "L'eau rouge"), 646: ('John Zorn', 'Spy vs Spy'),
            649: ('Baaba Maal', 'Djam Leelii'), 602: ('Ladysmith Black Mambazo', 'Shaka Zulu'),
            652: ('808 State', '90'), 653: ('Coldcut', "What's That Noise"), 659: ('Soul II Soul', 'Club Classics Vol. One'), 660: ('De La Soul', '3 Feet High and Rising'),
            661: ('Janet Jackson', 'Rhythm Nation 1814'), 662: ('Jungle Brothers', 'Done by the Forces of Nature'), 663: ('N.W.A', 'Straight Outta Compton'),
            665: ('The Shamen', 'En-Tact'), 667: ("The La's", "The La's"), 672: ('Digital Underground', 'Sex Packets'), 674: ('Happy Mondays', "Pills 'n' Thrills and Bellyaches"),
            675: ('George Michael', 'Listen Without Prejudice Vol. 1'), 676: ('Neil Young', 'Ragged Glory'), 677: ('Ice Cube', "AmeriKKKa's Most Wanted"),
            678: ("Jane's Addiction", 'Ritual de lo Habitual'), 679: ('LL Cool J', 'Mama Said Knock You Out'), 681: ("Sinead O'Connor", "I Do Not Want What I Haven't Got"),
            682: ('A Tribe Called Quest', "People's Instinctive Travels and the Paths of Rhythm"), 691: ('MC Solaar', 'Qui seme le vent recolte le tempo'),
            692: ('Jah Wobble', 'Rising Above Bedlam'), 694: ('Ice-T', 'O.G. Original Gangster'), 696: ('Public Enemy', 'Apocalypse 91'), 685: ('My Bloody Valentine', 'Loveless'),
            709: ('Aphex Twin', 'Selected Ambient Works 85-92'), 710: ('Arrested Development', '3 Years 5 Months and 2 Days in the Life Of'),
            711: ('Koffi Olomide', 'Haut de gamme Koweit rive gauche'), 714: ('The Lemonheads', "It's a Shame About Ray"),
            716: ('The Disposable Heroes of Hiphoprisy', 'Hypocrisy Is the Greatest Luxury'), 717: ('k.d. lang', 'Ingenue'),
            720: ('The Pharcyde', 'Bizarre Ride II the Pharcyde'), 725: ("Stereo MC's", 'Connected'), 726: ('Ministry', 'Psalm 69'),
            731: ('Nick Cave & The Bad Seeds', "Henry's Dream"), 732: ('Nusrat Fateh Ali Khan', 'Devotional Songs'), 738: ('Liz Phair', 'Exile in Guyville'),
            743: ('Jamiroquai', 'Emergency on Planet Earth'), 749: ('Wu-Tang Clan', 'Enter the Wu-Tang (36 Chambers)'), 750: ('Bjork', 'Debut'), 713: ('Baaba Maal', 'Lam Toro'),
            752: ('Snoop Dogg', 'Doggystyle'), 758: ('Girls Against Boys', 'Venus Luxure No.1 Baby'), 774: ('Ali Farka Toure & Ry Cooder', 'Talking Timbuktu'),
            788: ('Nightmares on Wax', 'Smokers Delight'), 790: ('Raekwon', 'Only Built 4 Cuban Linx'), 801: ('GZA', 'Liquid Swords'), 786: ('Foo Fighters', 'Foo Fighters')}
# Extra words for the YouTube search when the plain query finds the wrong playlists (live versions, other albums).
YT_QUERY = {276: 'Hawkwind Space Ritual 1973 full album', 285: 'Herbie Hancock Head Hunters 1973 full album Chameleon',
            298: 'Iggy and the Stooges Raw Power 1973 full album',
            308: 'Van Morrison Its Too Late to Stop Now 1974 live album', 340: 'Shalimar 1978 R D Burman soundtrack songs',
            302: 'Bad Company 1974 debut album full', 349: 'Tom Petty and the Heartbreakers 1976 debut album full',
            353: 'Boston 1976 debut album full', 359: 'Joan Armatrading 1976 album full', 364: 'Ramones 1976 debut album full',
            377: 'The Clash 1977 debut album UK full', 382: 'Talking Heads 77 full album', 386: 'Suicide 1977 debut album full Alan Vega',
            388: 'Peter Gabriel 1 Car 1977 full album', 400: 'The Only Ones 1978 debut album full', 398: 'Elis Regina Elis 1980 album',
            384: 'David Bowie Heroes 1977 full album',
            415: 'Van Halen 1978 debut album full', 417: 'The Cars 1978 debut album full', 419: 'Dire Straits 1978 debut album full',
            431: 'The B-52s 1979 debut album full', 438: 'The Undertones 1979 debut album full', 430: 'Germs GI 1979 full album',
            405: 'Big Star Third Sister Lovers full album', 407: 'Public Image Ltd First Issue 1978 full album', 432: 'Holger Czukay Movies 1979 full album',
            434: 'The Fall Live at the Witch Trials full album',
            453: 'The Specials 1979 debut album full', 459: 'Peter Gabriel 3 Melt 1980 full album', 464: 'Killing Joke 1980 debut album full',
            469: 'Iron Maiden 1980 debut album full', 477: 'Pretenders 1980 debut album full', 493: 'Tom Tom Club 1981 debut album full',
            482: 'Motorhead No Sleep til Hammersmith 1981 live album full', 487: 'X Wild Gift 1981 full album', 466: 'Circle Jerks Group Sex 1980 full album',
            515: 'Violent Femmes 1983 debut album full', 533: 'Run DMC 1984 debut album full', 537: 'Van Halen 1984 album full',
            539: 'The Replacements Let It Be 1984 full album', 510: 'Venom Black Metal 1982 full album', 540: 'The Style Council Cafe Bleu 1984 full album',
            545: "Youssou N'Dour Immigres 1984 album", 548: 'Abdullah Ibrahim Water from an Ancient Well album', 530: 'Meat Puppets II 1984 full album',
            555: 'Suzanne Vega 1985 debut album full', 577: 'Throwing Muses 1986 debut album full', 553: 'Mekons Fear and Whiskey 1985 full album',
            588: 'Dolly Parton Linda Ronstadt Emmylou Harris Trio 1987 full album', 598: 'Astor Piazzolla Gary Burton The New Tango 1987',
            605: 'Sonic Youth Sister 1987 full album', 606: 'The Triffids Calenture 1987 full album', 622: 'Tracy Chapman 1988 debut album full',
            626: 'Dinosaur Jr Bug 1988 full album', 629: 'American Music Club California 1988 album', 647: 'The Stone Roses 1989 debut album full',
            617: 'Mudhoney Superfuzz Bigmuff 1988 EP', 627: 'Dagmar Krause Tank Battles Hanns Eisler', 649: 'Baaba Maal Mansour Seck Djam Leelii',
            646: 'John Zorn Spy vs Spy Ornette Coleman', 645: 'The Young Gods L eau rouge 1989', 610: 'Terence Trent DArby Introducing the Hardline 1987 full album',
            611: 'The Pogues If I Should Fall from Grace with God 1988 full album', 642: 'Spacemen 3 Playing with Fire 1989 full album',
            652: '808 State 90 1989 album', 654: 'Barry Adamson Moss Side Story 1989 album', 667: "The La's 1990 debut album full", 688: 'Cypress Hill 1991 debut album full',
            684: 'Ride Nowhere 1990 full album', 687: 'Crowded House Woodface 1991 full album', 689: 'Julian Cope Peggy Suicide 1991 full album',
            690: 'Gang Starr Step in the Arena 1991 full album', 700: 'Sepultura Arise 1991 full album', 701: 'Slint Spiderland 1991 full album', 658: 'Fugazi Repeater 1990 full album',
            707: 'Metallica Black Album 1991 full album', 715: 'Rage Against the Machine 1992 debut album full', 734: 'Suede 1993 debut album full',
            751: 'Orbital 1993 Brown Album full', 733: 'PJ Harvey Dry 1992 full album', 722: 'Sugar Copper Blue 1992 full album', 702: 'U2 Achtung Baby 1991 full album',
            726: 'Ministry Psalm 69 1992 full album', 711: 'Koffi Olomide Haut de gamme Koweit rive gauche', 732: 'Nusrat Fateh Ali Khan Devotional Songs 1992',
            786: 'Foo Fighters 1995 debut album full', 787: 'Garbage 1995 debut album full', 795: 'Elastica 1995 debut album full',
            799: 'Femi Kuti 1995 album', 773: 'G Love and Special Sauce 1994 debut album', 781: 'Orbital Snivilisation 1994 full album',
            782: 'Nirvana MTV Unplugged in New York full album', 755: 'William Orbit Strange Cargo III album'}
# Candidates found by hand (web search): extra playlists to score, and full-album videos whose chapters are read.
EXTRA_PLAYLISTS = {276: ['OLAK5uy_lFFPjJvqQDLVRR8HA3an2aZZUIH_s4ogk', 'OLAK5uy_kCFLJeEuBQmuXIHWYQxX-zjcXtceZe8UY', 'PLycVTiaj8OI_vlOI_Hhs7lHuTeAAf57c5'],
                   285: ['OLAK5uy_nvlpZLPE7acPh4D5k2lvtdFCe68yEIqV4', 'OLAK5uy_m789U0dt-J4aLVd7p-dXJxSfDliep-NT0', 'PLm4I8tP6UbWayMmspp9ucpplfT2twORSe', 'PLLpV5usM_H_YUpR35cBBP4fwXrSQOH-qZ'],
                   311: ['OLAK5uy_lhwiy3qPEpBwBTOpyy-KK8Pmcn7x9fI2k', 'OLAK5uy_m0wBxaewH-lbo6eGyZQUbE-fzlUeug7fM', 'PL4wwexJLSb3mF35yaNEVCZiX68Lb9FnEm'],
                   331: ['PLlziogY0fk9phBIR0pGySlfV92DebcKrc', 'PLfdMKJMGPPtwRzlKi6bCI1_mSv0cJkm4r', 'PL8SFNbbOmAYMsaQSCbbv5oC4aY5o_4t6s', 'PL0766CFA4CBD669D6'],
                   340: ['OLAK5uy_kzduVKq3Un4mx4ssOCWgbvq5AMRBvvNv4', 'OLAK5uy_nrjFfBfmaNOYAL09VgoinGl5IW59qFw2U', 'PLw61iWYSKReevacFkh4SlEafze-k8qXn0'],
                   365: ['OLAK5uy_kz-CwckiMEJh2jW1jU0-j0e9mi4vXxGPY', 'PL4ZqKOqeg4cVrjNjVVfB8UU36iO4enFVJ'],
                   377: ['PLHTo__bpnlYX4wXCfUXsk8atvR0zpbpPN'], 401: ['PLNPGM2D7aODeIwtlLA51o7d-DAkqffyrb'],
                   405: ['OLAK5uy_nEfRmzliYZ8KP0g2PRBjmQdJ6kPSuU86g', 'PLEvr99j7ruPzc3YXLXOnxQGVMw4iWAA6c', 'PLOJWuc3CN303QT7RnWuruRLJJxEnf6TUu', 'PLJvYa4hB_Ul-5gdY9UcBDXNbuLGhQKim_'],
                   407: ['OLAK5uy_m2PSh2Vw6s0PdINtbPCyv81N5nMX3yNac', 'OLAK5uy_l8aOiSeHdlBuY6Uiiz2__J280s7Yh8o6k', 'PLw31gx_Af1g-uYdvOjGTI3T1WieKas-51'],
                   432: ['OLAK5uy_niijN27zTnrqADCiWObap5-AK22HsC7qI', 'PLDCQnAwuT7e-oi-BQrVV8o5DrCiOVKZV1'],
                   442: ['PLOJWuc3CN301YxZG_I_ZniHGfb4tl7vug', 'PLo2aaBamFnLTj8Ad0ymIx81CavqxNcjnB', 'PLmna7oCNK2MmgBrbPZPciNsXxAMQEjUao'],
                   459: ['OLAK5uy_l6J0IYQQ9zTbh_teJb7GYlx9T1nUKIyro', 'PL4mbw3LEmSEmMXVWZsY6J3fuIEWYB_fs9', 'PLEvwWAEnoCLlNVdGVLAWGHmMhAAwOey_W'],
                   464: ['PLG9675Na1SXZs7yvrbLkdTsoZH4bUmJjx', 'PL2j_Wb5pKu_2V16IOI--3s_F2XV__gW38'],
                   466: ['PLreQ0V6eABfILf1X0KFOA7bVzfFcUsPaI'],
                   477: ['PLahyulnypeEyK9PA4r6QoeDzA1nJ4wgG7', 'PLBokfEObLPHAU9IejPCwVkJs0E-Y8mkhc', 'OLAK5uy_n58mJ_2quIcm6sKFTWa90TEedpuAqj3x8'],
                   500: ['OLAK5uy_kojS0C3l6gUvDaGXWmRH8_lYvIyfvVk_M', 'PLE6gHCwAovfDEU0bQ2mOWKTa9Gj6bSQ63', 'PLfimnwaZdumh8CA9TGQuYLwYLMePx5SbQ'],
                   571: ['PLuFrIncMdIQzSOBw9mJg_jhMO8zp4DoHC'], 554: ['PLVxakxoWul5UcH8THGanJuzSyIorJfVQr', 'PLF56F94BE1CDFF4DD']}
# Spotify album ids to check (the embed page lists the album's tracks), when web search found several albums with one name.
SPOTIFY_CHECK = {398: ['3NOxICud3CE6svBnR9WqC7', '4huMvebKxtKXAm51LCfOoC', '67UdOjU4vLZx8yoHgXkNes', '21XmM8dZGAfwUXTnAPqxdC'], 472: ['22mcOt74IVtCeR5hoIfveO', '2fgQN85UzwZMRIBTs06FjX', '3zeDrhkNv8872fC7CsOCpI', '4xrUp1M9XmKHFzRRyXIx71', '53fzZMZ3ENBY0BpLFOMy9p', '6GjMcck9c4i6cQo194xKl6', '7lCEnPYYkUuvnkrCbA6RCa', '7lGDjzmvAcNl6kEtn1rTaJ', '7qLJ8bzny3tynTPW2U2Anv'], 499: ['0LSWSMW0LVJX3fmSgDnk2A', '0rhmwOflgYrPntNuEe8chN', '1aucGNKimhgARC7iO2xLt2', '1pK8MLyjgvt8pNVkQCBnSg', '27qrMWYugzTnAvn2mtZdcx', '2B6i9ZY0NF8UkESEIL0taZ', '2srC8Ls3xXdRUH3n7jvHQD', '4HWzj6tf8nXvH7GzXAl1ld', '5h4pJfrTGROIhFJpTHa1Cu', '65Al3RSB7zeQeYcinysMxJ', '6A4MecoyRjnDtYeAZ7JGQf', '6Iyeo7CPHen8QEW4x31TpI', '6zwFIyWKbdHi9mwrQcrEY1']}
# Spotify track ids (found by web search) whose album id is wanted, when no album page turned up in search.
SPOTIFY_TRACKS = {653: ['6rvinglzwGWPaO9N9nnHeR', '1F5QCrmxZ18xN9jkOI94aU', '3w9fto7To0gKvUzYWxthP8'], 691: ['0JYiIbdztz6KjiJt9OXfYS', '55u4IiABkTGzBfs2iXwhbo'], 692: ['1sffL3V01zHOByMZxAMCfD', '1kZJYvBOXRBA6zgB5vocqY']}
# Track lists given by hand (n -> names) when the automatic edition is the wrong album: the iTunes edition that matches
# them best gives the lengths, and the playlists are scored against these names.
WANT = {459: ['Intruder', 'No Self Control', 'Start', "I Don't Remember", 'Family Snapshot', 'And Through the Wire',
              'Games Without Frontiers', 'Not One of Us', 'Lead a Normal Life', 'Biko'],
        474: ['Ha Ha I\'m Drowning', 'Sleeping Gas', 'Treason', 'Second Head', 'Poppies in the Field', 'Went Crazy',
              'Brave Boys Keep Their Promises', 'Bouncing Babies', 'Books', 'Thief of Baghdad', 'When I Dream'],
        493: ['Wordy Rappinghood', 'Genius of Love', 'Tom Tom Theme', "L'Éléphant", 'As Above, So Below', 'Lorelei', 'On, On, On, On...', 'Booming and Zooming'],
        477: ['Precious', 'The Phone Call', 'Up the Neck', 'Tattooed Love Boys', 'Space Invader', 'The Wait', 'Stop Your Sobbing',
              'Kid', 'Private Life', 'Brass in Pocket', 'Lovers of Today', 'Mystery Achievement'],
        510: ['Black Metal', 'To Hell and Back', 'Buried Alive', 'Raise the Dead', "Teacher's Pet", 'Leave Me in Hell', 'Sacrifice',
              "Heaven's on Fire", 'Countess Bathory', "Don't Burn the Witch", 'At War with Satan'],
        464: ['Requiem', 'Wardance', "Tomorrow's World", 'Bloodsport', 'The Wait', 'Complications', 'S.O. 36', 'Primitive'],
        610: ['If You All Get to Heaven', 'If You Let Me Stay', 'Wishing Well', "I'll Never Turn My Back on You (Father's Words)", 'Dance Little Sister',
              'Seven More Days', "Let's Go Forward", 'Rain', 'Sign Your Name', 'As Yet Untitled', "Who's Loving You"],
        611: ['If I Should Fall from Grace with God', 'Turkish Song of the Damned', 'Bottle of Smoke', 'Fairytale of New York', 'Metropolis',
              'Thousands Are Sailing', 'Fiesta', 'Medley: The Recruiting Sergeant / The Rocky Road to Dublin / The Galway Races',
              'Streets of Sorrow / Birmingham Six', 'Lullaby of London', 'Sit Down by the Fire', 'The Broad Majestic Shannon', 'Worms'],
        642: ['Honey', 'Come Down Softly to My Soul', 'How Does It Feel?', 'I Believe It', 'Revolution', 'Let Me Down Gently',
              'So Hot (Wash Away All of My Tears)', 'Suicide', 'Lord Can You Hear Me?']}
# 701–750 second pass
EXTRA_PLAYLISTS.update({734: ['OLAK5uy_lgrJED_9IOrwM_apbNCgfW59JSbzOobnE'], 749: ['OLAK5uy_nysk5zmSkNeO06IpaImRO7kzoP0Iw8YSs']})
SPOTIFY_TRACKS.update({707: ['3VqHuw0wFlIHcIPWkhIbdQ'], 726: ['46cTw1Xxyq8UX7MNAcFot7'], 737: ['288nj7X7UnHg2MrisAHMhh'],
                       746: ['7dU0naThnlYiA3EaQlMFhg', '2ZU4gtRTj53RJddZkqeOu7'], 751: ['76UmpTenKN4jWFagdnmVCo', '3Qy9rFEBH2h6FuJz0ofihm']})
WANT.update({
    714: ['Rockin Stroll', 'Confetti', "It's a Shame About Ray", 'Rudderless', 'My Drug Buddy', 'The Turnpike Down', 'Bit Part',
          "Alison's Starting to Happen", 'Hannah & Gabi', 'Kitchen', 'Ceiling Fan in My Spoon', 'Frank Mills'],
    725: ['Connected', 'Ground Level', 'Everything', 'Sketch', 'Fade Away', 'All Night Long', 'Step It Up', 'Playing with Fire',
          'Pressure', 'Chicken Shake', 'Creation', 'The End'],
    735: ['Sunflower', 'Can You Heal Us (Holy Man)', 'Wild Wood', 'Instrumental One (Part 1)', 'All the Pictures on the Wall',
          'Has My Fire Really Gone Out?', 'Country', 'Instrumental Two', '5th Season', 'The Weaver', 'Instrumental One (Part 2)',
          'Foot of the Mountain', 'Shadow of the Sun', 'Holy Man (Reprise)', 'Moon on Your Pyjamas'],
    751: ['Time Becomes', 'Planet of the Shapes', 'Lush 3-1', 'Lush 3-2', 'Impact (The Earth Is Burning)', 'Remind',
          'Walk Now...', 'Monday', 'Halcyon + On + On', 'Input Out']})
# 751–800 second pass
# 751–800 third pass
EXTRA_PLAYLISTS.update({758: ['PL9D59045747AB9F3A'], 752: ['PLUEMihO9lT7_LFYYRqJ-3mYsTAsM8AUqi', 'PLQeroY7XkiFGixwefr9FdTtSgOTrb6NP-', 'PLabhUJtJ9ji-BajW4D2QLdOSx6ojorKL5', 'PLhE094uPOcyb3b7DPWiwi1jhledlqp9AP']})
SPOTIFY_TRACKS.update({755: ['0SXXHxlC61nrSODzxjcEti', '64ceFPkKvlMxnVpGHdkmGU'], 776: ['39MevbqnkqtayGeHujte3n', '4YJoVxtIVoDL71wGwrqQ2j', '1XJ1LUBZDUFf5f6v38562R']})
WANT.update({
    752: ['Bathtub', 'G Funk Intro', 'Gin and Juice', 'W Balls', 'Tha Shiznit', 'Lodi Dodi', 'Murder Was the Case', 'Serial Killa',
          "Who Am I (What's My Name)?", 'For All My Niggaz & Bitches', "Ain't No Fun (If the Homies Can't Have None)", 'Doggy Dogg World',
          'Gz and Hustlas', 'Pump Pump'],
    795: ['Line Up', 'Annie', 'Connection', 'Car Song', 'Smile', 'Hold Me Now', 'S.O.F.T.', 'Indian Song', 'Blue', 'All-Nighter',
          'Waking Up', '2:1', 'Vaseline', 'Never Here', 'Stutter']})
# 801–850 second pass
SPOTIFY_TRACKS.update({808: ['7MJ7HFbvjTv9F60jdludgb', '1erjdjgmqLwoxNI1KfDvFq'], 809: ['6hK0ln2TayCrTbul9f3Kve', '2KTpsmJ3l6m0kkTAcO4IpV'],
                       810: ['6m5LnidB0c4sBInIrk4j1X', '5oefjw7i602MPGSTUjeiQJ'], 821: ['5bZpHnxYgIH7GLVTRkc1rC', '2AgMxAo250PE5JR6olyz14'],
                       826: ['0mX3QD1FSB6a55vDmS78kZ', '2gDqY4FScnezysSpsw2Tpa'], 840: ['2WRzpLD8qDRrxMXc63E5WJ'],
                       842: ['76mCw71NjJoyUzwZvm08ts', '0mPi7OzFdbqdjtRrtMSCC8'], 848: ['1cFYFeniVjSqQswDGyYLyM', '1a5PrrbiFfLJWKSV68TJZY'],
                       835: ['2q3Q18Iog6pyB7ooQHVzc7', '2yvvqbSGet4LAXzpwaroPz']})
SPOTIFY_CHECK.update({806: ['0MbeekWXeO9BFjImhNH5gf', '6avrxdTyI3jUxVPVEtmT8o'], 812: ['2EvCXuFV2Oduqo3cVqeU5W', '490GQTZ4gHnqAe83K9eGjt'],
                      816: ['7ssmEk3nxZq0EGOdGz1kAu', '7N0W5QxnRMP3s1mMxfQo1p'], 832: ['0YI7QPNUGq8NTB6Nd8nWfd', '56vFkneGivqQcoNQq362iZ'],
                      835: ['6Zj0LtkX3xTnaNwO1Bia3Z', '5MrIBMRh9FJf1iB2LGeMeS']})
WANT.update({
    806: ['Timeless', 'Saint Angel', 'State of Mind', 'This Is a Bad', 'Sea of Tears', 'Jah', 'Angel', 'Adrift', 'Kemistry', 'Sensual',
          'You & Me', 'Still Life'],
    821: ['Roots Bloody Roots', 'Attitude', 'Cut-Throat', 'Ratamahatta', 'Breed Apart', 'Straighthate', 'Spit', 'Lookaway', 'Dusted',
          'Born Stubborn', 'Jasco', 'Itsári', 'Ambush', 'Endangered Species', 'Dictatorshit']})
# 851–900 second pass
EXTRA_PLAYLISTS.update({868: ['OLAK5uy_nnykGh8RUrN5xlrj3NnXcKQKBdQOsfyVw', 'PLmOQOIaLKSCgmgi-581mSROwwZb5COqJ9'],
                        900: ['PLdglF_k2dXLWDFD7bBSBUUa2q6H6HvAKw', 'PLm4I8tP6UbWbFVjU6G2i-_UgNWgJS2t9G']})
YT_QUERY.update({892: 'Flaming Lips The Soft Bulletin 1999 full album Race for the Prize', 853: 'Mariah Carey Butterfly 1997 full album Honey'})
SPOTIFY_TRACKS.update({876: ['7viecLL3E8L4OJ6OGzgs4n', '2JdQsEl2hijBasn39JALBR'], 890: ['1cYo2sWoz6ybZKUwjMxy0K', '0XcEly9Np3fhe84FneCIDh'],
                       894: ['6JIq2EDv3kR2oIj0X9R0AR', '6uAX7MehkRJeHgdycRfa5Y'], 896: ['3MjUtNVVq3C8Fn0MP3zhXa']})
SPOTIFY_CHECK.update({853: ['6qoD3WaEeRFUTIjQLPsSjy', '7aDBFWp72Pz4NZEtVBANi9'], 859: ['56YzQ0dhmRMDryZsrjdHun', '4GMgNPA4fMv3U0QQsdRLJk'],
                      865: ['5dbW25KDJWBkv2gtaQdmxJ', '7G7cCHgQKbDD6zvwDQZyJu'], 877: ['0gsiszk6JWYwAyGvaTTud4', '5eAoPNZzWRn2C409kAUsbE'],
                      878: ['4PQFrVyQ6xWGjbq5kkVVaX', '0IPrsbOiX2tgYnJw3l8AbR'], 881: ['74HTGmkjvbilVJjTCsneXD', '4rezpGly476QPhbmG2SITq'],
                      888: ['6lijTrmA0yAucg4Axbj1up', '3yIFysHpeQKb1dAuHQICVW'], 895: ['1pAakXNiYkGzS7gRzxGyHn', '0vE6mttRTBXRe9rKghyr1l']})
WANT.update({
    853: ['Honey', 'Butterfly', 'My All', 'The Roof (Back in Time)', 'Fourth of July', 'Breakdown', 'Babydoll', 'Close My Eyes',
          'Whenever You Call', 'Fly Away (Butterfly Reprise)', 'The Beautiful Ones', 'Outside'],
    892: ['Race for the Prize', 'A Spoonful Weighs a Ton', 'The Spark That Bled', 'The Spiderbite Song', "Buggin'", 'What Is the Light?',
          'The Observer', "Waitin' for a Superman", 'Suddenly Everything Has Changed', 'The Gash', 'Feeling Yourself Disintegrate',
          'Sleeping on the Roof']})
# 901–950 second pass
YT_QUERY.update({911: 'U2 All That You Can\'t Leave Behind 2000 full album', 936: 'Gillian Welch Time The Revelator full album'})
SPOTIFY_TRACKS.update({908: ['6I5eFZDHx6BWKztvq30AHH', '5vIniO9ClKFIeMG4oFy7mG'], 917: ['3AJwUDP919kvQ9QcozQPxg'], 920: ['5u3ppK9fCA5gBdFVdRywOf', '1w4xMh8oVSS5ylNtNYSwZX'],
                       923: ['48wtZV65X2JwfkxplBnOBI', '7prAcROrmK9ZUIN5EgSXTe'], 925: ['7xb1hyP7AoQJ36iGBWotvK'], 926: ['7yXIJ2sBHsUAWjL1FqcgcH'],
                       950: ['0NJjOFqKFSbbHM8HOke7GA', '02DNqgAg5jtr5BoaB8zmSC']})
SPOTIFY_CHECK.update({902: ['7LKQtdC6uWxqLzSbDonFij', '4dTCMO1A5HyZ1upLiw0zAE'], 904: ['2E1q8eohZZ1BUQ7Bq5WUIY', '6pJSkIvinycPLXlH8BG8lS'],
                      907: ['6Vp1b0Xsv8dbpBZfvkWSZG', '6HeyW5oBSlc7CrSoyJ67Fd', '4onsS61UR8uhzfRbQIyYES'], 909: ['3hGM52SddRWwI4yatyZYmb', '7McxSOyMEbKhHlCqBIaQ6w'],
                      912: ['6PFPjumGRpZnBzqnDci6qJ', '2pKw6GERJVAD61449B1EEM'], 914: ['7y0QwysyQgSf9fyBFr6Q3x', '7qdi1B4jqHEA5NvV34haRP'],
                      916: ['1BROiAW4CtstJEwqMds6Pu', '3cADvHRdKniF9ELCn1zbGH'], 918: ['5Vdh9NszWNh82xuzTBdNHO', '72GMOkq47rXzdAMJrjf4RV'],
                      921: ['6t7956yu5zYf5A829XRiHC', '5xifZlByZcZecgkP7sYSoW', '04Xgxe2lRRSK9MN3xDt16s'], 934: ['2HcjLD0ButtKsQYqzoyOx9', '45X9HQfGolie9tQHYD4bD1'],
                      935: ['2yNaksHgeMQM9Quse463b5', '5yIIxsXGdQucmqHN82xGig', '2k8KgmDp9oHrmu0MIj4XDE'], 939: ['5ElnMKBlg21XKlqAynLH9x', '4JG7AXihvAyyliHwcTDovw'],
                      940: ['54I5tDCMjnNVWSENHg8EDH', '2NaYh6NEBGVAV9la4vKJSK'], 941: ['4WOZU9evfEO7eI6ICsoGN0', '31KW4rB15ZKePadjCPv1xw'],
                      944: ['0f0nGqpgiu4z6wg0Mrcs8L', '2w9KjhjN2oMGhEvE15HK5T'], 946: ['4hF66CtQgAPU6LzedAQi4V', '2DV2rxp2DAqCJyBC2Zc1Fu'],
                      948: ['3ul9GmXlTkmRMh3OciXxFR'], 951: ['2SuUATTRN6HEIrCTGH9Xes', '09atk4oR2eXg6ICTo0mdhP', '2BlL4Gv2DLPu8p58Wcmlm9']})
WANT.update({
    911: ['Beautiful Day', "Stuck in a Moment You Can't Get Out Of", 'Elevation', 'Walk On', 'Kite', 'In a Little While', 'Wild Honey',
          'Peace on Earth', 'When I Look at the World', 'New York', 'Grace'],
    936: ['Revelator', 'My First Lover', 'Dear Someone', 'Red Clay Halo', 'April the 14th Part 1', 'I Want to Sing That Rock and Roll',
          'Elvis Presley Blues', 'Ruination Day Part 2', 'Everything Is Free', 'I Dream a Highway']})
# Numbers above are book numbers after the White Album was inserted as #134 (2026-10; older batch files use the old numbers).
# White Album (#134)
EXTRA_PLAYLISTS.update({134: ['OLAK5uy_nAhSkEAxM0tk1ss30ACox-roQiREyiWrg', 'PLpwHb97XjkRsC8lcHjmy4DlHZicQuQE5M', 'PLycVTiaj8OI80AsTGjYJAPi7-i8kTH-Bq', 'PLZczbX_Vy3bDxm2by1AZP2T1qonTinG7c']})
YT_QUERY.update({134: 'The Beatles White Album 1968 full album'})
WANT.update({134: ['Back in the U.S.S.R.', 'Dear Prudence', 'Glass Onion', 'Ob-La-Di, Ob-La-Da', 'Wild Honey Pie',
  'The Continuing Story of Bungalow Bill', 'While My Guitar Gently Weeps', 'Happiness Is a Warm Gun', 'Martha My Dear',
  "I'm So Tired", 'Blackbird', 'Piggies', 'Rocky Raccoon', "Don't Pass Me By", "Why Don't We Do It in the Road?", 'I Will',
  'Julia', 'Birthday', 'Yer Blues', "Mother Nature's Son", "Everybody's Got Something to Hide Except Me and My Monkey",
  'Sexy Sadie', 'Helter Skelter', 'Long, Long, Long', 'Revolution 1', 'Honey Pie', 'Savoy Truffle', 'Cry Baby Cry',
  'Revolution 9', 'Good Night']})

# 952–1001 second pass
EXTRA_PLAYLISTS.update({976: ['OLAK5uy_nP8WL3zRNsgq9kN-qGdjqx0S12VFMX4gg', 'PL1PBfSEqTSeDOdFW-TztsPsGLTTLp8SB3'],
  978: ['OLAK5uy_mKyu9Gu2T9PtSdJT_zRo2uoux3eOEE9LE'], 995: ['PLJvUA1YdQ7RjA8skfxx4u9uChTUN5jXWq']})
YT_QUERY.update({977: 'Morrissey You Are the Quarry 2004 full album', 995: 'Rufus Wainwright Want Two 2004 full album Agnus Dei'})
WANT.update({
  995: ['Agnus Dei', 'The One You Love', 'Peach Trees', 'Little Sister', 'The Art Teacher', 'This Love Affair', 'Gay Messiah',
        'Hometown Waltz', 'Memphis Skyline', 'Waiting for a Dream', 'Crumb by Crumb', "Old Whore's Diet"],
  972: ['Intro', 'What Up Gangsta', 'Patiently Waiting', 'Many Men (Wish Death)', 'In da Club', 'High All the Time', 'Heat',
        "If I Can't", 'Blood Hound', 'Back Down', 'P.I.M.P.', 'Like My Style', 'Poor Lil Rich', '21 Questions', "Don't Push Me",
        'Gotta Make It to Heaven'],
  997: ['Jenny Was a Friend of Mine', 'Mr. Brightside', 'Smile Like You Mean It', 'Somebody Told Me', "All These Things That I've Done",
        "Andy, You're a Star", 'On Top', 'Change Your Mind', 'Believe Me Natalie', 'Midnight Show', 'Everything Will Be Alright'],
})

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
