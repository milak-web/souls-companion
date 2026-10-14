// Extract only factual object literals from the research cache; no imported code runs.
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.resolve(__dirname,'..'),raw=fs.readFileSync(path.join(root,'audit/ds1/planner-full.js'),'utf8');
function literal(name){
 const start=raw.indexOf(name+'=')+name.length+1;
 if(start<name.length+1||raw[start]!=='{')throw Error('Missing literal '+name);
 let depth=0,quote='',escape=false,end=start;
 for(;end<raw.length;end++){
  const c=raw[end];if(quote){if(escape)escape=false;else if(c==='\\')escape=true;else if(c===quote)quote='';continue;}
  if(c==='"'||c==="'"){quote=c;continue;}
  if(c==='{')depth++;if(c==='}'&&!--depth)break;
 }
 return raw.slice(start,end+1);
}
const out={source:'https://soulsplanner.com/darksouls/weaponatk',retrieved:'2026-10-11'};
for(const name of ['stamina','itemDiscovery']){
 const match=raw.match(new RegExp('DarkSouls\\.'+name+'=(\\[[^\\]]*\\])'));if(!match)throw Error('Missing '+name);out[name]=JSON.parse(match[1]);
}
const ctx=vm.createContext({DarkSouls:{}});
for(const name of ['weaponType','weaponGroups','upgrades','CalcCorrectGraph','EquipParamWeapon','ReinforceParamWeapon','SpEffectParam','EquipParamProtector','ReinforceParamProtector','EquipParamAccessory','EquipParamGoods','Magic','classes']){
 let value=literal('DarkSouls.'+name);
 // Object functions in display metadata are not imported; permit literals only.
 if(/function|=>/.test(value)){if(name!=='weapons')throw Error('Non-data '+name);value=value.replace(/,getDescription:function\([^)]*\)\{[^}]*\}/g,'');}
 const data=vm.runInContext('('+value+')',ctx,{timeout:1000});out[name]=data;ctx.DarkSouls[name]=data;
}
out.param={};
for(const name of ['EquipParamWeapon','ReinforceParamWeapon','SpEffectParam','EquipParamProtector','ReinforceParamProtector','EquipParamAccessory','EquipParamGoods','Magic','classes'])out.param[name]=vm.runInNewContext('('+literal('DarkSouls.param.'+name)+')',{}, {timeout:1000});
for(const name of ['weapons','protectors','rings','items','spells']){
 const data={};let value=literal('DarkSouls.'+name);
 // Read individual factual metadata fields, ignoring display functions entirely.
 const regex=/(\d+(?:e\d+)?):\{name:("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g;
 for(const m of value.matchAll(regex)){
  const id=Number(m[1]),label=vm.runInNewContext(m[2],{}, {timeout:100});data[id]={name:label};
  const tail=value.slice(m.index+m[0].length,m.index+m[0].length+150);
  const group=tail.match(/^,type:DarkSouls\.weaponType\.(\w+),group:(\d+)/);
  if(group){data[id].type=out.weaponType[group[1]];data[id].group=Number(group[2]);}
 }
 out[name]=data;
}
fs.writeFileSync(path.join(root,'database/ds1/parameters.json'),JSON.stringify(out));
console.log(Object.fromEntries(Object.entries(out).map(([k,v])=>[k,typeof v==='object'?Object.keys(v).length:v])));
