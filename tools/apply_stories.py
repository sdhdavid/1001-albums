"""Write story/picks from a stories module into dist/albums/N.json (audio data untouched).

Usage: python3 tools/apply_stories.py stories            (1–50)
       python3 tools/apply_stories.py stories_51_100     (51–100)
A module defines STORIES = {n: {'story': [para, ...], 'picks': [(track name, note), ...]}}.
Pick names must equal track names (spelling/apostrophes are normalised to the track's own).
"""
import importlib, re, sys
sys.path.insert(0, 'tools'); import store

def norm(s): return re.sub(r'[^a-z0-9]+', '', s.replace('’', "'").lower())

stories = importlib.import_module(sys.argv[1]).STORIES
for n, s in sorted(stories.items()):
    a = store.load(n); names = {norm(t[0]): t[0] for t in a['tracks']}
    assert len(s['story']) >= 3, n
    picks = []
    for name, note in s['picks']:
        assert norm(name) in names, (n, name)
        picks.append([names[norm(name)], note])
    a['story'] = list(s['story']); a['picks'] = picks
    store.save(n, a)
print('updated', len(stories), 'albums')
