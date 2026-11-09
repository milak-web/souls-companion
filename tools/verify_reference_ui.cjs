const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('assert/strict'),fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8765/#game=ds2&view=enemies');
  await page.waitForFunction(()=>window.app?.ready);
  const result=await page.evaluate(()=>{
   const app=window.app;
   const ring=app.data.items.find(r=>r.name==='Ring of Blades +2');
   const variant=app.localReferenceTarget('Ring of Blades +2',app.data.items.find(r=>r.name==='Ring of Blades').source_url);
   const merchant=app.localReferenceTarget('Merchant Hag Melentia','https://darksouls2.wiki.fextralife.com/Merchants');
   return {ring:ring.id,variant:variant?.record.id,merchant:merchant?.record.id,merchantView:merchant?.view};
  });
  assert.equal(result.variant,result.ring);assert.equal(result.merchant,'merchant-hag-melentia');assert.equal(result.merchantView,'npc-detail');
  async function show(view,id){await page.evaluate(([view,id])=>app.renderView(view,{id}),[view,id]);return page.locator('#view-container').innerText();}
  let text=await show('enemy-detail','hollow_infantry');assert(!/Not verified|Unverified/i.test(text));assert(/Backstab:\s*Yes/i.test(text));assert(/Parry:\s*Yes/i.test(text));
  await page.locator('.enemy-stat-profiles summary').click();assert((await page.locator('.enemy-stat-profiles tbody tr').count())>=8);
  await page.screenshot({path:path.join(__dirname,'../audit/reviewed-hollow-infantry-mobile.png'),fullPage:true});
  text=await show('enemy-detail','exiled-brave');assert(text.includes('2,550'));assert(text.includes('Frigid Outskirts'));assert(!/HP \(NG\):\s*760/.test(text));
  text=await show('enemy-detail','archdrake_pilgrim');assert.equal(await page.locator('#view-container h1').innerText(),'Lindelt Cleric');assert(/Parry:\s*No/i.test(text));
  text=await show('enemy-detail','faraam-knight-phantom');assert(/HP \(NG\+\):\s*3,230/.test(text));
  text=await show('enemy-detail','hollow-pyromancer');assert(text.includes('1,830'));assert(text.includes('Great Chaos Fireball'));
  text=await show('enemy-detail','prowling-magus-and-congregation');assert(text.includes('1,100 Magus'));assert(text.includes('900'));
  text=await show('npc-detail','blacksmith-lenigrast');assert(text.includes('Inventory'));await page.locator('.wiki-reference-facts summary').filter({hasText:/Inventory/}).first().click();text=await page.locator('#view-container').innerText();assert(text.includes('1,300'));assert(!text.includes('icon hp'));
  text=await show('npc-detail','emerald-herald');assert(text.includes('Leveling / Estus Flask upgrades'));assert(!text.includes('is a summon'));
  text=await show('npc-detail','alva-the-wayfarer');assert(text.includes('Saint Serreta'));assert(text.includes('Alva Set'));
  for(const width of [320,390,768,1440]) {
   await page.setViewportSize({width,height:900});
   for(const [view,id] of [['enemy-detail','hollow_infantry'],['enemy-detail','alonne_knight'],['enemy-detail','dragonriders'],['enemy-detail','afflicted-graverobber-ancient-soldier-varg-and-cerah-the-old-explorer'],['npc-detail','blacksmith-lenigrast'],['weapon-detail','moonlight-greatsword'],['armor-detail','havel-s-armor']]) {
    await show(view,id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),width+' '+id);
    const clipped=await page.evaluate(()=>[...document.querySelectorAll('.detail-header,.detail-image,.detail-title-box h1,.location-tag,.quick-stats .stat,.res-item,.wiki-reference-facts,.detail-grid>section')].filter(el=>el.getClientRects().length).map(el=>({tag:el.className||el.tagName,left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right})).filter(rect=>rect.left < -1 || rect.right > innerWidth+1));
    assert.deepEqual(clipped,[],width+' '+id+' clipped content');
   }
  }
  text=await show('quests');assert(text.includes('All four proof items'));assert(text.includes('Elana does not count'));
  const imageResult=await page.locator('.quest-header img').evaluateAll(images=>images.every(i=>!i.src.startsWith('data:')));assert(imageResult);
  await page.setViewportSize({width:1440,height:1000});await show('npc-detail','blacksmith-lenigrast');
  await page.locator('.wiki-reference-facts summary').filter({hasText:/Inventory/}).first().click();
  await page.screenshot({path:path.join(__dirname,'../audit/reviewed-merchant-stock.png'),fullPage:true});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({checks:'Source variants, common enemies, group health, exact internal targets, NPC services, merchant stock, quests, 28 responsive detail layouts',errors}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
