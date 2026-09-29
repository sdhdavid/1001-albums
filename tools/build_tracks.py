import json, re, sys, unicodedata
sys.path.insert(0, 'tools'); from tracklists import TRACKS
CORRECTED = {26: 'PLowQCq3Ss89ikMwB_bPRQuaQttWp0xaD4', 31: 'PL1a1FcevWP19h-lU6yce1_TuLRWCzXJ20', 34: 'PLowQCq3Ss89jz1iejIedRBojbvYe3MSzK'}
CONTINUOUS = {27, 29, 47, 49}
def norm(s): return re.sub(r'[^a-z0-9 ]', '', unicodedata.normalize('NFKD', s.replace('’', "'")).encode('ascii', 'ignore').decode().lower())
def secs(d): m, s = d.split(':'); return int(m) * 60 + int(s)
p = json.load(open('dist/pilot.json'))
for n, tracks in TRACKS.items():
    a = p[str(n)]
    names = [(t[0] if isinstance(t, tuple) else t).replace("'", '’') for t in tracks]
    focus = []
    for h in a['guide'].get('highlights', []):
        hn = norm(h)
        idx = next((i for i, x in enumerate(names) if norm(x) == hn), None)
        if idx is None: idx = next((i for i, x in enumerate(names) if hn in norm(x) or norm(x) in hn), None)
        if idx is None: print('focus miss', n, h)
        elif idx not in focus: focus.append(idx)
    if len(focus) < 2: focus = sorted({0, len(names) // 2, len(names) - 1})
    video = a.get('youtubeAlbumVideo'); playlist = CORRECTED.get(n) or a.get('youtubeAlbumPlaylist')
    for k in ('externalAlbum', 'youtubeAlbumPlaylist', 'youtubeAlbumVideo', 'youtubeAlbumComplete', 'tracks', 'youtubePlaylist', 'focus'):
        a.pop(k, None)
    if n in CONTINUOUS:
        start, out = 0, []
        for name, (_, d) in zip(names, tracks):
            out.append([name, video, None, start]); start += secs(d)
        a['fullAlbumVideo'] = True; a['tracks'] = out
    else:
        a['youtubePlaylist'] = playlist; a['tracks'] = [[name, None, i] for i, name in enumerate(names)]
    a['focus'] = focus
    p[str(n)] = {k: a[k] for k in ['note', 'youtubePlaylist', 'fullAlbumVideo', 'focus', 'tracks', 'guide'] if k in a} | {k: v for k, v in a.items() if k not in ('note','youtubePlaylist','fullAlbumVideo','focus','tracks','guide')}
json.dump(p, open('dist/pilot.json', 'w'), ensure_ascii=False, indent=2); open('dist/pilot.json','a').write('\n')
for n in TRACKS: print(n, len(p[str(n)]['tracks']), p[str(n)]['focus'], p[str(n)].get('youtubePlaylist') or 'video')
