"""English stories and picks for the English version of the site (dist/en/).

Faithful translations of the Hebrew texts in dist/albums/N.json (same four paragraphs, same three picks).
Pick names must equal the track names in albums/N.json. Built into dist/en/ by tools/build_en.py.
"""
EN = {}


def add(n, story, picks):
    EN[n] = {'story': story, 'picks': picks}


add(1, [
    "By the early 1950s Frank Sinatra's career looked finished. The bobby-soxers who had screamed for him in the forties had moved on to younger stars, his voice had suffered, Columbia Records had let him go, and his stormy marriage to the actress Ava Gardner was on the edge of collapse. Then everything turned around: in 1953 he signed with Capitol and began working with the arranger Nelson Riddle, and a year later he won an Oscar for his role in From Here to Eternity. In the Wee Small Hours, released in April 1955, is the moment when that comeback sounds most personal.",
    "Sixteen songs, all about the same thing: night, loneliness and a love that has ended. Almost all of them are older songs by the great American songwriters, such as Duke Ellington, Cole Porter, and Rodgers and Hart; only the title song was written especially for the album. Riddle wrapped the voice in soft strings, woodwinds and a quiet piano, and never tried to impress. And Sinatra, who ten years earlier had been a teen idol, sings like a man sitting alone at a bar at three in the morning: quietly, without overdoing it, every word in its place. Even the cover tells the story: he stands alone on a dark street, under a streetlamp, with a cigarette.",
    "In those years a long-playing record was usually a pile of unrelated songs. Sinatra and Riddle built a whole record around a single mood, which is why many people regard it as one of the first concept albums in popular music. It also came out as a single 12-inch LP, one of the first of its kind in pop, reached number two on the American album chart, and showed the record companies that people were willing to sit down and listen to a record from beginning to end, like one story. A year later Sinatra and Riddle did exactly the opposite, on album 7 in the book.",
    "Save this album for the night: a late hour, dim light, and no skipping. It is built so that every song continues the one before it. And if you want to see how far you can go with the same singer and the same arranger, move on afterwards, in daylight, to album 7 in the book.",
], [
    ['In The Wee Small Hours Of The Morning', "The title song, the only one written especially for the album. From the very first line it sets the hour: the middle of the night, and sleep won't come."],
    ['Mood Indigo', "The Duke Ellington classic, slow and deep blue. Notice how little Riddle plays around the voice, and how much that is enough."],
    ['It Never Entered My Mind', "A ballad by Rodgers and Hart, and perhaps the most broken moment on the album. Sinatra sings it like someone only now understanding what he has lost."],
])

add(2, [
    "In the summer of 1954, in the small Sun studio in Memphis, a 19-year-old truck driver named Elvis Presley recorded his first records, with the guitarist Scotty Moore and the bassist Bill Black. Within a year he had become a phenomenon in the American South, and in November 1955 the giant RCA bought out his contract for 35,000 dollars, a huge sum in those days. In January 1956 he recorded Heartbreak Hotel in Nashville, and in those same weeks he appeared on national television for the first time and caused an uproar. His debut album came out in March 1956, just as all of America began to talk about him.",
    "The album joins two kinds of recordings: new songs recorded at RCA, and five older recordings from the Sun period that had not yet been released. You hear here all the ingredients rock and roll was built from: rhythm and blues by Black singers (Ray Charles's I Got a Woman, Little Richard's Tutti Frutti), white country, old ballads and gospel. All of it passes through Elvis's voice: teasing, trembling, panting, and sometimes almost laughing. The band is small and plays lean and fast, with Moore's guitar, Black's bass and D. J. Fontana's drums.",
    "It was the first rock and roll album to reach number one on the American album chart, and it stayed there for ten weeks. In doing so it proved that the new music was not just cheap singles for teenagers but big business too. The cover also became an icon: Elvis mid-shout with his guitar, in black and white, with his name above in pink and green letters. Twenty-three years later The Clash copied it for the cover of London Calling, as a tribute to the moment when it all began.",
    "Try a comparison: listen to Tutti Frutti here, and right after it Little Richard's original on album 14 in the book. Elvis sang it a year after the original, and you can hear what he took from it and what he added of his own.",
], [
    ['Blue Suede Shoes', "The song by Carl Perkins, Elvis's friend from Sun, opens the album with a bang. Elvis's version turned it into the anthem of the era."],
    ['I Got a Woman', "A Ray Charles hit, from which Elvis took the energy of gospel into rock and roll. Notice how he stretches out the first word."],
    ['Blue Moon', "A recording from the Sun period: an old ballad that becomes something strange and ghostly, with long echo and almost no accompaniment."],
])

add(3, [
    "Ira and Charlie Loudermilk grew up in the twenties and thirties in a poor farming family in a mountainous part of northern Alabama. At home and in church they learned to sing in harmony, and along the way they also absorbed ancient ballads passed down from generation to generation. When they began performing they changed the family name to Louvin, and in the fifties they became one of country music's great brother duos, mostly with gospel songs. Tragic Songs of Life, their debut album, was recorded in Nashville in May 1956. In the very year Elvis conquered the radio, they chose to record old ballads about death, parting and sin.",
    "The accompaniment is modest: Ira plays mandolin, Charlie guitar, and a few more players sit in the background. But the stars are the two voices. Ira sings very high, in a sharp, clear tone, and Charlie below him, in a lower, warmer voice, and they are so close that it is sometimes hard to tell who is singing what. The songs tell harsh stories: a girl murdered by her lover, a young mother who died in a storm at her father's door, a soldier asking that his mother be told he will not come back. And they sing all of it without drama and without tears, quietly, almost like a prayer. That is what makes it chilling.",
    "At a time when country music was starting to try to sound modern, the Louvin Brothers devoted a whole album to the songs they grew up on, and because of that it sounds almost like a concept album. Their harmonies influenced the Everly Brothers directly, and through them a whole generation of rock and pop singers. Years later they were rediscovered by Gram Parsons, one of the pioneers of country rock, who recorded songs of theirs and gave Emmylou Harris a tape of them; one of her first big hits was a Louvin Brothers song. The duo itself broke up in 1963, and two years later Ira was killed in a car accident.",
    "On this album the words matter as much as the music, so it is worth looking them up and reading along as you listen. And after In The Pines, try listening to Where Did You Sleep Last Night by Nirvana, from their MTV acoustic performance: it is the same folk song, almost forty years later.",
], [
    ['Knoxville Girl', "A murder ballad rooted in ancient English ballads, sung in an almost sweet quiet, and that is what makes it even more frightening."],
    ['In The Pines', "An ancient folk song that later reached Nirvana too. Here it sounds isolated and cold, like the night it describes."],
    ['Kentucky', "The perfect example of the brothers' tight harmony: two voices that sound like one."],
])
