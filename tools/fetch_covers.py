"""Fetch the cover image address of every playable album from Spotify's oEmbed endpoint.

Usage: python3 tools/fetch_covers.py tools/covers.json     (runs in GitHub Actions: "Fetch covers"; Spotify is blocked here)

Keeps addresses already in the output file, asks slowly, and waits when Spotify says "too many requests".
store.rebuild_index() copies the addresses into dist/albums.json as "cover", so visitors' browsers don't
have to ask Spotify for each cover.
"""
import json, sys, time, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, 'tools')
import store

out = sys.argv[1]
try: covers = json.load(open(out))
except FileNotFoundError: covers = {}
for n in store.numbers():
    sid = store.load(n).get('spotifyAlbum')
    if not sid or covers.get(sid): continue
    url = 'https://open.spotify.com/oembed?url=' + urllib.parse.quote(f'https://open.spotify.com/album/{sid}', safe='')
    for attempt in range(5):
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30))
            if str(data.get('thumbnail_url', '')).startswith('https://'): covers[sid] = data['thumbnail_url']
            break
        except urllib.error.HTTPError as e:
            if e.code != 429: print(n, sid, e.code, flush=True); break
            time.sleep(30 * (attempt + 1))
        except Exception as e:
            print(n, sid, e, flush=True); time.sleep(5)
    time.sleep(.5)
json.dump(covers, open(out, 'w'), indent=1, sort_keys=True)
print(len(covers), 'covers')
