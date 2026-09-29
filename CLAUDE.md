# 1001 אלבומים — project notes for Claude

A Hebrew (RTL) static site for listening through *1001 Albums You Must Hear Before You Die* (2005 edition) in book order, for the owner's friends and family. Live at https://sdhdavid.github.io/1001-albums/ (GitHub Pages). Currently 51 albums: book #1–50 plus #53 (A Love Supreme); #51–52 are missing.

## Working with the owner
- The owner does not code and doesn't know GitHub. Reply in Hebrew, in plain language, no jargon; say what changed on the site, not how.
- Don't list commit hashes or file paths in replies unless asked.
- The owner reviews on the live site, so ship finished work (see Deploy), then report. Ask before big direction changes or anything personal (e.g. adding their name).
- Personal texts on the site (welcome story) are in the owner's voice; don't rewrite them unasked.

## Layout
- `dist/` is the whole site (no build step): `index.html`, `app.js` (vanilla JS, no deps), `styles.css`, `albums.json` (book catalog: n/year/title/artist, first 200 entries), `pilot.json` (per-album data for playable albums, keyed by book number).
- `pilot.json` per album: `tracks` (playlist albums: `[name, null, playlistIndex]`; continuous-video albums #27/#29/#47/#49: `[name, videoId, null, startSeconds]`), `durations` ("m:ss" per track), `focus` (track indexes for the focused queue), `youtubePlaylist` or `fullAlbumVideo`, `spotifyAlbum` (22-char id), `story` (3 Hebrew paragraphs: who & when / what you hear / why it matters), `picks` ([track name, Hebrew note] ×3), `guide` (older intro text, sources, book metadata — kept as fallback/for checks, book box no longer shown).
- `tools/`: `tracklists.py` + `build_tracks.py` (track programs → pilot.json), `stories.py` + `build_stories.py` (album stories → pilot.json), `fetch_durations.py` (median track lengths from iTunes + MusicBrainz).
- `tests/player-smoke.cjs`: node DOM/YouTube mock harness. Run `node --check dist/app.js && node tests/player-smoke.cjs` before every push; update assertions when behavior changes.

## Features (don't break)
YouTube player (IFrame API, youtube.com host so Premium is recognized) and a YouTube/Spotify switch (Spotify album embed), per-song ▶ in track list and in story picks, full/focused queues, covers from Spotify oEmbed (cached in localStorage, lazy in list) with per-album background tint, progress "האזנת ל־X מתוך N" + bar, phone album drawer, first-visit welcome box (reopen via "מה זה?"), premium-cookies help box with copy buttons, English names left-aligned and bidi-isolated inside Hebrew text (`bidiText`). Font: Rubik (Google Fonts).

## Deploy
Push to branch → open PR to `main` → merge. `.github/workflows/pages.yml` publishes `dist/` to Pages and stamps `?v=<commit>` on CSS/JS/JSON URLs (cache busting). Check the "Publish site" run succeeds afterwards.

## Environment constraints (cloud sandbox)
- Spotify, YouTube, MusicBrainz, iTunes, github.io are blocked from the sandbox. Google Fonts CSS is reachable via curl but not from the headless browser.
- Workarounds: find Spotify album ids with WebSearch (`allowed_domains: open.spotify.com`); run network lookups in GitHub Actions (e.g. the manual "Fetch track durations" workflow prints JSON between `===DURATIONS-BEGIN/END===` in the job log — read it with the GitHub MCP job-logs tool) and check each album's total against `guide.book.duration`.
- Visual checks: Playwright is installed globally (`$(npm root -g)/playwright`, Chromium preinstalled). Serve `dist/` with `python3 -m http.server`, stub Spotify/YouTube/fonts with `page.route`. Don't `pkill -f http.server` (it kills the shell).

## Writing album stories
Original Hebrew, never copied from the book. ~150 words: three short paragraphs + three picks whose names match `tracks` exactly (build_stories.py asserts this). Warm, clear, non-academic; link to other albums on the site by number when relevant ("אלבום 14"). Only state facts you're sure of; soften or drop uncertain dates, chart positions and personnel.

## Next steps (agreed with the owner)
1. Infrastructure round: split `pilot.json` into per-album files loaded on demand; extend `albums.json` to all 1001 entries; a repeatable batch pipeline for adding albums (tracklist, YouTube playlist, Spotify id, durations, story, checks); fill in #51–52.
2. Add albums in batches of 25–50; the owner reviews texts.
3. Polish from friends' feedback.
4. Later: shared layer (who listened to what, ratings, comments) with accounts.
