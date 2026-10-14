const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('assert/strict'),fs=require('fs');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
const p=await b.newPage({viewport:{width:1440,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto('http://127.0.0.1:8765/?v=1.7.0#view=magic');await p.waitForFunction(()=>window.app?.ready);
const id=await p.evaluate(()=>app.data.magic.find(m=>m.name==='Soul Arrow').id);
await p.evaluate(id=>localStorage.setItem('ds2_favorites',JSON.stringify([{id,type:'item'}])),id);await p.reload();await p.waitForFunction(()=>app.ready);
assert.equal(await p.locator('li[data-tab=magic]').count(),1);
const results=await p.evaluate(id=>{const a=app,checks=[];if(a.data.magic.length!==106||a.data.items.length!==335)throw Error('Catalog count');if(a.data.items.some(i=>['Sorcery','Miracle','Pyromancy','Hex'].includes(i.type)))throw Error('Spell in items');checks.push('Separated catalogs');
for(const [type,count] of [['Sorcery',31],['Miracle',28],['Pyromancy',24],['Hex',23]]){a.setCatalogFilter('magic','type',type);if(document.querySelectorAll('#view-container .item-card').length!==count)throw Error('School filter '+type);checks.push(type+' filter');}
a.resetCatalogFilters('magic');for(const metric of ['int_required','faith_required','slots','uses_min']){a.setCatalogFilter('magic','sort',metric);const rs=a.catalogResults('magic',a.data.magic).map(r=>a.catalogMetric('magic',r,metric)).filter(v=>v!==null);if(!rs.length||rs.some((v,i)=>i&&v>rs[i-1]))throw Error('Incorrect sort '+metric);checks.push(metric+' sort control');}
a.resetCatalogFilters('magic');if(!a.favorites.some(f=>f.id===id&&f.type==='magic'))throw Error('Favorite migration');a.renderView('favorites');if(!document.querySelector('.item-card'))throw Error('Favorite missing');checks.push('Favorite migration');
a.renderView('item-detail',{id});if(a.currentView!=='magic-detail'||document.querySelector('#view-container h1').textContent!=='Soul Arrow')throw Error('Legacy route');checks.push('Legacy spell route');
a.handleSearch('Soul Arrow');if(!document.querySelector('a[data-view=magic-detail]'))throw Error('Search');checks.push('Global search');
if(a.findDropTarget('Warmth')?.view!=='magic-detail'||a.localReferenceTarget('Soul Arrow')?.view!=='magic-detail')throw Error('Cross links');checks.push('Drop and reference links');
a.renderView('npc-detail',{id:a.data.npcs.find(n=>n.name==='Jester Thomas').id});if(!document.querySelector('.detail-image img').getAttribute('src').includes('portrait-'))throw Error('Jester image');checks.push('Jester portrait');return checks;},id);
await p.evaluate(()=>{app.resetCatalogFilters('magic');app.renderView('magic')});await p.screenshot({path:'DarkSouls-Guide/audit/magic-desktop.png'});
await p.setViewportSize({width:390,height:844});await p.screenshot({path:'DarkSouls-Guide/audit/magic-mobile.png'});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
assert.deepEqual(errors,[]);fs.writeFileSync('DarkSouls-Guide/audit/magic-check.json',JSON.stringify({checks:results,errors},null,2));console.log(JSON.stringify({checks:results.length,errors}));
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
