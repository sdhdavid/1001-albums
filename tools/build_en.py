#!/usr/bin/env python3
"""Builds the English version's data (dist/en/albums.json + dist/en/albums/N.json) from the Hebrew site's data.

Only albums that have an entry in tools/stories_en.py are marked ready (playable) in the English catalog; the rest
of the book's list stays in it so the decade rail keeps the full picture. Tracks, durations, focus, YouTube and
Spotify ids are copied from dist/albums/N.json; story and picks come from stories_en.py; the Hebrew-only `note` and
`guide` are dropped. Re-run after changing stories_en.py or the Hebrew catalog:  python3 tools/build_en.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stories_en import EN  # noqa: E402

DIST = Path(__file__).resolve().parent.parent / 'dist'
OUT = DIST / 'en'
GENRES = {
    'סטנדרטים וקברט': 'Standards & Cabaret', "רוק'נרול": "Rock 'n' Roll", 'קאנטרי': 'Country', 'פולק': 'Folk',
    "ג'אז": 'Jazz', 'מוזיקת עולם': 'World Music', 'סול ופאנק': 'Soul & Funk', 'בלוז': 'Blues', 'רוק': 'Rock',
    'פופ': 'Pop', 'פרוגרסיב ופסיכדליה': 'Prog & Psychedelia', 'פאנק וניו וויב': 'Punk & New Wave',
    'רוק אלטרנטיבי': 'Alternative Rock', 'מטאל': 'Metal',
    'היפ הופ': 'Hip Hop', 'רגאיי': 'Reggae', 'אלקטרוני': 'Electronic',
}


def main():
    (OUT / 'albums').mkdir(parents=True, exist_ok=True)
    for old in (OUT / 'albums').glob('*.json'):
        if int(old.stem) not in EN:
            old.unlink()
    catalog = json.loads((DIST / 'albums.json').read_text(encoding='utf-8'))
    out = []
    for a in catalog:
        e = {k: v for k, v in a.items() if k not in ('ready', 'spotifyAlbum', 'genres')}
        if a.get('genres'):
            e['genres'] = [GENRES[g] for g in a['genres']]
        if a['n'] in EN:
            assert a.get('ready') and a.get('spotifyAlbum'), a['n']
            e['ready'] = True
            e['spotifyAlbum'] = a['spotifyAlbum']
        out.append(e)
    (OUT / 'albums.json').write_text('[\n' + ',\n'.join(json.dumps(e, ensure_ascii=False) for e in out) + '\n]\n', encoding='utf-8')
    for n, text in EN.items():
        d = json.loads((DIST / 'albums' / f'{n}.json').read_text(encoding='utf-8'))
        for k in ('note', 'guide'):
            d.pop(k, None)
        names = [t[0] for t in d['tracks']]
        for name, _ in text['picks']:
            assert name in names, (n, name)
        d['story'], d['picks'] = text['story'], text['picks']
        (OUT / 'albums' / f'{n}.json').write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'English catalog: {len(out)} albums, {len(EN)} translated: {sorted(EN)}')


if __name__ == '__main__':
    main()
