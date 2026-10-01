// Small DOM/YouTube contract harness. No external videos or browser are loaded.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
class El {
  constructor(tag='div') { this.tag=tag; this.children=[]; this.listeners={}; this.attributes={}; this.hidden=false; this.disabled=false; this.value=''; this.dataset={}; this.style={setProperty(){}}; const cls=this.classSet=new Set(); this.classList={toggle(c,on){ if(on??!cls.has(c)) cls.add(c); else cls.delete(c); },contains:c=>cls.has(c)}; }
  querySelectorAll(sel) { const c=sel.slice(1); return this.children.filter(x=>(x.className||'').split(' ').includes(c)); }
  getBoundingClientRect() { return {top:0,bottom:100}; }
  scrollTo(o) { this.scrolledTo=o; }
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
async function boot({broken=false, noStorage=false, hash='', phone=false, lang='he', animations=false, reduceMotion=false, holdAnimation=false}={}) {
  const html=fs.readFileSync('dist/index.html','utf8'), nodes={};
  for (const [,id] of html.matchAll(/id="([^"]+)"/g)) { assert(!nodes[id], `duplicate ${id}`); nodes[id]=new El(); }
  const storage=new Map([['album-journey-2005-done','[1,999]']]);
  const calls=[], fetched=[]; let mock, stageMock=null, failAlbum=null;
  const ctx={console, requestAnimationFrame:f=>setImmediate(f), location:{origin:'https://example.test',hash},setTimeout:(f,ms)=>ms===20?setTimeout(f,ms):1,clearTimeout(){},setInterval:()=>1,clearInterval(){},
    document:{getElementById:id=>nodes[id],createElement:t=>new El(t),createTextNode:t=>({textContent:t}),head:new El(),querySelector:()=>new El(),addEventListener:(k,fn)=>{nodes['__'+k]=fn;}},
    localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>{if(noStorage)throw Error('blocked');storage.set(k,v)}},
    fetch:async url=>(fetched.push(url),{ok:!broken&&!(failAlbum&&url.includes(`/${failAlbum}.json`)),json:async()=>JSON.parse(fs.readFileSync('dist/'+url.slice(2).replace(/\?.*$/,''),'utf8'))}),
    YT:{Player:class {
      constructor(id,options){this.options=options;this.index=0;this.frame=new El();this.host=id;if(id==='youtube-player-2'){stageMock=this;return;}mock=this;calls.push(['create']);}
      getIframe(){return this.frame;} getPlaylistIndex(){return this.index;}
      stopVideo(){calls.push(['stop']);} cuePlaylist(ids,index){this.ids=ids;this.index=Array.isArray(ids)?index:ids.index;calls.push(['cue',...(Array.isArray(ids)?ids:[ids.list,ids.index])]);}
      cueVideoById(o){this.ids=[o.videoId];calls.push(['cueVideo',o.videoId,o.startSeconds]);}
      loadPlaylist(ids,index){this.ids=ids;this.index=Array.isArray(ids)?index:ids.index;calls.push(['load',...(Array.isArray(ids)?ids:[ids.list,ids.index])]);this.options.events.onStateChange({data:1});}
      loadVideoById(o){this.ids=[o.videoId];this.time=o.startSeconds;calls.push(['loadVideo',o.videoId,o.startSeconds]);this.options.events.onStateChange({data:1});}
      setLoop(){} setShuffle(){} destroy(){} getPlaylist(){return this.playlist||[];} getCurrentTime(){return this.time||0;} seekTo(s){this.time=s;calls.push(['seek',s]);}
      playVideoAt(index){this.index=index;calls.push(['playAt',index]);this.options.events.onStateChange({data:1});}
      playVideo(){calls.push(['play']);this.options.events.onStateChange({data:1});}
      pauseVideo(){calls.push(['pause']);this.options.events.onStateChange({data:2});}
    }}
  };const motion=[];
  if (animations) nodes['album-view'].animate=(frames,options)=>{
    let resolve,reject;const finished=holdAnimation?new Promise((yes,no)=>{resolve=yes;reject=no;}):Promise.resolve();
    const animation={frames,options,finished,finish:()=>resolve?.(),cancel(){this.cancelled=true;reject?.(Error('cancelled'));}};motion.push(animation);return animation;
  };
  ctx.history={replaceState:(_state,_title,hash)=>{ctx.location.hash=hash;}};ctx.innerWidth=phone?390:1200;ctx.matchMedia=query=>({matches:query.includes('prefers-reduced-motion')?reduceMotion:phone});ctx.document.documentElement={lang};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync('dist/app.js','utf8'),ctx);
  await new Promise(resolve=>setImmediate(resolve));
  return {nodes,calls,fetched,storage,ctx,motion,fail:n=>{failAlbum=n;},get player(){return mock;},get stage(){return stageMock;}};
}
(async()=>{
  // Swipes navigate only on phones in the album view, and respect RTL/LTR.
  for (const lang of ['he','en']) {
    const s=await boot({phone:true,lang,hash:'#/album/2',animations:true});await flush();await flush();
    const v=s.nodes['album-view'], target={closest:()=>null};
    const touch=(x,y=200,id=1)=>({clientX:x,clientY:y,identifier:id});
    const begin=(x=190,extra={})=>v.listeners.touchstart({touches:[touch(x)],target,...extra});
    const end=async(x,y=200)=>{v.listeners.touchend({touches:[],changedTouches:[touch(x,y)]});await flush();};
    const number=()=>s.ctx.location.hash;
    begin();let prevented=0;v.listeners.touchmove({touches:[touch(lang==='he'?290:90)],cancelable:true,preventDefault:()=>prevented++});assert.equal(v.style.transform,`translateX(${lang==='he'?60:-60}px)`,'content follows finger');assert.equal(prevented,1,'sideways drag stops page scroll');assert.ok(Number(v.style.opacity)<1,'content dims while dragging');
    await end(lang==='he'?290:90);assert.equal(number(),'#/album/3','swipe next');
    assert.equal(s.motion.at(-2).frames[1].opacity,0,'old album fades out');assert.equal(s.motion.at(-1).frames[0].transform,`translateX(${lang==='he'?-64:64}px)`,'new album enters from opposite side');assert.equal(v.style.transform,'','motion cleaned up');
    begin();await end(lang==='he'?90:290);assert.equal(number(),'#/album/2','swipe previous');
    begin();await end(220);assert.equal(number(),'#/album/2','short swipe ignored');
    begin(190,{timeStamp:1000});v.listeners.touchend({touches:[],changedTouches:[touch(lang==='he'?235:145)],timeStamp:1600});await flush();assert.equal(number(),'#/album/2','slow short drag ignored');
    begin(190,{timeStamp:1000});v.listeners.touchend({touches:[],changedTouches:[touch(lang==='he'?235:145)],timeStamp:1080});await flush();assert.equal(number(),'#/album/3','quick flick changes album');
    begin();await end(lang==='he'?90:290);assert.equal(number(),'#/album/2');
    begin();v.listeners.touchmove({touches:[touch(195,240)]});await end(290,240);assert.equal(number(),'#/album/2','vertical scroll remains scroll even when ending horizontally');
    begin();await end(290,270);assert.equal(number(),'#/album/2','diagonal swipe ignored');
    begin(10);await end(290);assert.equal(number(),'#/album/2','browser edge gesture ignored');
    begin(190,{target:{closest:()=>({})}});await end(290);assert.equal(number(),'#/album/2','controls excluded');
    begin();v.listeners.touchmove({touches:[touch(200),touch(250,200,2)]});await end(290);assert.equal(number(),'#/album/2','pinch ignored');
    begin();v.listeners.touchcancel();await end(290);assert.equal(number(),'#/album/2','cancelled gesture ignored');
    s.nodes['catalog-toggle'].click();begin();await end(290);assert.equal(number(),'#/album/2','open drawer blocks swipe');s.nodes['catalog-toggle'].click();
    begin();s.nodes['next-album'].click();await flush();await end(290);assert.equal(number(),'#/album/3','album change cancels an old swipe');
    s.player.options.events.onReady();s.nodes['quick-play'].click();const before=s.calls.length;
    begin();await end(lang==='he'?290:90);assert.equal(number(),'#/album/4');assert.equal(s.calls.length,before,'swipe keeps current music playing');
    s.nodes['show-welcome'].click();await flush();begin();await end(290);assert.equal(number(),'#/','home does not swipe');
  }
  { const s=await boot({phone:true,hash:'#/album/2',animations:true,reduceMotion:true});await flush();await flush();const v=s.nodes['album-view'];
    v.listeners.touchstart({touches:[{clientX:190,clientY:200,identifier:1}],target:{closest:()=>null}});
    v.listeners.touchmove({touches:[{clientX:290,clientY:200,identifier:1}]});assert.equal(v.style.transform,'','reduced motion does not drag');
    v.listeners.touchend({touches:[],changedTouches:[{clientX:290,clientY:200,identifier:1}]});await flush();assert.equal(s.ctx.location.hash,'#/album/3');assert.equal(s.motion.length,0,'reduced motion skips animations');
  }
  { const s=await boot({phone:true,hash:'#/album/2',animations:true,holdAnimation:true});await flush();await flush();const v=s.nodes['album-view'];
    const swipe=()=>{v.listeners.touchstart({touches:[{clientX:190,clientY:200,identifier:1}],target:{closest:()=>null}});v.listeners.touchend({touches:[],changedTouches:[{clientX:290,clientY:200,identifier:1}]});};
    swipe();await flush();assert.equal(s.motion.length,1);assert.equal(s.ctx.location.hash,'#/album/2','old album remains until exit finishes');
    swipe();await flush();assert.equal(s.motion.length,1,'repeated swipes blocked during transition');
    s.nodes['show-welcome'].click();await flush();s.motion[0].finish();await flush();assert.equal(s.ctx.location.hash,'#/','home navigation cancels animation');assert.equal(v.style.transform,'');
  }
  { const s=await boot({hash:'#/album/2'});await flush();await flush();const v=s.nodes['album-view'];
    v.listeners.touchstart({touches:[{clientX:190,clientY:200,identifier:1}],target:{closest:()=>null}});
    v.listeners.touchend({touches:[],changedTouches:[{clientX:290,clientY:200,identifier:1}]});await flush();
    assert.equal(s.ctx.location.hash,'#/album/2','desktop touch does not navigate'); }
  for (const [n,dx] of [[1,-100],[700,100]]) {
    const s=await boot({phone:true,hash:`#/album/${n}`});await flush();await flush();const v=s.nodes['album-view'];
    v.listeners.touchstart({touches:[{clientX:190,clientY:200,identifier:1}],target:{closest:()=>null}});
    v.listeners.touchend({touches:[],changedTouches:[{clientX:190+dx,clientY:200,identifier:1}]});await flush();
    assert.equal(s.ctx.location.hash,`#/album/${n}`,'swipe stops at catalog boundaries');
  }
  // Album X playing, album Y on screen: the frame shows Y, cued in a standby player; starting Y is instant
  // (the standby player takes over and X stops), also when ▶ is pressed inside Y's frame.
  { const s=await boot({hash:'#/album/2'});await flush();await flush();const main=s.player;main.options.events.onReady();
    const first=n=>JSON.parse(fs.readFileSync(`dist/albums/${n}.json`,'utf8')).tracks[0][1];
    s.nodes['quick-play'].click();assert.equal(s.calls.at(-1)[0],'playAt');const before=s.calls.length;
    s.nodes['next-album'].click();await flush();const stage=s.stage;assert(stage,'standby player created');
    stage.options.events.onReady();
    assert.deepEqual(s.calls.at(-1).slice(0,2),['cue',first(3)],'album on screen cued in the standby player');
    assert.equal(s.calls.slice(before).some(c=>['stop','pause','load'].includes(c[0])),false,'the playing album keeps playing');
    assert(main.frame.classSet.has('yt-standby')&&!stage.frame.classSet.has('yt-standby'),'the frame shows the album on screen');
    assert.match(s.nodes['player-status'].textContent,/ממשיך להתנגן/);
    s.nodes['track-list'].children[1].children[1].click();
    assert.deepEqual(s.calls.slice(-2).map(c=>c[0]),['stop','playAt'],'starting it stops the old album and plays at once');
    assert.equal(s.calls.at(-1)[1],1);assert.equal(s.nodes['play-pause'].textContent,'השהיה ❚❚');
    assert(!stage.frame.classSet.has('yt-standby')&&main.frame.classSet.has('yt-standby'));
    s.nodes['next-album'].click();await flush();
    assert.deepEqual(s.calls.at(-1).slice(0,2),['cue',first(4)],'the old player now waits with the next album');
    main.options.events.onStateChange({data:1});
    assert.equal(s.calls.at(-1)[0],'stop','▶ inside the waiting frame stops the other album');
    assert.equal(s.nodes['play-pause'].textContent,'השהיה ❚❚','and the album on screen is now playing');
    assert(!main.frame.classSet.has('yt-standby')); }
  // Switching to another album while one plays: pause the old one, cue the new list, play it once cued;
  // if YouTube still holds the old list a moment later, loadPlaylist is tried as well.
  { const s=await boot({hash:'#/album/101'});await flush();await flush();const y=s.player;y.options.events.onReady();
    const listOf=n=>JSON.parse(fs.readFileSync(`dist/albums/${n}.json`,'utf8')).youtubePlaylist;
    y.playlist=['old1','old2'];s.nodes['quick-play'].click();assert.equal(s.calls.at(-1)[0],'playAt');
    s.nodes['next-album'].click();await flush();
    s.nodes['track-list'].children[0].children[1].click();
    assert.deepEqual(s.calls.slice(-2).map(c=>c.slice(0,2)),[['pause'],['cue',listOf(102)]],'old album paused, new one cued');
    y.options.events.onStateChange({data:5});assert.equal(s.calls.at(-1)[0],'play','and played once cued');
    s.nodes['next-album'].click();await flush();
    y.cuePlaylist=function(o){s.calls.push(['cue',o.list,o.index]);};   // ignored by YouTube: the old list stays
    s.nodes['play-pause'].click();assert.deepEqual(s.calls.slice(-2).map(c=>c.slice(0,2)),[['pause'],['cue',listOf(103)]]);
    s.ctx.checkSwitch();assert.deepEqual(s.calls.at(-1).slice(0,2),['load',listOf(103)],'fallback: load the new list'); }
  const t=await boot(), {nodes:n,calls,storage}=t; const p=t.player;
  const rows=()=>n['album-list'].children.filter(c=>c.tag==='button').length;
  const nx=async()=>{p.options.events.onStateChange({data:5});n['next-album'].click();await flush();}, pv=async()=>{p.options.events.onStateChange({data:5});n['previous-album'].click();await flush();};
  assert.deepEqual(n['album-list'].children.filter(c=>c.tag==='div').map(c=>c.textContent),['שנות ה־50','שנות ה־60','שנות ה־70','שנות ה־80','שנות ה־90'],'decade markers in book order');
  // Decade line above the list and the decade rail beside it.
  assert.equal(n['list-now'].children[0].textContent,'שנות ה־50','decade of the album at the top of the list');
  const rail=n['decade-rail'].children;assert.equal(rail.length,6,'one rail part per decade of the book');
  assert.equal(rail[0].disabled,false);assert.equal(rail[2].disabled,false);assert.equal(rail[3].disabled,false);assert.equal(rail[4].disabled,false);assert.equal(rail[5].disabled,true,'decades not on the site yet cannot be clicked');
  assert(rail[0].classSet.has('current'),'current decade highlighted');
  rail[1].click();assert(n['album-list'].scrolledTo,'clicking a decade scrolls the list');
  assert.deepEqual(n['album-genres'].children.map(c=>c.textContent),['סטנדרטים וקברט'],'genre labels shown on the album page');assert.equal(n['album-genres'].hidden,false);
  assert.equal(rows(),700);assert.equal(n['edition-label'].textContent,'700 האלבומים הראשונים','album count label follows the site'); assert.equal(n['album-title'].textContent,'In the Wee Small Hours');
  assert.equal(n['track-list'].children.length,16);
  // "Next album" from the bottom of the page jumps up to the new album; no jump when already at the top.
  { const v=n['album-view']; let jumps=0; v.scrollIntoView=()=>jumps++;
    v.getBoundingClientRect=()=>({top:-900}); await nx(); assert.equal(jumps,1,'next album scrolls up to the new album');
    v.getBoundingClientRect=()=>({top:40}); await pv(); assert.equal(jumps,1,'no jump when the album top is visible');
    delete v.getBoundingClientRect; }
  // Top arrows and keyboard arrows move between albums like the bottom pager (← next, → previous in RTL).
  assert.equal(n['previous-album-top'].disabled,true,'no previous album on the first one');
  n['next-album-top'].click();await flush();assert.equal(n['album-title'].textContent,'Elvis Presley');
  n['previous-album-top'].click();await flush();assert.equal(n['album-title'].textContent,'In the Wee Small Hours');
  n['__keydown']({key:'ArrowLeft',target:{tagName:'BODY'}});await flush();assert.equal(n['album-title'].textContent,'Elvis Presley');
  n['__keydown']({key:'ArrowLeft',target:{tagName:'INPUT'}});await flush();assert.equal(n['album-title'].textContent,'Elvis Presley','typing in search does not switch albums');
  n['__keydown']({key:'ArrowRight',target:{tagName:'BODY'}});await flush();assert.equal(n['album-title'].textContent,'In the Wee Small Hours');
  const pilotData=pilotAll();
  for (const [k,a] of Object.entries(pilotData)) { assert.equal(a.durations.length,a.tracks.length,`durations for ${k}`); for (const d of a.durations) assert.match(d,/^\d{1,2}:\d{2}$/,`duration format in ${k}`); }
  assert.equal(n['track-list'].children[0].children[0].children[0].textContent,pilotData['1'].durations[0]);
  assert.equal(n['list-progress'].textContent,'האזנת ל־1 מתוך 700 אלבומים');assert.equal(n['progress-meter'].value,1);assert.equal(n['progress-meter'].max,700);
  assert.equal(n['toggle-progress'].textContent,'1 מתוך 700');
  for (let i=0;i<10;i++) {
    const data=pilotAll()[String(i+1)];
    assert.equal(n['track-list'].children.length,data.tracks.length);
    noteMatches(n,data);
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
  assert(!n['play-pause'].disabled);
  assert.equal(p.ids.length,5);
  n['play-pause'].click();assert.equal(calls.at(-1)[0],'play');
  p.index=1;p.options.events.onStateChange({data:1});
  assert.equal(n['track-note-title'].textContent,'Freddie Freeloader');
  const before=calls.length;n['mark-done'].click();assert.equal(calls.length,before,'mark heard must not interrupt');
  assert.deepEqual(JSON.parse(storage.get('album-journey-2005-done')),[1,999,21]);
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
  // Quick play under the title and the now-playing bar while the player is out of sight.
  { const data=added['22'];
    assert.equal(n['quick-play'].textContent,'❚❚ השהיה','quick play follows the player');
    assert.equal(n['mini-player'].hidden,false,'now-playing bar shows while playing');
    assert.equal(n['mini-song'].textContent,data.tracks[6][0]);assert.match(n['mini-album'].textContent,/Gunfighter Ballads/);
    n['mini-play'].click();assert.equal(n['mini-play'].textContent,'▶','bar pauses');assert.equal(n['quick-play'].textContent,'▶ המשך');
    n['quick-play'].click();assert.equal(n['mini-play'].textContent,'❚❚','quick play resumes');
    n['mini-next'].click();assert.equal(p.index,data.tracks[7][2],'bar skips to the next song');
  }
  n['mode-short'].click();assert.equal(n['track-list'].children.length,3);
  n['mode-full'].click();
  // Browsing to another album keeps the music playing; starting the shown album moves the player over to it.
  { const quiet=()=>calls.filter(c=>['cue','cueVideo','stop','load','loadVideo'].includes(c[0])).length;
    n['track-list'].children[6].children[1].click();const before=quiet();
    n['next-album'].click();await flush();assert.equal(n['album-title'].textContent,'Time Out');
    assert.equal(quiet(),before,'switching albums does not stop the music');assert.equal(p.ids.list,added['22'].youtubePlaylist);
    assert.equal(n['mini-player'].hidden,false,'bar shows the other album while its player is in view');assert.match(n['mini-album'].textContent,/Gunfighter/);
    assert.match(n['player-status'].textContent,/ממשיך להתנגן/);assert.equal(n['track-note'].hidden,true);
    assert.equal(n['play-pause'].textContent,'הפעלת הרצף ▶');assert.equal(n['quick-play'].textContent,'▶ להאזנה');
    assert.equal(n['next-track'].disabled,true);assert(!n['track-list'].children.some(li=>li.attributes['aria-current']==='true'));
    n['mini-next'].click();assert.equal(p.index,added['22'].tracks[7][2],'bar still controls the playing album');
    n['mini-open'].click();await flush();await flush();assert.equal(n['album-title'].textContent,'Gunfighter Ballads and Trail Songs','bar returns to the playing album');
    assert.equal(quiet(),before,'coming back keeps playing');assert.equal(n['play-pause'].textContent,'השהיה ❚❚');
    assert.equal(n['track-list'].children[7].attributes['aria-current'],'true');
    n['next-album'].click();await flush();n['play-pause'].click();
    assert.equal(calls.at(-1)[0],'cue','starting the shown album cues it');p.options.events.onStateChange({data:5});assert.equal(calls.at(-1)[0],'play','and plays it once cued');assert.equal(p.ids.length,7);
    assert.match(n['mini-album'].textContent,/Time Out/);assert.equal(n['play-pause'].textContent,'השהיה ❚❚');
    n['previous-album'].click();await flush();n['track-list'].children[2].children[1].click();
    assert.deepEqual(calls.at(-1),['cue',added['22'].youtubePlaylist,added['22'].tracks[2][2]],'a song of the shown album moves the player to it');p.options.events.onStateChange({data:5});
    await nx();
  }
  assert.equal(n['album-title'].textContent,'Time Out');assert.equal(p.ids.length,7);assert.equal(n['embedded-listening'].hidden,false);
  assert.equal(n['album-youtube-player'].src,'about:blank','switching to the mapped player unloads prior album');
  p.options.events.onError({data:150});assert.equal(n['player-error'].hidden,false);assert.match(n['player-error-text'].textContent,/150/);
  n['next-track'].click();assert.equal(n['player-error'].hidden,true);
  const catalog=JSON.parse(fs.readFileSync('dist/albums.json','utf8'));const lastAlbum=added['700'];
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
  }
  for (let number=51; number<=700; number++) {
    await nx();assert.equal(n['album-title'].textContent,catalog[number-1].title,`album ${number}`);
    const album=added[String(number)];
    if (number===53||number===544) { assert.equal(p.ids.length,4); continue; }
    if (number===145||number===232) { assert.equal(album.fullAlbumVideo,true);assert.equal(p.ids[0],album.tracks[0][1]);assert.equal(album.picks.length,Math.min(3,album.tracks.length),'one pick per piece, up to three');assert(catalog[number-1].genres?.length>0);continue; }
    assert.equal(n['embedded-listening'].hidden,false);
    assert.equal(n['track-list'].children.length,album.tracks.length,`album ${number} queue`);
    assert.equal(p.ids.list,album.youtubePlaylist,`album ${number} playlist`);
    assert.equal(album.durations.length,album.tracks.length);
    assert(album.genres===undefined&&catalog[number-1].genres?.length>0,`album ${number} has genres in the catalog`);
    const last=album.tracks.length-1;
    n['track-list'].children[last].children[1].click();assert.equal(p.index,album.tracks[last][2],`album ${number} last song plays at its playlist position`);
    n['mode-short'].click();assert.equal(n['track-list'].children.length,album.focus.length);
    n['mode-full'].click();
    assert.equal(n['album-note'].children.length,album.story.length+1,`album ${number} story sections + picks`);
  }
  assert(n['next-album'].disabled);
  assert.equal(n['album-youtube-player'].src,'about:blank');
  n['track-list'].children[lastAlbum.tracks.length-1].children[1].click();p.options.events.onStateChange({data:0});assert.match(n['player-status'].textContent,/הסתיים/);
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
  while(n['album-title'].textContent!=='Are You Experienced')await nx();
  n['album-search'].value='Miles';n['album-search'].listeners.input();assert.equal(rows(),4);
  assert.equal(calls.filter(x=>x[0]==='create').length,1,'only one player');
  // Genre filter: the menu lists the labels in use; picking one narrows the list without touching the journey order.
  n['album-search'].value='';n['album-search'].listeners.input();
  const menu=n['genre-select'];assert.equal(menu.hidden,false);assert.equal(menu.children[0].textContent,"כל הז'אנרים");
  const pick=g=>{menu.value=g;menu.listeners.change();};
  const catalogNow=JSON.parse(fs.readFileSync('dist/albums.json','utf8')).filter(a=>a.ready);
  assert(menu.children.some(o=>o.value==="ג'אז"&&o.textContent.startsWith("ג'אז ·")));
  pick("ג'אז");assert.equal(rows(),catalogNow.filter(a=>a.genres?.includes("ג'אז")).length);
  n['album-search'].value='Miles';n['album-search'].listeners.input();assert.equal(rows(),4,'search combines with genre');
  pick('');assert.equal(rows(),4);n['album-search'].value='';n['album-search'].listeners.input();
  assert.equal(rows(),catalogNow.length);
  // Spotify: every album but #626 (not on Spotify) has an embed; switching stops YouTube, is remembered, and switching back restores the queue.
  const all=pilotAll();
  for (const [k,a] of Object.entries(all)) if (!a.noSpotify) assert.match(a.spotifyAlbum||'',/^[A-Za-z0-9]{22}$/,`spotify id for ${k}`);
  assert.deepEqual(Object.keys(all).filter(k=>all[k].noSpotify),['626'],'only #626 lacks a Spotify album');
  n['service-spotify'].click();
  assert.equal(n['spotify-listening'].hidden,false);assert.equal(n['embedded-listening'].hidden,true);assert.equal(n['mode-switch'].hidden,true);
  assert.equal(n['spotify-player'].src,`https://open.spotify.com/embed/album/${all['100'].spotifyAlbum}?utm_source=generator`);
  assert.equal(calls.at(-1)[0],'stop');assert.equal(storage.get('album-journey-2005-service'),'"spotify"');
  await pv();assert.equal(n['spotify-player'].src,`https://open.spotify.com/embed/album/${all['99'].spotifyAlbum}?utm_source=generator`);
  n['service-youtube'].click();
  assert.equal(n['spotify-listening'].hidden,true);assert.equal(n['spotify-player'].src,'about:blank');assert.equal(n['embedded-listening'].hidden,false);
  assert.equal(n['track-list'].children.length,all['99'].tracks.length);
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
  // Home page: without an album in the address the site opens on the grid; the hero offers the next unheard album.
  { const h=await boot(), m=h.nodes; await flush();
    assert.equal(m['home'].hidden,false,'home shown first');assert.equal(m['album-page'].hidden,true);
    const hero=m['home-hero'].children;assert.equal(hero[1].children[1].textContent,'Elvis Presley','next unheard album (1 is heard)');
    assert.match(hero[1].children[0].textContent,/להמשיך במסע · אלבום 2 מתוך 700/);
    const sections=m['home-grid'].children;assert.deepEqual(sections.filter((c,i)=>i%2===0).map(c=>c.children[0].textContent),['שנות ה־50','שנות ה־60','שנות ה־70','שנות ה־80','שנות ה־90']);
    const tiles=sections.filter((c,i)=>i%2===1).flatMap(g=>g.children);assert.equal(tiles.length,700,'one tile per album on the site');
    assert(tiles[0].children.some(c=>c.className==='tile-check'),'heard album has a check');assert(!tiles[2].children.some(c=>c.className==='tile-check'));
    assert(tiles[1].className.includes('next'),'next album outlined');
    m['home-unheard'].click();assert.equal(m['home-grid'].children.filter((c,i)=>i%2===1).flatMap(g=>g.children).length,699,'"not heard yet" hides heard albums');
    m['home-all'].click();m['home-search'].value='Miles';m['home-search'].listeners.input();assert.equal(m['home-grid'].children.filter((c,i)=>i%2===1).flatMap(g=>g.children).length,4);
    m['home-search'].value='';m['home-search'].listeners.input();
    // Clicking a tile opens that album and puts it in the address; "מה זה?" returns home with the welcome box.
    const tile5=m['home-grid'].children[1].children[4];tile5.click();await flush();await flush();
    assert.equal(h.ctx.location.hash,'#/album/5');assert.equal(m['album-title'].textContent,'This Is Fats Domino!');
    assert.equal(m['album-page'].hidden,false);assert.equal(m['home'].hidden,true);assert.equal(m['nav-album'].href,'#/album/5');
    assert.equal(h.storage.get('album-journey-2005-last-album'),'5','current album remembered');
    m['next-album'].click();await flush();assert.equal(m['nav-album'].href,'#/album/6','album link follows next/previous');
    m['show-welcome'].click();await flush();assert.equal(m['home'].hidden,false);assert.equal(m['welcome'].hidden,false);assert.equal(h.ctx.location.hash,'#/');
  }
  // A shared link to an album opens that album directly.
  { const d=await boot({hash:'#/album/41'}); await flush();await flush();
    assert.equal(d.nodes['album-page'].hidden,false);assert.equal(d.nodes['home'].hidden,true);assert.equal(d.nodes['album-title'].textContent,'Getz / Gilberto'); }
  console.log('PASS: book entries 1–700 (including the 51–100 through 651–700 batches; #626 has no Spotify album with stories, genres and playlist positions), all YouTube queues or continuous album videos, track buttons, focused selection, transport, replay, errors, search, progress, the phone album drawer, the home page grid and album links, the welcome box, track lengths and the Spotify switch. Mock API only; live playback is not verified.');
})().catch(err=>{console.error(err);process.exitCode=1});
