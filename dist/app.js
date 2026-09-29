'use strict';
const $ = id => document.getElementById(id);
const DONE_KEY = 'album-journey-2005-done';
const FOCUS_KEY = 'album-journey-2005-focus-ids';
const SERVICE_KEY = 'album-journey-2005-service';
const COVERS_KEY = 'album-journey-2005-covers';
const WELCOME_KEY = 'album-journey-2005-welcomed';
function readStore(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function writeStore(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {
    $('storage-note').textContent = 'השמירה בדפדפן חסומה כרגע. הבחירה תישמר רק עד לרענון.';
  }
}
let albums = [], active = 0, mode = 'full', player = null, ready = false;
let queue = [], queueIndex = 0, playerTimer = null, chapterTimer = null, state = -1;
let guideRenderKey = ''; 
let service = readStore(SERVICE_KEY, 'youtube') === 'spotify' ? 'spotify' : 'youtube';
const TITLES_KEY = 'album-journey-2005-video-titles';
const TITLE_CACHE_LIMIT = 1500;
// Official album programs live in albums/N.json. For YouTube playlists the site
// reads the playlist's real video titles at runtime and maps each song to the
// matching playlist entry, so reordered, extended or partial playlists still
// play the right song.
const resolved = {};
const titleCache = (() => { const c = readStore(TITLES_KEY, {}); return c && typeof c === 'object' && !Array.isArray(c) ? c : {}; })();
function playableAlbum(album) {
  const a = {...album};
  if (a.fullAlbumVideo) a.tracks = a.tracks.map((t, i) => [t[0], t[1], i, t[3] || 0]);
  return a;
}
const storedDone = readStore(DONE_KEY, []);
const done = new Set(Array.isArray(storedDone) ? storedDone.filter(Number.isInteger) : []);
const storedFocus = readStore(FOCUS_KEY, {});
const focus = storedFocus && typeof storedFocus === 'object' && !Array.isArray(storedFocus) ? storedFocus : {};
const currentAlbum = () => albums[active];
const trackKey = (a, t) => a.youtubePlaylist || a.fullAlbumVideo ? t[2] : t[1];
// Where a song sits inside the YouTube playlist (-1: not in this playlist).
const playlistIndex = (a, t) => resolved[a.n]?.[t[2]] ?? t[2];
const playable = (a, t) => !a.youtubePlaylist || playlistIndex(a, t) >= 0;
function simplify(text, artist = '') {
  let s = String(text).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’‘`´]/g, "'");
  for (const part of artist.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().split(/\s*(?:&|\/|,|\+|and|featuring|with)\s+/)) if (part.length > 3) s = s.split(part).join(' ');
  s = s.replace(/\((?:[^)]*(?:remaster|live|mono|stereo|version|take|mix|edit|audio|official|lyric|bonus|19\d\d|20\d\d)[^)]*)\)|\[[^\]]*\]/g, ' ');
  s = s.replace(/-\s*(?:\d{4}\s*)?(?:remaster|live|mono|stereo|single).*$/g, ' ');
  return s.replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').replace(/\b(the|a|an|de|la|le|les|of)\b/g, ' ').replace(/\s+/g, ' ').trim();
}
function similarity(song, title, artist) {
  const a = simplify(song, artist), b = simplify(title, artist);
  if (!a || !b) return 0;
  if (a === b) return 1;
  const words = a.split(' '), have = new Set(b.split(' '));
  const hit = words.filter(w => have.has(w)).length / words.length;
  return b.includes(a) ? Math.max(hit, .95) : hit * (words.length === 1 ? .9 : 1);
}
// Maps each song of the official program to a playlist entry using real video titles.
function matchPlaylist(a, titles) {
  const used = new Set(), map = a.tracks.map(() => -1);
  const known = titles.filter(Boolean).length;
  a.tracks.forEach((t, song) => {
    let best = -1, score = .6;
    titles.forEach((title, index) => {
      if (!title || used.has(index)) return;
      const value = similarity(t[0], title, a.artist) - Math.abs(index - song) * .002;
      if (value > score) { score = value; best = index; }
    });
    if (best >= 0) { map[song] = best; used.add(best); }
  });
  const matched = map.filter(i => i >= 0).length;
  if (!known || matched < Math.ceil(a.tracks.length / 2)) return a.tracks.map((t, i) => i < titles.length ? i : -1);
  // A title that could not be read keeps its album position if that slot is free.
  map.forEach((index, song) => { if (index < 0 && song < titles.length && !titles[song] && !used.has(song)) { map[song] = song; used.add(song); } });
  return map;
}
async function videoTitle(id) {
  if (titleCache[id]) return titleCache[id];
  const url = encodeURIComponent(`https://www.youtube.com/watch?v=${id}`);
  for (const endpoint of [`https://www.youtube.com/oembed?format=json&url=${url}`, `https://noembed.com/embed?url=${url}`]) {
    try {
      const response = await fetch(endpoint);
      if (!response.ok) continue;
      const title = (await response.json()).title;
      if (typeof title === 'string' && title) { titleCache[id] = title; return title; }
    } catch { /* try the next endpoint */ }
  }
  return '';
}
const resolving = {};
async function resolvePlaylist(a) {
  if (!a.youtubePlaylist || resolved[a.n] || resolving[a.n] || typeof player?.getPlaylist !== 'function') return;
  const ids = player.getPlaylist();
  if (!Array.isArray(ids) || !ids.length) return;
  resolving[a.n] = true;
  try {
    const titles = await Promise.all(ids.map(videoTitle));
    const keys = Object.keys(titleCache);
    if (keys.length > TITLE_CACHE_LIMIT) keys.slice(0, keys.length - TITLE_CACHE_LIMIT).forEach(k => delete titleCache[k]);
    try { localStorage.setItem(TITLES_KEY, JSON.stringify(titleCache)); } catch { /* cache is optional */ }
    resolved[a.n] = matchPlaylist(a, titles);
  } finally { resolving[a.n] = false; }
  if (currentAlbum() === a) { renderQueue(); renderFocus(); if (![1, 2, 3].includes(state)) cueQueue(); }
}
const defaultFocus = a => a.focus.map(i => trackKey(a, a.tracks[i]));
function focusedIds(a) {
  const ids = Array.isArray(focus[a.n]) ? focus[a.n].filter(id => a.tracks.some(t => trackKey(a, t) === id)) : [];
  return ids.length ? ids : defaultFocus(a);
}
function element(tag, className, text) {
  const el = document.createElement(tag); el.className = className; if (text !== undefined) el.textContent = text; return el;
}
// Album covers come from Spotify's public oEmbed endpoint and are cached per
// browser. Anything that fails simply leaves the numbered placeholder in place.
const storedCovers = readStore(COVERS_KEY, {});
const coverCache = storedCovers && typeof storedCovers === 'object' && !Array.isArray(storedCovers) ? storedCovers : {};
const coverPending = new Map(), coverRows = new WeakMap();
let catalogOpen = false;
function coverFor(a) {
  const id = a.spotifyAlbum;
  if (!id) return Promise.resolve(null);
  if (typeof coverCache[id] === 'string') return Promise.resolve(coverCache[id]);
  if (!coverPending.has(id)) coverPending.set(id, (async () => {
    try {
      const response = await fetch(`https://open.spotify.com/oembed?url=${encodeURIComponent(`https://open.spotify.com/album/${id}`)}`);
      if (!response.ok) return null;
      const url = (await response.json()).thumbnail_url;
      if (typeof url !== 'string' || !url.startsWith('https://')) return null;
      coverCache[id] = url;
      try { localStorage.setItem(COVERS_KEY, JSON.stringify(coverCache)); } catch { /* cache is optional */ }
      return url;
    } catch { return null; }
  })());
  return coverPending.get(id);
}
function paintRowCover(box, a) {
  coverFor(a).then(url => {
    if (!url) return;
    const img = element('img', ''); img.alt = ''; img.loading = 'lazy'; img.decoding = 'async';
    img.onerror = () => img.remove(); img.src = url; box.replaceChildren(img);
  });
}
const coverObserver = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
  for (const entry of entries) if (entry.isIntersecting) {
    coverObserver.unobserve(entry.target); paintRowCover(entry.target, coverRows.get(entry.target));
  }
}, {root: $('album-list'), rootMargin: '240px 0px'}) : null;
function setTint(rgb) { document.querySelector('.detail')?.style?.setProperty('--tint', rgb || '16 26 36'); }
function sampleTint(url, n) {
  if (typeof Image !== 'function') return;
  const probe = new Image(); probe.crossOrigin = 'anonymous';
  probe.onload = () => {
    try {
      const canvas = document.createElement('canvas'); canvas.width = canvas.height = 12;
      const ctx = canvas.getContext('2d'); ctx.drawImage(probe, 0, 0, 12, 12);
      const px = ctx.getImageData(0, 0, 12, 12).data; let r = 0, g = 0, b = 0, w = 0;
      for (let i = 0; i < px.length; i += 4) {
        const hi = Math.max(px[i], px[i + 1], px[i + 2]), lo = Math.min(px[i], px[i + 1], px[i + 2]);
        const weight = ((hi - lo) / 255) ** 2 * (1 - Math.abs((hi + lo) / 510 - .5)) + .01;
        r += px[i] * weight; g += px[i + 1] * weight; b += px[i + 2] * weight; w += weight;
      }
      const k = 210 / Math.max(r / w, g / w, b / w, 1);
      if (currentAlbum().n === n) setTint([r, g, b].map(v => Math.min(255, Math.round(v / w * k))).join(' '));
    } catch { /* image served without CORS: keep the default tint */ }
  };
  probe.src = url;
}
function renderCover() {
  const a = currentAlbum(), n = a.n, img = $('album-cover');
  $('record-graphic').classList.toggle('has-cover', false); img.hidden = true; img.removeAttribute('src'); setTint(null);
  coverFor(a).then(url => {
    if (!url || currentAlbum().n !== n) return;
    img.onload = () => { if (currentAlbum().n === n) { img.hidden = false; $('record-graphic').classList.toggle('has-cover', true); } };
    img.src = url; sampleTint(url, n);
  });
}
function setCatalogOpen(open) {
  catalogOpen = open; $('catalog').classList.toggle('open', open);
  $('catalog-toggle').setAttribute('aria-expanded', String(open));
}
// English names inside Hebrew text: isolate each Latin run so it keeps its own
// order, and keep short ones on one line so a title never splits mid-phrase.
function bidiText(el, text) {
  const parts = text.split(/([A-Za-z][A-Za-z0-9’'.,&!?()\- ]*[A-Za-z0-9!?.)’'])/);
  el.replaceChildren(...parts.map((part, i) => {
    if (i % 2 === 0) return document.createTextNode(part);
    const run = element('bdi', part.length <= 28 ? 'latin nowrap' : 'latin', part); run.dir = 'ltr'; return run;
  }));
}
const STORY_HEADINGS = ['מי ומתי', 'מה שומעים כאן', 'למה זה חשוב', 'טיפ להאזנה'];
function renderStory(a) {
  if (!a.story) {
    const p = element('p', ''); bidiText(p, a.guide ? a.guide.intro.map(section => section.text).join(' ') : a.note);
    $('album-note').replaceChildren(p); return;
  }
  const sections = a.story.map((text, i) => {
    const section = element('section', 'story-section'), p = element('p', '');
    bidiText(p, text); section.append(element('h4', '', STORY_HEADINGS[i] ?? ''), p); return section;
  });
  if (a.picks?.length) {
    const section = element('section', 'story-section story-picks'), list = element('ul', 'picks');
    for (const [name, text] of a.picks) {
      const li = element('li', ''), head = element('div', 'pick-head'), p = element('p', '');
      const play = element('button', 'pick-play', '▶'); play.type = 'button'; play.setAttribute('aria-label', `ניגון ${name}`);
      play.addEventListener('click', () => playPick(a, name));
      const title = element('bdi', 'pick-name', name); title.dir = 'ltr';
      bidiText(p, text); head.append(play, title); li.append(head, p); list.append(li);
    }
    section.append(element('h4', '', 'שירים לשים לב אליהם'), list); sections.push(section);
  }
  $('album-note').replaceChildren(...sections);
}
// A pick's ▶ plays that song in the site's YouTube player (switching to the
// full album if the focused queue leaves it out); in Spotify mode it just
// brings the Spotify player into view.
function playPick(a, name) {
  const track = a.tracks.find(t => t[0] === name);
  $('listening-panel').scrollIntoView?.({behavior: 'smooth', block: 'start'});
  if (!track || service === 'spotify') return;
  if (!queue.includes(track)) { mode = 'full'; renderMode(); }
  playAt(queue.indexOf(track));
}
let genre = '';
// Genre menu: "כל הז'אנרים" plus every label in use, most common first. Filters the list only; the journey order is unchanged.
function renderGenres() {
  const counts = {};
  for (const a of albums) for (const g of a.genres ?? []) counts[g] = (counts[g] ?? 0) + 1;
  const names = Object.keys(counts).sort((x, y) => counts[y] - counts[x] || x.localeCompare(y, 'he'));
  const menu = $('genre-select');
  menu.hidden = names.length === 0;
  menu.replaceChildren(...['', ...names].map(g => {
    const o = element('option', '', g ? `${g} · ${counts[g]}` : "כל הז'אנרים"); o.value = g; return o;
  }));
  menu.value = genre;
}
$('genre-select').addEventListener('change', () => { genre = $('genre-select').value; renderList(); });
// The book groups albums by decade. A few entries carry a much later or earlier release year than their place in the book
// (e.g. a 1985 release of a 1963 concert), so each album's decade is the median year of its neighbours in book order.
function markDecades(list) {
  list.forEach((a, i) => {
    const years = list.slice(Math.max(0, i - 5), i + 6).map(x => x.year).sort((x, y) => x - y);
    a.decade = Math.floor(years[years.length >> 1] / 10) * 10;
  });
}
const decadeLabel = d => `שנות ה־${d < 2000 ? d - 1900 : d}`;
function renderList() {
  const search = $('album-search').value.trim().toLocaleLowerCase();
  const visible = albums.filter(a => (!genre || a.genres?.includes(genre)) && `${a.title} ${a.artist} ${a.n}`.toLocaleLowerCase().includes(search));
  let lastDecade = null;
  $('album-list').replaceChildren(...visible.flatMap(a => {
    const marker = a.decade !== lastDecade ? [element('div', 'decade-mark', decadeLabel(a.decade))] : [];
    lastDecade = a.decade;
    const b = element('button', 'album-row' + (a === currentAlbum() ? ' active' : ''));
    b.type = 'button'; b.setAttribute('aria-current', String(a === currentAlbum()));
    const titles = element('span', 'row-titles');
    const title = element('span', 'row-title', a.title); title.dir = 'auto';
    const artist = element('span', 'row-artist', a.artist); artist.dir = 'auto'; titles.append(title, artist);
    const cover = element('span', 'row-cover'), meta = element('span', 'row-meta');
    meta.append(element('span', 'row-number', String(a.n).padStart(3, '0')), element('span', 'row-check', done.has(a.n) ? '✓' : ''));
    b.append(cover, titles, meta);
    if (coverObserver) { coverRows.set(cover, a); coverObserver.observe(cover); } else paintRowCover(cover, a);
    b.addEventListener('click', () => selectAlbum(albums.indexOf(a))); return [...marker, b];
  }));
  $('list-empty').hidden = visible.length > 0;
  $('catalog-count').textContent = albums.length;
  const heard = albums.filter(a => done.has(a.n)).length;
  $('list-progress').textContent = `האזנת ל־${heard} מתוך ${albums.length} אלבומים`;
  $('progress-meter').max = albums.length; $('progress-meter').value = heard;
  $('toggle-progress').textContent = `${heard} מתוך ${albums.length}`;
}
function renderDone() {
  const yes = done.has(currentAlbum().n);
  $('mark-done').setAttribute('aria-pressed', String(yes));
  $('mark-done').textContent = yes ? '✓ האזנתי לאלבום' : 'סימון שהאזנתי';
}
function renderAlbum() {
  const a = currentAlbum();
  $('album-title').textContent = a.title; $('album-artist').textContent = a.artist;
  $('album-genres').replaceChildren(...(a.genres ?? []).map(g => element('li', 'album-genre', g))); $('album-genres').hidden = !a.genres?.length;
  $('album-year').textContent = a.year; $('album-number').textContent = `#${String(a.n).padStart(3, '0')}`;
  $('record-number').textContent = String(a.n).padStart(3, '0');
  $('chapter').textContent = `אלבום ${active + 1} מתוך ${albums.length} במסע`;
  renderStory(a);
  $('previous-album').disabled = $('previous-album-top').disabled = active === 0;
  $('next-album').disabled = $('next-album-top').disabled = active === albums.length - 1;
  $('focus-editor').open = false;
  prepareGuide(); renderDone(); renderList(); renderMode(); renderCover();
}
let selecting = 0;
async function selectAlbum(index) {
  if (index === active || index < 0 || index >= albums.length) return;
  const ticket = ++selecting;
  try { await loadAlbum(albums[index]); } catch { if (ticket === selecting) $('album-error').hidden = false; return; }
  if (ticket !== selecting) return; // a newer pick superseded this one while it loaded
  $('album-error').hidden = true;
  active = index; renderAlbum(); prefetchNeighbours();
  if (catalogOpen) { setCatalogOpen(false); window.scrollTo?.({top: 0, behavior: 'smooth'}); }
  // Picking the next album from the bottom of the page: jump up to the new album's top.
  else if ($('album-view').getBoundingClientRect?.().top < 0) $('album-view').scrollIntoView?.({block: 'start'});
}
$('catalog-toggle').addEventListener('click', () => setCatalogOpen(!catalogOpen));
// First visit: a short explanation of the site, dismissed once and reopenable from the header.
$('welcome').hidden = Boolean(readStore(WELCOME_KEY, false));
$('close-welcome').addEventListener('click', () => { $('welcome').hidden = true; writeStore(WELCOME_KEY, true); });
// Premium help: show this site's own address and copy snippets to the clipboard.
for (const el of document.querySelectorAll?.('.site-host') ?? []) el.textContent = location.host || el.textContent;
for (const b of document.querySelectorAll?.('.copy-button') ?? []) {
  if (b.classList.contains('site-copy') && location.host) b.dataset.copy = location.host;
  b.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = 'הועתק ✓'; }
    catch { b.textContent = 'לא הצלחתי, סמנו והעתיקו ידנית'; }
    setTimeout(() => { b.textContent = 'העתקה'; }, 2500);
  });
}
$('show-welcome').addEventListener('click', () => { $('welcome').hidden = false; window.scrollTo?.({top: 0, behavior: 'smooth'}); });
function renderMode() {
  const a = currentAlbum(); const selected = focusedIds(a);
  const external = Boolean(a.externalAlbum);
  const spotify = service === 'spotify';
  for (const s of ['youtube', 'spotify']) {
    $('service-' + s).classList.toggle('active', service === s);
    $('service-' + s).setAttribute('aria-pressed', String(service === s));
  }
  $('spotify-listening').hidden = !spotify;
  $('mode-explain').hidden = spotify;
  $('mode-switch').hidden = external || spotify;
  $('embedded-listening').hidden = external || spotify;
  $('external-listening').hidden = !external || spotify;
  if (spotify) {
    if (ready) player.stopVideo();
    clearInterval(chapterTimer); queue = []; queueIndex = 0; state = -1;
    if ($('album-youtube-player').src !== 'about:blank') $('album-youtube-player').src = 'about:blank';
    $('listen-eyebrow').textContent = 'מנגנים כאן, בנגן של Spotify';
    const src = a.spotifyAlbum ? `https://open.spotify.com/embed/album/${a.spotifyAlbum}?utm_source=generator` : 'about:blank';
    if ($('spotify-player').src !== src) $('spotify-player').src = src;
    $('spotify-player').hidden = !a.spotifyAlbum;
    $('spotify-player').title = `נגן Spotify — ${a.title}`;
    $('spotify-direct').hidden = !a.spotifyAlbum;
    $('spotify-direct').href = a.spotifyAlbum ? `https://open.spotify.com/album/${a.spotifyAlbum}` : '#';
    $('spotify-search').href = `https://open.spotify.com/search/${encodeURIComponent(`${a.artist} ${a.title}`)}/albums`;
    return;
  }
  if ($('spotify-player').src && $('spotify-player').src !== 'about:blank') $('spotify-player').src = 'about:blank';
  $('listen-eyebrow').textContent = external ? 'האזנה ב־YouTube בתוך האתר' : 'מנגנים כאן, בתוך האתר';
  $('youtube-direct').href = a.youtubePlaylist
    ? `https://www.youtube.com/playlist?list=${a.youtubePlaylist}`
    : `https://www.youtube.com/watch?v=${a.tracks[0][1]}`;
  if (external) {
    player?.stopVideo(); queue = []; queueIndex = 0; state = -1;
    const complete = a.youtubeAlbumComplete;
    $('mode-explain').textContent = complete ? 'נגן YouTube של האלבום. בפלייליסט אפשר לבחור קטע מתוך הנגן ולהמשיך להאזין ברצף.' : 'נגן YouTube עם קטע מתוך האלבום. עדיין לא נמצא מקור אמין לכל ההקלטות של מהדורת האלבום.';
    $('album-youtube-player').src = a.youtubeAlbumPlaylist
      ? `https://www.youtube.com/embed/videoseries?list=${a.youtubeAlbumPlaylist}`
      : `https://www.youtube.com/embed/${a.youtubeAlbumVideo}`;
    $('album-youtube-player').title = `נגן YouTube — ${a.title}`;
    $('album-youtube-direct').href = a.youtubeAlbumPlaylist
      ? `https://www.youtube.com/playlist?list=${a.youtubeAlbumPlaylist}`
      : `https://www.youtube.com/watch?v=${a.youtubeAlbumVideo}`;
    $('album-source-note').textContent = complete
      ? (a.youtubeAlbumPlaylist ? 'בחרו קטע מתוך רשימת הניגון של YouTube. ייתכנו הבדלים בין המהדורה הזמינה למהדורת הספר.' : 'ההקלטה הרציפה של האלבום זמינה בנגן YouTube. בחירת קטע נפרד אינה זמינה כאן כרגע.')
      : 'הנגן מציג קטע זמין בלבד. שאר קטעי האלבום טרם אומתו לניגון בתוך האתר.';
    $('external-album-link').href = a.externalAlbum;
    $('external-highlights').replaceChildren(...a.guide.highlights.map(title => {
      const li = element('li', '');
      const link = element('a', '', title); link.href = `https://music.youtube.com/search?q=${encodeURIComponent(`${a.artist} ${title}`)}`;
      link.target = '_blank'; link.rel = 'noopener noreferrer'; li.append(link); return li;
    }));
    return;
  }
  if ($('album-youtube-player').src !== 'about:blank') $('album-youtube-player').src = 'about:blank';
  queue = mode === 'full' ? a.tracks : a.tracks.filter(t => selected.includes(trackKey(a, t)));
  queueIndex = 0; state = -1;
  for (const m of ['full', 'short']) {
    $('mode-' + m).classList.toggle('active', mode === m);
    $('mode-' + m).setAttribute('aria-pressed', String(mode === m));
  }
  $('mode-explain').textContent = mode === 'full'
    ? (a.fullAlbumVideo
      ? `${queue.length} שירים לפי סדר האלבום, בתוך הקלטה רציפה אחת. לחיצה על שיר מדלגת אליו (זמני הפתיחה מחושבים לפי אורכי השירים וייתכן הפרש של שניות).`
      : `${queue.length} שירים לפי סדר רשימת האלבום. בחרו שיר או הפעילו את הרצף.`)
    : `${queue.length} שירים למסלול ממוקד. אלה המלצות האתר, לא סימוני הספר. אפשר לשנות את הבחירה למטה.`;
  $('focus-editor').hidden = mode !== 'short';
  $('focus-error').hidden = true;
  renderQueue(); renderFocus(); cueQueue(); syncGuide();
}
function renderQueue() {
  const a = currentAlbum();
  const missing = queue.filter(t => !playable(a, t)).length;
  $('queue-count').textContent = `${queue.length} שירים` + (a.fullAlbumVideo ? ' · הקלטה רציפה' : '') + (missing ? ` · ${missing} לא זמינים בנגן` : '');
  $('track-list').replaceChildren(...queue.map((t, i) => {
    const li = element('li', playable(a, t) ? '' : 'track-missing');
    const name = element('span', 'track-name', t[0]); name.dir = 'auto';
    const length = a.durations?.[a.tracks.indexOf(t)];
    if (length) name.append(element('span', 'track-time', length));
    const b = element('button', 'track-play', playable(a, t) ? 'ניגון ▶' : 'לא זמין'); b.type = 'button';
    b.setAttribute('aria-label', playable(a, t) ? `ניגון ${t[0]}` : `${t[0]} אינו זמין ברשימת הניגון`);
    b.addEventListener('click', () => playAt(i));
    li.append(name, b); return li;
  }));
  updateControls();
}
function renderFocus() {
  const a = currentAlbum(), ids = focusedIds(a);
  $('focus-options').replaceChildren(...a.tracks.map(t => {
    const label = element('label', 'focus-option'); const input = document.createElement('input');
    input.type = 'checkbox'; const key = trackKey(a, t); input.checked = ids.includes(key);
    input.addEventListener('change', () => {
      const selection = new Set(focusedIds(a)); input.checked ? selection.add(key) : selection.delete(key);
      if (!selection.size) { input.checked = true; $('focus-error').hidden = false; return; }
      focus[a.n] = [...selection]; writeStore(FOCUS_KEY, focus); renderMode();
    });
    const name = element('span', '', t[0]); name.dir = 'auto'; label.append(input, name); return label;
  }));
}
function updateControls() {
  $('play-pause').disabled = !ready || !queue.length;
  $('play-pause').textContent = state === 1 ? 'השהיה ❚❚' : state === 2 ? 'המשך ▶' : 'הפעלת הרצף ▶';
  $('previous-track').disabled = !ready || firstPlayable(queueIndex - 1, -1) < 0;
  $('next-track').disabled = !ready || firstPlayable(queueIndex + 1) < 0;
  [...$('track-list').children].forEach((li, i) => {
    li.classList.toggle('current-track', i === queueIndex);
    li.querySelector('button').disabled = !ready || !playable(currentAlbum(), queue[i]);
    if (i === queueIndex) li.setAttribute('aria-current', 'true'); else li.removeAttribute('aria-current');
  });
}
function sourceLinks(ids) {
  const links = element('div', 'guide-sources');
  (ids || []).forEach(id => {
    const source = currentAlbum().guide.sources[id];
    if (!source) return;
    const link = element('a', '', source.label); link.href = source.url;
    link.target = '_blank'; link.rel = 'noopener noreferrer'; links.append(link);
  });
  return links;
}
function prepareGuide() {
  $('track-note').hidden = true;
  guideRenderKey = '';
}
function syncGuide() {
  const a = currentAlbum(), track = queue[queueIndex];
  const note = a?.guide?.tracks?.[track?.[1]];
  $('track-note').hidden = !note?.text;
  if (!note?.text) return;
  const key = `${a.n}:${track[1]}`;
  if (key === guideRenderKey) return;
  guideRenderKey = key;
  $('track-note-title').textContent = track[0];
  $('track-note-text').textContent = note.text;
  $('track-note-sources').replaceChildren(sourceLinks(note.sources));
}
function clearError() { $('player-error').hidden = true; }
function showError(message) {
  $('player-error-text').textContent = message; $('player-error').hidden = false;
  $('player-status').textContent = 'ההאזנה נעצרה. אפשר לנסות שוב או לבחור קטע אחר.';
}
function firstPlayable(from = 0, step = 1) {
  const a = currentAlbum();
  for (let i = from; i >= 0 && i < queue.length; i += step) if (playable(a, queue[i])) return i;
  return -1;
}
function cueQueue() {
  clearError(); clearInterval(chapterTimer);
  if (!ready || !queue.length) return;
  player.stopVideo();
  const a = currentAlbum();
  queueIndex = Math.max(0, firstPlayable());
  if (a.youtubePlaylist) player.cuePlaylist({list: a.youtubePlaylist, listType: 'playlist', index: Math.max(0, playlistIndex(a, queue[queueIndex])), startSeconds: 0});
  // A one-video "playlist" is not reliably swapped in by YouTube's player; cue the video itself.
  else if (a.fullAlbumVideo) player.cueVideoById({videoId: a.tracks[0][1], startSeconds: queue[0][3]});
  else player.cuePlaylist(queue.map(t => t[1]), 0, 0);
  player.setLoop(false); player.setShuffle(false);
  $('player-status').textContent = 'מוכן להאזנה. לחץ על הפעלה כאן או בנגן.';
  updateControls();
}
function finishQueue() {
  player.stopVideo(); state = 0; clearInterval(chapterTimer);
  $('player-status').textContent = 'הרצף הסתיים. אפשר להאזין שוב או לעבור לאלבום הבא.';
  updateControls();
}
function playAt(index) {
  if (!ready || index < 0 || index >= queue.length) return;
  const a = currentAlbum();
  if (!playable(a, queue[index])) return;
  clearError(); queueIndex = index;
  if (a.fullAlbumVideo) { player.seekTo(queue[index][3], true); player.playVideo(); }
  else player.playVideoAt(a.youtubePlaylist ? playlistIndex(a, queue[index]) : index);
  updateControls(); syncGuide();
}
// Continuous album videos: follow the song boundaries inside the recording.
function followChapter() {
  const a = currentAlbum();
  if (!a?.fullAlbumVideo || state !== 1 || typeof player.getCurrentTime !== 'function') return;
  const time = player.getCurrentTime() + .5;
  let chapter = 0;
  a.tracks.forEach((t, i) => { if (t[3] <= time) chapter = i; });
  const position = queue.indexOf(a.tracks[chapter]);
  if (position >= 0) {
    if (position !== queueIndex) { queueIndex = position; announce(); updateControls(); }
    return;
  }
  const next = queue.findIndex(t => t[3] > a.tracks[chapter][3]);
  if (next >= 0) playAt(next); else finishQueue();
}
function announce() {
  const title = queue[queueIndex]?.[0] || '';
  if (state === 1) { clearError(); $('player-status').textContent = `מתנגן ${queueIndex + 1} מתוך ${queue.length}: ${title}`; }
  if (state === 2 && $('player-error').hidden) $('player-status').textContent = `מושהה: ${title}`;
}
function onStateChange(event) {
  state = event.data;
  const a = currentAlbum();
  if (a?.youtubePlaylist && (state === 5 || state === 1)) resolvePlaylist(a);
  if (a?.fullAlbumVideo) {
    clearInterval(chapterTimer);
    if (state === 1) { chapterTimer = setInterval(followChapter, 1000); followChapter(); if (state !== 1) return; }
    if (state === 0) { queueIndex = queue.length - 1; $('player-status').textContent = 'הרצף הסתיים. אפשר להאזין שוב או לעבור לאלבום הבא.'; updateControls(); return; }
    announce(); updateControls(); syncGuide(); return;
  }
  const index = player.getPlaylistIndex();
  if (a?.youtubePlaylist && Number.isInteger(index) && index >= 0 && state === 1) {
    const position = queue.findIndex(t => playlistIndex(a, t) === index);
    if (position < 0) {
      // A playlist entry outside the album program or the focused queue: continue with the next song.
      const next = firstPlayable(queueIndex + 1);
      if (next >= 0) playAt(next); else finishQueue();
      return;
    }
    queueIndex = position;
  } else if (!a?.youtubePlaylist && Number.isInteger(index) && index >= 0 && index < queue.length) queueIndex = index;
  announce();
  if (state === 0 && (a?.youtubePlaylist || queueIndex === queue.length - 1)) {
    const next = a?.youtubePlaylist ? firstPlayable(queueIndex + 1) : -1;
    if (next >= 0) { playAt(next); return; }
    if (a?.youtubePlaylist) player.stopVideo();
    $('player-status').textContent = 'הרצף הסתיים. אפשר להאזין שוב או לעבור לאלבום הבא.';
  }
  updateControls(); syncGuide();
}
function playerError(event) {
  const messages = {
    2: 'YouTube לא הצליח לזהות את הקטע הזה.',
    5: 'הדפדפן לא הצליח לנגן את הקטע. נסה שוב או רענן את העמוד.',
    100: 'הקטע הזה אינו זמין כרגע ב־YouTube.',
    101: 'בעל ההקלטה לא מאפשר להפעיל את הקטע בנגן מוטמע.',
    150: 'בעל ההקלטה לא מאפשר להפעיל את הקטע בנגן מוטמע.',
    153: 'YouTube לא הצליח לזהות את האתר. נסה לרענן; אם השגיאה נמשכת, יש לבדוק את הגדרות הפרטיות בדפדפן.'
  };
  player.pauseVideo(); state = 2;
  showError((messages[event.data] || 'YouTube לא הצליח להפעיל את הקטע כרגע.') + ` (קוד ${event.data})`);
  updateControls();
}
function createPlayer() {
  if (player || !albums.length || !window.YT?.Player) return;
  player = new YT.Player('youtube-player', {
    width: '100%', height: '100%', ...(currentAlbum().youtubePlaylist ? {} : {videoId: queue[0][1]}),
    playerVars: {autoplay: 0, controls: 1, playsinline: 1, origin: location.origin, rel: 0, ...(currentAlbum().youtubePlaylist ? {listType: 'playlist', list: currentAlbum().youtubePlaylist} : {})},
    events: {
      onReady: () => { clearTimeout(playerTimer); ready = true; cueQueue(); },
      onStateChange, onError: playerError,
      onAutoplayBlocked: () => { $('player-status').textContent = 'הדפדפן ממתין ללחיצה. לחץ על ▶ בתוך נגן YouTube כדי להתחיל.'; }
    }
  });
  const frame = player.getIframe(); frame.title = 'נגן YouTube — מסע באלבומים';
  frame.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
  frame.setAttribute('allow', 'autoplay; encrypted-media; fullscreen; picture-in-picture');
}
window.onYouTubeIframeAPIReady = createPlayer;
function loadPlayer() {
  $('player-status').textContent = 'טוען את נגן YouTube…';
  clearTimeout(playerTimer);
  playerTimer = setTimeout(() => {
    if (!ready) showError('הנגן לא נטען. בדוק את החיבור לרשת או אם חוסם תוכן מונע מ־YouTube להיטען, ונסה שוב.');
  }, 15000);
  if (window.YT?.Player) { createPlayer(); return; }
  const script = document.createElement('script'); script.id = 'youtube-api'; script.src = 'https://www.youtube.com/iframe_api';
  script.onerror = () => { clearTimeout(playerTimer); showError('לא ניתן להתחבר ל־YouTube כרגע. בדוק את החיבור ונסה שוב.'); };
  document.head.append(script);
}
$('retry-player').addEventListener('click', () => {
  clearError();
  if (ready) { playAt(queueIndex); return; }
  player?.destroy(); player = null;
  const host = document.createElement('div'); host.id = 'youtube-player'; document.querySelector('.youtube-frame').replaceChildren(host);
  $('youtube-api')?.remove(); loadPlayer();
});
$('play-pause').addEventListener('click', () => {
  if (!ready) return; clearError();
  if (state === 1) player.pauseVideo();
  else if (state === 0 && queueIndex >= firstPlayable(queue.length - 1, -1)) playAt(firstPlayable());
  else player.playVideo();
});
$('previous-track').addEventListener('click', () => playAt(firstPlayable(queueIndex - 1, -1)));
$('next-track').addEventListener('click', () => playAt(firstPlayable(queueIndex + 1)));
$('album-search').addEventListener('input', renderList);
$('previous-album').addEventListener('click', () => selectAlbum(active - 1));
$('next-album').addEventListener('click', () => selectAlbum(active + 1));
$('previous-album-top').addEventListener('click', () => selectAlbum(active - 1));
$('next-album-top').addEventListener('click', () => selectAlbum(active + 1));
// Keyboard: in this right-to-left site ← is the next album and → the previous one
// (not while typing in the search box or with modifier keys held).
document.addEventListener?.('keydown', e => {
  if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target?.tagName ?? '') || e.target?.isContentEditable) return;
  if (e.key === 'ArrowLeft') selectAlbum(active + 1);
  else if (e.key === 'ArrowRight') selectAlbum(active - 1);
});
for (const s of ['youtube', 'spotify']) $('service-' + s).addEventListener('click', () => {
  if (service !== s) { service = s; writeStore(SERVICE_KEY, s); renderMode(); }
});
for (const m of ['full', 'short']) $('mode-' + m).addEventListener('click', () => {
  if (mode !== m) { mode = m; renderMode(); }
});
$('mark-done').addEventListener('click', () => {
  const n = currentAlbum().n; done.has(n) ? done.delete(n) : done.add(n);
  writeStore(DONE_KEY, [...done]); renderDone(); renderList();
});
$('reset-focus').addEventListener('click', () => { delete focus[currentAlbum().n]; writeStore(FOCUS_KEY, focus); renderMode(); });
// Data version: the deploy workflow stamps the commit here so browsers never mix old and new files.
const V = '';
const loaded = new Map();
// Fetches one album's full data (tracks, story, durations) the first time it is needed.
function loadAlbum(a) {
  if (a.tracks) return Promise.resolve(a);
  if (!loaded.has(a.n)) {
    loaded.set(a.n, fetch(`./albums/${a.n}.json${V}`).then(r => { if (!r.ok) throw new Error('Album unavailable'); return r.json(); }).then(data => {
      if (!validAlbum(data)) throw new Error('Invalid album');
      return Object.assign(a, playableAlbum(data));
    }).catch(e => { loaded.delete(a.n); throw e; }));
  }
  return loaded.get(a.n);
}
const validAlbum = a => Array.isArray(a.tracks) && a.tracks.length > 0 && a.tracks.every(t => a.youtubePlaylist ? typeof t[0] === 'string' && Number.isInteger(t[2]) : /^[A-Za-z0-9_-]{11}$/.test(t[1]));
async function init() {
  try {
    const response = await fetch(`./albums.json${V}`);
    if (!response.ok) throw new Error('Data unavailable');
    const catalog = (await response.json()).sort((a, b) => a.n - b.n);
    markDecades(catalog);
    albums = catalog.filter(a => a.ready);
    if (!albums.length) throw new Error('No albums');
    await loadAlbum(albums[0]);
    $('loading').hidden = true; $('album-view').hidden = false;
    renderGenres(); renderAlbum(); loadPlayer(); prefetchNeighbours();
  } catch { $('loading').hidden = true; $('album-view').hidden = true; $('load-error').hidden = false; }
}
function prefetchNeighbours() {
  for (const a of [albums[active + 1], albums[active - 1]]) if (a) loadAlbum(a).catch(() => {});
}
init();
