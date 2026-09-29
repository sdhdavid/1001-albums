"""Merge tools/stories.py into dist/pilot.json as album-level "story" and "picks"."""
import json, sys
sys.path.insert(0, 'tools'); from stories import STORIES
p = json.load(open('dist/pilot.json'))
for n, s in STORIES.items():
    a = p[str(n)]; names = [t[0] for t in a['tracks']]
    assert len(s['story']) == 3, n
    for name, _ in s['picks']:
        assert name in names, (n, name)
    a['story'] = s['story']; a['picks'] = [list(x) for x in s['picks']]
json.dump(p, open('dist/pilot.json', 'w'), ensure_ascii=False, indent=2); open('dist/pilot.json', 'a').write('\n')
print('stories:', len(STORIES), 'albums:', len(p))
