"""Add or update albums from a batch file.  Usage: python3 tools/add_albums.py tools/batches/NAME.json

A batch file is a JSON list; each entry is one album's data plus its book number:
  {"n": 51,
   "youtubePlaylist": "PL…",                      (or "fullAlbumVideo": true with [name, videoId, null, startSeconds] tracks)
   "spotifyAlbum": "22-character id",
   "tracks": [["Song", null, 0], ...],            (playlist index = position in the YouTube playlist)
   "durations": ["3:04", ...],                    (from fetch_durations.py + merge_durations.py)
   "focus": [0, 3, 7],                            (track indexes of the short queue)
   "story": ["who & when", "what you hear", "why it matters"],
   "picks": [["Song", "why"], ...×3]}
Every entry is validated (tools/check_albums.py). Nothing is written unless all pass;
then dist/albums/N.json is written and the catalog's ready/spotify flags are refreshed.
"""
import json, sys
sys.path.insert(0, 'tools'); import store; from check_albums import problems

def main(path):
    batch = json.load(open(path)); known = {e['n'] for e in store.catalog()}; bad = 0
    for a in batch:
        for msg in problems(a['n'], a, known): print(f"#{a['n']}: {msg}"); bad += 1
    if bad: print(f'{bad} problems, nothing written'); return 1
    numbers = sorted(a['n'] for a in batch)
    for a in batch:
        n = a.pop('n'); store.save(n, a)
    store.rebuild_index()
    print('written:', ', '.join(map(str, numbers)))
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv[1]))
