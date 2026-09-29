# 1001 אלבומים — project notes for Claude

A Hebrew (RTL) static site for listening through *1001 Albums You Must Hear Before You Die* (2005 edition) in book order, for the owner's friends and family. Live at https://sdhdavid.github.io/1001-albums/ (GitHub Pages). Currently 100 playable albums (book #1–100; the catalog lists all 1001, currently 1000 because one album is missing from the source list).

## Working with the owner
- The owner does not code and doesn't know GitHub. Reply in Hebrew, in plain language, no jargon; say what changed on the site, not how.
- Don't list commit hashes or file paths in replies unless asked.
- The owner reviews on the live site, so ship finished work (see Deploy), then report. Ask before big direction changes or anything personal (e.g. adding their name).
- Personal texts on the site (welcome story) are in the owner's voice; don't rewrite them unasked.

## Layout
- `dist/` is the whole site (no build step): `index.html`, `app.js` (vanilla JS, no deps), `styles.css`, `albums.json` (book catalog: n/year/title/artist; albums that are playable also have `"ready": true` + `spotifyAlbum` — the list shows only ready ones and needs the cover), and `albums/N.json` (per-album data, fetched on demand when the album is opened; neighbours are prefetched).
- `albums/N.json` per album: `tracks` (playlist albums: `[name, null, playlistIndex]`; continuous-video albums #27/#29/#47/#49: `[name, videoId, null, startSeconds]`; albums 1–10, 21, 23, 53: `[name, videoId]`), `durations` ("m:ss" per track), `focus` (track indexes for the focused queue), `youtubePlaylist` or `fullAlbumVideo`, `spotifyAlbum` (22-char id), `story` (3 Hebrew paragraphs: who & when / what you hear / why it matters), `picks` ([track name, Hebrew note] ×3), `guide` (older intro text, sources, book metadata — only on the first 50; new albums don't need it).
- `tools/`: `store.py` (read/write albums + refresh the catalog flags — never edit `ready`/`spotifyAlbum` in albums.json by hand), `tracklists.py` + `build_tracks.py`, `stories.py` + `build_stories.py` (older track/story sources for 1–50), `check_albums.py` (validates every album), `add_albums.py` (batch → albums/N.json), `fetch_durations.py` + `merge_durations.py` (lengths from iTunes + MusicBrainz).
- New pipeline (worked well for 51–100): manual workflow "Discover albums" (yt-dlp finds playlists and checks them against iTunes track lists) → review `tools/discovered.json` on the `discover-data` branch → write stories → build the batch → "Fetch track durations" with the batch → `merge_durations.py` → `add_albums.py`. Note `focus` are indexes into `tracks`, and playlist positions (`t[2]`) must be unique.
- Original batch pipeline for new albums: write `tools/batches/NAME.json` (format in the docstring of `add_albums.py`; tracklist, YouTube playlist, Spotify id, focus, story, picks) → run the manual "Fetch track durations" workflow with `batch=tools/batches/NAME.json`, read the JSON from the log, save it and run `merge_durations.py` (check each total against the book) → `python3 tools/add_albums.py tools/batches/NAME.json` (validates, then writes) → smoke test → deploy.
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
Original Hebrew, never copied from the book. Length (the owner found the first 100 too short; **confirm the exact target with them**): proposed ~250–300 words, 3–4 paragraphs (who & when / what you hear / why it matters / optionally a listening tip or context), plus three picks whose names match `tracks` exactly, each with a 1–2 sentence note. Warm, clear, non-academic; link to other albums on the site by number when relevant ("אלבום 14", only numbers ≤ the highest playable album). Only state facts you're sure of; soften or drop uncertain dates, chart positions and personnel. Re-read every story for fluent Hebrew and for claims you can't back — the first drafts of 51–100 needed two correction passes. Stories live in `tools/stories.py` (1–50) and `tools/stories_51_100.py`; `python3 tools/apply_stories.py <module>` writes them into `dist/albums/N.json`. The app shows headings for the first three paragraphs only (`STORY_HEADINGS` in app.js) — add a heading (or drop the fourth) if you write more.

## NEXT TASK (owner asked to start it in a fresh session, ideally on Opus 5.5 with high effort)
Rewrite and extend the stories/pick notes for albums 1–100 to the longer length above (ask the owner to confirm length first), then apply with `apply_stories.py`, run the checks and tests, deploy, and have the owner review a few on the live site. After that: the next 50 albums (101–150) with the discover pipeline, tagging genres in `tools/genres.py`.

## Next steps (agreed with the owner)
1. Infrastructure round. Done: per-album files loaded on demand; batch pipeline + validation. `albums.json` now holds the full numbered list (from the MusicBrainz series via the manual "Fetch catalog" workflow; source copy in `tools/catalog-2005.json`; entries 1–200 keep their earlier hand-checked titles). Known oddities in the source, resolved with the owner's book: the source listed 336 twice (Dion's *Born to Be With You* is the book's #336, inserted after Emmylou Harris), and had a stray duplicate *It Takes a Nation of Millions* right after *Surfer Rosa* (not in the book), and no album sits between Lambchop's *Nixon* and Ute Lemper's *Punishing Kiss*. Numbers are now simply the book order (n = position). That gives **1000 albums, one short of the book's 1001**: one album is missing from the source somewhere after #336 (position unknown), so numbers after it may be one too low. When it's found, insert it and renumber everything after it (only albums 1–53 are playable so far, so nothing published depends on it yet). Batch 51–100 is done (built with `tools/discover.py` → `tools/batches/build_51_100.py`; stories in `tools/stories_51_100.py`; the Spotify ids there came from web search and are unverified; YouTube playlists are mostly user-uploaded 'full album' playlists).
   Genres: `tools/genres.py` (labels per album, applied to the catalog by `store.rebuild_index()`; 1–100 tagged so far — tag the rest, owner reviews).
2. Add albums in batches of 25–50; the owner reviews texts.
3. Polish from friends' feedback.
4. Later: shared layer (who listened to what, ratings, comments) with accounts.
