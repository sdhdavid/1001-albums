"""Merge tools/stories.py into dist/albums/N.json as album-level "story" and "picks"."""
import json, sys
sys.path.insert(0, 'tools'); from stories import STORIES; import store
p = {str(n): a for n, a in store.load_all().items()}
for n, s in STORIES.items():
    a = p[str(n)]; names = [t[0] for t in a['tracks']]
    assert len(s['story']) == 3, n
    for name, _ in s['picks']:
        assert name in names, (n, name)
    a['story'] = s['story']; a['picks'] = [list(x) for x in s['picks']]
store.save_all({int(k): v for k, v in p.items()})
print('stories:', len(STORIES), 'albums:', len(p))
