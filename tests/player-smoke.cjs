// Small DOM/YouTube contract harness. No external videos or browser are loaded.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
class El {
  constructor(tag='div') { this.tag=tag; this.children=[]; this.listeners={}; this.attributes={}; this.hidden=false; this.disabled=false; this.value=''; this.classList={toggle(){}}; }
  append(...els) { this.children.push(...els); }
  replaceChildren(...els) { this.children=els; }
  setAttribute(k,v) { this.attributes[k]=v; }
  removeAttribute(k) { delete this.attributes[k]; }
  addEventListener(k,fn) { this.listeners[k]=fn; }
  querySelector(tag) { return this.children.find(x=>x.tag===tag); }
  click() { if (!this.disabled) this.listeners.click?.(); }
  remove() {}
}
const flush=()=>new Promise(r=>setImmediate(r));
const pilotAll=()=>Object.fromEntries(fs.readdirSync('dist/albums').map(f=>[f.slice(0,-5),JSON.parse(fs.readFileSync('dist/albums/'+f,'utf8'))]));
function noteMatches(n,data){
  if (data.story) assert.equal(n['album-note'].children.length,data.story.length+(data.picks?.length?1:0));
  else assert.equal(n['album-note'].children[0].children.map(c=>c.textContent).join(''),data.guide.intro.map(s=>s.text).join(' '));
}
async function boot({broken=false, noStorage=false}={}) {
  const html=fs.readFileSync('dist/index.html','utf8'), nodes={};
  for (const [,id] of html.matchAll(/id="([^"]+)"/g)) { assert(!nodes[id], `duplicate ${id}`); nodes[id]=new El(); }
  const storage=new Map([['album-journey-2005-done','[1,200]']]);
  const calls=[], fetched=[]; let mock, failAlbum=null;
  const ctx={console, location:{origin:'https://example.test'},setTimeout:(f,ms)=>ms===20?setTimeout(f,ms):1,clearTimeout(){},setInterval:()=>1,clearInterval(){},
    document:{getElementById:id=>nodes[id],createElement:t=>new El(t),createTextNode:t=>({textContent:t}),head:new El(),querySelector:()=>new El()},
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>{if(noStorage)throw Error('blocked');storage.set(k,v)}},
    fetch:async url=>(fetched.push(url),{ok:!broken&&!(failAlbum&&url.includes(`/${failAlbum}.json`)),json:async()=>JSON.parse(fs.readFileSync('dist/'+url.slice(2).replace(/\?.*$/,''),'utf8'))}),
    YT:{Player:class {
      constructor(id,options){this.options=options;this.index=0;this.frame=new El();mock=this;calls.push(['create']);}
      getIframe(){return this.frame;} getPlaylistIndex(){return this.index;}
      stopVideo(){calls.push(['stop']);} cuePlaylist(ids,index){this.ids=ids;this.index=Array.isArray(ids)?index:ids.index;calls.push(['cue',...(Array.isArray(ids)?ids:[ids.list,ids.index])]);}
      cueVideoById(o){this.ids=[o.videoId];calls.push(['cueVideo',o.videoId,o.startSeconds]);}
      setLoop(){} setShuffle(){} destroy(){} getPlaylist(){return this.playlist||[];} getCurrentTime(){return this.time||0;} seekTo(s){this.time=s;calls.push(['seek',s]);}
      playVideoAt(index){this.index=index;calls.push(['playAt',index]);this.options.events.onStateChange({data:1});}
      playVideo(){calls.push(['play']);this.options.events.onStateChange({data:1});}
      pauseVideo(){calls.push(['pause']);this.options.events.onStateChange({data:2});}
    }}
  };ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync('dist/app.js','utf8'),ctx);
  await new Promise(resolve=>setImmediate(resolve));
  return {nodes,calls,fetched,storage,ctx,fail:n=>{failAlbum=n;},get player(){return mock;}};
}
(async()=>{
  const t=await boot(), {nodes:n,calls,storage}=t; const p=t.player;
  const rows=()=>n['album-list'].children.filter(c=>c.tag==='button').length;
  const nx=async()=>{n['next-album'].click();await flush();}, pv=async()=>{n['previous-album'].click();await flush();};
  assert.deepEqual(n['album-list'].children.filter(c=>c.tag==='div').map(c=>c.textContent),['שנות ה־50','שנות ה־60'],'decade markers in book order');
  assert.deepEqual(n['album-genres'].children.map(c=>c.textContent),['סטנדרטים וקברט'],'genre labels shown on the album page');assert.equal(n['album-genres'].hidden,false);
  assert.equal(rows(),51); assert.equal(n['album-title'].textContent,'In the Wee Small Hours');
  assert.equal(n['track-list'].children.length,16);
  const pilotData=pilotAll();
  for (const [k,a] of Object.entries(pilotData)) { assert.equal(a.durations.length,a.tracks.length,`durations for ${k}`); for (const d of a.durations) assert.match(d,/^\d{1,2}:\d{2}$/,`duration format in ${k}`); }
  assert.equal(n['track-list'].children[0].children[0].children[0].textContent,pilotData['1'].durations[0]);
  assert.equal(n['list-progress'].textContent,'האזנת ל־1 מתוך 51 אלבומים');assert.equal(n['progress-meter'].value,1);assert.equal(n['progress-meter'].max,51);
  assert.equal(n['toggle-progress'].textContent,'1 מתוך 51');
  for (let i=0;i<10;i++) {
    const data=pilotAll()[String(i+1)];
    assert.equal(n['track-list'].children.length,data.tracks.length);
    noteMatches(n,data);
    assert.equal(n['album-essay'].hidden,false);
    n['mode-short'].click();assert.equal(n['track-list'].children.length,data.focus.length);
    n['mode-full'].click();await nx();
  }
  assert.equal(n['album-title'].textContent,'Palo Congo');
  p.options.events.onReady();
  const added=pilotAll();
  assert.equal(p.ids.list,'PLowQCq3Ss89iHLhI8fLDx6Tdu4fj_Fcgu');
  assert.equal(n['track-list'].children.length,8);
  n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
  n['next-track'].click();assert.equal(p.index,1);
  n['mode-full'].click();await nx();assert.equal(n['album-title'].textContent,'Birth of the Cool');
  assert.equal(n['track-list'].children.length,12);
  assert.equal(p.ids.list,'PLowQCq3Ss89jlWMOmeDEJEawXiV901pAs');
  await nx();assert.equal(n['album-title'].textContent,'Kenya');
  assert.equal(n['track-list'].children.length,12);
  assert.equal(p.ids.list,'PLowQCq3Ss89i33_zzDhdErj7Ymwm6I_EZ');
  n['mode-short'].click();n['next-track'].click();assert.equal(p.index,5,'playlist-focused next jumps to original album position');
  n['mode-full'].click();
  for (let number=14; number<=20; number++) {
    await nx();
    const album=added[String(number)];
    assert.equal(n['track-list'].children.length,album.tracks.length,`album ${number} original program`);
    noteMatches(n,album);
    assert.equal(n['album-essay'].hidden,false);
    assert.equal(p.ids.list,album.youtubePlaylist);
    n['mode-short'].click();assert.equal(n['track-list'].children.length,album.focus.length);
    n['next-track'].click();assert.equal(p.index,album.focus[1],`album ${number} playlist focus index`);
    if (number===14) {
      p.index=album.focus[1]+1;p.options.events.onStateChange({data:1});
      assert.equal(p.index,album.focus[2],'autoplay skips a track outside the focused queue');
    }
    n['mode-full'].click();
  }
  assert.equal(n['album-title'].textContent,'The Genius of Ray Charles');
  await nx();assert.equal(n['album-title'].textContent,'Kind of Blue');
  assert.equal(n['album-essay'].hidden,false);
  assert(!n['play-pause'].disabled);
  assert.equal(p.ids.length,5);
  n['play-pause'].click();assert.equal(calls.at(-1)[0],'play');
  assert.equal(n['album-essay'].hidden,false);
  const essay=n['essay-body'].children;
  p.index=1;p.options.events.onStateChange({data:1});
  assert.equal(n['track-note-title'].textContent,'Freddie Freeloader');
  assert.equal(n['essay-body'].children,essay,'track changes must not replace album essay');
  const before=calls.length;n['mark-done'].click();assert.equal(calls.length,before,'mark heard must not interrupt');
  assert.deepEqual(JSON.parse(storage.get('album-journey-2005-done')),[1,200,21]);
  n['mode-short'].click();assert.deepEqual([...p.ids],['ylXk1LBvIqU','TLDflhhdPCg','-488UORrfJ0']);
  n['next-track'].click();assert.equal(p.index,1);
  assert.equal(n['track-note-title'].textContent,'Blue in Green','focused playlist index maps to actual video');
  n['focus-options'].children[0].children[0].checked=false;n['focus-options'].children[0].children[0].listeners.change();
  assert.equal(p.ids.length,2);assert.equal(p.ids[0],'TLDflhhdPCg');
  n['focus-options'].children[2].children[0].checked=false;n['focus-options'].children[2].children[0].listeners.change();
  n['focus-options'].children[3].children[0].checked=false;n['focus-options'].children[3].children[0].listeners.change();
  assert.equal(p.ids.length,1);assert.equal(n['focus-error'].hidden,false);
  n['mode-full'].click();await nx();assert.equal(n['album-title'].textContent,'Gunfighter Ballads and Trail Songs');
  assert.equal(n['embedded-listening'].hidden,false);assert.equal(n['external-listening'].hidden,true);
  assert.equal(n['track-list'].children.length,12);
  assert.equal(p.ids.list,added['22'].youtubePlaylist);
  n['track-list'].children[6].children[1].click();assert.equal(p.index,6);
  n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
  n['mode-full'].click();
  await nx();assert.equal(n['album-title'].textContent,'Time Out');assert.equal(p.ids.length,7);assert.equal(n['embedded-listening'].hidden,false);
  assert.equal(n['album-youtube-player'].src,'about:blank','switching to the mapped player unloads prior album');
  assert.equal(n['album-essay'].hidden,false);
  p.options.events.onError({data:150});assert.equal(n['player-error'].hidden,false);assert.match(n['player-error-text'].textContent,/150/);
  n['next-track'].click();assert.equal(n['player-error'].hidden,true);
  const catalog=JSON.parse(fs.readFileSync('dist/albums.json','utf8'));
  for (let number=24; number<=50; number++) {
    await nx();assert.equal(n['album-title'].textContent,catalog[number-1].title);
    assert.equal(n['embedded-listening'].hidden,false);
    assert.equal(n['external-listening'].hidden,true);
    const album=added[String(number)];
    assert(album.tracks.every(tr=>!/^קטע \d/.test(tr[0])),`album ${number} has real song names`);
    assert.equal(n['track-list'].children.length,album.tracks.length,`album ${number} queue`);
    assert.equal(n['track-list'].children[0].children[0].textContent,album.tracks[0][0]);
    assert.equal(n['mode-switch'].hidden,false);
    const last=album.tracks.length-1;
    if ([27,29,47,49].includes(number)) {
      assert.equal(p.ids[0],album.tracks[0][1]);
      assert.deepEqual(calls.filter(c=>c[0]==='cueVideo').at(-1).slice(1,2),[album.tracks[0][1]],'continuous album cues its own video');
      assert.equal(album.fullAlbumVideo,true);
      n['track-list'].children[last].children[1].click();assert.deepEqual(calls.at(-2),['seek',album.tracks[last][3]]);
      assert.equal(n['track-list'].children[last].attributes['aria-current'],'true');
      p.time=album.tracks[1][3]+3;p.options.events.onStateChange({data:1});
      assert.match(n['player-status'].textContent,new RegExp(`2 מתוך ${album.tracks.length}`),'chapter follows playback time');
      n['mode-short'].click();assert.equal(n['track-list'].children.length,album.focus.length);
      const skipped=album.tracks.findIndex((tr,i)=>!album.focus.includes(i));
      p.time=album.tracks[skipped][3]+1;p.options.events.onStateChange({data:1});
      assert(album.focus.some(i=>p.time===album.tracks[i][3])||/הסתיים/.test(n['player-status'].textContent),'focused chapter skip');
      n['mode-full'].click();
    } else {
      assert.equal(p.ids.list,album.youtubePlaylist);
      assert.equal(p.ids.list,number===31?'PL1a1FcevWP19h-lU6yce1_TuLRWCzXJ20':number===26?'PLowQCq3Ss89ikMwB_bPRQuaQttWp0xaD4':number===34?'PLowQCq3Ss89jz1iejIedRBojbvYe3MSzK':album.youtubePlaylist);
      assert.equal(n['youtube-direct'].href,`https://www.youtube.com/playlist?list=${p.ids.list}`);
      n['track-list'].children[last].children[1].click();assert.equal(p.index,last);
      n['mode-short'].click();assert.equal(n['track-list'].children.length,album.focus.length);
      n['mode-full'].click();
    }
    assert.equal(n['album-essay'].hidden,false);
  }
  await nx();assert.equal(n['album-title'].textContent,'A Love Supreme');assert.equal(p.ids.length,4);assert(n['next-album'].disabled);
  assert.equal(n['album-youtube-player'].src,'about:blank');
  p.index=3;p.options.events.onStateChange({data:0});assert.match(n['player-status'].textContent,/הסתיים/);
  n['play-pause'].click();assert.equal(p.index,0,'replay starts from beginning');
  // Runtime matching: a reordered playlist with an extra bonus video maps songs by their real titles.
  n['album-search'].value='';
  while(n['album-title'].textContent!=='Getz / Gilberto')await pv();
  const gg=added['41'];const order=[3,0,1,2,5,4,7,6];
  p.playlist=[...order.map(i=>'vid'+i),'bonus'];
  const titleOf={};order.forEach(i=>titleOf['vid'+i]=`Stan Getz & João Gilberto - ${gg.tracks[i][0]} (Remastered 2003)`);titleOf.bonus='Stan Getz - Ipanema interview';
  t.ctx.fetch=async url=>{const id=decodeURIComponent(url).match(/v=([^&]+)/)[1];return {ok:true,json:async()=>({title:titleOf[id]})};};
  p.options.events.onStateChange({data:5});
  await new Promise(r=>setTimeout(r,20));
  n['track-list'].children[0].children[1].click();assert.equal(p.index,1,'Girl from Ipanema found at playlist position 1');
  n['track-list'].children[3].children[1].click();assert.equal(p.index,0,'Desafinado found at playlist position 0');
  p.index=8;p.options.events.onStateChange({data:1});assert.equal(n['track-list'].children[4].attributes['aria-current'],'true','bonus video is skipped to the next album song');
  p.playlist=[];
  while(n['album-title'].textContent!=='A Love Supreme')await nx();
  n['album-search'].value='Miles';n['album-search'].listeners.input();assert.equal(rows(),2);
  assert.equal(calls.filter(x=>x[0]==='create').length,1,'only one player');
  // Genre filter: the menu lists the labels in use; picking one narrows the list without touching the journey order.
  n['album-search'].value='';n['album-search'].listeners.input();
  const menu=n['genre-select'];assert.equal(menu.hidden,false);assert.equal(menu.children[0].textContent,"כל הז'אנרים");
  const pick=g=>{menu.value=g;menu.listeners.change();};
  const catalogNow=JSON.parse(fs.readFileSync('dist/albums.json','utf8')).filter(a=>a.ready);
  assert(menu.children.some(o=>o.value==="ג'אז"&&o.textContent.startsWith("ג'אז ·")));
  pick("ג'אז");assert.equal(rows(),catalogNow.filter(a=>a.genres?.includes("ג'אז")).length);
  n['album-search'].value='Miles';n['album-search'].listeners.input();assert.equal(rows(),2,'search combines with genre');
  pick('');assert.equal(rows(),2);n['album-search'].value='';n['album-search'].listeners.input();
  assert.equal(rows(),catalogNow.length);
  // Spotify: every album has an embed; switching stops YouTube, is remembered, and switching back restores the queue.
  const all=pilotAll();
  for (const [k,a] of Object.entries(all)) assert.match(a.spotifyAlbum||'',/^[A-Za-z0-9]{22}$/,`spotify id for ${k}`);
  n['service-spotify'].click();
  assert.equal(n['spotify-listening'].hidden,false);assert.equal(n['embedded-listening'].hidden,true);assert.equal(n['mode-switch'].hidden,true);
  assert.equal(n['spotify-player'].src,`https://open.spotify.com/embed/album/${all['53'].spotifyAlbum}?utm_source=generator`);
  assert.equal(calls.at(-1)[0],'stop');assert.equal(storage.get('album-journey-2005-service'),'"spotify"');
  await pv();assert.equal(n['spotify-player'].src,`https://open.spotify.com/embed/album/${all['50'].spotifyAlbum}?utm_source=generator`);
  n['service-youtube'].click();
  assert.equal(n['spotify-listening'].hidden,true);assert.equal(n['spotify-player'].src,'about:blank');assert.equal(n['embedded-listening'].hidden,false);
  assert.equal(n['track-list'].children.length,all['50'].tracks.length);
  // Story picks: ▶ on a pick plays that song in the site player.
  while(n['album-title'].textContent!=='Brilliant Corners')await pv();
  const bc=pilotAll()['10'];
  n['mode-short'].click();
  const picks=n['album-note'].children.at(-1).children[1].children;
  const pannonica=picks.findIndex(li=>li.children[0].children[1].textContent==='Pannonica');
  picks[pannonica].children[0].children[0].click();
  const pi=bc.tracks.findIndex(t=>t[0]==='Pannonica');
  assert.equal(p.index,bc.youtubePlaylist?pi:bc.focus.indexOf(pi),'pick plays Pannonica from the focused queue');
  n['mode-full'].click();
  // Welcome box: shown on first visit, dismissed and remembered, reopenable from the header.
  assert.equal(n['welcome'].hidden,false);n['close-welcome'].click();assert.equal(n['welcome'].hidden,true);
  assert.equal(storage.get('album-journey-2005-welcomed'),'true');n['show-welcome'].click();assert.equal(n['welcome'].hidden,false);
  // Phone drawer: opening the list and picking an album closes it again.
  n['catalog-toggle'].click();assert.equal(n['catalog-toggle'].attributes['aria-expanded'],'true');
  await pv();assert.equal(n['catalog-toggle'].attributes['aria-expanded'],'false');
  // On-demand loading: only the catalog, the first album and its neighbour are fetched up front; a failed album keeps the current one on screen.
  const l=await boot();
  assert.deepEqual(l.fetched.filter(u=>u.startsWith('./')).map(u=>u.replace(/\?.*/,'')),['./albums.json','./albums/1.json','./albums/2.json']);
  l.fail(3);l.nodes['next-album'].click();await flush();l.nodes['next-album'].click();await flush();
  assert.equal(l.nodes['album-title'].textContent,'Elvis Presley');assert.equal(l.nodes['album-error'].hidden,false);
  l.fail(null);l.nodes['next-album'].click();await flush();
  assert.equal(l.nodes['album-title'].textContent,'Tragic Songs of Life');assert.equal(l.nodes['album-error'].hidden,true,'retry after a failed load works');
  const b=await boot({broken:true});assert.equal(b.nodes['load-error'].hidden,false);assert(!b.player);
  const s=await boot({noStorage:true});s.nodes['mark-done'].click();assert.match(s.nodes['storage-note'].textContent,/חסומה/);
  console.log('PASS: book entries 1–50 and jazz encore, all fifty YouTube queues or continuous album videos, track buttons, focused selection, transport, replay, errors, search, progress, the phone album drawer, the welcome box, track lengths and the Spotify switch. Mock API only; live playback is not verified.');
})().catch(err=>{console.error(err);process.exitCode=1});
