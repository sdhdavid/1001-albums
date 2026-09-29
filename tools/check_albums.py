"""Validate album data. Usage: python3 tools/check_albums.py [N ...]   (no numbers = every album)

Also imported by add_albums.py. Exits non-zero with a list of problems.
"""
import re, sys
sys.path.insert(0, 'tools'); import store

def problems(n, a, known):
    """Return a list of problems with album n's data (empty list = ready to publish)."""
    out = []
    if n not in known: out.append('not in the catalog (albums.json)')
    if not re.fullmatch(r'[A-Za-z0-9]{22}', a.get('spotifyAlbum') or ''): out.append('spotifyAlbum must be a 22-character id')
    tracks = a.get('tracks') or []
    if not tracks: return out + ['no tracks']
    names = [t[0] for t in tracks]
    if len(set(names)) != len(names): out.append('duplicate track names')
    if a.get('youtubePlaylist'):
        if not re.fullmatch(r'(PL|OLAK5uy_)[A-Za-z0-9_-]{16,}', a['youtubePlaylist']): out.append('youtubePlaylist looks wrong')
        if a.get('fullAlbumVideo'): out.append('both youtubePlaylist and fullAlbumVideo')
        for t in tracks:
            if not (len(t) == 3 and t[1] is None and isinstance(t[2], int) and t[2] >= 0): out.append(f'playlist track must be [name, null, index]: {t}')
    elif a.get('fullAlbumVideo') is True:
        starts = [t[3] for t in tracks if len(t) == 4]
        if len(starts) != len(tracks) or starts != sorted(starts) or starts[0] != 0: out.append('video chapters need increasing start seconds beginning at 0')
        if any(not re.fullmatch(r'[A-Za-z0-9_-]{11}', str(t[1])) for t in tracks): out.append('bad video id')
        if len({t[1] for t in tracks}) != 1: out.append('chapters must share one video')
    else:  # one YouTube video per song: [name, videoId]
        for t in tracks:
            if not re.fullmatch(r'[A-Za-z0-9_-]{11}', str(t[1])): out.append(f'bad video id: {t}')
    d = a.get('durations') or []
    if len(d) != len(tracks) or any(not re.fullmatch(r'\d{1,2}:\d{2}', str(x)) for x in d): out.append('durations must be "m:ss", one per track')
    f = a.get('focus') or []
    if not (2 <= len(f) <= len(tracks)) or any(not isinstance(i, int) or not 0 <= i < len(tracks) for i in f) or len(set(f)) != len(f): out.append('focus: 2+ distinct valid track indexes')
    s = a.get('story') or []
    if not 3 <= len(s) <= 5 or any(not isinstance(p, str) or len(p) < 40 for p in s): out.append('story must be 3–5 paragraphs')
    picks = a.get('picks') or []
    if len(picks) != min(3, len(tracks)): out.append('need three picks (or one per track when the album has fewer)')
    for p in picks:
        if p[0] not in names: out.append(f'pick not in tracks: {p[0]}')
    return out

def main(argv):
    known = {e['n'] for e in store.catalog()}
    wanted = [int(x) for x in argv] or store.numbers()
    bad = 0
    for n in wanted:
        for msg in problems(n, store.load(n), known): print(f'#{n}: {msg}'); bad += 1
    print(f'{len(wanted)} albums checked, {bad} problems')
    return 1 if bad else 0

if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
