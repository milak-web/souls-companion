const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
 const p=await b.newPage({viewport:{width:1600,height:1050}}),errors=[],remote=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))remote.push(r.url())});
 await p.route('http://127.0.0.1:8765/assets/**',async route=>{const u=new URL(route.request().url()),f=path.resolve('DarkSouls-Guide','.'+decodeURIComponent(u.pathname));await route.fulfill({body:fs.readFileSync(f),contentType:{'.webp':'image/webp','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.ttf':'font/ttf'}[path.extname(f)]||'application/octet-stream'})});
 await p.goto('http://127.0.0.1:8765/?v=1.8.0#view=blacksmith');await p.waitForFunction(()=>app?.ready);
 const result=await p.evaluate(()=>{
  const a=app,checks=[],issues=[];let paths=0,rows=0;
  const same=(x,y,label)=>{if(JSON.stringify(x)!==JSON.stringify(y))throw Error(label+': '+JSON.stringify(x))};
  const long=a.smithEquipment('longsword'),at=(path,level)=>a.smithRow(long,path,level);
  same([at('Poison',5).attack.physical,at('Poison',5).auxiliary.poison],[118,126],'Poison +5');checks.push('Published Poison Longsword +5 attack and buildup');
  same([at('Poison',10).attack.physical,at('Poison',10).auxiliary.poison],[158,140],'Poison +10');checks.push('Published Poison Longsword +10 attack and buildup');
  same([at('Poison',10).scaling_percent.str,at('Poison',10).scaling_percent.dex,at('Poison',10).aux_scaling_percent.poison],[18,9,21],'Poison scaling');checks.push('Numeric physical and poison scaling at selected level');
  same(at('Normal',2).attack.physical,135,'Normal +2');same(at('Normal',0).scaling_percent.str,45,'Base STR scaling');checks.push('Individual rows replace endpoint interpolation');
  const quote=(fromPath,fromLevel,toPath,toLevel)=>a.smithQuote(long,{path:fromPath,level:fromLevel},{path:toPath,level:toLevel});
  let q=quote('Normal',0,'Poison',10);same(q.totalSouls,14140,'Full fee');same(q.materials,{'Titanite Shard':6,'Large Titanite Shard':6,'Titanite Chunk':6,'Titanite Slab':1,'Poison Stone':1},'Full materials');checks.push('Full standard upgrade plus one infusion');
  q=quote('Normal',5,'Poison',10);same(q.totalSouls,10130,'Remaining fee');same(q.materials,{'Large Titanite Shard':3,'Titanite Chunk':6,'Titanite Slab':1,'Poison Stone':1},'Remaining materials');checks.push('Already upgraded equipment charges only remaining steps');
  q=quote('Poison',10,'Bleed',10);same(q.totalSouls,2000,'Switch fee');same(q.materials,{'Bleed Stone':1},'No palestone on switch');checks.push('Switching infusion retains level and uses one new stone');
  q=quote('Poison',10,'Normal',10);same(q.totalSouls,1000,'Remove fee');same(q.materials,{'Palestone':1},'Remove stone');checks.push('Palestone removal retains reinforcement');
  same(quote('Poison',10,'Poison',10).totalSouls,0,'No-op fee');same(quote('Normal',10,'Normal',5).valid,false,'No downgrade');checks.push('No-op and downgrade handling');
  for(const [id,material,count,max] of [['black-knight-greataxe','Twinkling Titanite',15,5],['moonlight-greatsword','Petrified Dragon Bone',15,5],['pyromancy-flame','Fire Seed',10,10]]){const e=a.smithEquipment(id),q=a.smithQuote(e,{path:'Normal',level:0},{path:'Normal',level:max});same(q.materials[material],count,id+' material schedule');if(!q.complete)throw Error(id+' incomplete');checks.push(id+' reinforcement material schedule');}
  if(a.smithEquipment('mace').paths.Bleed)throw Error('Mace bleed');if(a.smithEquipment('short-bow').paths.Poison)throw Error('Bow poison');if(a.smithEquipment('buckler').paths.Raw)throw Error('Shield raw');checks.push('Unsupported infusion restrictions');
  const varangian=a.smithEquipment('varangian-shield');same(a.smithRow(varangian,'Normal',0).attack.physical,52,'Varangian base');if(!varangian.paths.Poison||!varangian.paths.Magic)throw Error('Varangian tab identity');checks.push('Infusion tab labels keep shield paths distinct');
  const partial={paths:{Normal:{rows:[]}},steps:{1:{material:'Titanite Shard',quantity:1,souls:null}}};q=a.smithQuote(partial,{path:'Normal',level:0},{path:'Normal',level:1});same(q.totalSouls,null,'Unknown fee');same(q.materials['Titanite Shard'],1,'Known material kept');checks.push('Unknown costs never become a zero bill');
  for(const e of a.data.blacksmith.equipment){
   const ids=new Set();for(const [path,pr] of Object.entries(e.paths)){
    paths++;for(const r of pr.rows){rows++;const id=path+':'+r.level;if(ids.has(id))issues.push(e.id+' duplicate '+id);ids.add(id);if(Object.values(r.attack).some(v=>v!==null&&(!Number.isFinite(v)||v<0)))issues.push(e.id+' invalid attack');}
    a.setBlacksmithWeapon(e.id);a.setSmith('path',path);a.setBlacksmithLevel(e.max_level);if(!document.querySelector('[data-smith-benefit]'))issues.push(e.id+' missing preview');
    for(const link of document.querySelectorAll('a[data-view]'))if(!a.localReferenceTarget(link.textContent)?.record && ![...a.data.weapons,...a.data.items,...a.data.npcs,...a.data.articles].some(x=>x.id===link.dataset.id))issues.push(e.id+' dead link '+link.dataset.id);
   }
  }
  a.setBlacksmithWeapon('longsword');a.setSmith('path','Poison');a.setBlacksmithLevel(10);return {checks,paths,rows,issues};
 });
 assert.deepEqual(result.issues,[]);await p.reload();await p.waitForFunction(()=>app.ready);assert.equal(await p.locator('[data-smith-field=path]').inputValue(),'Poison');assert.equal(await p.locator('[data-smith-field=level]').inputValue(),'10');result.checks.push('Selection survives refresh');
 await p.locator('[data-smith-picker]').click();await p.locator('[data-smith-field=query]').fill('Moonlight');assert.equal(await p.locator('.smith-choice').count(),1);assert.equal(await p.locator('.smith-choice img').count(),1);await p.locator('.smith-choice').click();assert.equal(await p.locator('.smith-equipment h3').innerText(),'Moonlight Greatsword');result.checks.push('Searchable equipment picker includes icons');
 await p.evaluate(()=>{app.setBlacksmithWeapon('longsword');app.setSmith('path','Poison');app.setBlacksmithLevel(10)});await p.screenshot({path:'DarkSouls-Guide/audit/blacksmith-desktop.png'});
 await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await p.screenshot({path:'DarkSouls-Guide/audit/blacksmith-mobile.png'});result.checks.push('Mobile controls fit viewport');
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);fs.writeFileSync('DarkSouls-Guide/audit/blacksmith-runtime-check.json',JSON.stringify({...result,errors,externalRequests:remote},null,2));console.log(JSON.stringify({checks:result.checks.length,paths:result.paths,rows:result.rows,issues:result.issues,errors,externalRequests:remote},null,2));
}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
