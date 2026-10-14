const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
 const p=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],remote=[],issues=[];let links=0;
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))remote.push(r.url());});
 await p.route('http://127.0.0.1:8765/images/**',async route=>{const url=new URL(route.request().url()),file=path.resolve('DarkSouls-Guide','.'+decodeURIComponent(url.pathname));try{await route.fulfill({body:fs.readFileSync(file),contentType:{'.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png'}[path.extname(file)]||'image/png'});}catch(e){issues.push('Missing asset '+file);await route.abort();}});
 await p.goto('http://127.0.0.1:8765/ds1.html');await p.waitForFunction(()=>window.ds1);
 const entries=await p.evaluate(()=>ds1.catalog.map(r=>({id:r.id,category:r.category})));
 for(let i=0;i<entries.length;i++){
  const r=entries[i];await p.evaluate(r=>location.hash='game=ds1&view='+r.category+'&id='+r.id,r);await p.waitForFunction(id=>document.title.startsWith(ds1.catalog.find(r=>r.id===id).name+' ·'),r.id);
  const current=await p.evaluate(async()=>{
   const errors=[],ids=new Set(ds1.catalog.map(r=>r.id));const images=[...document.querySelectorAll('#view-container img')];await Promise.all(images.map(im=>im.decode().catch(()=>errors.push('Image '+im.src))));
   let count=0;for(const a of document.querySelectorAll('#view-container a[href^="#"]')){count++;const hash=new URLSearchParams(a.hash.slice(1)),id=hash.get('id');if(id&&!ids.has(id))errors.push('Dead '+id);}
   if(document.querySelector('h1')?.textContent==='Unable to display this view')errors.push('Render failure');return {count,errors};
  });links+=current.count;issues.push(...current.errors.map(e=>r.id+': '+e));if(i%100===0)console.log('Checked '+i+'/'+entries.length);
 }
 await p.goto('http://127.0.0.1:8765/ds1.html#view=bonfires');await p.waitForSelector('.gallery');assert.equal(await p.locator('.quest-step').count(),0);
 await p.screenshot({path:'DarkSouls-Guide/audit/ds1/bonfires-desktop.png'});
 await p.goto('http://127.0.0.1:8765/games.html');await p.waitForSelector('.game-card');assert.equal(await p.locator('.game-card[href]').count(),2);await p.screenshot({path:'DarkSouls-Guide/audit/ds1/game-hub.png'});
 await p.goto('http://127.0.0.1:8765/index.html#view=weapons');await p.waitForFunction(()=>window.app?.ready);assert.equal(await p.locator('.game-switch[href="#view=games"]').count(),1);await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'DS2 mobile overflow');
 const result={entries:entries.length,internalLinks:links,issues,errors,externalRequests:remote,ds2Regression:'DS2 ready; game links present; mobile layout fits'};fs.writeFileSync('DarkSouls-Guide/audit/ds1/archive-runtime.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));assert.deepEqual(issues,[]);assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});
