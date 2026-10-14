/* DS1 calculations written for this guide. Factual parameters live in database/ds1. */
export const attributes=['vitality','attunement','endurance','strength','dexterity','resistance','intelligence','faith'];
export const channels=['physical','magic','fire','lightning'];
const grade=x=>x<1?'—':x<21?'E':x<51?'D':x<81?'C':x<101?'B':x<141?'A':'S';
export function curve(p,id,value){
 const g=p.CalcCorrectGraph[id];if(!g)return 0;
 const x=Math.max(g[0],Math.min(g[4],value));let i=x<g[1]?0:x<g[2]?1:x<g[3]?2:3;
 const t=(x-g[i])/(g[i+1]-g[i]),power=g[10+i],fraction=power>0?t**power:1-(1-t)**Math.abs(power);
 return g[5+i]+fraction*(g[6+i]-g[5+i]);
}
export function paths(p,id){
 const base=p.EquipParamWeapon[id];if(!base)return [];
 const keys=base[p.param.EquipParamWeapon.ORIGIN_0]===Number(id)?Object.keys(p.upgrades).map(Number).filter(x=>p.EquipParamWeapon[Number(id)+x]):[0];
 return keys.map(path=>({id:path,name:path?p.upgrades[path]:'Normal / original',max:Number(id)===1330000?15:Number(id)===1332000?5:p.EquipParamWeapon[Number(id)+path][2]}));
}
export function effects(p,ids){
 const out=[],seen=new Set();
 function visit(id){if(id<=0||seen.has(id)||!p.SpEffectParam[id])return;seen.add(id);const row=p.SpEffectParam[id];out.push({id,row});visit(row[p.param.SpEffectParam.REFERENCE_SP_EFFECT_ID]);}
 ids.forEach(visit);return out;
}
export function weapon(p,id,path=0,level=0,stats={},twoHand=false,humanity=0){
 const result={base:{},bonus:{},attack:{},scaling:{},requirements:{},guard:{},aux:{bleed:0,poison:0,divine:0,occult:0},selfEffects:[]};
 id=Number(id);path=Number(path);level=Number(level);
 const available=paths(p,id).find(x=>x.id===path);if(!available)throw Error('Unsupported upgrade path');
 level=Math.max(0,Math.min(available.max,level));
 const flame=id===1330000||id===1332000;
 const row=p.EquipParamWeapon[flame?id+100*level:id+path],w=p.param.EquipParamWeapon;
 const r=p.ReinforceParamWeapon[row[w.REINFORCE_ID]+(flame?0:level)],rp=p.param.ReinforceParamWeapon;
 if(!r)throw Error('Missing reinforcement data');
 const a=['STR','DEX','INT','FTH'],values=a.map((_,i)=>Number(stats[['strength','dexterity','intelligence','faith'][i]]||10));
 const bow=[17,18].includes(p.weapons[id]?.type),boost=(twoHand&&row[w.CAN_EQUIP_IN_BOTH_HANDS]===1)||bow;
 const strength=boost?Math.min(99,Math.floor(values[0]*1.5)):values[0];
 const actual=[strength,...values.slice(1)],requirements=a.map(k=>row[w['REQUIRE_'+k]]);
 result.met=actual.every((v,i)=>v>=requirements[i]);result.weight=Math.round(row[w.WEIGHT]*10)/10;result.max=available.max;result.level=level;
 result.buffable=!!row[w.CAN_BUFFED_IN_RH];result.spellTool=!!row[w.IS_SPELL_TOOL];
 const scales=a.map(k=>row[w['SCALE_'+k]]*r[rp['SCALE_'+k+'_CORRECT']]);
 a.forEach((k,i)=>{result.scaling[k]=grade(scales[i]);result.requirements[k]=requirements[i];});
 const penalty=(v,req)=>req===0?0:v<=req*.8?-.802005:-.802005*(1-((v-req*.8)/(req*.2))**2);
 const humanityBonus=humanity<=0?0:humanity===1?.05:humanity===2?.075:humanity===3?.1:.1+.11*(Math.min(10,humanity)-3)/7;
 for(const channel of channels){
  const k=channel.toUpperCase(),inds=channel==='physical'?[0,1]:[2,3];
  const relevant=channel==='physical'?[strength,values[1]]:values.slice(2);
  let scale=relevant.every((v,i)=>v>=requirements[inds[i]])?inds.reduce((sum,j,i)=>sum+scales[j]/100*curve(p,row[w.ATK_CORRECT_GRAPH_ID],relevant[i])/100,0):Math.min(...inds.map((j,i)=>penalty(relevant[i],requirements[j])));
  let base=row[w[k+'_ATK']]*r[rp[k+'_ATK_CORRECT']],rating=base*(1+scale);
  if(row[w.IS_USE_HUMANITY_SCALE])rating*=1+humanityBonus;
  result.base[channel]=base;result.attack[channel]=rating;result.bonus[channel]=rating-base;
  result.guard[channel]=row[w[k+'_DEF']]*r[rp[k+'_DEF_CORRECT']];
 }
 const se=p.param.SpEffectParam;
 for(let n=1;n<=3;n++){
  const eff=row[w['ATK_SP_EFFECT_'+n+'_ID']]+r[rp['ATK_SP_EFFECT_'+n+'_ID']],er=p.SpEffectParam[eff];
  if(er&&!er[se.IS_APPLY_TO_CHARACTER_ON_HIT]){result.aux.bleed+=er[se.BLEED_AUX];result.aux.poison+=er[se.POISON_AUX];}
  result.selfEffects.push(row[w['SELF_SP_EFFECT_'+n+'_ID']]+r[rp['SELF_SP_EFFECT_'+n+'_ID']]);
 }
 result.aux.divine=row[w.DIVINE_AUX]>1.0001?row[w.DIVINE_AUX]*100:0;result.aux.occult=row[w.OCCULT_AUX]>1.0001?row[w.OCCULT_AUX]*100:0;
 result.stability=row[w.STABILITY]*r[rp.STABILITY_CORRECT];
 result.magAdjust=result.spellTool?100*(1+[2,3].reduce((sum,i)=>sum+(values[i]>=requirements[i]?scales[i]/100*curve(p,row[w.ATK_CORRECT_GRAPH_ID],values[i])/100:penalty(values[i],requirements[i])),0)):0;
 result.total=channels.reduce((s,k)=>s+Math.floor(Math.round(result.attack[k]*1e4)/1e4),0);return result;
}
export function armor(p,id,level=0){
 const row=p.EquipParamProtector[id];if(!row)return null;const a=p.param.EquipParamProtector,b=p.param.ReinforceParamProtector;
 level=Math.max(0,Math.min(row[a.MAX_REINFORCE],Number(level)||0));const r=p.ReinforceParamProtector[row[a.REINFORCE_ID]+level];
 const out={weight:Math.round(row[a.WEIGHT]*10)/10,poise:row[a.POISE],max:row[a.MAX_REINFORCE],level,slot:row[a.GROUP],effects:[]};
 for(const k of ['PHYSICAL_DEF','MAGIC_DEF','FIRE_DEF','LIGHTNING_DEF','POISON_RES','TOXIC_RES','BLEED_RES','CURSE_RES'])out[k.toLowerCase()]=row[a[k]]*r[b[k+'_CORRECT']];
 for(const k of ['STRIKE','SLASH','THRUST'])out[k.toLowerCase()+'_def']=out.physical_def*(1+row[a[k+'_DEF_RATE']]/100);
 for(let n=1;n<=3;n++){const id=row[a['SELF_SP_EFFECT_'+n+'_ID']];if(id!==6300)out.effects.push(id);}return out;
}
export function quote(record,path,level,fromLevel=0){
 const mapping={0:['Basic','Normal','Regular','Upgrades'],100:['Crystal'],200:['Lightning'],300:['Raw'],400:['Magic'],500:['Enchanted'],600:['Divine'],700:['Occult'],800:['Fire'],900:['Chaos']};
 const materials={},steps=[];let souls=record.param_id===1332000?174500:0,complete=true;
 if(record.param_id===1332000){materials['Pyromancy Flame +15']=1;}
 const sequence=path===0?[[0,level]]:[500,700,900].includes(Number(path))?[[0,5],[{500:400,700:600,900:800}[path],5],[path,level]]:[[0,[100,200].includes(Number(path))?10:5],[path,level]];
 if(fromLevel>sequence[0][1])return {valid:false,complete:false,reason:'The starting Normal level is above this path’s required precursor. Ascension would need a different starting weapon.'};
 for(const [part,max]of sequence){
  const table=record.tables.find(t=>mapping[part]?.includes(t.heading)&&t.rows[0].includes('Name')&&t.rows[0].some(x=>x==='Damage'||x==='MagAdjust'));
  if(!table){if(max>0||part>0)complete=false;continue;}
  const heads=table.rows[0];let found=0;
  for(const row of table.rows.slice(1)){
   if(row.length!==heads.length)continue;
   const n=Number(row[0].match(/\+(\d+)/)?.[1]??0);
   if(n>max||(part===0&&n<=fromLevel))continue;
   if(part===0&&n===0)continue;
   found++;const feeIndex=heads.findIndex(x=>['Souls','Soul Cost','Cost (souls)'].includes(x));let fee=feeIndex>=0?row[feeIndex]:String(record.upgrade_fee??'');
   if(!/^\d[\d,]*$/.test(fee)&&Number.isFinite(record.upgrade_fee))fee=String(record.upgrade_fee);
   if(!/^\d[\d,]*$/.test(fee)){complete=false;fee=null;}else{fee=Number(fee.replaceAll(',',''));souls+=fee;}
   const bill={};
   for(let i=0;i<heads.length;i++){
    if(['Req. Material','Materials Cost','Upgrade Requirements'].includes(heads[i])){
     const matches=[...row[i].matchAll(/[x×]?\s*(\d+)\s*[x×]?\s*([A-Za-z .]+?(?:Shard|Chunk|Slab|Scale|Titanite))/gi)];
     for(const match of matches){const name=match[2].trim().replace(/\b[a-z]/g,c=>c.toUpperCase()),qty=Number(match[1]);bill[name]=qty;materials[name]=(materials[name]||0)+qty;}
     if(!matches.length){const suffix=row[i].match(/^([A-Za-z .]+(?:Shard|Chunk|Slab|Scale|Titanite))\s*[x×]\s*(\d+)$/i);if(suffix){const name=suffix[1].trim().replace(/\b[a-z]/g,c=>c.toUpperCase()),qty=Number(suffix[2]);bill[name]=qty;materials[name]=(materials[name]||0)+qty;}}
     if(!matches.length&&/^Twinkling Titanite$/.test(row[i])&&n>=1&&n<=5){const qty=[1,1,2,2,4][n-1];bill['Twinkling Titanite']=qty;materials['Twinkling Titanite']=(materials['Twinkling Titanite']||0)+qty;}
     continue;
    }
    let name=heads[i];if(!/shard|chunk|slab|titanite|scale/i.test(name)||!/^\d+$/.test(row[i]))continue;
    name=({'Shard':'Titanite Shard','L. Shard':'Large Titanite Shard','Chunk':'Titanite Chunk','Slab':'Titanite Slab'})[name]||name;
    bill[name]=Number(row[i]);materials[name]=(materials[name]||0)+Number(row[i]);
   }
   steps.push({path:part,level:n,souls:fee,materials:bill});
  }
  const expected=part===0?Math.max(0,max-fromLevel):max+1;if(found<expected)complete=false;
 }
 return {valid:true,complete,souls:complete?souls:null,knownSouls:souls,materials,steps};
}
export function character(p,build){
 const cls=p.classes[build.classId||0],stats=build.stats;const level=cls[1]+attributes.reduce((s,k,i)=>s+stats[k]-cls[i+2],0),humanity=Number(build.humanity||0);
 const allArmor=(build.armor||[]).map(x=>armor(p,x.id,x.level)).filter(Boolean);
 const weapons=(build.weapons||[]).filter(x=>x.id).map(x=>weapon(p,x.id,x.path,x.level,stats,!!x.twoHand,humanity));
 const active=[build.activeRight??0,build.activeLeft??2];
 let ids=allArmor.flatMap(x=>x.effects).concat(weapons.filter((x,i)=>active.includes((build.weapons||[]).map((w,i)=>({...w,index:i})).filter(w=>w.id)[i].index)).flatMap(x=>x.selfEffects));
 for(const id of new Set(build.rings||[])){const ring=p.EquipParamAccessory[id];if(ring&&ring[1]===2)ids.push(ring[0]);}
 for(const id of build.consumables||[]){const item=p.EquipParamGoods[id];if(item&&item[1]===2)ids.push(item[0]);}
 const body=p.Magic[build.bodySpellId];if(body&&body[5]===2&&stats.intelligence>=body[1]&&stats.faith>=body[2])ids.push(body[6]);
 const eff=effects(p,ids).filter(({row})=>row[0]<=0||(row[0]===20&&build.lowHp)),sp=p.param.SpEffectParam;
 const factor=k=>eff.reduce((v,{row})=>v*(row[sp[k]]||1),1),added=k=>eff.reduce((v,{row})=>v+(row[sp[k]]||0),0);
 const out={level,hp:Math.floor(curve(p,100,stats.vitality)*factor('HP_CORRECT')),stamina:Math.floor((p.stamina?.[stats.endurance]??Math.min(160,80+2*stats.endurance))*factor('STAMINA_CORRECT')),load:(40+stats.endurance)*factor('EQUIPMENT_LOAD_CORRECT'),poise:allArmor.reduce((s,a)=>s+a.poise,0)+added('POISE_CORRECT'),slots:[10,12,14,16,19,23,28,34,41,50].filter(x=>stats.attunement>=x).length+added('ATTUNEMENT_SLOT_COUNT_CORRECT'),defenses:{},resistances:{},weapons,effects:eff};
 out.poise=Math.max(0,out.poise);out.weight=allArmor.reduce((s,a)=>s+a.weight,0)+weapons.reduce((s,w)=>s+w.weight,0);out.ratio=100*out.weight/out.load;out.roll=out.ratio<=25?'Fast roll':out.ratio<=50?'Medium roll':out.ratio<=100?'Heavy roll':'Overburdened';
 out.staminaRegen=(45+added('STAMINA_REGEN_SPEED_CORRECT'))*(out.ratio>100?.7:out.ratio>50?.8:1);
 out.itemDiscovery=Math.min(410,(p.itemDiscovery?.[Math.min(99,humanity)]||100)+(eff.some(({row})=>row[sp.STATE_INFO]===66)?200:0));
 out.damageTaken=Object.fromEntries(channels.map(k=>[k,factor(k.toUpperCase()+'_DMG_CORRECT')]));
 const combined=level+humanity;
 const points={physical:.9*combined+.9*stats.resistance,magic:.85*combined+1.35*stats.faith,fire:.85*combined+1.35*stats.resistance,lightning:combined};
 for(const k of channels)out.defenses[k]=(Math.round(curve(p,102,Math.min(800,points[k])))+allArmor.reduce((s,a)=>s+a[k+'_def'],0))*factor(k.toUpperCase()+'_DEF_CORRECT')+added(k.toUpperCase()+'_DEF');
 for(const [key,id,value]of [['bleed',112,stats.endurance],['poison',110,stats.resistance],['curse',113,Math.min(30,humanity)]])out.resistances[key]=(Math.round(curve(p,id,value))+allArmor.reduce((s,a)=>s+a[key+'_res'],0))*factor(key.toUpperCase()+'_RES_CORRECT');
 for(let i=0;i<weapons.length;i++){
  const w=weapons[i],slot=(build.weapons||[]).map((x,index)=>({...x,index})).filter(x=>x.id)[i].index;
  const weaponEffects=eff.filter(({row})=>{const target=row[sp.WEAPON_PARAM_CHANGE];return target===0||(target===1&&slot===active[0]&&w.buffable)||(target===2&&slot===active[1]&&w.buffable);});
  for(const k of channels){const f=key=>weaponEffects.reduce((v,{row})=>v*(row[sp[key]]||1),1),a=key=>weaponEffects.reduce((v,{row})=>v+(row[sp[key]]||0),0);w.attack[k]=w.attack[k]*f(k.toUpperCase()+'_ATK_RATE')*f(k.toUpperCase()+'_ATK_CORRECT')+a(k.toUpperCase()+'_ATK');}
  w.gearBonus=Object.fromEntries(channels.map(k=>[k,w.attack[k]-w.base[k]-w.bonus[k]]));
  w.total=channels.reduce((s,k)=>s+Math.floor(Math.round(w.attack[k]*1e4)/1e4),0);
 }
 return out;
}
