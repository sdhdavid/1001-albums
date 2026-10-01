// Real-browser check of album switching with the real YouTube player (runs in GitHub Actions: "Player check").
// Serves dist/ on localhost:8000 (started by the workflow), plays album A, moves to the next album and starts it
// with a song's ▶ and with "הפעלת הרצף", logging what the YouTube player actually holds after each step.
const {chromium} = require('playwright');
const A = Number(process.env.ALBUM || 101);
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({args: ['--autoplay-policy=no-user-gesture-required']});
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('console error:', m.text().slice(0, 200)); });
  page.on('pageerror', e => console.log('page error:', e.message));
  const snap = async label => {
    const s = await page.evaluate(() => {
      try {
        const d = player?.getVideoData?.() || {};
        return {shown: currentAlbum().n, playing: playingAlbum?.n, state, ytState: player?.getPlayerState?.(), video: d.title, videoId: d.video_id,
          ytList: (player?.getPlaylist?.() || []).slice(0, 3), ytIndex: player?.getPlaylistIndex?.(), status: document.getElementById('player-status').textContent,
          shownList: currentAlbum().youtubePlaylist, playingList: playingAlbum?.youtubePlaylist};
      } catch (e) { return {error: String(e)}; }
    });
    console.log(label, JSON.stringify(s));
  };
  await page.goto(`http://localhost:8000/#/album/${A}`);
  for (let i = 0; i < 40 && !(await page.evaluate(() => typeof ready !== 'undefined' && ready)); i++) await wait(500);
  await snap('ready');
  await page.click('#quick-play'); await wait(8000); await snap('after quick play on A');
  await page.click('#next-album'); await wait(3000); await snap('moved to B');
  await page.locator('#track-list li button').first().click(); await wait(8000); await snap('after song ▶ on B');
  await page.click('#next-album'); await wait(3000); await snap('moved to C');
  await page.click('#play-pause'); await wait(8000); await snap('after הפעלת הרצף on C');
  await page.click('#next-album'); await wait(3000);
  await page.locator('#track-list li button').nth(2).click(); await wait(8000); await snap('after third song ▶ on D');
  await browser.close();
})();
