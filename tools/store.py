"""Shared access to the album data.

dist/albums.json   catalog (n/year/title/artist). Albums that can be played on
                   the site also carry "ready": true and "spotifyAlbum" (the
                   list needs the cover before the album itself is opened).
dist/albums/N.json everything the player, story and track list need for album N.
"""
import json, os, sys
sys.path.insert(0, 'tools'); from genres import TAGS

ALBUMS_DIR = 'dist/albums'
CATALOG = 'dist/albums.json'

def _dump(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2); f.write('\n')

def catalog():
    return json.load(open(CATALOG))

def numbers():
    return sorted(int(f[:-5]) for f in os.listdir(ALBUMS_DIR) if f.endswith('.json'))

def load(n):
    return json.load(open(f'{ALBUMS_DIR}/{n}.json'))

def load_all():
    return {n: load(n) for n in numbers()}

def save(n, album):
    os.makedirs(ALBUMS_DIR, exist_ok=True)
    _dump(album, f'{ALBUMS_DIR}/{n}.json')

def save_all(albums):
    for n, a in albums.items(): save(n, a)
    rebuild_index()

def rebuild_index():
    """Refresh the ready/spotify flags in the catalog from the per-album files."""
    have = {n: load(n) for n in numbers()}
    try: covers = json.load(open(os.path.join(os.path.dirname(__file__), 'covers.json')))   # from the "Fetch covers" workflow
    except FileNotFoundError: covers = {}
    out = []
    for e in catalog():
        e = {k: e[k] for k in ('n', 'year', 'title', 'artist')}
        if e['n'] in have:
            e['ready'] = True
            if have[e['n']].get('spotifyAlbum'):   # albums not on Spotify (noSpotify) have no id and no cover from there
                e['spotifyAlbum'] = have[e['n']]['spotifyAlbum']
                if covers.get(e['spotifyAlbum']): e['cover'] = covers[e['spotifyAlbum']]
        if e['n'] in TAGS: e['genres'] = TAGS[e['n']]
        out.append(e)
    with open(CATALOG, 'w') as f:  # one album per line keeps the 1001-entry file compact and diffable
        f.write('[\n' + ',\n'.join(json.dumps(e, ensure_ascii=False) for e in out) + '\n]\n')
