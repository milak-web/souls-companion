const {chromium}=require('C:/Users/MK2/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});try{
 const p=await b.newPage({viewport:{width:390,height:844}}),errors=[],failed=[],remote=[];
 const base=process.argv[2]||'http://127.0.0.1:8770/DarkSouls-Guide/dist/',site=new URL(base);
 p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url());});p.on('request',r=>{if(new URL(r.url()).origin!==site.origin)remote.push(r.url());});
 await p.goto(base);await p.waitForSelector('.game-card');assert.equal(await p.locator('a.game-card').count(),2);await p.setViewportSize({width:1440,height:1000});await p.screenshot({path:path.join(__dirname,'../docs/screenshots/game-menu.png')});await p.setViewportSize({width:390,height:844});
 for(const game of ['ds1','ds2'])for(const view of ['home','weapons','blacksmith','builder','armor']){
  await p.evaluate(({game,view})=>location.hash=new URLSearchParams({game,view}),{game,view});
  await p.waitForFunction(({game,view})=>document.body.classList.contains('game-'+game)&&new URLSearchParams(location.hash.slice(1)).get('view')===view&&!document.querySelector('#view-container').textContent.includes('Loading the local archive'),{game,view});
  assert(!await p.locator('#view-container').innerText().then(t=>/could not|Unable to display/i.test(t)),game+' '+view);
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,game+' '+view+' mobile overflow');
 }
 const manifest=await p.request.get(base+'manifest.webmanifest');assert.equal(manifest.status(),200);assert.equal((await manifest.json()).start_url,'./#view=games');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert.deepEqual(remote,[]);console.log(JSON.stringify({base,mobileViews:10,scriptErrors:errors,failedRequests:failed,externalRequests:remote}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exit(1)});
