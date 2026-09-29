# Album Journey

Hebrew RTL static listening site for the 2005 book order.

The first 50 book entries are present consecutively, plus the earlier A Love Supreme listening pilot (53). All first 50 have original Hebrew story essays of at least 120 words, with edition metadata and printed page references from the provided 2005 book. The existing 23 albums with mapped recordings retain the embedded YouTube full and focused playback queues (278 listed tracks). Twenty-four more use verified multi-video YouTube playlists with numbered track controls in the site, including newly located complete playlists for #26 and #34 and a replacement for the unavailable #31 playlist. Four (#27, #29, #47, #49) use continuous full-album YouTube videos, clearly labeled as such. Playlist editions and order may differ from the printed LP, and regional availability and embedding rights may change. Entries 1–10 also include optional short track notes.

YouTube IFrame API handles explicit full/focused queues and native playback synchronization. Local storage preserves completion and custom focused selections. Existing progress outside the playable catalog remains intact.

Validation: `node --check dist/app.js` and `node tests/player-smoke.cjs`. The harness checks all 50 consecutive book entries, queue length and transport behavior. Third-party availability, embedding rights, and region-specific playback can change independently of this static site.

Static output: dist. Hosting configuration: .openai/hosting.json.

Track programs: every entry 1–50 lists its real song titles (official album order, from `tools/tracklists.py` → `dist/pilot.json` via `tools/build_tracks.py`). For YouTube playlists the site reads each playlist video's title at runtime (YouTube oEmbed, noembed fallback, cached in local storage) and maps every song to its matching playlist entry, so reordered playlists and bonus videos are handled; songs missing from a playlist are marked unavailable. The four continuous full-album videos (#27, #29, #47, #49) get per-song chapters computed from track durations, with seeking and focused-queue skipping.

Spotify: each entry also has a `spotifyAlbum` id in `dist/pilot.json`. A YouTube / Spotify switch in the listening panel (remembered in local storage) swaps the YouTube player for Spotify's album embed. Signed-in Spotify Premium users hear full tracks; others get previews.

Publishing: pushes to `main` deploy `dist/` to GitHub Pages (`.github/workflows/pages.yml`).

Track lengths: every entry has a `durations` array in `dist/pilot.json` (one "m:ss" per track), shown next to each song. They come from `tools/fetch_durations.py` (median across iTunes and MusicBrainz editions, run via the manual "Fetch track durations" workflow) and were checked against each album's book length; a few were corrected by hand.

Album stories: each entry has an original Hebrew `story` (three short sections: who & when, what you hear, why it matters) and `picks` (songs to notice, each with a ▶ that plays it in the site's player). Written in `tools/stories.py` and merged into `dist/pilot.json` with `python3 tools/build_stories.py`. The older `guide.intro` text stays as a fallback and for its source links.
