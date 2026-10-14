const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
 const p=await b.newPage({viewport:{width:1440,height:1000}}),errors=[],remote=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))remote.push(r.url());});
 await p.route('http://127.0.0.1:8765/images/**',async route=>{const u=new URL(route.request().url()),f=path.resolve('DarkSouls-Guide','.'+decodeURIComponent(u.pathname));await route.fulfill({body:fs.readFileSync(f),contentType:'image/webp'});});
 await p.goto('http://127.0.0.1:8765/ds1.html#view=home');await p.waitForFunction(()=>window.ds1);
 const result=await p.evaluate(()=>{
  const {catalog,params,weapon,armor,character,paths,quote}=window.ds1,issues=[],checks=[];
  const eq=(a,b,label)=>{if(a!==b)throw Error(label+': '+a+' != '+b);checks.push(label);},by=id=>catalog.find(x=>x.id===id);
  const stats={strength:40,dexterity:40,intelligence:40,faith:40};let pathsCount=0,rows=0;
  for(const r of catalog){
   for(const ref of Object.values(r.relations).flat())if(!by(ref.id))issues.push('Dead relation '+r.id+' → '+ref.id);
   if(r.category==='weapons'&&r.param_id)for(const path of paths(params,r.param_id)){
    pathsCount++;for(let level=0;level<=path.max;level++){const w=weapon(params,r.param_id,path.id,level,stats);rows++;if(!Number.isFinite(w.total)||w.total<0)issues.push('Invalid AR '+r.id+' '+path.id+' +'+level);}
   }
   if(r.category==='armor'&&r.param_id){const a=armor(params,r.param_id,99);if(!Number.isFinite(a.physical_def))issues.push('Invalid armor '+r.id);}
  }
  const w=(id,path,level)=>weapon(params,by(id).param_id,path,level,stats);
  eq(Math.floor(w('claymore',0,0).base.physical),103,'Claymore base 103');eq(Math.floor(w('claymore',0,15).base.physical),257,'Claymore +15 base 257');
  eq(Math.floor(w('claymore',200,5).base.physical),257,'Lightning Claymore +5 physical');eq(Math.floor(w('claymore',200,5).base.lightning),257,'Lightning Claymore +5 lightning');
  eq(w('claymore',200,5).scaling.STR,'—','Lightning removes STR scaling');eq(w('moonlight-greatsword',0,5).scaling.INT,'S','Moonlight Greatsword INT scaling');
  eq(paths(params,by('black-knight-sword').param_id).length,1,'Black Knight Sword no elemental ascensions');eq(w('black-knight-sword',0,5).max,5,'Special weapon +5 cap');
  const base={classId:0,stats:{vitality:30,attunement:16,endurance:40,strength:40,dexterity:40,resistance:11,intelligence:9,faith:9},armor:[],weapons:[],rings:[],consumables:[],humanity:0};
  const c=character(params,base);eq(c.hp,1100,'VIT 30 HP');eq(c.stamina,160,'END 40 stamina');eq(c.load,80,'END 40 equip load');eq(c.slots,4,'ATN 16 four slots');
  const ring=id=>by(id).param_id,rounded=x=>Math.round(x*100)/100;
  const favor=character(params,{...base,rings:[ring('ring-of-favor-and-protection')]});eq(favor.hp,1320,'Favor HP +20%');eq(favor.stamina,192,'Favor stamina +20%');eq(rounded(favor.load),96,'Favor load +20%');
  eq(character(params,{...base,rings:[ring('wolf-ring')]}).poise,40,'Wolf Ring +40 poise');
  eq(rounded(character(params,{...base,rings:[ring('havel-s-ring')]}).load),120,'Havel +50% load');
  eq(by('soul-of-sif').category,'items','Boss souls stay in items');eq(by('black-flame').type,'Pyromancies','Black Flame DS1 school');eq(catalog.filter(x=>x.category==='bosses').length,26,'26 base and DLC bosses');eq(catalog.filter(x=>x.category==='magic').length,71,'71 spells');
  eq(by('soul-of-sif').soul_value,16000,'Sif consumption 16000');eq(by('soul-of-gwyn-lord-of-cinder').soul_value,20000,'Gwyn consumption 20000');
  const normal=quote(by('longsword'),0,15);eq(normal.souls,3000,'Longsword +15 full fees');eq(normal.materials['Titanite Shard'],9,'Normal 9 shards');eq(normal.materials['Large Titanite Shard'],9,'Normal 9 large shards');eq(normal.materials['Titanite Chunk'],7,'Normal 7 chunks');eq(normal.materials['Titanite Slab'],1,'Normal 1 slab');
  const lightning=quote(by('longsword'),200,5);eq(lightning.souls,3200,'Lightning full precursor fees');eq(lightning.materials['Titanite Chunk'],8,'Lightning includes ascension chunk');
  eq(quote(by('longsword'),0,15,10).souls,1000,'Only remaining normal steps charged');eq(quote(by('black-knight-sword'),0,5).materials['Twinkling Titanite'],10,'Special weapon 10 twinkling');
  eq(quote(by('pyromancy-flame'),0,15).souls,149500,'Pyromancy Flame full fees');eq(quote(by('pyromancy-flame-ascended'),0,5).souls,340500,'Ascended flame with precursor and ascension fees');
  eq(armor(params,by('traveling-gloves-logan').param_id).weight,1.6,'Logan gloves distinct from sorcerer gloves');eq(armor(params,by('traveling-gloves').param_id).weight,.7,'Sorcerer gloves weight');
  eq(Math.round(armor(params,by('elite-knight-helm').param_id).strike_def*100),1455,'Armor strike correction is a percentage');
  const equipped={...base,weapons:[{id:by('longsword').param_id,path:0,level:15},{id:by('claymore').param_id,path:0,level:15}]};const naked=character(params,equipped),resin=character(params,{...equipped,consumables:[by('gold-pine-resin').param_id]});eq(Math.round(resin.weapons[0].attack.lightning),150,'Gold resin adds 150 lightning to active hand');eq(resin.weapons[1].attack.lightning,0,'Resin does not buff inactive weapon');
  const power=character(params,{...equipped,bodySpellId:4400});eq(Math.round(power.weapons[0].attack.physical/naked.weapons[0].attack.physical*100),140,'Power Within attack +40%');
  eq(character(params,{...base,humanity:10,rings:[ring('covetous-gold-serpent-ring')]}).itemDiscovery,410,'Discovery 410 cap');
  const missingQuotes=[];for(const r of catalog.filter(x=>x.category==='weapons'&&x.param_id))for(const path of paths(params,r.param_id)){const bill=quote(r,path.id,path.max);if(!bill.complete)missingQuotes.push(r.id+' '+path.name);if(path.max>0&&![1330000,1332000].includes(r.param_id)){if(!Object.keys(bill.materials).length)issues.push('Missing material schedule '+r.id);for(const step of bill.steps)if(!Object.keys(step.materials).length)issues.push('Missing step materials '+r.id+' '+step.path+' +'+step.level);}}
  return {checks,pathsCount,rows,entries:catalog.length,issues,missingQuotes};
 });
 assert.deepEqual(result.issues,[]);
 await p.goto('http://127.0.0.1:8765/ds1.html#view=blacksmith&id=claymore');await p.waitForSelector('[data-smith=path]');await p.locator('[data-smith=path]').selectOption('900');assert.equal(await p.locator('[data-smith=path]').inputValue(),'900');await p.locator('[data-smith=level]').fill('5');await p.locator('[data-smith=level]').dispatchEvent('change');await p.reload();await p.waitForSelector('[data-smith=path]');assert.equal(await p.locator('[data-smith=path]').inputValue(),'900');result.checks.push('Chaos path and level persist');
 await p.screenshot({path:'DarkSouls-Guide/audit/ds1/blacksmith-desktop.png'});
 for(const view of ['areas','bosses','enemies','weapons','armor','sets','rings','magic','items','npcs','covenants','mechanics','quests','classes','bonfires','builder']){
  await p.evaluate(view=>location.hash='game=ds1&view='+view,view);await p.waitForFunction(view=>document.title.endsWith(' · Dark Souls I')&&new URLSearchParams(location.hash.slice(1)).get('view')===view&&document.querySelector('#view-container h1'),view);console.log('Checked view '+view);assert(!await p.locator('h1').innerText().then(t=>/Unable|could not/.test(t)),view);
  result.checks.push('View '+view);
 }
 await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Builder mobile overflow');await p.screenshot({path:'DarkSouls-Guide/audit/ds1/builder-mobile.png'});
 await p.goto('http://127.0.0.1:8765/index.html#game=ds1&view=weapons&id=moonlight-greatsword');await p.waitForSelector('.detail-top');assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Detail mobile overflow');await p.screenshot({path:'DarkSouls-Guide/audit/ds1/weapon-mobile.png'});
 assert.deepEqual(errors,[]);assert.deepEqual(remote,[]);fs.writeFileSync('DarkSouls-Guide/audit/ds1/runtime.json',JSON.stringify({...result,errors,externalRequests:remote},null,2));console.log(JSON.stringify(result,null,2));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exit(1);});
