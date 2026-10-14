const { chromium } = require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
(async () => {
 const browser = await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const page = await browser.newPage({viewport:{width:1440,height:1000}});
 const errors = [];const failures=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.url().startsWith('http://127.0.0.1:8765/') && r.status()>=400) failures.push({url:r.url(),status:r.status()});});
 await page.route('**/*',route=>route.request().url().startsWith('http://127.0.0.1:8765/') || route.request().url().startsWith('data:') ? route.continue() : route.abort());
 await page.route('http://127.0.0.1:8765/assets/**',async route=>{const path=require('path'),u=new URL(route.request().url()),f=path.resolve('DarkSouls-Guide','.'+decodeURIComponent(u.pathname));await route.fulfill({body:fs.readFileSync(f),contentType:{'.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.ttf':'font/ttf'}[path.extname(f)]||'application/octet-stream'});});
 await page.goto('http://127.0.0.1:8765/');
 await page.waitForFunction(()=>window.app?.ready === true);
 const result = await page.evaluate(()=>{
   const app=window.app,issues=[];let rendered=0,links=0;
   for (const [view,catalog] of [['enemy-detail','enemies'],['enemy-detail','bosses'],['area-detail','areas'],['weapon-detail','weapons'],['armor-detail','armor'],['magic-detail','magic'],['item-detail','items'],['npc-detail','npcs'],['article-detail','articles']]) {
    for(const record of app.data[catalog]) {
     try { app.renderView(view,{id:record.id});const h=document.querySelector('#view-container h1');if(!h || h.textContent!==record.name)issues.push({view,id:record.id,problem:'wrong or missing heading',actual:h?.textContent});
      for(const a of document.querySelectorAll('a[data-view]')) { const target={'enemy-detail':[...app.data.bosses,...app.data.enemies],'area-detail':app.data.areas,'weapon-detail':app.data.weapons,'armor-detail':app.data.armor,'magic-detail':app.data.magic,'item-detail':app.data.items,'npc-detail':app.data.npcs,'article-detail':app.data.articles}[a.dataset.view];links++;if(!target?.some(x=>x.id===a.dataset.id))issues.push({view,id:record.id,problem:'dead link',link:a.dataset.id}); }
      rendered++;
     } catch(e) {issues.push({view,id:record.id,problem:e.message});}
    }
   }
   for(const view of ['home','enemies','bosses','areas','weapons','items','magic','armor','covenants','npcs','quests','mechanics','favorites','blacksmith','builder'])try{app.renderView(view);}catch(e){issues.push({view,problem:e.message});}
   const soldier=app.data.enemies.find(e=>e.id==='hollow_soldier');const short=app.findDropTarget('Bastard Sword');
   if(!short || !app.dropSources(short.record,short.view).some(e=>e.id===soldier.id))issues.push({problem:'Bastard Sword reverse drop link missing'});
   if(app.findDropTarget('Titanite Ores (Assorted)'))issues.push({problem:'Generic loot resolved to a specific item'});
   if(app.findDropTarget('Smelter Demon (Iron Passage)'))issues.push({problem:'Wrong catalog link'});
   app.renderView('enemy-detail',{id:'the-pursuer'});app.handleSearch('Ring of Blades');if(!document.querySelector('a[data-id="ring-of-blades"]'))issues.push({problem:'item search missing'});app.renderView(app.currentView);if(document.querySelector('#view-container h1')?.textContent!=='The Pursuer')issues.push({problem:'search clear lost detail'});
   app.renderView('enemy-detail',{id: 'no-such-entry'});if(!document.querySelector('.empty-msg'))issues.push({problem:'invalid route blanks page'});
   return {rendered,links,issues};
 });
 console.log(JSON.stringify({rendered:result.rendered,links:result.links,issueCount:result.issues.length,issues:result.issues.slice(0,15),errors,failures:failures.slice(0,15)},null,2));
 fs.writeFileSync('DarkSouls-Guide/audit/runtime-check.json',JSON.stringify({...result,errors,failures},null,2));
 await page.evaluate(()=>window.app.renderView('enemy-detail',{id:'fume-knight'}));
 await page.screenshot({path:'DarkSouls-Guide/audit/boss-preview.png',fullPage:true});
 await browser.close();
 if(result.issues.length||errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
