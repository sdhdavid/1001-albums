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
async function boot({broken=false, noStorage=false}={}) {
  const html=fs.readFileSync('dist/index.html','utf8'), nodes={};
  for (const [,id] of html.matchAll(/id="([^"]+)"/g)) { assert(!nodes[id], `duplicate ${id}`); nodes[id]=new El(); }
  const storage=new Map([['album-journey-2005-done','[1,200]']]);
  const calls=[]; let mock;
  const ctx={console, location:{origin:'https://example.test'},setTimeout:()=>1,clearTimeout(){},
    document:{getElementById:id=>nodes[id],createElement:t=>new El(t),head:new El(),querySelector:()=>new El()},
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>{if(noStorage)throw Error('blocked');storage.set(k,v)}},
    fetch:async url=>({ok:!broken,json:async()=>JSON.parse(fs.readFileSync('dist/'+url.slice(2),'utf8'))}),
    YT:{Player:class {
      constructor(id,options){this.options=options;this.index=0;this.frame=new El();mock=this;calls.push(['create']);}
      getIframe(){return this.frame;} getPlaylistIndex(){return this.index;}
      stopVideo(){calls.push(['stop']);} cuePlaylist(ids,index){this.ids=ids;this.index=Array.isArray(ids)?index:ids.index;calls.push(['cue',...(Array.isArray(ids)?ids:[ids.list,ids.index])]);}
      setLoop(){} setShuffle(){} destroy(){}
      playVideoAt(index){this.index=index;calls.push(['playAt',index]);this.options.events.onStateChange({data:1});}
      playVideo(){calls.push(['play']);this.options.events.onStateChange({data:1});}
      pauseVideo(){calls.push(['pause']);this.options.events.onStateChange({data:2});}
    }}
  };ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync('dist/app.js','utf8'),ctx);
  await new Promise(resolve=>setImmediate(resolve));
  return {nodes,calls,storage,ctx,get player(){return mock;}};
}
(async()=>{
  const t=await boot(), {nodes:n,calls,storage}=t; const p=t.player;
  assert.equal(n['album-list'].children.length,51); assert.equal(n['album-title'].textContent,'In the Wee Small Hours');
  assert.equal(n['track-list'].children.length,16);
  for (let i=0;i<10;i++) {
    const data=JSON.parse(fs.readFileSync('dist/pilot.json','utf8'))[String(i+1)];
    assert.equal(n['track-list'].children.length,data.tracks.length);
    assert.equal(n['album-note'].textContent,data.guide.intro[0].text);
    assert.equal(n['book-meta'].hidden,false);
    assert.equal(n['book-year'].textContent,String(data.guide.book.year));
    assert.equal(n['book-pages'].textContent,data.guide.book.pages);
    n['mode-short'].click();assert.equal(n['track-list'].children.length,data.focus.length);
    n['mode-full'].click();n['next-album'].click();
  }
  assert.equal(n['album-title'].textContent,'Palo Congo');
  p.options.events.onReady();
  const added=JSON.parse(fs.readFileSync('dist/pilot.json','utf8'));
  assert.equal(n['book-pages'].textContent,'32–33');
  assert.equal(p.ids.list,'PLowQCq3Ss89iHLhI8fLDx6Tdu4fj_Fcgu');
  assert.equal(n['track-list'].children.length,8);
  n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
  n['next-track'].click();assert.equal(p.index,1);
  n['mode-full'].click();n['next-album'].click();assert.equal(n['album-title'].textContent,'Birth of the Cool');
  assert.equal(n['track-list'].children.length,12);
  assert.equal(n['book-label'].textContent,'Capitol');
  assert.equal(p.ids.list,'PLowQCq3Ss89jlWMOmeDEJEawXiV901pAs');
  n['next-album'].click();assert.equal(n['album-title'].textContent,'Kenya');
  assert.equal(n['track-list'].children.length,12);
  assert.equal(n['book-year'].textContent,'1957');
  assert.equal(p.ids.list,'PLowQCq3Ss89i33_zzDhdErj7Ymwm6I_EZ');
  n['mode-short'].click();n['next-track'].click();assert.equal(p.index,5,'playlist-focused next jumps to original album position');
  n['mode-full'].click();
  for (let number=14; number<=20; number++) {
    n['next-album'].click();
    const album=added[String(number)];
    assert.equal(n['track-list'].children.length,album.tracks.length,`album ${number} original program`);
    assert.equal(n['album-note'].textContent,album.guide.intro[0].text);
    assert.equal(n['book-pages'].textContent,album.guide.book.pages);
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
  n['next-album'].click();assert.equal(n['album-title'].textContent,'Kind of Blue');
  assert.equal(n['book-meta'].hidden,false);assert.equal(n['book-pages'].textContent,'42–43');
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
  n['mode-full'].click();n['next-album'].click();assert.equal(n['album-title'].textContent,'Gunfighter Ballads and Trail Songs');
  assert.equal(n['embedded-listening'].hidden,false);assert.equal(n['external-listening'].hidden,true);
  assert.equal(n['track-list'].children.length,12);
  assert.equal(p.ids.list,added['22'].youtubeAlbumPlaylist);
  n['track-list'].children[6].children[1].click();assert.equal(p.index,6);
  n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
  n['mode-full'].click();
  n['next-album'].click();assert.equal(n['album-title'].textContent,'Time Out');assert.equal(p.ids.length,7);assert.equal(n['embedded-listening'].hidden,false);
  assert.equal(n['album-youtube-player'].src,'about:blank','switching to the mapped player unloads prior album');
  assert.equal(n['album-essay'].hidden,false);
  p.options.events.onError({data:150});assert.equal(n['player-error'].hidden,false);assert.match(n['player-error-text'].textContent,/150/);
  n['next-track'].click();assert.equal(n['player-error'].hidden,true);
  const catalog=JSON.parse(fs.readFileSync('dist/albums.json','utf8'));
  for (let number=24; number<=50; number++) {
    n['next-album'].click();assert.equal(n['album-title'].textContent,catalog[number-1].title);
    assert.equal(n['embedded-listening'].hidden,false);
    assert.equal(n['external-listening'].hidden,true);
    const album=added[String(number)];
    if ([27,29,47,49].includes(number)) {
      assert.equal(n['track-list'].children.length,1);
      assert.equal(n['mode-switch'].hidden,true);
      assert.equal(p.ids[0],album.youtubeAlbumVideo);
      assert.match(n['mode-explain'].textContent,/האלבום המלא/);
    } else {
      const expected={24:13,25:12,26:14,28:4,30:6,31:12,32:12,33:7,34:12,35:14,36:13,37:13,38:8,39:4,40:9,41:8,42:13,43:15,44:12,45:20,46:12,48:13,50:11}[number];
      assert.equal(n['track-list'].children.length,expected,`album ${number} queue`);
      assert.equal(p.ids.list,number===31?'PL1a1FcevWP19h-lU6yce1_TuLRWCzXJ20':number===26?'PLowQCq3Ss89ikMwB_bPRQuaQttWp0xaD4':number===34?'PLowQCq3Ss89jz1iejIedRBojbvYe3MSzK':album.youtubeAlbumPlaylist);
      assert.equal(n['youtube-direct'].href,`https://www.youtube.com/playlist?list=${p.ids.list}`);
      n['track-list'].children[expected-1].children[1].click();assert.equal(p.index,expected-1);
      n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
      n['mode-full'].click();
    }
    assert.equal(n['book-meta'].hidden,false);
  }
  n['next-album'].click();assert.equal(n['album-title'].textContent,'A Love Supreme');assert.equal(p.ids.length,4);assert(n['next-album'].disabled);
  assert.equal(n['album-youtube-player'].src,'about:blank');
  p.index=3;p.options.events.onStateChange({data:0});assert.match(n['player-status'].textContent,/הסתיים/);
  n['play-pause'].click();assert.equal(p.index,0,'replay starts from beginning');
  n['album-search'].value='Miles';n['album-search'].listeners.input();assert.equal(n['album-list'].children.length,2);
  assert.equal(calls.filter(x=>x[0]==='create').length,1,'only one player');
  const b=await boot({broken:true});assert.equal(b.nodes['load-error'].hidden,false);assert(!b.player);
  const s=await boot({noStorage:true});s.nodes['mark-done'].click();assert.match(s.nodes['storage-note'].textContent,/חסומה/);
  console.log('PASS: book entries 1–50 and jazz encore, all fifty YouTube queues or continuous album videos, track buttons, focused selection, transport, replay, errors, search and progress. Mock API only; live playback is not verified.');
})().catch(err=>{console.error(err);process.exitCode=1});
