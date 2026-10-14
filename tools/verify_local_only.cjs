const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),assert=require('assert/strict');let browser;
(async()=>{
 browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),remote=[],errors=[],failures=[],security=[];
 page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))remote.push(r.url());});
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failures.push({url:r.url(),status:r.status()});});
 page.on('console',m=>{if(m.type()==='error' && /content security|refused to (?:load|connect|execute|apply)/i.test(m.text()))security.push(m.text());});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto('http://127.0.0.1:8765/?v=1.7.0#view=item-detail&id=lifegem');await page.waitForFunction(()=>window.app?.ready===true);await page.evaluate(()=>document.fonts.ready);
 assert.equal(await page.locator('#view-container h1').innerText(),'Lifegem');
 // Serve the same bundled asset bytes directly during the rapid full-catalog sweep,
 // avoiding thousands of concurrent HTTP requests to the small development server.
 await page.route('http://127.0.0.1:8765/assets/**',async route=>{
  const path=require('path'),url=new URL(route.request().url());
  const root=path.resolve('DarkSouls-Guide/assets'),file=path.resolve('DarkSouls-Guide',decodeURIComponent(url.pathname).slice(1));
  assert(file.startsWith(root+path.sep));
  const mime={'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.ttf':'font/ttf','.woff2':'font/woff2'}[path.extname(file)];
  await route.fulfill({status:200,body:fs.readFileSync(file),contentType:mime||'application/octet-stream'});
 });
 const result=await page.evaluate(()=>{
  const app=window.app,issues=[];let rendered=0,links=0;
  const catalogs={'enemy-detail':[...app.data.enemies,...app.data.bosses],'area-detail':app.data.areas,'magic-detail':app.data.magic,'item-detail':app.data.items,'weapon-detail':app.data.weapons,'armor-detail':app.data.armor,'npc-detail':app.data.npcs,'article-detail':app.data.articles};
  for(const [view,records] of Object.entries(catalogs))for(const record of records){
   app.renderView(view,{id:record.id});rendered++;
   if(document.querySelector('#view-container h1')?.textContent!==record.name)issues.push({view,id:record.id,problem:'wrong heading'});
   for(const a of document.querySelectorAll('#view-container a[href]')){
    links++;
    if(!a.getAttribute('href').startsWith('#'))issues.push({view,id:record.id,problem:'outbound guide link',href:a.getAttribute('href')});
    if(a.dataset.view && !catalogs[a.dataset.view]?.some(x=>x.id===a.dataset.id))issues.push({view,id:record.id,problem:'missing local target'});
   }
  }
  return {rendered,links,issues,articles:app.data.articles.length};
 });
 assert.deepEqual(result.issues,[]);
 await page.evaluate(()=>window.app.renderView('item-detail',{id:'lifegem'}));
 await page.evaluate(()=>app.handleSearch(app.data.articles[0].name));
 const reference=page.locator('a[data-view="article-detail"]').first();assert(await reference.count());const name=await reference.innerText();await reference.click();assert.equal(await page.evaluate(()=>window.app.currentView),'article-detail');assert.equal(new URL(page.url()).origin,'http://127.0.0.1:8765');await page.reload();await page.waitForFunction(()=>window.app?.ready===true);assert.equal(await page.evaluate(()=>window.app.currentView),'article-detail');
 await page.evaluate(()=>window.app.renderView('item-detail',{id:'lifegem'}));await page.waitForFunction(()=>Array.from(document.querySelectorAll('#view-container img')).every(i=>i.complete));await page.screenshot({path:'DarkSouls-Guide/audit/local-lifegem-preview.png',animations:'disabled'});
 // Force a failed image to prove that the error path does not start a wiki lookup.
 await page.evaluate(()=>{const img=document.querySelector('#view-container img');window.app.handleImageError(img,'missing','item');return window.app.getProxiedUrl('https://example.com/image.png');});
 await page.evaluate(()=>window.app.renderView('area-detail',{id:'forest_of_fallen_giants'}));assert.equal(await page.locator('a[href^="http"]').count(),0);
 assert.deepEqual(remote,[]);assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);assert.deepEqual(security,[]);
 fs.writeFileSync('DarkSouls-Guide/audit/local-only-check.json',JSON.stringify({...result,clickedReference:name,externalRequests:remote,errors,failures,security},null,2));console.log(JSON.stringify({...result,clickedReference:name,externalRequests:remote,errors,failures,security},null,2));await browser.close();
})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exitCode=1});
