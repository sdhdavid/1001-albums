"""Download the numbered 2005 edition list (MusicBrainz series) as catalog entries.

Runs where MusicBrainz is reachable (GitHub Actions: "Fetch catalog"). Writes
tools/catalog-2005.json = [{n, year, title, artist}, ...] in book order and
prints how it compares with the entries already in dist/albums.json.
"""
import json, sys, time, urllib.request
SERIES = '4bc2a338-e1d8-4546-8a61-640da8aaf888'
UA = {'User-Agent': '1001-albums-site/1.0 (https://github.com/sdhdavid/1001-albums)'}

def get(path, pause=1.1):
    time.sleep(pause)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request('https://musicbrainz.org/ws/2/' + path + '&fmt=json', headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            print('retry', attempt, path[:80], e, file=sys.stderr); time.sleep(5 + attempt * 5)
    raise SystemExit('giving up on ' + path)

def credit(ac): return ''.join(c['name'] + c.get('joinphrase', '') for c in ac).strip()

series = get(f'series/{SERIES}?inc=release-group-rels')
rows = []
for r in series['relations']:
    rg = r.get('release_group')
    if not rg: continue
    rows.append((int(r.get('attribute-values', {}).get('number') or r.get('ordering-key') or 0), rg))
rows.sort(key=lambda x: x[0])
print('relations:', len(rows), 'numbers unique:', len({n for n, _ in rows}), 'range', rows[0][0], rows[-1][0], file=sys.stderr)
old = {a['n']: a for a in json.load(open('dist/albums.json'))}
out = []
for n, rg in rows:
    full = get(f"release-group/{rg['id']}?inc=artist-credits")
    out.append({'n': n, 'year': int((full.get('first-release-date') or '0')[:4]), 'title': full['title'], 'artist': credit(full['artist-credit'])})
    if n in old and {k: old[n][k] for k in ('year', 'title', 'artist')} != {k: out[-1][k] for k in ('year', 'title', 'artist')}:
        print('DIFF', n, old[n], out[-1], file=sys.stderr)
json.dump(out, open('tools/catalog-2005.json', 'w'), ensure_ascii=False, indent=0)
print('done', len(out), file=sys.stderr)
