# 1001 אלבומים — project notes for Claude

A Hebrew (RTL) static site for listening through *1001 Albums You Must Hear Before You Die* (2005 edition) in book order, for the owner's friends and family. Live at https://sdhdavid.github.io/1001-albums/ (GitHub Pages). Currently 51 playable albums (catalog lists all 1001): book #1–50 plus #53 (A Love Supreme); #51–52 are missing.

## Working with the owner
- The owner does not code and doesn't know GitHub. Reply in Hebrew, in plain language, no jargon; say what changed on the site, not how.
- Don't list commit hashes or file paths in replies unless asked.
- The owner reviews on the live site, so ship finished work (see Deploy), then report. Ask before big direction changes or anything personal (e.g. adding their name).
- Personal texts on the site (welcome story) are in the owner's voice; don't rewrite them unasked.

## Layout
- `dist/` is the whole site (no build step): `index.html`, `app.js` (vanilla JS, no deps), `styles.css`, `albums.json` (book catalog: n/year/title/artist; albums that are playable also have `"ready": true` + `spotifyAlbum` — the list shows only ready ones and needs the cover), and `albums/N.json` (per-album data, fetched on demand when the album is opened; neighbours are prefetched).
- `albums/N.json` per album: `tracks` (playlist albums: `[name, null, playlistIndex]`; continuous-video albums #27/#29/#47/#49: `[name, videoId, null, startSeconds]`; albums 1–10, 21, 23, 53: `[name, videoId]`), `durations` ("m:ss" per track), `focus` (track indexes for the focused queue), `youtubePlaylist` or `fullAlbumVideo`, `spotifyAlbum` (22-char id), `story` (3 Hebrew paragraphs: who & when / what you hear / why it matters), `picks` ([track name, Hebrew note] ×3), `guide` (older intro text, sources, book metadata — only on the first 50; new albums don't need it).
- `tools/`: `store.py` (read/write albums + refresh the catalog flags — never edit `ready`/`spotifyAlbum` in albums.json by hand), `tracklists.py` + `build_tracks.py`, `stories.py` + `build_stories.py` (older track/story sources for 1–50), `check_albums.py` (validates every album), `add_albums.py` (batch → albums/N.json), `fetch_durations.py` + `merge_durations.py` (lengths from iTunes + MusicBrainz).
- Batch pipeline for new albums: write `tools/batches/NAME.json` (format in the docstring of `add_albums.py`; tracklist, YouTube playlist, Spotify id, focus, story, picks) → run the manual "Fetch track durations" workflow with `batch=tools/batches/NAME.json`, read the JSON from the log, save it and run `merge_durations.py` (check each total against the book) → `python3 tools/add_albums.py tools/batches/NAME.json` (validates, then writes) → smoke test → deploy.
- `tests/player-smoke.cjs`: node DOM/YouTube mock harness. Run `node --check dist/app.js && python3 tools/check_albums.py && node tests/player-smoke.cjs` before every push; update assertions when behavior changes.

## Features (don't break)
YouTube player (IFrame API, youtube.com host so Premium is recognized) and a YouTube/Spotify switch (Spotify album embed), per-song ▶ in track list and in story picks, full/focused queues, covers from Spotify oEmbed (cached in localStorage, lazy in list) with per-album background tint, progress "האזנת ל־X מתוך N" + bar, phone album drawer, first-visit welcome box (reopen via "מה זה?"), premium-cookies help box with copy buttons, English names left-aligned and bidi-isolated inside Hebrew text (`bidiText`). Font: Rubik (Google Fonts).

## Deploy
Push to branch → open PR to `main` → merge. `.github/workflows/pages.yml` publishes `dist/` to Pages and stamps `?v=<commit>` on CSS/JS and (via `const V` in app.js) on every JSON fetch (cache busting). Check the "Publish site" run succeeds afterwards.

## Environment constraints (cloud sandbox)
- Spotify, YouTube, MusicBrainz, iTunes, github.io are blocked from the sandbox. Google Fonts CSS is reachable via curl but not from the headless browser.
- Workarounds: find Spotify album ids with WebSearch (`allowed_domains: open.spotify.com`); run network lookups in GitHub Actions (e.g. the manual "Fetch track durations" workflow prints JSON between `===DURATIONS-BEGIN/END===` in the job log — read it with the GitHub MCP job-logs tool) and check each album's total against `guide.book.duration`.
- Visual checks: Playwright is installed globally (`$(npm root -g)/playwright`, Chromium preinstalled). Serve `dist/` with `python3 -m http.server`, stub Spotify/YouTube/fonts with `page.route`. Don't `pkill -f http.server` (it kills the shell).

## Writing album stories
Original Hebrew, never copied from the book. ~150 words: three short paragraphs + three picks whose names match `tracks` exactly (build_stories.py asserts this). Warm, clear, non-academic; link to other albums on the site by number when relevant ("אלבום 14"). Only state facts you're sure of; soften or drop uncertain dates, chart positions and personnel.

## Next steps (agreed with the owner)
1. Infrastructure round. Done: per-album files loaded on demand; batch pipeline + validation. `albums.json` now holds the full numbered list (from the MusicBrainz series via the manual "Fetch catalog" workflow; source copy in `tools/catalog-2005.json`; entries 1–200 keep their earlier hand-checked titles). Known oddities in the source: number 336 appears twice (Dion's *Born to Be With You* was left out, *The Hissing of Summer Lawns* kept), 924 is missing, and 623/634 are both *It Takes a Nation of Millions*. Owner decides how to resolve. Still open: fill in #51–52 (Otis Blue, The Beach Boys Today!) as the first batch.
   Genres: `tools/genres.py` (labels per album, applied to the catalog by `store.rebuild_index()`; only 1–53 tagged so far — tag the rest, owner reviews).
2. Add albums in batches of 25–50; the owner reviews texts.
3. Polish from friends' feedback.
4. Later: shared layer (who listened to what, ratings, comments) with accounts.
