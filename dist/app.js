'use strict';
const $ = id => document.getElementById(id);
const DONE_KEY = 'album-journey-2005-done';
const FOCUS_KEY = 'album-journey-2005-focus-ids';
function readStore(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function writeStore(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {
    $('storage-note').textContent = 'השמירה בדפדפן חסומה כרגע. הבחירה תישמר רק עד לרענון.';
  }
}
let albums = [], active = 0, mode = 'full', player = null, ready = false;
let queue = [], queueIndex = 0, playerTimer = null, state = -1;
let guideRenderKey = ''; 
// Counts checked on the public YouTube playlist pages. The four remaining albums
// have a continuous full-recording video instead of separate song videos.
const albumPlaylistCounts = {
  22:12, 24:13, 25:12, 26:14, 28:4, 30:6, 31:12, 32:12,
  33:7, 34:12, 35:14, 36:13, 37:13, 38:8, 39:4, 40:9,
  41:8, 42:13, 43:15, 44:12, 45:20, 46:12, 48:13, 50:11
};
const correctedPlaylists = {
  26:'PLowQCq3Ss89ikMwB_bPRQuaQttWp0xaD4',
  31:'PL1a1FcevWP19h-lU6yce1_TuLRWCzXJ20',
  34:'PLowQCq3Ss89jz1iejIedRBojbvYe3MSzK'
};
function playableAlbum(album) {
  const a = {...album};
  if (!a.externalAlbum) return a;
  if (albumPlaylistCounts[a.n]) {
    a.youtubePlaylist = correctedPlaylists[a.n] || a.youtubeAlbumPlaylist;
    a.tracks = Array.from({length:albumPlaylistCounts[a.n]}, (_, i) => [`קטע ${i + 1}`, '', i]);
    a.focus = [...new Set([0, Math.floor(a.tracks.length / 2), a.tracks.length - 1])];
  } else if (a.youtubeAlbumVideo && [27,29,47,49].includes(a.n)) {
    a.fullAlbumVideo = true;
    a.tracks = [['הקלטה רציפה של האלבום', a.youtubeAlbumVideo]];
    a.focus = [0];
  }
  delete a.externalAlbum;
  return a;
}
const storedDone = readStore(DONE_KEY, []);
const done = new Set(Array.isArray(storedDone) ? storedDone.filter(Number.isInteger) : []);
const storedFocus = readStore(FOCUS_KEY, {});
const focus = storedFocus && typeof storedFocus === 'object' && !Array.isArray(storedFocus) ? storedFocus : {};
const currentAlbum = () => albums[active];
const trackKey = (a, t) => a.youtubePlaylist ? t[2] : t[1];
const defaultFocus = a => a.focus.map(i => trackKey(a, a.tracks[i]));
function focusedIds(a) {
  const ids = Array.isArray(focus[a.n]) ? focus[a.n].filter(id => a.tracks.some(t => trackKey(a, t) === id)) : [];
  return ids.length ? ids : defaultFocus(a);
}
function element(tag, className, text) {
  const el = document.createElement(tag); el.className = className; if (text !== undefined) el.textContent = text; return el;
}
function renderList() {
  const search = $('album-search').value.trim().toLocaleLowerCase();
  const visible = albums.filter(a => `${a.title} ${a.artist} ${a.n}`.toLocaleLowerCase().includes(search));
  $('album-list').replaceChildren(...visible.map(a => {
    const b = element('button', 'album-row' + (a === currentAlbum() ? ' active' : ''));
    b.type = 'button'; b.setAttribute('aria-current', String(a === currentAlbum()));
    const titles = element('span', 'row-titles');
    const title = element('span', 'row-title', a.title); title.dir = 'auto';
    const artist = element('span', 'row-artist', a.artist); artist.dir = 'auto'; titles.append(title, artist);
    b.append(element('span', 'row-number', String(a.n).padStart(3, '0')), titles, element('span', 'row-check', done.has(a.n) ? '✓' : ''));
    b.addEventListener('click', () => selectAlbum(albums.indexOf(a))); return b;
  }));
  $('list-empty').hidden = visible.length > 0;
  $('catalog-count').textContent = albums.length;
  $('list-progress').textContent = `${albums.filter(a => done.has(a.n)).length} מתוך ${albums.length} הושלמו`;
}
function renderDone() {
  const yes = done.has(currentAlbum().n);
  $('mark-done').setAttribute('aria-pressed', String(yes));
  $('mark-done').textContent = yes ? '✓ האזנתי לאלבום' : 'סימון שהאזנתי';
}
function renderAlbum() {
  const a = currentAlbum();
  $('album-title').textContent = a.title; $('album-artist').textContent = a.artist;
  $('album-year').textContent = a.year; $('album-number').textContent = `#${String(a.n).padStart(3, '0')}`;
  $('record-number').textContent = String(a.n).padStart(3, '0');
  $('chapter').textContent = `אלבום ${active + 1} מתוך ${albums.length} במסע`;
  $('album-note').textContent = a.guide ? a.guide.intro.map(section => section.text).join(' ') : a.note;
  $('previous-album').disabled = active === 0; $('next-album').disabled = active === albums.length - 1;
  $('focus-editor').open = false;
  prepareGuide(); renderDone(); renderList(); renderMode();
}
function selectAlbum(index) {
  if (index === active || index < 0 || index >= albums.length) return;
  active = index; renderAlbum();
}
function renderMode() {
  const a = currentAlbum(); const selected = focusedIds(a);
  const external = Boolean(a.externalAlbum);
  $('mode-switch').hidden = external || Boolean(a.fullAlbumVideo);
  $('embedded-listening').hidden = external;
  $('external-listening').hidden = !external;
  $('listen-eyebrow').textContent = external ? 'האזנה ב־YouTube בתוך האתר' : 'מנגנים כאן, בתוך האתר';
  $('youtube-direct').href = a.youtubePlaylist
    ? `https://www.youtube.com/playlist?list=${a.youtubePlaylist}`
    : `https://www.youtube.com/watch?v=${a.tracks[0][1]}`;
  if (external) {
    player?.stopVideo(); queue = []; queueIndex = 0; state = -1;
    const complete = a.youtubeAlbumComplete;
    $('mode-explain').textContent = complete ? 'נגן YouTube של האלבום. בפלייליסט אפשר לבחור קטע מתוך הנגן ולהמשיך להאזין ברצף.' : 'נגן YouTube עם קטע מתוך האלבום. עדיין לא נמצא מקור אמין לכל ההקלטות של מהדורת האלבום.';
    $('album-youtube-player').src = a.youtubeAlbumPlaylist
      ? `https://www.youtube-nocookie.com/embed/videoseries?list=${a.youtubeAlbumPlaylist}`
      : `https://www.youtube-nocookie.com/embed/${a.youtubeAlbumVideo}`;
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
  $('mode-explain').textContent = a.fullAlbumVideo
    ? 'האלבום המלא בהקלטת YouTube רציפה. לוחצים על הפעלה ומאזינים מהתחלה עד הסוף.'
    : mode === 'full'
    ? `${queue.length} קטעים לפי סדר רשימת האלבום. בחרו מספר קטע או הפעילו את הרצף.`
    : `${queue.length} קטעים מלאים למסלול ממוקד. אלה המלצות האתר, לא סימוני הספר. אפשר לשנות את הבחירה למטה.`;
  $('focus-editor').hidden = mode !== 'short' || Boolean(a.fullAlbumVideo);
  $('focus-error').hidden = true;
  renderQueue(); renderFocus(); cueQueue(); syncGuide();
}
function renderQueue() {
  $('queue-count').textContent = currentAlbum().fullAlbumVideo ? 'הקלטת אלבום רציפה' : `${queue.length} קטעים`;
  $('track-list').replaceChildren(...queue.map((t, i) => {
    const li = element('li', '');
    const name = element('span', 'track-name', t[0]); name.dir = 'auto';
    const b = element('button', 'track-play', 'ניגון ▶'); b.type = 'button'; b.disabled = !ready;
    b.setAttribute('aria-label', `ניגון ${t[0]}`); b.addEventListener('click', () => playAt(i));
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
  $('previous-track').disabled = !ready || queueIndex <= 0;
  $('next-track').disabled = !ready || queueIndex >= queue.length - 1;
  [...$('track-list').children].forEach((li, i) => {
    li.classList.toggle('current-track', i === queueIndex);
    li.querySelector('button').disabled = !ready;
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
  const guide = currentAlbum().guide;
  $('album-essay').hidden = !guide;
  $('track-note').hidden = true;
  guideRenderKey = '';
  if (!guide) { $('essay-body').replaceChildren(); $('book-meta').hidden = true; return; }
  $('essay-title').hidden = true;
  $('essay-body').replaceChildren(sourceLinks([...new Set([...guide.intro.flatMap(section => section.sources), ...(guide.sources.listen ? ['listen'] : [])])]));
  const book = guide.book;
  $('book-meta').hidden = !book;
  if (book) {
    $('book-year').textContent = String(book.year);
    $('book-label').textContent = book.label;
    $('book-producer').textContent = book.producer;
    $('book-duration').textContent = book.duration;
    $('book-pages').textContent = book.pages;
  }
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
function cueQueue() {
  clearError();
  if (!ready || !queue.length) return;
  player.stopVideo();
  const a = currentAlbum();
  if (a.youtubePlaylist) player.cuePlaylist({list: a.youtubePlaylist, listType: 'playlist', index: mode === 'full' ? 0 : queue[0][2], startSeconds: 0});
  else player.cuePlaylist(queue.map(t => t[1]), 0, 0);
  player.setLoop(false); player.setShuffle(false);
  $('player-status').textContent = 'מוכן להאזנה. לחץ על הפעלה כאן או בנגן.';
  updateControls();
}
function playAt(index) {
  if (!ready || index < 0 || index >= queue.length) return;
  clearError(); queueIndex = index;
  const a = currentAlbum(); player.playVideoAt(a.youtubePlaylist ? (mode === 'full' ? index : queue[index][2]) : index);
  updateControls(); syncGuide();
}
function onStateChange(event) {
  state = event.data;
  const index = player.getPlaylistIndex();
  if (Number.isInteger(index) && index >= 0) {
    const mapped = currentAlbum()?.youtubePlaylist && mode === 'short' ? queue.findIndex(t => t[2] === index) : index;
    if (state === 1 && mapped < 0 && currentAlbum()?.youtubePlaylist && mode === 'short') {
      const next = queue.findIndex(t => t[2] > index);
      if (next >= 0) { playAt(next); return; }
      player.stopVideo(); state = 0;
      $('player-status').textContent = 'הרצף הסתיים. אפשר להאזין שוב או לעבור לאלבום הבא.';
      updateControls(); return;
    }
    if (state === 1 && currentAlbum()?.youtubePlaylist && mode === 'full' && index >= queue.length) {
      player.stopVideo(); state = 0;
      $('player-status').textContent = 'הרצף הסתיים. אפשר להאזין שוב או לעבור לאלבום הבא.';
      updateControls(); return;
    }
    if (mapped >= 0 && mapped < queue.length) queueIndex = mapped;
  }
  const title = queue[queueIndex]?.[0] || '';
  if (state === 1) { clearError(); $('player-status').textContent = `מתנגן ${queueIndex + 1} מתוך ${queue.length}: ${title}`; }
  if (state === 2 && $('player-error').hidden) $('player-status').textContent = `מושהה: ${title}`;
  if (state === 0 && queueIndex === queue.length - 1) {
    if (currentAlbum()?.youtubePlaylist && mode === 'short') player.stopVideo();
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
  else if (state === 0 && queueIndex === queue.length - 1) playAt(0);
  else player.playVideo();
});
$('previous-track').addEventListener('click', () => playAt(queueIndex - 1));
$('next-track').addEventListener('click', () => playAt(queueIndex + 1));
$('album-search').addEventListener('input', renderList);
$('previous-album').addEventListener('click', () => selectAlbum(active - 1));
$('next-album').addEventListener('click', () => selectAlbum(active + 1));
for (const m of ['full', 'short']) $('mode-' + m).addEventListener('click', () => {
  if (mode !== m) { mode = m; renderMode(); }
});
$('mark-done').addEventListener('click', () => {
  const n = currentAlbum().n; done.has(n) ? done.delete(n) : done.add(n);
  writeStore(DONE_KEY, [...done]); renderDone(); renderList();
});
$('reset-focus').addEventListener('click', () => { delete focus[currentAlbum().n]; writeStore(FOCUS_KEY, focus); renderMode(); });
async function init() {
  try {
    const [catalogResponse, pilotResponse] = await Promise.all([fetch('./albums.json'), fetch('./pilot.json')]);
    if (!catalogResponse.ok || !pilotResponse.ok) throw new Error('Data unavailable');
    const [catalog, pilot] = await Promise.all([catalogResponse.json(), pilotResponse.json()]);
    albums = catalog.filter(a => Object.hasOwn(pilot, a.n)).map(a => playableAlbum({...a, ...pilot[a.n]})).sort((a, b) => a.n - b.n);
    if (!albums.length || albums.some(a => !a.tracks.length || a.tracks.some(t => a.youtubePlaylist ? !(typeof t[0] === 'string' && Number.isInteger(t[2])) : !/^[A-Za-z0-9_-]{11}$/.test(t[1])))) throw new Error('Invalid pilot');
    $('loading').hidden = true; $('album-view').hidden = false;
    renderAlbum(); loadPlayer();
  } catch { $('loading').hidden = true; $('album-view').hidden = true; $('load-error').hidden = false; }
}
init();
