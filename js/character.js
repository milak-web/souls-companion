// Offline character calculations. Parameter arrays are imported, never interpolated.
const ATTRS={vgr:'Vigor',end:'Endurance',vit:'Vitality',atn:'Attunement',str:'Strength',dex:'Dexterity',adp:'Adaptability',int:'Intelligence',fth:'Faith'};
const DAMAGE=['physical','magic','fire','lightning','dark'];
const DEFENSE=['strike','slash','thrust','magic','fire','lightning','dark','poison','bleed','petrify','curse'];
const ARMOR=['head','chest','hands','legs'];
const clamp=(n,a,b)=>Math.max(a,Math.min(b,Math.trunc(Number(n)||0)));
const sum=a=>a.reduce((x,y)=>x+y,0);
const round=(n,d=1)=>Number(n.toFixed(d));
const blank=keys=>Object.fromEntries(keys.map(k=>[k,0]));

export const characterMethods={
    characterState(){
        if(this.character)return this.character;
        const raw=this.readSaved('ds2_character_v1',{}),classes=this.data.character?.classes||{};
        const cls=classes[raw.className]?raw.className:'Knight',base=classes[cls]||Object.fromEntries(Object.keys(ATTRS).map(k=>[k,6]));
        const weapon=x=>{const w=this.data.weapons.find(w=>w.id===x?.id);if(!w)return {id:'',path:'Normal',level:0};const e=this.smithEquipment(w.id),p=e?.paths?.[x.path]?x.path:'Normal';return {id:w.id,path:p,level:clamp(x.level,0,e?.max_level||0)};};
        const valid=(id,cat)=>cat.some(x=>x.id===id)?id:'';
        this.character={className:cls,stats:Object.fromEntries(Object.keys(ATTRS).map(k=>[k,clamp(raw.stats?.[k]??base[k],base[k],99)])),weapons:Array.from({length:6},(_,i)=>weapon(raw.weapons?.[i])),armor:Object.fromEntries(ARMOR.map(k=>{const r=raw.armor?.[k],a=this.data.armor.find(a=>a.id===r?.id&&a.slot===k&&!a.unavailable);return [k,{id:a?.id||'',level:clamp(r?.level,0,this.data.character?.armor?.[a?.id]?.max_level||a?.max_level||0)}];})),rings:Array.from({length:4},(_,i)=>valid(raw.rings?.[i],this.data.items.filter(x=>x.type==='Ring'))),quick:Array.from({length:10},(_,i)=>valid(raw.quick?.[i],this.characterQuickItems())),spells:Array.from({length:10},(_,i)=>valid(raw.spells?.[i],this.data.magic)),active:clamp(raw.active,0,5),twoHand:!!raw.twoHand,body:valid(raw.body,this.characterBodyItems()),buff:this.data.character?.buffs?.some(x=>x.name===raw.buff)?raw.buff:'',hollow:clamp(raw.hollow,0,10),sin:clamp(raw.sin,0,100),souls:clamp(raw.souls,0,999999999),ng:clamp(raw.ng,0,10),pvp:!!raw.pvp,santierBroken:raw.santierBroken!==false,currentHp:raw.currentHp===null||raw.currentHp===undefined?null:clamp(raw.currentHp,0,99999),estus:clamp(raw.estus,0,5)};
        this.character.activeHands=[clamp(raw.activeHands?.[0],0,2),clamp(raw.activeHands?.[1]??3,3,5)];const families=new Set();this.character.rings=this.character.rings.map(id=>{const f=this.data.character.effects[id]?.family;if(families.has(f))return '';if(id)families.add(f);return id;});
        return this.character;
    },
    saveCharacter(){try{localStorage.setItem('ds2_character_v1',JSON.stringify(this.characterState()));}catch{}},
    characterQuickItems(){return this.data.items.filter(x=>['Consumable','Tool','Multiplayer item'].includes(x.type));},
    characterBodyItems(){return this.data.items.filter(x=>{const e=this.data.character?.effects?.[x.id];return e&&(Object.keys(e.stats||{}).length||Object.keys(e.defense||{}).length||e.regen||e.damage_mult);}).concat(this.data.magic.filter(x=>x.id==='sacred-oath'));},
    characterLevel(stat){return this.data.character?.levels?.[clamp(stat,1,99)]||{};},
    characterScaling(id,path,level){
        const p=this.data.character?.weapons?.[id]?.[path];if(!p||level>p.max_level)return null;
        const factor=1-p.infusion_multiplier/Math.max(1,p.element_count),coef={};
        for(const ch of ['str','dex'])coef[ch]=path==='Mundane'?0:(p.scaling[ch][level]??0)*(p.flags.physical===100?factor:p.flags.physical?1:0)*100;
        for(const ch of ['magic','fire','lightning','dark','poison','bleed'])coef[ch]=p.flags[ch]?p.scaling[ch][level]*(p.flags[ch]===200?p.innate[ch]+p.infusion_multiplier:factor)*100:0;
        coef.enchanted=path==='Enchanted'?p.scaling.enchanted[level]*100:0;coef.mundane=path==='Mundane'?p.mundane*100:0;
        return Object.fromEntries(Object.entries(coef).map(([k,v])=>[k,round(v,4)]));
    },
    equipInCharacter(id){this.chooseCharacterGear('weapon',this.characterState().active,id);this.renderView('builder');},
    characterWeaponParams(slot,state){
        const id=slot.id==='fists'&&state.rings.includes('vanquisher-s-seal')?'vanquisher_fists':slot.id==='majestic-greatsword'&&state.active>=3?'majestic_left':slot.id==='santier-s-spear'&&!state.santierBroken?'santier_unbroken':slot.id;
        return this.data.character?.weapons?.[id]?.[slot.path];
    },
    characterTotals(state=this.characterState()){
        const data=this.data.character,stats={...state.stats},effects=[],notes=[];
        const items=state.rings.map(id=>this.data.items.find(x=>x.id===id)).filter(Boolean);
        const gear=[...items,...ARMOR.map(k=>this.data.armor.find(x=>x.id===state.armor[k].id)).filter(Boolean)];
        // Only the selected weapon in each hand provides a passive effect; all six add weight.
        const other=state.active<3?(state.activeHands?.[1]??3):(state.activeHands?.[0]??0);
        const passives=[state.weapons[state.active],state.weapons[other]].map(s=>this.data.weapons.find(x=>x.id===s.id)).filter(Boolean);
        for(const g of [...gear,...passives]){const e=data.effects[g.id];if(e){effects.push({record:g,...e});for(const [k,v] of Object.entries(e.stats||{}))stats[k]+=v;if(e.embedded)for(const k of ['vgr','end','vit'])stats[k]+=state.stats[k]<=6?7:state.stats[k]<=19?6:state.stats[k]<=33?5:state.stats[k]<=46?4:3;}}
        const body=this.characterBodyItems().find(x=>x.id===state.body),bodyEffect=data.effects[state.body];
        if(bodyEffect&&!(state.pvp&&state.body==='brightbug')){effects.push({record:body,...bodyEffect});for(const [k,v] of Object.entries(bodyEffect.stats||{}))stats[k]+=v;}
        if(state.pvp&&state.body==='brightbug')notes.push('Brightbug cannot be used in multiplayer; its damage modifiers are excluded from the PvP preview.');
        for(const e of effects)if(e.source_note)notes.push(e.source_note);
        for(const k of Object.keys(stats))stats[k]=clamp(stats[k],1,99);
        const product=key=>effects.reduce((p,e)=>p*(e[key]??1),1),add=key=>sum(effects.map(e=>Number(e[key])||0));
        const hpBase=this.characterLevel(stats.vgr).hp+sum(Object.entries(stats).filter(([k])=>k!=='vgr').map(([,v])=>this.characterLevel(v).other_hp));
        const binding=state.rings.includes('ring-of-binding');
        const hp=Math.trunc(hpBase*product('hp_mult')),availableHp=Math.trunc(hp*Math.max(binding ? .75 : .5,1-state.hollow*(binding ? .025 : .05)));
        const stamina=Math.trunc(this.characterLevel(stats.end).stamina_x10/10*product('stamina_mult'));
        const load=this.characterLevel(stats.vit).load*product('load_mult');
        let weight=sum(state.weapons.map(s=>{const w=this.data.weapons.find(w=>w.id===s.id);return s.id==='santier-s-spear'?(state.santierBroken?12:16):Number(w?.weight)||0;}));
        weight+=sum(items.map(x=>data.effects[x.id]?.weight??(Number(x.equipment_stats?.weight)||0)));
        const defenses=blank(DEFENSE),armorDetails=[];
        const physLevel=Math.floor((stats.str+stats.dex+stats.end+stats.vit)/4),phys=this.characterLevel(physLevel);
        for(const k of ARMOR){
            const slot=state.armor[k],a=this.data.armor.find(x=>x.id===slot.id),m=data.armor[slot.id];
            if(!a){const ratio={head:.15,chest:.45,hands:.15,legs:.25}[k];for(const ch of ['strike','slash','thrust'])defenses[ch]+=phys.unarmored_defense*ratio;continue;}
            const missing=Object.entries(m?.requirements||a.requirements||{}).filter(([k,v])=>stats[k]<v);
            weight+=m?.weight??(Number(a.defenses_base?.weight)||0);
            if(m){
                const bonus=m.scaling*phys.armor_bonus;
                const exact=m.rows?.[slot.level];
                const vals=Object.fromEntries(Object.entries(exact||m.base).map(([ch,n])=>[ch,n+(exact?0:(m.increment[ch]||0)*slot.level)+(['strike','slash','thrust'].includes(ch)?bonus:0)]));
                for(const [ch,v] of Object.entries(vals))defenses[ch]+=v;
                armorDetails.push({name:a.name,level:slot.level,poise:m.poise,bonus:round(bonus),defenses:vals});
                // Petrify/curse are endpoint tables; intermediate values are not extrapolated.
                if(!exact)for(const ch of ['petrify','curse']){const v=(slot.level===0?a.defenses_base:slot.level===m.max_level?a.defenses_max:null)?.[ch];if(v!=null)defenses[ch]+=v;else if(a.defenses_max?.[ch])notes.push(`${a.name}: ${ch} resistance at +${slot.level} is not available; total is a subtotal.`);}
            }else{
                const endpoint=slot.level===0?a.defenses_base:slot.level===a.max_level?a.defenses_max:null;
                for(const ch of DEFENSE)defenses[ch]+=Number(endpoint?.[ch])||0;
                notes.push(`${a.name}: physical scaling is unavailable${endpoint?'':'; this intermediate reinforcement is also unavailable'}. Defense totals are subtotals.`);
                armorDetails.push({name:a.name,level:slot.level,poise:a.defenses_base?.poise||0,bonus:null});
            }
            if(missing.length)notes.push(`${a.name}: requirements not met (${missing.map(([k,v])=>`${k.toUpperCase()} ${v}`).join(', ')}). Defense penalty is not modeled; the listed defenses assume requirements are met.`);
        }
        const innate={magic:stats.int,lightning:stats.fth,fire:Math.floor((stats.int+stats.fth)/2),dark:Math.min(stats.int,stats.fth),poison:Math.floor((3*stats.adp+stats.vit)/4),bleed:Math.floor((3*stats.adp+stats.fth)/4),petrify:Math.floor((3*stats.adp+stats.vgr)/4),curse:Math.floor((3*stats.adp+stats.atn)/4)};
        for(const [ch,v] of Object.entries(innate))defenses[ch]+=this.characterLevel(v).element_defense;
        for(const e of effects)for(const [ch,v] of Object.entries(e.defense||{}))defenses[ch]+=v;
        if(state.body==='sacred-oath')for(const ch of ['strike','slash','thrust'])defenses[ch]+=75;
        const poise=this.characterLevel(Math.min(stats.end,stats.adp)).poise+sum(armorDetails.map(a=>a.poise))+add('poise');
        const investment=Math.floor((3*stats.adp+stats.atn)/4),agilityData=this.characterLevel(investment);
        const percent=weight/load,loss=percent<=.3?percent/4:percent<=.7?.075+(percent-.3)*.6875:Math.min(.6,.35+(percent-.7)*.5);
        const regen=51.9*(1-loss)*(1+add('regen'));
        const slots=this.characterLevel(stats.atn).slots+add('slots');
        const spellDetails=state.spells.map(id=>this.data.magic.find(x=>x.id===id)).filter(Boolean),usedSlots=sum(spellDetails.map(x=>Number(x.filter_stats?.slots)||Number(x.spell_stats?.Slots)||1));
        for(const spell of spellDetails){const req=spell.filter_stats||{};if(stats.int<(req.int_required||0)||stats.fth<(req.faith_required||0))notes.push(`${spell.name}: spell requirements are not met.`);}
        if(usedSlots>slots)notes.push(`Attuned spells use ${usedSlots} slots; only ${slots} are available.`);
        const soulLevel=sum(Object.values(state.stats))-53,cost=data.level_costs[soulLevel+1]??null;
        const castTime=this.characterLevel(Math.floor((2*stats.atn+stats.int+stats.fth)/4)).cast_time*product('cast_time_mult');
        const bns={str:this.characterLevel(stats.str).str,dex:this.characterLevel(stats.dex).dex,magic:this.characterLevel(stats.int).magic,lightning:this.characterLevel(stats.fth).lightning,fire:this.characterLevel(Math.floor((stats.int+stats.fth)/2)).fire,dark:this.characterLevel(Math.min(stats.int,stats.fth)).dark,poison:this.characterLevel(Math.floor((3*stats.dex+stats.adp)/4)).poison,bleed:this.characterLevel(Math.floor((3*stats.dex+stats.fth)/4)).bleed,mundane:this.characterLevel(Math.min(...Object.values(stats))).mundane};
        const result={stats,hp,hpBase,availableHp,stamina,load,weight,percent,regen,poise,agility:String(agilityData.agility).replace(/\.0$/,''),investment,rollFrames:agilityData.roll_frames,backstepFrames:agilityData.backstep_frames,castTime,slots,usedSlots,soulLevel,cost,bns,defenses:Object.fromEntries(Object.entries(defenses).map(([k,v])=>[k,Math.round(v)])),armorDetails,effects,notes,damageMult:product('damage_mult'),damageTakenMult:product('damage_taken_mult')};
        result.attack=this.characterAttack(state.weapons[state.active],result,state);
        return result;
    },
    characterAttack(slot,result,state){
        const w=this.data.weapons.find(x=>x.id===slot.id),p=this.characterWeaponParams(slot,state);
        if(!w||!p)return null;
        const row=this.smithRow(this.smithEquipment(w.id),slot.path,slot.level);
        const notes=[],missing=Object.entries(p.requirements||{}).filter(([k,v])=>result.stats[k]<(k==='str'&&state.twoHand?Math.floor(v/2):v));
        const disagreement=this.data.character.source_disagreements?.[w.id]?.[slot.path];if(disagreement)notes.push(disagreement);
        if(w.id==='majestic-greatsword')notes.push(`Majestic Greatsword: ${state.active>=3?'left':'right'}-hand variant. The left-hand base attack differs from the default weapon page.`);
        if(p.source_note)notes.push(p.source_note);
        let special=1;
        if(w.id==='lost-sinner-s-sword')special=Math.max(0,(30-state.sin)/30);
        if(w.id==='ruler-s-sword')special=.85+Math.min(1,Math.max(0,(state.souls-10000)/990000))*.45;
        if(['dark-pyromancy-flame','greatsword-of-the-forlorn','scythe-of-the-forlorn'].includes(w.id))special=state.hollow>=10?1:state.hollow/11+.1;
        if(w.id==='staff-of-amana')special=state.hollow>=10?.1:1-state.hollow/11;
        if(state.buff==='Bewitched Alonne Sword'&&w.id==='bewitched-alonne-sword')special*=1.6;
        const bns=result.bns,base=blank([...DAMAGE,'poison','bleed']),scaling=blank([...DAMAGE,'poison','bleed']),equipment=blank([...DAMAGE,'poison','bleed']),buff=blank([...DAMAGE,'poison','bleed']);
        const factor=1-p.infusion_multiplier/Math.max(1,p.element_count);
        for(const ch of Object.keys(base)){
            const variant=w.id==='majestic-greatsword';
            base[ch]=p.flags[ch]?(variant||w.id==='fists'||!row?Math.trunc((p.base[ch]+p.increment[ch]*slot.level)*p.base_multiplier*p.damage_multiplier[ch]):row.attack?.[ch]??row.auxiliary?.[ch]??0):0;
            if(ch==='physical'){
                if(slot.path==='Mundane')scaling[ch]=bns.mundane*p.mundane;
                else scaling[ch]=(bns.str*p.scaling.str[slot.level]+bns.dex*p.scaling.dex[slot.level])*(p.flags.physical===100?factor:p.flags.physical?1:0)+(slot.path==='Enchanted'?bns.magic*p.scaling.enchanted[slot.level]:0);
            }else if(p.flags[ch])scaling[ch]=bns[ch]*p.scaling[ch][slot.level]*(p.flags[ch]===200?p.innate[ch]+p.infusion_multiplier:factor);
            scaling[ch]*=special;
        }
        const blades=state.rings.find(id=>id.startsWith('ring-of-blades'));
        if(blades){const name=this.data.items.find(x=>x.id===blades)?.name||'',lv=/\+[12]$/.test(name)?Number(name.slice(-1)):0;equipment.physical+=p.blades[lv]*special;}
        if(state.body==='sacred-oath')equipment.physical+=p.oath*special;
        if(w.id==='curved-nil-greatsword')equipment.physical+=state.ng*(state.pvp?10:20);
        for(const [ch,id] of Object.entries({magic:'sorcery-clutch-ring',lightning:'lightning-clutch-ring',fire:'fire-clutch-ring',dark:'dark-clutch-ring'}))if(state.rings.includes(id)&&p.flags[ch])equipment[ch]+=p.clutch[ch]*special;
        if(state.rings.includes('king-s-ring')&&p.flags.fire)equipment.fire+=p.king_ring*special;
        const armorIds=ARMOR.map(k=>state.armor[k].id);
        if(p.flags.poison){if(state.rings.includes('crest-of-the-rat'))equipment.poison+=p.status_ring.poison*special;if(armorIds.includes('sanctum-soldier-gauntlet'))equipment.poison+=p.status_ring.poison*special;}
        if(p.flags.bleed){if(state.rings.includes('crest-of-blood'))equipment.bleed+=p.status_ring.bleed*special;if(armorIds.includes('shadow-gauntlets'))equipment.bleed+=(p.status_ring.bleed+(.2+(p.scaling.bleed[slot.level]-.2)*.8)*.125*bns.bleed)*special+(p.base.bleed+p.increment.bleed*slot.level)*p.base_multiplier*.1;}
        const selected=this.data.character.buffs.find(b=>b.name===state.buff);
        if(selected&&selected.channel!=='special'){
            const spell=this.data.magic.find(x=>x.id===selected.id),req=spell?.filter_stats||{};
            const legal=selected.type==='resin'?p.resin:selected.type==='spell'?p.spell_buff:w.name===selected.name;
            if(!legal)notes.push(`${selected.name} cannot buff this weapon on this path.`);
            else if(result.stats.int<(req.int_required||0)||result.stats.fth<(req.faith_required||0))notes.push(`${selected.name}: casting requirements are not met; buff excluded.`);
            else{
                const ch=selected.channel;
                const ring=ch==='fire'?((state.rings.includes('fire-clutch-ring')?30:0)+(state.rings.includes('king-s-ring')?6:0)):state.rings.includes({magic:'sorcery-clutch-ring',lightning:'lightning-clutch-ring',dark:'dark-clutch-ring'}[ch])?30:0;
                const innate=p.innate[ch]*100,match=slot.path.toLowerCase()===ch.toLowerCase()||(slot.path==='Magic'&&ch==='magic');
                const affinity=match?innate+p.buff_correction:innate===100?100-p.buff_correction/Math.max(1,p.element_count):0;
                buff[ch]=selected.multiplier*(selected.flat+ring+p.scaling[ch][slot.level]*bns[ch]+(p.base[ch]+p.increment[ch]*slot.level)*p.base_multiplier)+affinity*selected.flat*.01;
                if(['poison','bleed'].includes(ch))buff[ch]*=.2;
            }
        }
        const ranged=/Bow|Crossbow|Staff|Chime|Flame|Shield/i.test(w.type),flynn=state.rings.includes('flynn-s-ring')&&!ranged?(result.load<=60?50:result.load<=80?50-(result.load-60)*2:result.load<=100?10-(result.load-80)*.45:1):0;
        const menu=Object.fromEntries(DAMAGE.map(ch=>[ch,Math.trunc(base[ch]+scaling[ch]+equipment[ch]+1e-9)]));
        const attack=Object.fromEntries(DAMAGE.map(ch=>[ch,Math.trunc(base[ch]+scaling[ch]+equipment[ch]+buff[ch]+(ch==='physical'?flynn:0)+1e-9)]));
        const total=sum(Object.values(attack)),menuTotal=sum(Object.values(menu));
        if(missing.length)notes.push(`Weapon requirements not met: ${missing.map(([k,v])=>`${k.toUpperCase()} ${state.twoHand&&k==='str'?Math.floor(v/2):v}`).join(', ')}. The game's requirement penalty is not reproduced; attack totals are withheld.`);
        if(state.twoHand)notes.push('Two-handing halves the Strength requirement (rounded down). It does not double Strength scaling. Moveset damage multipliers are separate from attack rating.');
        return {weapon:w,base,scaling,equipment,buff,menu,attack,flynn,total:missing.length?null:total,menuTotal:missing.length?null:menuTotal,potentialTotal:total,auxiliary:Object.fromEntries(['poison','bleed'].map(ch=>[ch,Math.trunc(base[ch]+scaling[ch]+equipment[ch]+buff[ch]+1e-9)])),missing,notes,special};
    },
    setCharacterStat(key,value){if(!(key in ATTRS))return;const s=this.characterState(),min=this.data.character.classes[s.className][key];s.stats[key]=clamp(value,min,99);this.saveCharacter();this.updateCharacter();},
    setCharacterClass(name){const base=this.data.character.classes[name];if(!base)return;const s=this.characterState();s.className=name;s.stats={...base};this.saveCharacter();this.renderBuilder();},
    setCharacterField(key,value){const s=this.characterState();if(['twoHand','pvp','santierBroken'].includes(key))s[key]=!!value;else if(['hollow','sin','souls','ng','estus','active','currentHp'].includes(key))s[key]=clamp(value,0,{hollow:10,sin:100,souls:999999999,ng:10,estus:5,active:5,currentHp:99999}[key]);else if(key==='buff')s.buff=this.data.character.buffs.some(b=>b.name===value)?value:'';else if(key==='body')s.body=this.characterBodyItems().some(b=>b.id===value)?value:'';else return;if(key==='active')s.activeHands[s.active<3?0:1]=s.active;this.saveCharacter();this.renderBuilder();},
    setCharacterWeaponField(index,key,value){const s=this.characterState(),slot=s.weapons[index],e=this.smithEquipment(slot?.id);if(!slot)return;if(key==='path'){if(!e?.paths?.[value])return;slot.path=value;}else if(key==='level')slot.level=clamp(value,0,e?.max_level||0);else return;this.saveCharacter();this.renderBuilder();},
    setCharacterArmorLevel(key,value){const s=this.characterState(),slot=s.armor[key],a=this.data.armor.find(x=>x.id===slot?.id);if(!a)return;slot.level=clamp(value,0,this.data.character.armor[a.id]?.max_level||a.max_level||0);this.saveCharacter();this.renderBuilder();},
    chooseCharacterGear(kind,slot,id){
        const s=this.characterState();this.characterNotice='';
        if(kind==='weapon'){const w=this.data.weapons.find(x=>x.id===id);s.weapons[slot]={id:w?.id||'',path:'Normal',level:0};}
        else if(kind==='armor'){const a=this.data.armor.find(x=>x.id===id&&x.slot===slot&&!x.unavailable);s.armor[slot]={id:a?.id||'',level:0};}
        else if(kind==='ring'){const r=this.data.items.find(x=>x.id===id&&x.type==='Ring'),family=this.data.character.effects[id]?.family;if(r){for(let i=0;i<4;i++)if(i!==Number(slot)&&s.rings[i]&&this.data.character.effects[s.rings[i]]?.family===family){s.rings[i]='';this.characterNotice='Replaced the existing ring from the same family.';}}s.rings[slot]=r?.id||'';}
        else if(kind==='quick')s.quick[slot]=this.characterQuickItems().some(x=>x.id===id)?id:'';
        else if(kind==='spell')s.spells[slot]=this.data.magic.some(x=>x.id===id)?id:'';
        else return;
        this.saveCharacter();this.renderBuilder();
    },
    equipCharacterSet(id){const set=this.data.armor.find(x=>x.id===id&&!x.slot);if(!set)return;const s=this.characterState();for(const k of ARMOR){const a=this.data.armor.find(x=>x.slot===k&&!x.unavailable&&(set.pieces?.length?set.pieces.includes(x.id):x.source_url===set.source_url));s.armor[k]={id:a?.id||'',level:0};}this.saveCharacter();this.renderBuilder();},
    useCharacterQuick(index){
        const s=this.characterState(),id=s.quick[index],r=this.characterTotals(s),e=this.data.character.effects[id],item=this.data.items.find(x=>x.id===id);
        if(!item)return;
        const current=Math.min(r.availableHp,s.currentHp??r.availableHp);
        if(e?.human){s.hollow=0;s.currentHp=current;this.characterNotice='Humanity restored. Your HP limit is restored; current HP is unchanged.';}
        else if(e?.heal||e?.full_heal||id==='estus-flask'){
            let heal=e?.full_heal?r.availableHp:id==='estus-flask'?550+s.estus*50:e.heal;
            if(id==='estus-flask'&&s.rings.includes('ancient-dragon-seal'))heal+=50;
            s.currentHp=Math.min(r.availableHp,current+heal);this.characterNotice=`${item.name}: restores ${heal} HP${e?.heal_duration?` over ${e.heal_duration} seconds`:''}; ${s.currentHp-current} HP recovered at the entered health. Preview assumes the full healing duration completes.`;
        }else if(this.characterBodyItems().some(x=>x.id===id)){s.body=id;this.characterNotice=`${item.name} activated${e?.duration?` for a ${e.duration}-second preview`:''}. The previous body consumable is replaced.`;}
        else {const b=this.data.character.buffs.find(b=>b.id===id);if(b){s.buff=b.name;this.characterNotice=`${item.name} applied to the active weapon preview.`;}else this.characterNotice=`${item.name}: ${item.usage||item.description||'See the local item page for its effect.'} This use has no modeled character-stat change.`;}
        this.saveCharacter();this.renderBuilder();
    },
    openCharacterPicker(kind,slot){
        this.characterPicker={kind,slot};const dialog=document.getElementById('character-picker');if(!dialog)return;
        document.getElementById('character-picker-search').value='';document.getElementById('character-picker-title').textContent=`Choose ${kind==='armor'?slot:kind}`;this.filterCharacterPicker('');dialog.showModal();document.getElementById('character-picker-search').focus();
    },
    filterCharacterPicker(query){
        const {kind,slot}=this.characterPicker||{};let rows=kind==='weapon'?this.data.weapons:kind==='armor'?this.data.armor.filter(x=>x.slot===slot&&!x.unavailable):kind==='ring'?this.data.items.filter(x=>x.type==='Ring'):kind==='spell'?this.data.magic:this.characterQuickItems();
        rows=rows.filter(x=>`${x.name} ${x.type}`.toLowerCase().includes(query.toLowerCase())).sort((a,b)=>a.name.localeCompare(b.name));
        const host=document.getElementById('character-picker-list');if(!host)return;
        host.innerHTML=`<button class="char-picker-item" onclick="window.app.chooseCharacterGear('${kind}','${slot}','')">Empty slot</button>${rows.map(x=>`<button class="char-picker-item" data-id="${x.id}" onclick="window.app.chooseCharacterGear('${kind}','${slot}','${x.id}')"><img src="${this.getProxiedUrl(x.image)}" alt="" loading="lazy"><span><strong>${this.escapeHtml(x.name)}</strong><small>${this.escapeHtml(x.type)}${x.slot?' · '+x.slot:''}</small></span></button>`).join('')||'<p>No matches.</p>'}`;
    },
    characterSlot(kind,slot,record,extra=''){
        const view=`${kind==='weapon'?'weapon':kind==='armor'?'armor':kind==='spell'?'magic':'item'}-detail`;
        const detail=record?`<a class="char-info" href="#game=ds2&amp;view=${view}&amp;id=${record.id}" data-view="${view}" data-id="${record.id}" aria-label="Read ${this.escapeHtml(record.name)}">Details</a>`:'';
        return `<div class="char-slot"><button class="char-gear" onclick="window.app.openCharacterPicker('${kind}','${slot}')">${record?`<img src="${this.getProxiedUrl(record.image)}" alt=""><span>${this.escapeHtml(record.name)}</span>`:'<span>＋ Empty slot</span>'}</button>${detail}${extra}</div>`;
    },
    renderBuilder(){
        const host=document.getElementById('view-container'),d=this.data.character;
        if(!d?.levels){host.innerHTML='<h2 class="view-title">Character Lab</h2><p>Character parameter tables could not be loaded.</p>';return;}
        const s=this.characterState(),esc=x=>this.escapeHtml(x),selected=(a,b)=>a===b?'selected':'',opts=(records,v)=>`<option value="">None</option>${records.map(x=>`<option value="${esc(x.id)}" ${selected(x.id,v)}>${esc(x.name)}</option>`).join('')}`;
        host.innerHTML=`<div class="view-header"><h2 class="view-title">Character Lab</h2><p class="view-sub">Equip your build, level its attributes, and see each change.</p></div>${this.characterNotice?`<p class="data-note" role="status">${esc(this.characterNotice)}</p>`:''}<div class="character-layout"><div class="character-controls">
        <section class="char-panel"><div class="char-panel-heading"><h3>Attributes</h3><label>Starting class <select id="character-class" onchange="window.app.setCharacterClass(this.value)">${Object.keys(d.classes).map(c=>`<option ${selected(c,s.className)}>${c}</option>`).join('')}</select></label></div><div class="char-attributes">${Object.entries(ATTRS).map(([k,label])=>`<label><span>${label} <small id="char-effective-${k}"></small></span><input id="char-stat-${k}" type="number" min="${d.classes[s.className][k]}" max="99" value="${s.stats[k]}" oninput="window.app.setCharacterStat('${k}',this.value)"></label>`).join('')}</div><p class="fine-print">Purchased stats cannot go below the starting class. Equipment and temporary bonuses appear beside them.</p></section>
        <section class="char-panel"><h3>Weapons & shields</h3><p class="fine-print">Select one weapon in each hand. Clicking a slot also previews its attack. All six slots contribute to equipment weight.</p><div class="char-hand-grid">${['Right hand','Left hand'].map((hand,h)=>`<div><h4>${hand}</h4>${[0,1,2].map(i=>{const ix=h*3+i,slot=s.weapons[ix],w=this.data.weapons.find(x=>x.id===slot.id),e=this.smithEquipment(slot.id);return `<div class="char-weapon-slot"><label><input type="radio" name="char-active-${h}" value="${ix}" ${s.activeHands[h]===ix?'checked':''} onchange="window.app.setCharacterField('active',${ix})"> Slot ${i+1}</label>${this.characterSlot('weapon',ix,w,w?`<div class="char-upgrade"><label>Infusion<select onchange="window.app.setCharacterWeaponField(${ix},'path',this.value)">${Object.keys(e?.paths||{Normal:{}}).map(p=>`<option ${selected(p,slot.path)}>${p}</option>`).join('')}</select></label><label>Level<select onchange="window.app.setCharacterWeaponField(${ix},'level',this.value)">${Array.from({length:(e?.max_level||0)+1},(_,n)=>`<option value="${n}" ${selected(n,slot.level)}>+${n}</option>`).join('')}</select></label></div>`:'')}</div>`;}).join('')}</div>`).join('')}</div><label class="char-check"><input type="checkbox" ${s.twoHand?'checked':''} onchange="window.app.setCharacterField('twoHand',this.checked)"> Two-hand the active weapon</label><label>Applied weapon buff<select id="char-weapon-buff" onchange="window.app.setCharacterField('buff',this.value)"><option value="">None</option>${d.buffs.map(x=>`<option value="${esc(x.name)}" ${selected(x.name,s.buff)}>${esc(x.name)}</option>`).join('')}</select></label><p class="fine-print">Buff preview assumes it has been cast/applied. Spell requirements and weapon buff restrictions are checked; catalyst and casting resources are not consumed.</p></section>
        <section class="char-panel"><div class="char-panel-heading"><h3>Armor</h3><label>Equip a set<select aria-label="Equip armor set" onchange="window.app.equipCharacterSet(this.value)"><option value="">Choose a set</option>${this.data.armor.filter(x=>!x.slot&&/set$/i.test(x.name)&&!x.unavailable).map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('')}</select></label></div><div class="char-armor-grid">${ARMOR.map(k=>{const slot=s.armor[k],a=this.data.armor.find(x=>x.id===slot.id),max=d.armor[a?.id]?.max_level||a?.max_level||0;return `<div><h4>${k==='hands'?'Hands / gauntlets':k[0].toUpperCase()+k.slice(1)}</h4>${this.characterSlot('armor',k,a,a?`<label>Reinforcement<select onchange="window.app.setCharacterArmorLevel('${k}',this.value)">${Array.from({length:max+1},(_,n)=>`<option value="${n}" ${selected(n,slot.level)}>+${n}</option>`).join('')}</select></label>`:'')}</div>`;}).join('')}</div></section>
        <section class="char-panel"><h3>Rings · four slots</h3><div class="char-armor-grid">${s.rings.map((id,i)=>this.characterSlot('ring',i,this.data.items.find(x=>x.id===id))).join('')}</div><p class="fine-print">Another variant of the same ring replaces the equipped variant. Dragon rings share one family.</p></section>
        <details class="char-panel" open><summary>Quick items & active effects</summary><div class="char-quick-grid">${s.quick.map((id,i)=>this.characterSlot('quick',i,this.data.items.find(x=>x.id===id),id?`<button class="ds-btn" onclick="window.app.useCharacterQuick(${i})">Use / preview</button>`:'')).join('')}</div><label>Active body effect<select id="char-body-buff" onchange="window.app.setCharacterField('body',this.value)">${opts(this.characterBodyItems(),s.body)}</select></label><div class="char-inline"><label>Current HP<input type="number" min="0" value="${s.currentHp??this.characterTotals(s).availableHp}" onchange="window.app.setCharacterField('currentHp',this.value)"></label><label>Estus reinforcement<select onchange="window.app.setCharacterField('estus',this.value)">${Array.from({length:6},(_,n)=>`<option value="${n}" ${selected(n,s.estus)}>+${n}</option>`).join('')}</select></label></div><p class="fine-print">Equipping an item does not activate it or add weight. “Use” previews healing or activates a buff. Timed effects remain active in this lab until replaced or cleared; no inventory is consumed. Only one body effect is modeled at a time.</p></details>
        <details class="char-panel"><summary>Attuned magic</summary><div class="char-quick-grid">${s.spells.map((id,i)=>this.characterSlot('spell',i,this.data.magic.find(x=>x.id===id))).join('')}</div><p class="fine-print">Slot cost and spell requirements are checked. The listed casts on each local spell page depend on Attunement and equipment; this lab does not yet simulate casts remaining.</p></details>
        <details class="char-panel"><summary>Character conditions</summary><div class="char-attributes">${[['hollow','Hollowing (0–10)',10],['sin','Sin',100],['souls','Souls held',999999999],['ng','NG cycle (NG = 0)',10]].map(([k,label,max])=>`<label>${label}<input type="number" min="0" max="${max}" value="${s[k]}" onchange="window.app.setCharacterField('${k}',this.value)"></label>`).join('')}</div><label class="char-check"><input type="checkbox" ${s.pvp?'checked':''} onchange="window.app.setCharacterField('pvp',this.checked)"> PvP (Curved Nil bonus)</label><label class="char-check"><input type="checkbox" ${s.santierBroken?'checked':''} onchange="window.app.setCharacterField('santierBroken',this.checked)"> Santier’s Spear is broken (lighter moveset)</label></details>
        </div><aside class="character-results"><div id="character-result" aria-live="polite"></div></aside></div>
        <dialog id="character-picker" class="char-picker"><div class="char-panel-heading"><h3 id="character-picker-title">Choose equipment</h3><button class="ds-btn" onclick="document.getElementById('character-picker').close()">Close</button></div><input id="character-picker-search" type="search" placeholder="Search by name or type" oninput="window.app.filterCharacterPicker(this.value)"><div id="character-picker-list" class="char-picker-list"></div></dialog>`;
        this.updateCharacter();
    },
    updateCharacter(){
        const host=document.getElementById('character-result');if(!host)return;
        const s=this.characterState(),r=this.characterTotals(s),esc=x=>this.escapeHtml(x),fmt=n=>n==null?'Unknown':round(n),a=r.attack;
        for(const k of Object.keys(ATTRS)){const span=document.getElementById('char-effective-'+k);if(span)span.textContent=r.stats[k]===s.stats[k]?'':`→ ${r.stats[k]} effective`;const input=document.getElementById('char-stat-'+k);if(input&&document.activeElement!==input)input.value=s.stats[k];}
        const metric=(label,value,sub='')=>`<div class="char-metric"><span>${label}</span><strong>${value}</strong>${sub?`<small>${sub}</small>`:''}</div>`;
        const rows=a?DAMAGE.map(ch=>`<tr><th>${ch}</th><td>${fmt(a.base[ch])}</td><td>+${fmt(a.scaling[ch])}</td><td>+${fmt(a.equipment[ch])}</td><td>+${fmt(a.buff[ch]+(ch==='physical'?a.flynn:0))}</td><td>${a.missing.length?'—':a.attack[ch]}</td></tr>`).join(''):'';
        const delta=n=>`${n>0?'+':''}${round(n,2)}`;
        const upgrades=Object.entries(ATTRS).map(([k,label])=>{if(s.stats[k]>=99)return `<tr><th>${label}</th><td colspan="5">At maximum</td></tr>`;const next=this.characterTotals({...s,stats:{...s.stats,[k]:s.stats[k]+1}});return `<tr><th>${label}</th>${[next.availableHp-r.availableHp,next.stamina-r.stamina,next.load-r.load,next.poise-r.poise,a?.total!=null&&next.attack?.total!=null?next.attack.total-a.total:null].map(v=>`<td>${v===null?'—':delta(v)}</td>`).join('')}</tr>`;}).join('');
        const effects=r.effects.map(e=>{const numeric=[...Object.entries(e.stats||{}).map(([k,v])=>`${k.toUpperCase()} ${delta(v)}`),...Object.entries(e.defense||{}).map(([k,v])=>`${k} ${delta(v)}`),...['hp_mult','stamina_mult','load_mult'].filter(k=>e[k]).map(k=>`${k.replace('_mult','').replace('_',' ')} ${delta((e[k]-1)*100)}%`),...(e.poise?[`poise +${e.poise}`]:[]),...(e.regen?[`stamina recovery +${e.regen*100}%`]:[]),...(e.duration?[`${e.duration}s preview`]:[])];return `<li><strong>${esc(e.record?.name||'Effect')}</strong>${numeric.length?': '+esc(numeric.join(' · ')):''}${e.description?`<small>${esc(e.description)}</small>`:''}</li>`;}).join('');
        host.innerHTML=`<section class="char-panel char-status"><div class="char-panel-heading"><h3>Status</h3><span>Soul level <strong>${r.soulLevel}</strong></span></div><div class="char-metrics">${metric('HP limit',r.availableHp,`${r.hp} human maximum`)}${metric('Stamina',r.stamina)}${metric('Equip load',`${fmt(r.weight)} / ${fmt(r.load)}`,`${round(r.percent*100,2)}% · ${r.percent>=1.2?'Cannot roll':r.percent>=.7?'Heavy roll':'Normal roll'}`)}${metric('Poise',fmt(r.poise),'Armor + innate + rings')}${metric('Agility',esc(r.agility),`${r.rollFrames} roll / ${r.backstepFrames} backstep frames at 30 fps`)}${metric('Attunement',`${r.usedSlots} / ${r.slots}`,'Slots used / available')}${metric('Stamina recovery',`${round(r.regen,2)}/s`,'Community curve')}${metric('Next level',r.cost===null?'Maximum level':r.cost.toLocaleString(),'Souls required')}</div><p class="fine-print">Casting startup multiplier: ${round(r.castTime,3)}× (lower is faster). Current HP: ${Math.min(s.currentHp??r.availableHp,r.availableHp)}.</p></section>
        <section class="char-panel"><h3>${a?esc(a.weapon.name):'Active weapon'}</h3>${a?`<div class="char-active-weapon"><img src="${this.getProxiedUrl(a.weapon.image)}" alt=""><div><strong class="ar-total">${a.total===null?'—':a.total}</strong><p>Attack rating · ${esc(s.weapons[s.active].path)} +${s.weapons[s.active].level}</p><small>Menu rating ${a.menuTotal??'—'} · applied buffs and Flynn ${fmt(sum(Object.values(a.buff))+a.flynn)}</small></div></div><div class="table-scroll"><table class="ds-table char-ar-table"><thead><tr><th>Type</th><th>Base</th><th>Stats</th><th>Gear</th><th>Buff / Flynn</th><th>Total</th></tr></thead><tbody>${rows}</tbody></table></div><p>Poison ${a.auxiliary.poison} · Bleed ${a.auxiliary.bleed} (displayed buildup)</p>${r.damageMult!==1?`<p>Active damage multiplier: ${r.damageMult}×; incoming damage: ${r.damageTakenMult}×. These modify combat damage, not menu AR.</p>`:''}<p class="fine-print">Attack rating is before enemy defenses, attack animations, counters and critical multipliers. Buildup per hit also depends on moveset and target resistance. Ring and buff increments are shown separately.</p>${a.notes.map(n=>`<p class="data-note">${esc(n)}</p>`).join('')}`:'<p>Select a weapon slot to see its attack and scaling.</p>'}</section>
        <details class="char-panel"><summary>Defenses & armor contribution</summary>${this.facts(r.notes.some(n=>/subtotal|Defense penalty/.test(n))?'Known defense subtotal':'Status-screen defenses',r.defenses)}<p class="fine-print">Elemental and status resistances also have an invisible base of 100, excluded from these menu values. Physical defenses include attribute scaling; they are not damage-reduction percentages.</p><ul class="char-effect-list">${r.armorDetails.map(x=>`<li><strong>${esc(x.name)} +${x.level}</strong> · poise ${fmt(x.poise)} · physical scaling ${x.bonus===null?'unavailable':`+${x.bonus} per physical channel`}</li>`).join('')}</ul></details>
        <details class="char-panel" open><summary>Equipment & active effects</summary>${effects?`<ul class="char-effect-list">${effects}</ul>`:'<p>No equipment effects selected.</p>'}<p class="fine-print">Conditional effects such as low-HP damage, kills, headshots, fall damage, gender-dependent healing, spell damage and durability remain described on their local pages; only supported status and attack fields above are applied.</p></details>
        <details class="char-panel" open><summary>What one more level gives you</summary><div class="table-scroll"><table class="ds-table"><thead><tr><th>Attribute</th><th>HP</th><th>Stamina</th><th>Load</th><th>Poise</th><th>AR</th></tr></thead><tbody>${upgrades}</tbody></table></div></details>
        ${r.notes.length?`<section class="char-panel"><h3>Build checks</h3>${[...new Set(r.notes)].map(n=>`<p class="data-note">${esc(n)}</p>`).join('')}</section>`:''}
        <details class="char-panel"><summary>Calculation coverage & sources</summary><p>All weapon reinforcement rows use the same local data as Blacksmith. Character calculations use the wiki-linked combat parameter tables, including infusion affinity, Enchanted, Mundane and unique weapon conditions. Published references disagree on some values; this is a researched simulator, not a verified copy of the game executable.</p><p>Intermediate petrify/curse armor defenses, unmet-requirement penalties, spell casts remaining and conditional combat effects are not fully modeled. Unknown values are identified above.</p>${this.data.character.notes.map(n=>`<p class="fine-print">${esc(n)}</p>`).join('')}<p class="fine-print">Source: ${esc(this.data.character.source_url)} · ${esc(this.data.character.reference_version)}. Bundled locally; no connection is needed.</p></details>`;
    },
    // Legacy consumers now use the same exact per-level parameter model as the lab.
    computeAr(weapon,level,str,dex,intelligence=10,faith=10){
        if(!weapon)return null;const s={...this.characterState(),stats:{vgr:6,end:6,vit:6,atn:6,str,dex,adp:6,int:intelligence,fth:faith},weapons:Array.from({length:6},(_,i)=>({id:i?'':weapon.id,path:'Normal',level:i?0:level})),active:0,twoHand:false,rings:['','','',''],armor:Object.fromEntries(ARMOR.map(k=>[k,{id:'',level:0}])),spells:[],body:'',buff:'',hollow:0,sin:0,souls:1000000};
        const r=this.characterTotals(s),a=r.attack;if(!a)return null;return {base:sum(DAMAGE.map(k=>a.base[k])),bonus:sum(DAMAGE.map(k=>a.scaling[k])),total:a.potentialTotal,components:a.attack,bonuses:a.scaling,exact:true,strPct:this.characterWeaponParams(s.weapons[0],s).scaling.str[level],dexPct:this.characterWeaponParams(s.weapons[0],s).scaling.dex[level],magic:a.attack.magic,fire:a.attack.fire,ltn:a.attack.lightning,dark:a.attack.dark};
    }
};
