"""Fill "durations" into a batch file.  Usage: python3 tools/merge_durations.py BATCH.json DURATIONS.json

DURATIONS.json is the map printed between ===DURATIONS-BEGIN/END=== by the
"Fetch track durations" workflow ({"51": ["3:04", null, ...]}). Missing (null)
lengths are left as a problem for you to fill by hand: the script refuses to write them.
Compare each album's total with the book's running time before adding it.
"""
import json, sys
batch = json.load(open(sys.argv[1])); got = json.load(open(sys.argv[2])); bad = 0
for a in batch:
    d = got.get(str(a['n']))
    if not d: print(f"#{a['n']}: no durations found"); bad += 1; continue
    holes = [a['tracks'][i][0] for i, x in enumerate(d) if x is None]
    if holes: print(f"#{a['n']}: missing lengths for {holes}"); bad += 1; continue
    a['durations'] = d
    print(f"#{a['n']}: total {sum(int(x.split(':')[0]) * 60 + int(x.split(':')[1]) for x in d) // 60} min")
if bad: sys.exit(1)
json.dump(batch, open(sys.argv[1], 'w'), ensure_ascii=False, indent=2); open(sys.argv[1], 'a').write('\n')
