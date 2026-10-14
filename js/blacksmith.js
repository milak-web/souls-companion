/** Local blacksmith previews use individual published rows, never interpolation. */
export const blacksmithMethods = {
    smithEquipment(id) { return this.data.blacksmith?.equipment?.find(e => e.id === id); },
    smithRow(equipment, path, level) { return equipment?.paths?.[path]?.rows.find(r => r.level === Number(level)) || null; },
    smithQuote(equipment, from, to) {
        const materials={},steps=[];let reinforcementSouls=0,infusionSouls=0,complete=true;
        if(to.level<from.level)return {valid:false,reason:'Reinforcement cannot be reversed.'};
        for(let level=from.level+1;level<=to.level;level++) {
            const step=equipment?.steps?.[level];steps.push({level,...step});
            if(!step){complete=false;continue;}
            if(step.souls===null || step.souls===undefined)complete=false;else reinforcementSouls+=step.souls;
            if(!step.material || step.quantity===null || step.quantity===undefined)complete=false;else materials[step.material]=(materials[step.material] || 0)+step.quantity;
        }
        let infusion=null;
        if(from.path!==to.path) {
            infusion=to.path==='Normal' ? this.data.blacksmith.remove_infusion : equipment.paths[to.path];
            if(infusion?.stone)materials[infusion.stone]=(materials[infusion.stone] || 0)+1;
            if(infusion?.souls===null || infusion?.souls===undefined)complete=false;
            else infusionSouls=infusion.souls;
        }
        return {valid:true,materials,steps,reinforcementSouls,infusionSouls,infusion,complete,totalSouls:complete ? reinforcementSouls+infusionSouls : null};
    },
    smithState() {
        if(!this.smith)this.smith={weaponId:'longsword',currentPath:'Normal',currentLevel:0,path:'Normal',level:0,query:'',type:'',picker:false,...this.readSaved('ds2_blacksmith',{})};
        const s=this.smith,weapon=this.data.weapons.find(w=>w.id===s.weaponId) || this.data.weapons[0],e=this.smithEquipment(weapon.id);
        s.weaponId=weapon.id;
        const paths=Object.keys(e?.paths || {});
        if(!paths.includes(s.currentPath))s.currentPath=paths[0] || 'Normal';
        if(!paths.includes(s.path))s.path=paths[0] || 'Normal';
        const current=e?.paths?.[s.currentPath]?.rows || [],target=e?.paths?.[s.path]?.rows || [];
        if(!current.some(r=>r.level===s.currentLevel))s.currentLevel=current[0]?.level || 0;
        if(!target.some(r=>r.level===s.level) || s.level<s.currentLevel)s.level=target.find(r=>r.level>=s.currentLevel)?.level ?? s.currentLevel;
        return s;
    },
    saveSmith() { try {localStorage.setItem('ds2_blacksmith',JSON.stringify(this.smith));} catch {} },
    setSmith(field,value) {
        const s=this.smithState();
        if(!['currentPath','currentLevel','path','level','query','type','picker'].includes(field))return;
        s[field]=['currentLevel','level'].includes(field) ? Number(value) : value;
        this.smithState();this.saveSmith();
        if(field==='query'||field==='type'){this.renderSmithPicker();return;}
        this.renderBlacksmith();
    },
    setBlacksmithWeapon(id) {
        if(!this.data.weapons.some(w=>w.id===id))return;
        this.smithState();Object.assign(this.smith,{weaponId:id,currentPath:'Normal',currentLevel:0,path:'Normal',level:0,picker:false});
        this.blacksmithWeaponId=id;this.blacksmithLevel=0;this.saveSmith();this.renderBlacksmith();
    },
    setBlacksmithLevel(level) { this.setSmith('level',level);this.blacksmithLevel=this.smith.level; },
    applySmithPreview() {
        const s=this.smithState(),e=this.smithEquipment(s.weaponId);
        if(!this.smithRow(e,s.path,s.level))return;
        s.currentPath=s.path;s.currentLevel=s.level;this.saveSmith();this.renderBlacksmith();
    },
    smithValue(value) { return value===null || value===undefined ? '—' : Number(value).toLocaleString(undefined,{maximumFractionDigits:2}); },
    smithDelta(before,after) {
        if(before===null || before===undefined || after===null || after===undefined)return '—';
        const d=Math.round((after-before)*100)/100;return `${d>0?'+':''}${this.smithValue(d)}`;
    },
    smithMaterial(name,count) {
        const item=this.resolveByName(this.data.items,name);
        return `<div class="smith-material">${item ? `<img src="${this.escapeHtml(item.image)}" alt="">` : ''}<span>${this.namedReference(name)}</span><strong>× ${this.smithValue(count)}</strong></div>`;
    },
    renderSmithPicker() {
        const host=document.getElementById('smith-picker-results');if(!host)return;
        const s=this.smithState(),records=this.data.weapons.filter(w=>(!s.type || w.type===s.type) && (!s.query || [w.name,...(w.aliases || [])].some(n=>n.toLowerCase().includes(s.query.toLowerCase())))).sort((a,b)=>a.name.localeCompare(b.name));
        host.innerHTML=records.map(w=>`<button class="smith-choice ${w.id===s.weaponId?'selected':''}" data-weapon-id="${this.escapeHtml(w.id)}" onclick="window.app.setBlacksmithWeapon('${w.id}')"><img src="${this.getProxiedUrl(w.image)}" alt=""><span>${this.escapeHtml(w.name)}<small>${this.escapeHtml(w.type)}</small></span></button>`).join('') || '<p class="empty-msg">No matching equipment.</p>';
        const count=document.getElementById('smith-picker-count');if(count)count.textContent=`${records.length} equipment entries`;
    },
    renderBlacksmith() {
        const host=document.getElementById('view-container'),s=this.smithState(),w=this.data.weapons.find(w=>w.id===s.weaponId),e=this.smithEquipment(w.id);
        const paths=Object.keys(e?.paths || {}),before=this.smithRow(e,s.currentPath,s.currentLevel),after=this.smithRow(e,s.path,s.level),quote=this.smithQuote(e,{path:s.currentPath,level:s.currentLevel},{path:s.path,level:s.level});
        const label=p=>p==='Normal'?'Uninfused':p;
        const select=(field,title,options)=>`<label>${title}<select data-smith-field="${field}" onchange="window.app.setSmith('${field}',this.value)">${options.map(([v,l])=>`<option value="${this.escapeHtml(v)}" ${String(s[field])===String(v)?'selected':''}>${this.escapeHtml(l)}</option>`).join('')}</select></label>`;
        const channelLabels={physical:'Physical',magic:'Magic',fire:'Fire',lightning:'Lightning',dark:'Dark',poison:'Poison buildup',bleed:'Bleed buildup',petrify:'Petrification',curse:'Curse',str:'Strength',dex:'Dexterity'};
        const metricRows=(keys,object)=>keys.map(k=>`<tr><th>${channelLabels[k]}</th><td>${this.smithValue(before?.[object]?.[k])}</td><td>${this.smithValue(after?.[object]?.[k])}</td><td>${this.smithDelta(before?.[object]?.[k],after?.[object]?.[k])}</td></tr>`).join('');
        const comparisonHeader='<thead><tr><th>Stat</th><th>Current</th><th>Preview</th><th>Change</th></tr></thead>';
        const types=[...new Set(this.data.weapons.map(w=>w.type))].sort();
        const picker=s.picker ? `<section class="smith-picker"><div class="smith-picker-controls"><label>Find equipment<input type="search" data-smith-field="query" value="${this.escapeHtml(s.query)}" oninput="window.app.setSmith('query',this.value)" placeholder="Weapon, shield or spell tool"></label>${select('type','Equipment type',[['','All equipment'],...types.map(t=>[t,t])])}</div><p id="smith-picker-count" class="data-note"></p><div id="smith-picker-results"></div></section>` : '';
        const heading=`<div class="view-header"><h2 class="view-title">The Blacksmith</h2><p class="view-sub">Reinforce, infuse and compare your equipment.</p></div><section class="smith-equipment"><img src="${this.getProxiedUrl(w.image)}" alt="${this.escapeHtml(w.name)}"><div><h3>${this.escapeHtml(w.name)}</h3><p>${this.escapeHtml(w.type)} · ${e?.max_level ? `Maximum +${e.max_level}` : 'No reinforcement'}</p><div class="xlink-list">${this.detailLink('weapon-detail',w,'Equipment details')}<button class="ds-btn" data-smith-picker onclick="window.app.setSmith('picker',${!s.picker})">${s.picker?'Close selection':'Choose equipment'}</button></div></div></section>${picker}`;
        if(!paths.length) {
            host.innerHTML=`<div class="blacksmith-view">${heading}<section><p class="data-note">${this.escapeHtml(e?.unavailable_reason || 'Published reinforcement tables are unavailable.')}</p></section></div>`;
            if(s.picker)this.renderSmithPicker();return;
        }
        const controls=`<div class="smith-controls smith-plan-controls"><fieldset><legend>Current equipment</legend>${select('currentPath','Current infusion',paths.map(p=>[p,label(p)]))}${select('currentLevel','Current level',e.paths[s.currentPath].rows.map(r=>[r.level,`+${r.level}`]))}</fieldset><fieldset><legend>Preview result</legend>${select('path','Target infusion',paths.map(p=>[p,label(p)]))}${select('level','Target level',e.paths[s.path].rows.filter(r=>r.level>=s.currentLevel).map(r=>[r.level,`+${r.level}`]))}</fieldset></div>`;
        const cost=`<section class="smith-cost" data-smith-cost><h3>Materials and souls needed</h3><p>${this.escapeHtml(label(s.currentPath))} +${s.currentLevel} → ${this.escapeHtml(label(s.path))} +${s.level}</p><div class="smith-soul-total">${quote.totalSouls===null?'Incomplete cost data':this.smithValue(quote.totalSouls)+' souls'}</div>${Object.entries(quote.materials).map(([name,n])=>this.smithMaterial(name,n)).join('') || '<p>No materials needed for this selection.</p>'}<div class="stat-line"><span>Reinforcement fee</span><strong>${this.smithValue(quote.reinforcementSouls)} souls${!quote.complete?' (known subtotal)':''}</strong></div><div class="stat-line"><span>Infusion fee</span><strong>${quote.infusion?.souls===null?'Not verified':this.smithValue(quote.infusionSouls)+' souls'}</strong></div>${!quote.complete?'<p class="data-note">Some costs are not recorded. The displayed materials and fees are a known subtotal, not the complete bill.</p>':''}${w.type==='Pyromancy Flame' ? `<p>Reinforcement by ${this.namedReference('Rosabeth of Melfia')} or ${this.namedReference('Carhillion of the Fold')}.</p>` : ''}<p class="data-note">Service fees only; buying materials is additional. Switching infusion needs the new stone once. Removing it uses a Palestone. Reinforcement levels are retained.</p><button class="ds-btn" onclick="window.app.applySmithPreview()" ${!after?'disabled':''}>Use result as current preview</button><p class="fine-print">Saves your plan locally.</p></section>`;
        const currentEffective=this.characterScaling(w.id,s.currentPath,s.currentLevel),targetEffective=this.characterScaling(w.id,s.path,s.level);
        const scaling=`<section class="smith-scaling"><h3>Scaling at this level</h3><table class="ds-table"><thead><tr><th>Channel</th><th>Current</th><th>Preview</th></tr></thead><tbody>${['str','dex','magic','fire','lightning','dark'].map(k=>`<tr><th>${channelLabels[k]}</th><td>${this.escapeHtml(before?.scaling?.[k] || '?')}${currentEffective?.[k]!==undefined && currentEffective?.[k]!==null && before?.scaling?.[k]!=='-' ? ` (${this.smithValue(currentEffective[k])}%)` : ''}</td><td>${this.escapeHtml(after?.scaling?.[k] || '?')}${targetEffective?.[k]!==undefined && targetEffective?.[k]!==null && after?.scaling?.[k]!=='-' ? ` (${this.smithValue(targetEffective[k])}%)` : ''}</td></tr>`).join('')}${['poison','bleed'].map(k=>`<tr><th>${channelLabels[k]} scaling</th><td>${before?.aux_scaling_percent?.[k]!==undefined && before?.aux_scaling_percent?.[k]!==null ? this.smithValue(before.aux_scaling_percent[k])+'%' : '—'}</td><td>${after?.aux_scaling_percent?.[k]!==undefined && after?.aux_scaling_percent?.[k]!==null ? this.smithValue(after.aux_scaling_percent[k])+'%' : '—'}</td></tr>`).join('')}${s.path==='Mundane' || s.path==='Enchanted' ? `<tr><th>Special physical scaling</th><td>${s.currentPath==='Mundane'?'Lowest attribute':s.currentPath==='Enchanted'?'Intelligence':'—'}</td><td>${s.path==='Mundane'?'Lowest attribute':'Intelligence (see effective coefficients below)'}</td></tr>` : ''}</tbody></table><p class="data-note">Letters are the published equipment grades. Percentages use the same effective combat parameters as Character Lab, including infusion affinity. The source warning identifies conflicting references; grades alone do not determine the attribute bonus.</p><details><summary>Attribute requirements</summary>${this.facts('Requirements',w.requirements,{str:'Strength',dex:'Dexterity',int:'Intelligence',fth:'Faith'})}</details></section>`;
        const infusionAdvice={Enchanted:'Enchanted adds a separate Intelligence bonus to physical attack. The character parameter table supplies this separate coefficient; a dash in the normal Magic channel does not mean Intelligence has no effect.',Mundane:'Mundane uses the lowest of all nine character attributes for its special physical bonus. Its displayed Strength and Dexterity grades do not describe that bonus.'}[s.path];
        const benefit=`<section class="smith-benefit"><h3>Attack and status changes</h3>${e.variant_note?`<p class="data-note">${this.escapeHtml(e.variant_note)}</p>`:""}${this.data.character?.source_disagreements?.[w.id]?.[s.path]?`<p class="data-note">${this.escapeHtml(this.data.character.source_disagreements[w.id][s.path])}</p>`:""}<div class="table-scroll"><table class="ds-table" data-smith-benefit>${comparisonHeader}<tbody>${metricRows(['physical','magic','fire','lightning','dark'],'attack')}${metricRows(['poison','bleed'],'auxiliary')}</tbody></table></div><p class="data-note">Attack values are base equipment attack before your character's attribute bonus. Poison and bleed are buildup, not hit damage. Damage dealt depends on the attack and target defenses.</p>${infusionAdvice ? `<p class="data-note">${infusionAdvice}</p>` : ''}${!after || Object.values(after.attack).some(v=>v===null)?'<p class="data-note">Some attack values in this exact infusion/level row are unavailable. No estimated result is substituted.</p>':''}</section>`;
        const block=(after?.block_reduction || after?.status_reduction || after?.stability!==undefined)?`<details class="smith-extra"><summary>Blocking and resistances</summary><div class="table-scroll"><table class="ds-table">${comparisonHeader}<tbody>${metricRows(['physical','magic','fire','lightning','dark'],'block_reduction')}${metricRows(['poison','bleed','petrify','curse'],'status_reduction')}<tr><th>Stability</th><td>${this.smithValue(before?.stability)}</td><td>${this.smithValue(after?.stability)}</td><td>${this.smithDelta(before?.stability,after?.stability)}</td></tr></tbody></table></div><p class="data-note">Blocking values are percentages. Missing values are left blank; they are not copied from the uninfused weapon.</p></details>`:'';
        const levels=`<details class="smith-extra"><summary>All reinforcement levels · ${this.escapeHtml(label(s.path))}</summary><div class="table-scroll"><table class="ds-table"><thead><tr><th>Level</th><th>Physical</th><th>Magic</th><th>Fire</th><th>Lightning</th><th>Dark</th><th>Poison</th><th>Bleed</th><th>Material for step</th><th>Step fee</th></tr></thead><tbody>${e.paths[s.path].rows.map(r=>{const st=e.steps[r.level];return `<tr class="${r.level===s.level?'current':''}"><td><button class="ds-btn" ${r.level<s.currentLevel?'disabled':''} onclick="window.app.setBlacksmithLevel(${r.level})">+${r.level}</button></td>${['physical','magic','fire','lightning','dark'].map(k=>`<td>${this.smithValue(r.attack[k])}</td>`).join('')}<td>${this.smithValue(r.auxiliary?.poison)}</td><td>${this.smithValue(r.auxiliary?.bleed)}</td><td>${r.level===0?'—':st?.material?`${this.smithValue(st.quantity)} × ${this.escapeHtml(st.material)}`:'Not verified'}</td><td>${r.level===0?'—':this.smithValue(st?.souls)}</td></tr>`;}).join('')}</tbody></table></div></details>`;
        const pathCompare=`<details class="smith-extra"><summary>Compare all infusions at +${s.level}</summary><div class="table-scroll"><table class="ds-table"><thead><tr><th>Infusion</th><th>Physical</th><th>Magic</th><th>Fire</th><th>Lightning</th><th>Dark</th><th>Poison</th><th>Bleed</th></tr></thead><tbody>${paths.map(path=>{const r=this.smithRow(e,path,s.level);return `<tr><th><button class="ds-btn" onclick="window.app.setSmith('path','${path}')">${label(path)}</button></th>${['physical','magic','fire','lightning','dark'].map(k=>`<td>${this.smithValue(r?.attack[k])}</td>`).join('')}<td>${this.smithValue(r?.auxiliary?.poison)}</td><td>${this.smithValue(r?.auxiliary?.bleed)}</td></tr>`;}).join('')}</tbody></table></div></details>`;
        host.innerHTML=`<div class="blacksmith-view">${heading}${controls}<div class="smith-result-grid">${benefit}${cost}${scaling}</div>${this.characterScaling(w.id,s.path,s.level)?`<details class="smith-extra"><summary>Effective scaling coefficients from combat parameters</summary>${this.facts("Preview at +"+s.level+" (%)",this.characterScaling(w.id,s.path,s.level),{str:"Strength",dex:"Dexterity",magic:"Magic",fire:"Fire",lightning:"Lightning",dark:"Dark",poison:"Poison",bleed:"Bleed",enchanted:"INT → physical (Enchanted)",mundane:"Lowest attribute (Mundane)"})}<p class="data-note">These coefficients include infusion affinity and preserve parameter precision. The published percentages beside equipment grades above may be rounded. Unique weapon conditions can multiply scaling; use Character Lab to set hollowing, souls held, sin and buffs.</p></details>`:""}${pathCompare}${levels}${block}<details class="smith-extra"><summary>Effects, infusion rules and smith services</summary><p>${this.escapeHtml(w.special_effect || '')}</p><p>${this.escapeHtml(w.mechanics_notes || '')}</p><p><strong>Temporary buffs:</strong> ${this.escapeHtml(w.buffable || 'Not verified')}. Resins and spell buffs are separate from permanent infusion.</p><p>Infusion is offered by ${this.namedReference('Steady Hand McDuff')} after giving him the ${this.namedReference('Dull Ember')}. The ember is in Iron Keep in original DSII, and near the Tower Apart bonfire in the Lost Bastille in Scholar of the First Sin.</p><p>Blacksmiths can also repair broken equipment; reinforcement and infusion previews here do not simulate durability loss.</p><p>Ordinary reinforcement is available from blacksmiths without the Dull Ember. Standard reinforcement uses Titanite to +10; special equipment uses Twinkling Titanite to +5; boss equipment uses Petrified Dragon Bone to +5. Pyromancy Flames use Fire Seeds to +10 through ${this.namedReference('Rosabeth of Melfia')} or ${this.namedReference('Carhillion of the Fold')}.</p>${e.infusion_note ? `<p><strong>Infusion availability:</strong> ${this.escapeHtml(e.infusion_note)}</p>` : ''}<p>Only paths with individual weapon tables appear. A missing path is not proof that the game forbids it. Shields do not support Raw, Enchanted or Mundane; bows and crossbows do not support Poison or Bleed; hammers do not support Bleed.</p><p>Poison and bleed activate after sufficient buildup against the target's resistance. These tables give base buildup; Character Lab adds the attribute bonus. Per-hit buildup also depends on the attack and target resistance.</p></details>${this.referenceSection({source_url:e.source_url,additional_sources:[this.data.character?.source_url,e.parameter_source,this.data.blacksmith.source_url,this.data.blacksmith.remove_infusion.source_url,...[before,after].map(r=>r?.coefficient_source).filter(Boolean)]})}</div>`;
        if(s.picker)this.renderSmithPicker();
    }
};
