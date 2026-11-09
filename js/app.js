import {referenceMethods} from './reference-facts.js?v=2.3.0';
import { blacksmithMethods } from './blacksmith.js?v=2.1.0';
import { characterMethods } from './character.js?v=2.1.0';
/**
 * DSII Companion Codex - Core Logic
 */

const OFFLINE_PLACEHOLDER = `data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22400%22%20height%3D%22400%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22%231a1a1a%22/%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20font-family%3D%22serif%22%20font-size%3D%2224%22%20fill%3D%22%23c5a059%22%20text-anchor%3D%22middle%22%20dominant-baseline%3D%22middle%22%3EDARK%20SOULS%20II%3C/text%3E%3C/svg%3E`;
const DATA_VERSION = '2.3.0';

export class CodexApp {
    constructor() {
        this.data = {
            enemies: [],
            areas: [],
            bosses: [],
            weapons: [],
            items: [],
            magic: [],
            covenants: [],
            quests: [],
            npcs: [],
            armor: []
        };
        this.catalogFilters = this.readSaved('ds2_catalog_filters', {});
        this.currentView = 'home';
        this.currentParams = {};
        this.dropTargetCache = new Map();
        this.favorites = this.readSaved('ds2_favorites', []);
        this.questProgress = this.readSaved('ds2_quest_progress', {});
        // Blacksmith / character-builder state.
        this.blacksmithWeaponId = null;
        this.blacksmithLevel = 0;

        this.loading = this.init();
    }

    readSaved(key, fallback) {
        try {
            const value = JSON.parse(localStorage.getItem(key));
            return value && (Array.isArray(fallback) ? Array.isArray(value) : typeof value === 'object' && !Array.isArray(value)) ? value : fallback;
        } catch { return fallback; }
    }

    toggleQuestStep(questId, stepIndex) {
        if (!this.questProgress[questId]) {
            this.questProgress[questId] = [];
        }
        const index = this.questProgress[questId].indexOf(stepIndex);
        if (index === -1) {
            this.questProgress[questId].push(stepIndex);
        } else {
            this.questProgress[questId].splice(index, 1);
        }
        localStorage.setItem('ds2_quest_progress', JSON.stringify(this.questProgress));
        this.renderQuests();
    }

    toggleFavorite(id, type) {
        const index = this.favorites.findIndex(f => f.id === id && f.type === type);
        if (index === -1) {
            this.favorites.push({ id, type });
        } else {
            this.favorites.splice(index, 1);
        }
        localStorage.setItem('ds2_favorites', JSON.stringify(this.favorites));
        this.renderView(this.currentView, this.currentParams); // Keep the current detail selection
    }

    isFavorite(id, type) {
        return this.favorites.some(f => f.id === id && (!type || f.type === type));
    }

    normalizeImageKey(value) {
        return String(value || '')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, ' ')
            .trim();
    }

    findEntityForImage(type, name) {
        const target = this.normalizeImageKey(name);
        if (!target) {
            return null;
        }

        const collections = {
            enemy: this.data.enemies,
            boss: this.data.bosses,
            area: this.data.areas,
            weapon: this.data.weapons,
            item: this.data.items,
            covenant: this.data.covenants,
            armor: this.data.armor,
            quest: this.data.quests
        };

        const collection = collections[type] || [];
        // Exact match only. The old fuzzy `.includes()` test let a short name
        // match an unrelated entity and drag that entity's artwork in with it.
        return collection.find(entity => {
            const entityName = this.normalizeImageKey(entity.name);
            const entityTitle = this.normalizeImageKey(entity.title);
            return entityName === target || entityTitle === target;
        }) || null;
    }

    handleImageError(img) {
        img.onerror = null;
        img.classList.add('error');
        img.src = OFFLINE_PLACEHOLDER;
    }

    getProxiedUrl(url) {
        // A missing local asset remains local; remote images are never requested.
        return typeof url === 'string' && url.trim() && !/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(url.trim()) ? url : OFFLINE_PLACEHOLDER;
    }

    async init() {
        console.log('Codex initializing...');
        await this.loadData();

        this.ready = true;
    }

    async loadData() {
        try {
            const dataUrl = (name) => `database/${name}?v=${DATA_VERSION}`;
            const [enemiesRes, areasRes, covenantsRes, weaponsRes, questsRes, mechanicsRes, itemsRes, bossesRes, npcsRes, armorRes] = await Promise.all([
                fetch(dataUrl('enemies.json')),
                fetch(dataUrl('areas.json')),
                fetch(dataUrl('covenants.json')),
                fetch(dataUrl('weapons.json')),
                fetch(dataUrl('quests.json')),
                fetch(dataUrl('mechanics.json')),
                fetch(dataUrl('items.json')),
                fetch(dataUrl('bosses.json')),
                fetch(dataUrl('npcs.json')),
                fetch(dataUrl('armor.json'))
            ]);

            this.data.enemies = await enemiesRes.json();
            this.data.areas = await areasRes.json();
            this.data.covenants = await covenantsRes.json();
            this.data.weapons = await weaponsRes.json();
            this.data.quests = await questsRes.json();
            this.data.mechanics = await mechanicsRes.json();
            this.data.items = await itemsRes.json();
            this.data.magic = await this.loadAux('magic.json', []);
            this.data.npcs = await npcsRes.json();
            this.data.armor = await armorRes.json();

            // Optional data files. These are loaded separately so a missing one
            // cannot reject the Promise.all above and blank out the whole app.
            this.data.upgrades = await this.loadAux('upgrades.json', []);
            this.data.blacksmith = await this.loadAux('blacksmith.json', {equipment:[],remove_infusion:{}});
            this.data.scalingConstants = await this.loadAux('scaling.json', null);
            this.data.character = await this.loadAux('character.json', null);
            
            // Bosses now load from their own catalog file. The old despawn-derived
            // filter is kept only as a fallback and made string-safe, so a record
            // without `despawn` can no longer throw during load.
            this.data.bosses = await bossesRes.json();
            if (!Array.isArray(this.data.bosses) || !this.data.bosses.length) {
                this.data.bosses = this.data.enemies.filter(e => typeof e.despawn === 'string' && e.despawn.includes('Boss'));
            }
            this.data.redirects = await this.loadAux('redirects.json', {});
            this.data.npcRedirects = await this.loadAux('npc_redirects.json', {});
            this.data.areaRedirects = await this.loadAux('area_redirects.json', {});
            this.data.armorRedirects = await this.loadAux('armor_redirects.json', {});
            this.data.articles = await this.loadAux('articles.json', []);
            this.data.categoryRedirects = await this.loadAux('category_redirects.json', {});
            this.favorites = this.favorites.map(f => ({...f, type: f.type === 'weapon' && ['binoculars','eternal-sanctum-key','iron-key','scorching-iron-scepter'].includes(f.id) ? 'item' : f.type, id: f.type === 'enemy' ? this.data.redirects[f.id] || f.id : f.type === 'armor' ? this.data.armorRedirects[f.id] || f.id : f.id}));
            this.favorites=this.favorites.map(f=>{const moved=f.type==='enemy' && this.data.categoryRedirects?.['enemy-detail']?.[f.id];return moved ? {...f,id:moved.id,type:'npc'} : f;});
            this.favorites = this.favorites.map(f => f.type === 'item' && this.data.magic.some(m => m.id === f.id) ? {...f, type:'magic'} : f);
            this.favorites=this.favorites.map(f=>f.type==='npc'?{...f,id:this.data.npcRedirects[f.id] || f.id}:f).filter((f,i,all)=>all.findIndex(other=>other.id===f.id && other.type===f.type)===i);
            try {localStorage.setItem('ds2_favorites', JSON.stringify(this.favorites));} catch {}
            console.log('Data loaded:', this.data);
        } catch (error) {
            console.error('Failed to load data:', error);
        }
    }

    async loadAux(name, fallback) {
        try {
            const res = await fetch(`database/${name}?v=${DATA_VERSION}`);
            if (!res.ok) return fallback;
            return await res.json();
        } catch {
            return fallback;
        }
    }

    // --- blacksmith / attack rating maths -----------------------------------
    // Legacy upgrade metadata lookup. Character calculations live in character.js.
    upgradeFor(weapon) {
        if (!weapon || !Array.isArray(this.data.upgrades)) return null;
        const key = this.normalizeImageKey(weapon.name);
        return this.data.upgrades.find(u => u.id === weapon.id)
            || this.data.upgrades.find(u => this.normalizeImageKey(u.name) === key)
            || null;
    }

    // Stat bonus from the community BNS table. Returns 0 when the table is
    // missing so the UI degrades to base AR instead of inventing a curve.
    statBonus(stat, value, fallbackGain = 0) {
        const table = this.data.scalingConstants
            && this.data.scalingConstants.bns
            && this.data.scalingConstants.bns[stat];
        if (!table) return fallbackGain;
        const v = Math.max(1, Math.min(99, Math.round(Number(value) || 1)));
        const hit = table[String(v)];
        return hit === undefined ? fallbackGain : Number(hit);
    }

    hasBnsTables() {
        const b = this.data.scalingConstants && this.data.scalingConstants.bns;
        return !!(b && b.STR && b.DEX);
    }

    restoreRoute() {
        const route = new URLSearchParams(location.hash.slice(1));
        this.renderView(route.get('view') || 'home', { id: route.get('id') || undefined, ...(route.get('ids') ? {ids: route.get('ids').split(',')} : {}) });
    }

    escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
    }

    updateStats() {
        const enemyCount = document.querySelector('.stat-card:nth-child(1) .count');
        const areaCount = document.querySelector('.stat-card:nth-child(2) .count');
        const bossCount = document.querySelector('.stat-card:nth-child(3) .count');

        if (enemyCount) enemyCount.textContent = this.data.enemies.length;
        if (areaCount) areaCount.textContent = this.data.areas.length;
        if (bossCount) bossCount.textContent = this.data.bosses.length;
    }

    renderView(viewName, params) {
        if (new URLSearchParams(location.hash.slice(1)).get('game') !== 'ds2') return;
        params = params || (viewName === this.currentView ? this.currentParams : {});
        const moved=this.data.categoryRedirects?.[viewName]?.[params.id];
        if(moved){viewName=moved.view;params={...params,id:moved.id};}
        if(viewName==='item-detail' && ['carvings','weapon-buff'].includes(params.id)) viewName='article-detail';
        if(viewName==='item-detail' && params.id==='crown-of-the-ivory-king-helm') viewName='armor-detail';
        if (viewName === 'weapon-detail' && ['binoculars','eternal-sanctum-key','iron-key','scorching-iron-scepter'].includes(params.id)) viewName = 'item-detail';
        if (viewName === 'armor-detail' && this.data.armorRedirects?.[params.id]) params = {...params, id: this.data.armorRedirects[params.id]};
        if (viewName === 'area-detail' && this.data.areaRedirects?.[params.id]) params = {...params, id: this.data.areaRedirects[params.id]};
        if (viewName === 'enemy-detail' && this.data.redirects?.[params.id]) params = {...params, id: this.data.redirects[params.id]};
        if (viewName === 'npc-detail' && this.data.npcRedirects?.[params.id]) params = {...params, id: this.data.npcRedirects[params.id]};
        this.currentView = viewName;
        this.currentParams = {...params};
        const route = new URLSearchParams({game: 'ds2', view: viewName});
        if (params.id) route.set('id', params.id);
        if (params.ids?.length) route.set('ids', params.ids.join(','));
        const hash = '#' + route.toString();
        if (location.hash !== hash) history.pushState(null, '', hash);
        const section = {'enemy-detail': this.data.bosses.some(b => b.id === params.id) ? 'bosses' : 'enemies', 'magic-detail':'magic', 'item-detail':'items', 'weapon-detail':'weapons', 'armor-detail':'armor', 'area-detail':'areas', 'npc-detail':'npcs'}[viewName] || viewName;
        document.querySelectorAll('.sidebar nav li').forEach(li => li.classList.toggle('active', li.dataset.tab === section));
        const container = document.getElementById('view-container');
        container.innerHTML = '';

        switch (viewName) {
            case 'home': this.renderHome(); break;
            case 'enemies': this.renderEnemyList(); break;
            case 'enemy-detail': this.renderEnemyDetail(params.id); break;
            case 'areas': this.renderAreaList(); break;
            case 'area-detail': this.renderAreaDetail(params.id); break;
            case 'bosses': this.renderBossList(); break;
            case 'weapons': this.renderWeaponList(); break;
            case 'weapon-detail': this.renderWeaponDetail(params.id); break;
            case 'weapon-compare': this.renderWeaponComparison(params.ids); break;
            case 'magic': this.renderItemList('magic'); break;
            case 'magic-detail': this.renderItemDetail(params.id, 'magic'); break;
            case 'items': this.renderItemList(); break;
            case 'item-detail': this.renderItemDetail(params.id); break;
            case 'covenants': this.renderCovenants(); break;
            case 'npcs': this.renderNpcList(); break;
            case 'npc-detail': this.renderNpcDetail(params.id); break;
            case 'article-detail': this.renderArticleDetail(params.id); break;
            case 'armor': this.renderArmorList(); break;
            case 'armor-detail': this.renderArmorDetail(params.id); break;
            case 'blacksmith': this.renderBlacksmith(); break;
            case 'builder': this.renderBuilder(); break;
            case 'quests': this.renderQuests(); break;
            case 'mechanics': this.renderMechanics(); break;
            case 'favorites': this.renderFavorites(); break;
            default:
                container.innerHTML = `<div class="placeholder"><h2>${viewName.toUpperCase()} View</h2><p>Coming soon.</p></div>`;
        }
        if (!container.innerHTML.trim()) {
            container.innerHTML = '<p class="empty-msg">This entry could not be found. Choose a category or use search.</p>';
        }
        this.renderWikiReference(viewName, params, container);
        container.querySelector('.detail-view')?.insertAdjacentHTML('afterbegin', '<div class="detail-navigation"><button class="ds-btn" onclick="history.back()">Back</button></div>');
        document.querySelector('.content-area').scrollTop = 0;
    }

    renderHome() {
        const container = document.getElementById('view-container');
        container.innerHTML = `
            <div class="home-view">
                <div class="hero">
                    <h2>Welcome, Bearer of the Curse</h2>
                    <p>Your ultimate offline companion for Drangleic.</p>
                </div>
                
                <div class="dashboard-grid">
                    <div class="stat-card">
                        <h3>Enemies</h3>
                        <div class="count">${this.data.enemies.length}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Items</h3>
                        <div class="count">${this.data.items.length}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Magic</h3><div class="count">${this.data.magic.length}</div>
                    </div><div class="stat-card">
                        <h3>Bosses</h3>
                        <div class="count">${this.data.bosses.length}</div>
                    </div>
                </div>

                <div class="recent-section">
                    <h3>Recently Viewed</h3>
                    <div class="recent-list" id="recent-views">
                        <p class="empty-msg">No history yet.</p>
                    </div>
                </div>
            </div>
        `;
    }


    catalogConfig(category) {
        const damage=['physical','magic','fire','lightning','dark'];
        const resistance=[...damage,'strike','slash','thrust','poison','bleed','petrify','curse','poise'];
        const labels={physical:'Physical defense',magic:'Magic defense',fire:'Fire defense',lightning:'Lightning defense',dark:'Dark defense',strike:'Strike defense',slash:'Slash defense',thrust:'Thrust defense',poison:'Poison resistance',bleed:'Bleed resistance',petrify:'Petrification resistance',curse:'Curse resistance',poise:'Poise'};
        const stats=category==='armor' ? resistance.map(k=>[k,labels[k]]) : category==='weapons' ? [...damage.map(k=>[k,`${k[0].toUpperCase()+k.slice(1)} attack`]),...['str','dex','magic','fire','lightning','dark'].map(k=>['scale_'+k,`${{str:'Strength',dex:'Dexterity',magic:'Magic',fire:'Fire',lightning:'Lightning',dark:'Dark'}[k]} scaling`]),['poison','Poison buildup'],['bleed','Bleed buildup']] : ['enemies','bosses'].includes(category) ? [['hp','HP'],['souls','Souls']] : category==='magic' ? [['int_required','Intelligence required'],['faith_required','Faith required'],['slots','Attunement slots'],['uses_min','Minimum casts']] : category==='items' ? [['soul_value','Souls when consumed']] : category==='areas' ? [['bonfires','Bonfire count']] : [];
        if(['armor','weapons'].includes(category))stats.push(['weight','Weight']);
        return {stats,typeField:{armor:'slot',weapons:'type',items:'type',magic:'type',areas:'region',npcs:'role'}[category],typeLabel:{armor:'Equipment',weapons:'Weapon type',items:'Item type',magic:'Magic school',areas:'Region',npcs:'Role'}[category] || 'Type'};
    }

    catalogState(category) {
        return {query:'',type:'',sort:'name',order:'asc',basis:'base',channel:'',weakness:'',area:'',maxWeight:'',...(this.catalogFilters[category] || {})};
    }

    setCatalogFilter(category, field, value) {
        const state=this.catalogState(category);
        state[field]=value;
        if(field==='sort')state.order=value==='name'||value==='weight' ? 'asc' : 'desc';
        this.catalogFilters[category]=state;
        try {localStorage.setItem('ds2_catalog_filters',JSON.stringify(this.catalogFilters));} catch {}
        const active=document.activeElement, key=active?.dataset.catalogField, selection=active?.selectionStart;
        this.renderView(category);
        const control=document.querySelector(`[data-catalog-field="${key}"]`);
        if(control){control.focus();if(typeof selection==='number' && control.type==='search')control.setSelectionRange(selection,selection);}
    }

    resetCatalogFilters(category) {
        delete this.catalogFilters[category];
        try {localStorage.setItem('ds2_catalog_filters',JSON.stringify(this.catalogFilters));} catch {}
        this.renderView(category);
    }

    catalogNumber(value) {
        if(value===null||value===undefined||value==='')return null;
        if(typeof value==='number')return Number.isFinite(value) ? value : null;
        return /^\d+(?:,\d{3})*(?:\.\d+)?$/.test(String(value).trim()) ? Number(String(value).replaceAll(',','')) : null;
    }

    catalogMetric(category, record, metric, basis='base') {
        if(category==='armor') {
            if(record.pieces?.length) {
                const members=record.pieces.map(id=>this.data.armor.find(a=>a.id===id));
                const values=members.map(a=>a ? this.catalogMetric(category,a,metric,basis) : null);
                return values.every(v=>v!==null) ? values.reduce((a,b)=>a+b,0) : null;
            }
            return this.catalogNumber(record[basis==='max'?'defenses_max':'defenses_base']?.[metric]);
        }
        if(category==='weapons') {
            const row=basis==='max' ? (record.upgrade_stats || []).filter(r=>r.path==='Normal').sort((a,b)=>b.level-a.level)[0] : null;
            if(basis==='max' && !row)return null;
            if(metric.startsWith('scale_')) {
                const grade=(row?.scaling || record.scaling)?.[metric.slice(6)];
                return {S:6,A:5,B:4,C:3,D:2,E:1,'-':0}[grade] ?? null;
            }
            if(['physical','magic','fire','lightning','dark'].includes(metric))return this.catalogNumber((row?.attack || record.attack)?.[metric]);
            if(['poison','bleed'].includes(metric))return basis==='max' ? null : this.catalogNumber(record.auxiliary?.[metric]);
        }
        if(category==='magic')return this.catalogNumber(record.filter_stats?.[metric]);
        if(category==='areas' && metric==='bonfires')return record.bonfires?.length ?? null;
        return this.catalogNumber(record[metric]);
    }

    catalogResults(category, records) {
        const state=this.catalogState(category);
        const result=records.filter(r=>{
            if(state.query && ![r.name,...(r.aliases || [])].some(n=>String(n).toLowerCase().includes(state.query.toLowerCase())))return false;
            const type=category==='armor' ? r.pieces?.length ? 'set' : r.slot || 'unverified' : r[this.catalogConfig(category).typeField] || 'unclassified';
            if(state.type && state.type!==type)return false;
            if(state.area && !(r.areas || []).includes(state.area))return false;
            if(state.weakness && r.weaknesses?.[state.weakness]!=='weak')return false;
            if(state.channel && !(this.catalogMetric(category,r,state.channel,state.basis)>0))return false;
            if(state.maxWeight!=='' && !(this.catalogMetric(category,r,'weight',state.basis)!==null && this.catalogMetric(category,r,'weight',state.basis)<=Number(state.maxWeight)))return false;
            return true;
        });
        result.sort((a,b)=>{
            if(state.sort==='name')return (state.order==='desc'?-1:1)*a.name.localeCompare(b.name);
            const x=this.catalogMetric(category,a,state.sort,state.basis),y=this.catalogMetric(category,b,state.sort,state.basis);
            if(x===null||y===null)return x===y ? a.name.localeCompare(b.name) : x===null ? 1 : -1;
            return (state.order==='desc'?-1:1)*(x-y) || a.name.localeCompare(b.name);
        });
        return result;
    }

    renderCatalogControls(category, records) {
        const state=this.catalogState(category),config=this.catalogConfig(category),result=this.catalogResults(category,records);
        const select=(field,label,options)=>`<label>${label}<select data-catalog-field="${field}" onchange="window.app.setCatalogFilter('${category}','${field}',this.value)">${options.map(([value,text])=>`<option value="${this.escapeHtml(value)}" ${state[field]===value?'selected':''}>${this.escapeHtml(text)}</option>`).join('')}</select></label>`;
        const types=category==='armor' ? [['set','Armor sets'],['head','Head'],['chest','Chest'],['hands','Hands / gloves'],['legs','Legs'],['unverified','Slot not verified']] : [...new Set(records.map(r=>r[config.typeField] || 'unclassified'))].sort().map(t=>[t,t==='unclassified'?'Unclassified':t]);
        let html=`<div class="catalog-controls"><label>Find by name<input type="search" data-catalog-field="query" value="${this.escapeHtml(state.query)}" placeholder="Search this category" oninput="window.app.setCatalogFilter('${category}','query',this.value)"></label>${config.typeField?select('type',config.typeLabel,[['','All'],...types]):''}${select('sort','Sort by',[['name','Name'],...config.stats])}${select('order','Order',[['asc',state.sort==='name'?'A to Z':'Lowest first'],['desc',state.sort==='name'?'Z to A':'Highest first']])}`;
        if(['armor','weapons'].includes(category))html+=select('basis','Equipment stats',[['base','Base / +0'],['max','Maximum normal upgrade']]);
        if(category==='weapons')html+=select('channel','Must have',[['','Any attack / scaling'],...config.stats.filter(([k])=>k!=='weight')]);
        if(['enemies','bosses'].includes(category))html+=select('area','Area',[['','All areas'],...[...new Set(records.flatMap(r=>r.areas || []))].sort().map(a=>[a,a])]);
        if(category==='enemies')html+=select('weakness','Known weakness',[['','Any / unknown'],...['strike','slash','thrust','magic','fire','lightning','dark'].map(k=>[k,k[0].toUpperCase()+k.slice(1)])]);
        if(['armor','weapons'].includes(category))html+=`<label>Maximum weight<input type="number" min="0" step="0.1" data-catalog-field="maxWeight" value="${this.escapeHtml(state.maxWeight)}" placeholder="Any" onchange="window.app.setCatalogFilter('${category}','maxWeight',this.value)"></label>`;
        html+=`<button class="ds-btn" onclick="window.app.resetCatalogFilters('${category}')">Reset</button></div><p class="catalog-count" aria-live="polite">${result.length} of ${records.length} entries${['armor','weapons'].includes(category)?`. ${state.basis==='max'?'Maximum normal upgrade':'Base (+0)'} stats. ${category==='armor'?'Set values sum all listed pieces.':'Attack is before attribute bonuses.'} Unknown values sort last.`:''}</p>${!result.length?'<p class="catalog-empty">No entries match these filters. Try another filter or Reset.</p>':''}`;
        document.getElementById('view-container').insertAdjacentHTML('beforeend',html);
        return result;
    }

    catalogCardMetric(category, record) {
        const state=this.catalogState(category);
        if(state.sort==='name')return '';
        const label=this.catalogConfig(category).stats.find(([key])=>key===state.sort)?.[1] || state.sort;
        const value=this.catalogMetric(category,record,state.sort,state.basis);
        const formatted=value===null ? 'Not verified' : state.sort.startsWith('scale_') ? ['-','E','D','C','B','A','S'][value] : Number(value.toFixed(2)).toLocaleString();
        return `<p class="catalog-card-stat">${this.escapeHtml(label)}: <strong>${formatted}</strong></p>`;
    }

    renderEnemyList(filteredEnemies = null) {
        const enemies = filteredEnemies || this.data.enemies;
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Bestiary of Drangleic</h2>`;
        const results=this.renderCatalogControls('enemies',enemies);
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        
        results.forEach(enemy => {
            const card = document.createElement('div');
            card.className = 'item-card enemy-card';
            const imageUrl = this.getProxiedUrl(enemy.image, enemy.name);

            card.innerHTML = `
                <div class="card-image placeholder-enemy">
                    <img src="${imageUrl}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${enemy.name.replace(/'/g, "\\'")}', 'enemy')">
                    <div class="card-overlay">
                        <span class="enemy-hp"><img class="ico" src="assets/ui/stat/stat-hp.webp" alt=""> ${this.escapeHtml(enemy.hp || enemy.stat_notes?.hp || 'See encounter details')}</span>
                        <span class="enemy-souls"><img class="ico" src="assets/ui/stat/stat-souls.webp" alt=""> ${this.escapeHtml(enemy.souls === 0 ? 0 : enemy.souls || enemy.stat_notes?.souls || 'See encounter details')}</span>
                    </div>
                </div>
                <div class="card-info">
                    <h4>${enemy.name}</h4>${enemy.data_status ? `<p class="data-note">${this.escapeHtml(enemy.data_status)}</p>` : ''}
                    <p class="enemy-area">${enemy.areas[0] || 'Location not verified'}${enemy.areas.length > 1 ? ' + More' : ''}</p>
                    <div class="weakness-dots">
                        ${Object.entries(enemy.weaknesses)
                            .filter(([_, status]) => status === 'weak')
                            .map(([type]) => `<span class="dot ${type}" title="Weak to ${type}"></span>`)
                            .join('')}
                    </div>
                </div>
            `;
            card.dataset.recordId=enemy.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('enemies',enemy));
            card.onclick = () => this.renderView('enemy-detail', { id: enemy.id });
            grid.appendChild(card);
        });

        container.appendChild(grid);
    }

    filterEnemies(weakness) {
        if (!weakness) {
            this.renderEnemyList();
            return;
        }
        const filtered = this.data.enemies.filter(e => e.weaknesses[weakness] === 'weak');
        this.renderEnemyList(filtered);
    }

    // --- cross-linking ------------------------------------------------------
    // Resolve a free-text name (a drop name, a location label) to a record so the
    // UI can jump between entries. Exact match first; the looser pass is length
    // guarded so a short name cannot latch onto an unrelated record.
    referenceKey(name) {
        return this.normalizeImageKey(name).replace(/^the /, '');
    }

    resolveByName(collection, name) {
        const key = this.referenceKey(name);
        if (!key) return null;
        const hits = collection.filter(x => [x.name, x.id, ...(x.aliases || [])].some(alias => this.referenceKey(alias) === key));
        return hits.length === 1 ? hits[0] : null;
    }

    findItemByName(name) {
        const bare = String(name || '').replace(/\s*\((?:rare|common|guaranteed|very rare|ng\+[^)]*|bonfire intensity[^)]*)\)\s*$/i, '').replace(/\s+[x×]\s*\d+$/i, '').trim();
        return this.resolveByName([...this.data.items,...this.data.magic], name) || this.resolveByName([...this.data.items,...this.data.magic], bare);
    }

    // A drop can be a consumable, a weapon or a shield, so try each catalog and
    // remember which view the target lives in.
    findDropTarget(name) {
        const cacheKey = String(name || '');
        if (this.dropTargetCache.has(cacheKey)) return this.dropTargetCache.get(cacheKey);
        const bare = String(name || '').replace(/\s*\((?:rare|common|guaranteed|very rare|ng\+[^)]*|bonfire intensity[^)]*)\)\s*$/i, '').replace(/\s+[x×]\s*\d+$/i, '').trim();
        const catalogs = [
            ['magic-detail', this.data.magic],
            ['item-detail', this.data.items],
            ['weapon-detail', this.data.weapons],
            ['armor-detail', this.data.armor]
        ];
        for (const [view, collection] of catalogs) {
            const hit = this.resolveByName(collection, name) || this.resolveByName(collection, bare);
            if (hit) { const target = {view, record: hit}; this.dropTargetCache.set(cacheKey, target); return target; }
        }
        this.dropTargetCache.set(cacheKey, null);
        return null;
    }

    dropLink(name) {
        const target = this.findDropTarget(name);
        return this.detailLink(target ? target.view : 'item-detail', target ? target.record : null, name)
            .replace('class="xlink"', 'class="xlink drop-name"')
            .replace('class="xlink-plain"', 'class="xlink-plain drop-name"');
    }

    findAreaByName(name) {
        return this.resolveByName(this.data.areas, name);
    }

    findEnemyByName(name) {
        return this.resolveByName(this.data.bosses, name) || this.resolveByName(this.data.enemies, name);
    }

    // Renders a name as a link into another detail view. Falls back to a plain
    // span when nothing matches, so the UI never offers a dead click.
    detailLink(view, record, label, icon = '') {
        const text = this.escapeHtml(label);
        if (!record) return `<span class="xlink-plain" title="No catalog entry is available for this reference">${icon}${text}</span>`;
        const route = new URLSearchParams({game: 'ds2', view, id: record.id});
        return `<a class="xlink" href="#${this.escapeHtml(route.toString())}" data-view="${this.escapeHtml(view)}" data-id="${this.escapeHtml(record.id)}">${icon}${text}</a>`;
    }

    dropSources(record, view) {
        const seen = new Set();
        return [...this.data.bosses, ...this.data.enemies].filter(enemy => {
            if (seen.has(enemy.id)) return false;
            const found = this.enemyDrops(enemy).some(drop => {
                const target = this.findDropTarget(drop.name);
                return target && target.view === view && target.record.id === record.id;
            });
            if (found) seen.add(enemy.id);
            return found;
        });
    }

    renderBossCombat(boss) {
        if (!boss.combat) return '';
        const combat = boss.combat;
        return `<section class="boss-combat"><h3>Boss combat guide</h3>
            <p>${this.escapeHtml(combat.strategy)}</p>
            <h4>Physical damage effectiveness</h4>
            <div class="res-grid">${Object.entries(combat.physical || {}).map(([type, value]) => `<div class="res-item"><span>${this.getResistanceIcon(type)}${this.escapeHtml(type)}</span><span>${this.escapeHtml(value)}</span></div>`).join('') || '<p class="data-note">Physical modifiers have not been verified.</p>'}</div>
            <p class="data-note">Physical percentages describe relative damage taken; larger values favor that damage type.</p>
            <h4>Elemental defenses</h4>
            <div class="res-grid">${Object.entries(combat.elemental || {}).map(([type, tier]) => `<div class="res-item"><span class="type">${this.getResistanceIcon(type)}${this.escapeHtml(type)}</span><span>${this.escapeHtml(tier)}</span></div>`).join('')}</div>
            <p>${this.escapeHtml(combat.notes || '')}</p>
            <p class="data-note">Lower resistance tiers mean that element is more effective. These are relative tiers; DLC enemies can still resist elemental damage heavily. Water, phases and individual members can change defenses.</p>
            ${this.referenceSection(boss)}
        </section>`;
    }

    renderEnemyDetail(id) {
        const enemy = this.data.bosses.find(b => b.id === id) || this.data.enemies.find(e => e.id === id);
        if (!enemy) return;

        const container = document.getElementById('view-container');
        container.innerHTML = `
            <div class="detail-view enemy-detail">
                <header class="detail-header">
                    <div class="detail-image">
                        <img src="${this.getProxiedUrl(enemy.image, enemy.name)}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${enemy.name.replace(/'/g, "\\'")}', 'enemy')">
                        <div class="image-overlay"></div>
                    </div>
                    <div class="detail-title-box">
                        <div class="title-with-fav">
                            <h1>${enemy.name}</h1>
                            <button class="fav-btn ${this.isFavorite(enemy.id, 'enemy') ? 'active' : ''}" onclick="window.app.toggleFavorite('${enemy.id}', 'enemy')"><img class="ico" src="assets/ui/menu-rings.webp" alt=""></button>
                        </div>
                        <p class="subtitle">${enemy.title}</p>
                        <div class="locations-list">
                            ${enemy.areas.map(area => {
                                const found = this.findAreaByName(area);
                                return this.detailLink('area-detail', found, area, '<img class="ico" src="assets/items/Bonfire_Ascetic.webp" alt=""> ')
                                    .replace('class="xlink"', 'class="xlink location-tag"')
                                    .replace('class="xlink-plain"', 'class="xlink-plain location-tag"');
                            }).join('')}
                        </div>
                        <p class="data-note">${this.escapeHtml(enemy.stat_context || 'Stats may vary with location and bonfire intensity.')}</p>${enemy.image_verified===false ? '<p class="data-note">Portrait unavailable; a labeled placeholder is shown.</p>' : ''}
                        <div class="quick-stats">${this.enemyQuickFacts(enemy)}</div>
                    </div>
                </header>

                <div class="detail-grid">
                    ${this.renderBossCombat(enemy)}${this.enemyStatProfiles(enemy)}
                    <section class="resistances">
                        <h3>Strengths & Weaknesses</h3>${enemy.effectiveness_notes ? `<p>${this.escapeHtml(enemy.effectiveness_notes)}</p>` : ''}
                        ${!Object.keys(enemy.weaknesses || {}).length ? '<p class="data-note">No comparative damage modifiers are published for this reference variant.</p>' : ''}
                        <div class="res-grid">
                            ${Object.entries(enemy.weaknesses || {}).map(([type, status]) => `
                                <div class="res-item ${status}">
                                    <span class="type">${this.getResistanceIcon(type)}${type}</span>
                                    <span class="status-label">${this.escapeHtml(String(status).toUpperCase())}</span>
                                    <span class="status-icon">${this.getStatusIcon(status)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </section>

                    <section class="status-effects">
                        <h3>Immunities & Status</h3>
                        ${!Object.keys(enemy.status_effects || {}).length ? '<p class="data-note">The reference does not provide status thresholds for this variant.</p>' : ''}
                        <div class="res-grid">
                            ${Object.entries(enemy.status_effects || {}).map(([type, status]) => `
                                <div class="res-item ${status}">
                                    <span class="type">${this.getResistanceIcon(type)}${type}</span>
                                    <span class="status-label">${this.escapeHtml(String(status).toUpperCase())}</span>
                                    <span class="status-icon">${this.getStatusIcon(status)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </section>

                    <section class="drops">
                        <h3>Item Drops (Chances)</h3>
                        <ul class="drop-list">
                            ${this.enemyDrops(enemy).map(drop => `
                                <li>
                                    <img src="${this.getProxiedUrl(drop.icon, drop.name)}" crossorigin="anonymous" class="drop-icon-img" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${drop.name.replace(/'/g, "\\'")}', 'item')">
                                    ${this.dropLink(drop.name)}
                                    <span class="drop-chance">${drop.chance}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </section>

                    <section class="farming">
                        <h3>Tactical Guide</h3>
                        ${enemy.farming.bonfire ? `<p><strong>Nearby bonfire:</strong> ${this.escapeHtml(enemy.farming.bonfire)}</p>` : ''}
                        ${enemy.farming.gear.length ? `<p><strong>Equipment suggestions:</strong> ${this.escapeHtml(enemy.farming.gear.join(', '))}</p>` : ''}
                        ${enemy.farming.notes || enemy.combat?.strategy ? `<p><strong>Strategy:</strong> ${this.escapeHtml(enemy.farming.notes || enemy.combat.strategy)}</p>` : ''}
                        ${enemy.encounter_notes?.length ? `<ul>${enemy.encounter_notes.map(note=>`<li>${this.escapeHtml(note)}</li>`).join('')}</ul>` : ''}
                        <div class="difficulty">Threat Level: ${enemy.farming.difficulty ? '★'.repeat(enemy.farming.difficulty) + '☆'.repeat(5-enemy.farming.difficulty) : 'Not rated'}</div>
                    </section>
                </div>

                <section class="ai-notes">
                    <h3>Codex Insights</h3>
                    <blockquote>${enemy.ai_notes || 'No additional notes recorded.'}</blockquote>
                </section>
            ${this.referenceSection(enemy)}</div>
        `;
    }

    getStatusIcon(status) {
        const icons = {
            'weak': '▼',
            'neutral': '–',
            'resistant': '▲',
            'immune': '✕'
        };
        return icons[status] || '';
    }

    getResistanceIcon(type) {
        const icons = {
            'slash': 'assets/ui/stat/stat-slash-defense-total.webp',
            'thrust': 'assets/ui/stat/stat-thrust-defense-total.webp',
            'strike': 'assets/ui/stat/stat-strike-defense-total.webp',
            'fire': 'assets/ui/stat/stat-fire-defense-player.webp',
            'magic': 'assets/ui/stat/stat-magic-defense-player.webp',
            'lightning': 'assets/ui/stat/stat-lightning-defense-player.webp',
            'dark': 'assets/ui/stat/stat-dark-defense-player.webp',
            'poison': 'assets/ui/stat/stat-poison-buildup.webp',
            'toxic': 'assets/ui/stat/stat-poison-buildup.webp',
            'bleed': 'assets/ui/stat/stat-bleed-buildup.webp',
            'curse': 'assets/ui/stat/stat-curse-buildup.webp',
            'petrify': 'assets/ui/stat/stat-petrify-buildup.webp'
        };
        const path = icons[String(type || '').toLowerCase()];
        return path ? `<img class="ico" src="${path}" alt="">` : '';
    }

    renderAreaList() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Areas of Drangleic</h2>`;
        
        const results=this.renderCatalogControls('areas',this.data.areas);
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        
        results.forEach(area => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-area">
                    <img src="${this.getProxiedUrl(area.image, area.name)}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${area.name.replace(/'/g, "\\'")}', 'area')">
                </div>
                <h4>${area.name}</h4>
                <p>Level: ${area.recommended_level}</p>
            `;
            card.dataset.recordId=area.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('areas',area));
            card.onclick = () => this.renderView('area-detail', {id: area.id});
            grid.appendChild(card);
        });

        container.appendChild(grid);
    }

    facts(title, values, labels = {}) {
        const entries = Object.entries(values || {}).filter(([,v]) => v !== undefined && v !== null && v !== '');
        return entries.length ? `<section><h3>${this.escapeHtml(title)}</h3><dl class="fact-grid">${entries.map(([k,v]) => `<div><dt>${this.escapeHtml(labels[k] || k.replaceAll('_',' '))}</dt><dd>${this.escapeHtml(v)}</dd></div>`).join('')}</dl></section>` : '';
    }

    referenceSection(record) {
        const urls = [...new Set([record.source_url, record.combat_source, record.scaling_source, record.defenses_max_source, record.effect_source, record.image_reference, record.image_source, ...(record.additional_sources || [])].filter(Boolean))];
        return `${record.image_kind === 'generated' ? `<p class="data-note image-provenance">Generated lore illustration · ${this.escapeHtml(record.image_note || 'Interpretive artwork; appearance is not canonical. This is not an in-game screenshot.')}</p>` : record.image_verified === false ? `<p class="data-note">${this.escapeHtml(record.image_note || 'Exact icon unavailable; a bundled generic icon is shown.')}</p>` : ''}${urls.length ? `<details class="source-credit"><summary>Source credits</summary><p>These reference facts and images are stored in this guide. No website is needed to read them.</p>${urls.map(url=>`<p class="data-note">${this.escapeHtml(url)}</p>`).join('')}</details>` : ''}`;
    }

    localReferenceTarget(name, url) {
        const normalized=value=>{try{return decodeURIComponent(String(value||'').split('#')[0]).replace(/\/$/,'').replace('http://','https://');}catch{return String(value||'');}};
        if(!this.referenceIndex) {
            const byName=new Map(),bySource=new Map();
            const catalogs=[['magic-detail',this.data.magic],['item-detail',this.data.items],['weapon-detail',this.data.weapons],['armor-detail',this.data.armor],['npc-detail',this.data.npcs],['area-detail',this.data.areas],['enemy-detail',this.data.bosses],['enemy-detail',this.data.enemies],['article-detail',this.data.articles || []]];
            for(const [view,records] of catalogs)for(const record of records) {
                const target={view,record};
                for(const value of [record.name,...(record.aliases||[])]) {
                    const key=this.normalizeImageKey(value);
                    if(!byName.has(key))byName.set(key,[]);
                    byName.get(key).push(target);
                }
                for(const value of new Set([record.source_url,record.wiki_reference?.source_url,...(record.additional_sources||[])].filter(Boolean).map(normalized))) {
                    if(!bySource.has(value))bySource.set(value,[]);
                    bySource.get(value).push(target);
                }
            }
            this.referenceIndex={byName,bySource};
        }
        const source=normalized(url), key=this.normalizeImageKey(name);
        const named=this.referenceIndex.byName.get(key)||[],sourced=this.referenceIndex.bySource.get(source)||[];
        // Names preserve ring ranks and merchant identities even when a wiki link
        // points at a shared set page or at the general Merchants index.
        const intersection=named.find(target=>sourced.includes(target));
        if(intersection)return intersection;
        if(named.length)return named.find(target=>this.normalizeImageKey(target.record.name)===key)||named[0];
        if(sourced.length===1)return sourced[0];
        return null;
    }

    namedReference(name, url) {
        const target=this.localReferenceTarget(name,url);
        return target ? this.detailLink(target.view,target.record,name) : this.detailLink('article-detail',null,name);
    }

    renderArticleDetail(id) {
        const article=(this.data.articles || []).find(a=>a.id===id);
        if(!article)return;
        const sections=new Map();
        for(const block of article.blocks) {
            const content=block.type==='table' ? `<div class="table-scroll"><table class="ds-table"><tbody>${block.rows.map((row,i)=>`<tr>${row.map(cell=>`<${i===0?'th':'td'}>${this.escapeHtml(cell)}</${i===0?'th':'td'}>`).join('')}</tr>`).join('')}</tbody></table></div>` : block.type==='list' ? `<ul>${block.lines.map(line=>`<li>${this.escapeHtml(line)}</li>`).join('')}</ul>` : block.lines.map(line=>`<p>${this.escapeHtml(line)}</p>`).join('');
            sections.set(block.heading,(sections.get(block.heading)||'')+content);
        }
        document.getElementById('view-container').innerHTML=`<div class="detail-view article-detail"><h1>${this.escapeHtml(article.name)}</h1><div class="detail-grid">${[...sections].map(([heading,content])=>`<section><h3>${this.escapeHtml(heading)}</h3>${content}</section>`).join('')}<section><h3>Related entries</h3><div class="xlink-list">${article.related.map(r=>this.namedReference(r.name,r.source_url)).join('')}</div></section></div>${this.referenceSection(article)}</div>`;
    }

    detailHeader(record, type, summary = '') {
        return `<header class="detail-header"><div class="detail-image"><img src="${this.getProxiedUrl(record.image, record.name)}" alt="${this.escapeHtml(record.name)}"></div><div class="detail-title-box"><div class="title-with-fav"><h1>${this.escapeHtml(record.name)}</h1><button class="fav-btn ${this.isFavorite(record.id,type) ? 'active' : ''}" aria-label="Favorite ${this.escapeHtml(record.name)}" onclick="window.app.toggleFavorite('${record.id}', '${type}')"><img class="ico" src="assets/ui/menu-rings.webp" alt=""></button></div><p class="subtitle">${this.escapeHtml(record.slot || record.type || '')}</p>${summary}</div></header>`;
    }

    renderAreaDetail(id) {
        id = this.data.areaRedirects?.[id] || id;
        const area = this.data.areas.find(a => a.id === id);
        if (!area) return;
        const list = (title,names,records,view) => `<section><h3>${title} (${(names||[]).length})</h3><div class="xlink-list">${(names||[]).map(name => this.namedReference(name)).join('') || '<p>None recorded for this area.</p>'}</div></section>`;
        const fires = area.bonfire_details || [];
        document.getElementById('view-container').innerHTML = `<div class="detail-view area-detail"><h1>${this.escapeHtml(area.name)}</h1><div class="area-hero"><img src="${this.getProxiedUrl(area.image,area.name)}" alt="${this.escapeHtml(area.name)}"></div><div class="detail-grid"><section><h3>Overview</h3><p>${this.escapeHtml(area.description)}</p><p>${this.escapeHtml(area.overview_notes || '')}</p><p><strong>Region:</strong> ${this.escapeHtml(area.region || 'Drangleic')}</p>${area.recommended_level ? `<p><strong>Suggested level:</strong> ${this.escapeHtml(area.recommended_level)}</p>` : ''}</section>${list('Connected areas',area.connections,this.data.areas,'area-detail')}${list('Bosses',area.bosses,this.data.bosses,'enemy-detail')}${list('Enemies',area.enemies,this.data.enemies,'enemy-detail')}${list('NPCs',area.npcs,this.data.npcs,'npc-detail')}${area.items?.length ? list('Notable loot',area.items) : ''}${area.mini_bosses?.length ? list('Other encounters',area.mini_bosses) : ''}${area.secrets?.length ? `<section><h3>Secrets and access</h3><ul>${area.secrets.map(x=>`<li>${this.escapeHtml(x)}</li>`).join('')}</ul></section>` : ''}</div><section class="bonfire-section"><h2>Bonfires (${area.bonfires.length})</h2>${area.bonfires.length ? `<div class="bonfire-grid">${area.bonfires.map(name=>{
            const fire=fires.find(f=>this.referenceKey(f.name)===this.referenceKey(name)) || {name};
            return `<article class="bonfire-card"><h3>${this.escapeHtml(name)}</h3><p>${this.escapeHtml(fire.location || fire.landmark || 'Detailed directions are not yet verified.')}</p>${fire.notes ? `<p class="data-note">${this.escapeHtml(fire.notes)}</p>` : ''}${(fire.screenshots||[]).map(photo=>`<figure><img loading="lazy" src="${this.escapeHtml(photo.image)}" alt="${this.escapeHtml(photo.caption)}"><figcaption>${this.escapeHtml(photo.caption)} · <span>Bundled location screenshot</span></figcaption></figure>`).join('')}${!fire.screenshots?.length ? '<p class="data-note">Location screenshot not yet available.</p>' : ''}</article>`;
        }).join('')}</div>` : '<p>This area has no bonfire; use the connected area’s bonfire.</p>'}</section>${this.referenceSection(area)}</div>`;
    }

    renderBossList() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Bosses of Drangleic</h2>`;
        const results=this.renderCatalogControls('bosses',this.data.bosses);
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        results.forEach(boss => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-boss">
                    <img src="${this.getProxiedUrl(boss.image, boss.name)}" crossorigin="anonymous" onerror="window.app.handleImageError(this, '${boss.name.replace(/'/g, "\\'")}', 'boss')">
                </div>
                <h4>${boss.name}</h4>
                <p>${boss.title}</p>
            `;
            card.dataset.recordId=boss.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('bosses',boss));
            card.onclick = () => this.renderView('enemy-detail', { id: boss.id });
            grid.appendChild(card);
        });
        container.appendChild(grid);
    }

    renderNpcList() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Characters of Drangleic</h2>`;
        const results=this.renderCatalogControls('npcs',this.data.npcs);
        const grid = document.createElement('div');
        grid.className = 'card-grid';

        results.forEach(npc => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-npc">
                    <img src="${this.getProxiedUrl(npc.image, npc.name)}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${npc.name.replace(/'/g, "\\'")}', 'npc')">
                </div>
                <h4>${npc.name}</h4>
                ${npc.image_kind==='generated'?'<span class="image-art-badge">Generated illustration</span>':''}
                <p>${npc.role || ''}</p>
            `;
            card.dataset.recordId=npc.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('npcs',npc));
            card.onclick = () => this.renderView('npc-detail', {id: npc.id});
            grid.appendChild(card);
        });

        container.appendChild(grid);
    }

    renderNpcDetail(id) {
        const npc = this.data.npcs.find(n => n.id === id);
        if (!npc) return;
        const areas = this.data.areas.filter(area => (area.npcs || []).some(name => this.resolveByName(this.data.npcs, name)?.id === npc.id));
        document.getElementById('view-container').innerHTML = `<div class="detail-view npc-detail">
            <header class="detail-header"><div class="detail-image"><img src="${this.getProxiedUrl(npc.image, npc.name)}" alt="${this.escapeHtml(npc.name)}${npc.image_kind==='generated'?' — generated interpretation':''}"></div><div class="detail-title-box"><h1>${this.escapeHtml(npc.name)}</h1><p>${this.escapeHtml(npc.role || npc.title || '')}</p>${npc.image_kind==='generated'?'<span class="image-art-badge">Generated lore illustration · non-canonical appearance</span>':''}</div></header>
            <div class="detail-grid"><section><h3>${npc.role==='Lore figure'?'Lore reference':'Locations'}</h3><div class="xlink-list">${areas.map(area => this.detailLink('area-detail', area, area.name)).join('')}</div><p>${this.escapeHtml(npc.location || '')}</p>${npc.related?.length?`<div class="xlink-list">${npc.related.map(ref=>this.namedReference(ref.name,ref.source_url)).join('')}</div>`:''}</section><section><h3>About</h3><p>${this.escapeHtml(npc.description || '')}</p>${npc.use_notes ? `<h3>Interactions</h3><p>${this.escapeHtml(npc.use_notes)}</p>` : ''}${npc.interaction_details?.length?`<ul>${npc.interaction_details.map(note=>`<li>${this.escapeHtml(note)}</li>`).join('')}</ul>`:''}</section></div>${this.referenceSection(npc)}</div>`;
    }

    renderArmorList() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Armor of Drangleic</h2>`;
        const results=this.renderCatalogControls('armor',this.data.armor.filter(piece=>!piece.content_status));
        const grid = document.createElement('div');
        grid.className = 'card-grid';

        results.forEach(piece => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-armor">
                    <img src="${this.getProxiedUrl(piece.image, piece.name)}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${piece.name.replace(/'/g, "\\'")}', 'armor')">
                </div>
                <h4>${piece.name}</h4>
                <p>${piece.type && piece.type !== 'Armor' ? piece.type : ''}</p>
            `;
            card.dataset.recordId=piece.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('armor',piece));
            card.onclick = () => this.renderView('armor-detail', {id: piece.id});
            grid.appendChild(card);
        });

        container.appendChild(grid);
    }

    renderArmorDetail(id) {
        const piece = this.data.armor.find(a => a.id === id);
        if (!piece) return;
        const members = (piece.pieces || []).map(id=>this.data.armor.find(a=>a.id===id)).filter(Boolean);
        const labels={str:'Strength',dex:'Dexterity',int:'Intelligence',fth:'Faith',physical:'Physical',strike:'Strike',slash:'Slash',thrust:'Thrust',magic:'Magic',fire:'Fire',lightning:'Lightning',dark:'Dark',poison:'Poison resistance',bleed:'Bleed resistance',petrify:'Petrification resistance',curse:'Curse resistance',poise:'Poise',weight:'Weight',durability:'Durability'};
        const sets=this.data.armor.filter(a=>a.pieces?.includes(id));
        document.getElementById('view-container').innerHTML=`<div class="detail-view armor-detail">${this.detailHeader(piece,'armor')}<div class="detail-grid"><section><h3>Equipment</h3><p>${this.escapeHtml(piece.description || 'Armor equipment.')} ${piece.content_status ? `<strong>${this.escapeHtml(piece.content_status)}</strong>` : ''}</p>${!members.length ? `<p>${Object.keys(piece.requirements||{}).length ? this.escapeHtml(piece.equipment_note || 'Meet the requirements below to equip effectively.') : 'No attribute requirement is listed. Weight contributes to your equipment load.'}</p>` : ''}</section>${members.length ? `<section><h3>Set pieces (${members.length})</h3><div class="xlink-list">${members.map(a=>this.detailLink('armor-detail',a,a.name)).join('')}</div><p>Open a piece for its weight, defenses and individual effects.</p></section>` : ''}${sets.length ? `<section><h3>Armor set</h3><div class="xlink-list">${sets.map(a=>this.detailLink('armor-detail',a,a.name)).join('')}</div></section>` : ''}${this.facts('Requirements',piece.requirements,labels)}${this.facts('Defenses and equipment at +0',piece.defenses_base,labels)}${piece.stat_note ? `<section><h3>Variant details</h3><p>${this.escapeHtml(piece.stat_note)}</p></section>` : ''}${this.facts(`Defenses and equipment at +${piece.max_level}`,piece.defenses_max,labels)}<section><h3>Special effects</h3><p>${this.escapeHtml(piece.special_effect || (members.length ? 'See the individual pieces for their effects.' : 'Special effects have not yet been verified.'))}</p></section>${piece.obtaining ? `<section><h3>Where to obtain</h3><p>${this.escapeHtml(piece.obtaining)}</p></section>` : ''}${this.renderItemSources(piece,'armor-detail')}${this.referenceSection(piece)}</div></div>`;
    }

    gradeFor(stat, pct) {
        const t = this.data.scalingConstants
            && this.data.scalingConstants.letterThresholds
            && this.data.scalingConstants.letterThresholds[stat];
        if (!t || !pct) return '';
        const entries = Object.entries(t).sort((a, b) => Number(b[1]) - Number(a[1]));
        for (const [grade, min] of entries) if (pct >= Number(min)) return grade;
        return '';
    }

    weaponOptions(selectedId) {
        return this.data.weapons
            .filter(w => this.upgradeFor(w))
            .map(w => `<option value="${w.id}" ${w.id === selectedId ? 'selected' : ''}>${w.name}${w.type ? ` — ${w.type}` : ''}</option>`)
            .join('');
    }

    renderWeaponList() {
        const container = document.getElementById('view-container');
        container.innerHTML = `
            <div class="list-header">
                <h2 class="view-title">Weapons</h2>
                <button class="ds-btn" onclick="window.app.renderView('weapon-compare', {ids: []})">Compare Weapons</button>
            </div>
        `;
        const results=this.renderCatalogControls('weapons',this.data.weapons);
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        results.forEach(weapon => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-weapon">
                    <img src="${this.getProxiedUrl(weapon.image, weapon.name)}" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="window.app.handleImageError(this, '${weapon.name.replace(/'/g, "\\'")}', 'weapon')">
                </div>
                <h4>${weapon.name}</h4>
                <p>${weapon.type}</p>
            `;
            card.dataset.recordId=weapon.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric('weapons',weapon));
            card.onclick = () => this.renderView('weapon-detail', { id: weapon.id });
            grid.appendChild(card);
        });
        container.appendChild(grid);
    }

    renderWeaponDetail(id) {
        const weapon = this.data.weapons.find(w=>w.id===id);
        if (!weapon) return;
        const attrs={str:'Strength',dex:'Dexterity',int:'Intelligence',fth:'Faith'};
        const attack=weapon.attack || {physical:weapon.base_damage,...weapon.elemental_damage};
        const summary = `<div class="weapon-essentials">${this.facts('Base attack at +0',attack)}${this.facts('Requirements',weapon.requirements,attrs)}${this.facts('Scaling at +0',weapon.scaling,{str:'Strength',dex:'Dexterity',magic:'Magic (INT)',fire:'Fire (INT + FTH)',lightning:'Lightning (FTH)',dark:'Dark (min INT/FTH)'})}</div><dl class="weapon-handling">${Object.entries({weight:weapon.weight,durability:weapon.durability,damage_type:weapon.damage_type}).filter(([,v])=>v!==undefined && v!==null && v!=='').map(([k,v])=>`<div><dt>${this.escapeHtml(k.replaceAll('_',' '))}</dt><dd>${this.escapeHtml(v)}</dd></div>`).join('')}</dl>${(/shield/i.test(weapon.type) && weapon.block_reduction) || Object.values(weapon.auxiliary || {}).some(v=>Number(v)>0) ? `<div class="weapon-extra-stats">${/shield/i.test(weapon.type) && weapon.block_reduction ? this.facts('Blocking damage reduction (%)',weapon.block_reduction) : ''}${Object.values(weapon.auxiliary || {}).some(v=>Number(v)>0) ? this.facts('Status buildup',weapon.auxiliary) : ''}</div>` : ''}`;
        document.getElementById('view-container').innerHTML=`<div class="detail-view weapon-detail">${this.detailHeader(weapon,'weapon',summary)}<div class="weapon-lab-actions"><button class="ds-btn" onclick="window.app.equipInCharacter('${weapon.id}')">Equip in Character Lab</button><button class="ds-btn" onclick="window.app.setBlacksmithWeapon('${weapon.id}');window.app.renderView('blacksmith')">Preview upgrades & infusions</button></div><div class="detail-grid"><section><h3>About</h3><p>${this.escapeHtml(weapon.description || weapon.notes || weapon.type)}</p><p>${this.escapeHtml(weapon.notes || '')}</p></section>${weapon.obtaining ? `<section><h3>Where to obtain</h3><p>${this.escapeHtml(weapon.obtaining)}</p></section>` : ''}${weapon.special_effect || weapon.mechanics_notes ? `<section><h3>Effects and mechanics</h3><p>${this.escapeHtml(weapon.special_effect || '')}</p><p>${this.escapeHtml(weapon.mechanics_notes || '')}</p></section>` : ''}${this.facts('Handling',{damage_type:weapon.damage_type,weight:weapon.weight,durability:weapon.durability,counter_strength:weapon.counter_strength,poise_damage:weapon.poise_damage,buffable:weapon.buffable})}${weapon.block_reduction && !/shield/i.test(weapon.type) ? this.facts('Blocking damage reduction (%)',weapon.block_reduction) : ''}${this.facts('Status buildup',weapon.auxiliary)}${this.renderItemSources(weapon,'weapon-detail')}${this.referenceSection(weapon)}</div>${weapon.upgrade_stats?.length ? `<details class="char-panel"><summary>Reinforcement and infusion tables</summary><p>Base attack before attribute bonuses. Grade order: Strength / Dexterity / Magic / Fire / Lightning / Dark. Damage dealt also depends on the target’s defenses.</p><div class="table-scroll"><table class="ds-table"><thead><tr><th>Path</th><th>Level</th><th>Physical</th><th>Magic</th><th>Fire</th><th>Lightning</th><th>Dark</th><th>Scaling</th></tr></thead><tbody>${weapon.upgrade_stats.map(row=>`<tr><td>${this.escapeHtml(row.path)}</td><td>+${row.level}</td>${['physical','magic','fire','lightning','dark'].map(ch=>`<td>${row.attack[ch]}</td>`).join('')}<td>${['str','dex','magic','fire','lightning','dark'].map(ch=>this.escapeHtml(row.scaling[ch]||'-')).join(' / ')}</td></tr>`).join('')}</tbody></table></div></details>` : '<p class="data-note">Detailed reinforcement rows are not yet verified for this weapon.</p>'}</div>`;
    }

    renderWeaponComparison(ids = []) {
        const container = document.getElementById('view-container');
        const selectedWeapons = this.data.weapons.filter(w => ids.includes(w.id));
        
        container.innerHTML = `
            <div class="comparison-view">
                <h2 class="view-title">Weapon Comparison</h2>
                <div class="comparison-selector">
                    <select id="weapon-select">
                        <option value="">Add a weapon to compare...</option>
                        ${this.data.weapons.filter(w => !ids.includes(w.id)).map(w => `<option value="${w.id}">${w.name}</option>`).join('')}
                    </select>
                    <button class="ds-btn" id="add-to-compare">Add</button>
                </div>
                
                <div class="comparison-table-wrapper">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>Feature</th>
                                ${selectedWeapons.map(w => `<th>${w.name} <button class="remove-btn" onclick="window.app.removeFromComparison('${w.id}', [${ids.map(i => `'${i}'`).join(',')}])">×</button></th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td>Type</td>${selectedWeapons.map(w => `<td>${w.type}</td>`).join('')}</tr>
                            <tr><td>Base Damage</td>${selectedWeapons.map(w => `<td>${w.base_damage}</td>`).join('')}</tr>
                            <tr><td>Weight</td>${selectedWeapons.map(w => `<td>${w.weight}</td>`).join('')}</tr>
                            <tr><td>Damage Type</td>${selectedWeapons.map(w => `<td>${w.damage_type}</td>`).join('')}</tr>
                            <tr><td>Requirements (STR / DEX / INT / FTH)</td>${selectedWeapons.map(w => `<td>${["str","dex","int","fth"].map(k=>w.requirements?.[k] ?? "?").join(" / ")}</td>`).join('')}</tr><tr><td>Scaling (STR / DEX / Magic / Fire / Lightning / Dark)</td>${selectedWeapons.map(w => `<td>${["str","dex","magic","fire","lightning","dark"].map(k=>w.scaling?.[k] ?? "?").join(" / ")}</td>`).join('')}</tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        document.getElementById('add-to-compare').onclick = () => {
            const select = document.getElementById('weapon-select');
            if (select.value) {
                this.renderWeaponComparison([...ids, select.value]);
            }
        };
    }

    removeFromComparison(id, currentIds) {
        const newIds = currentIds.filter(i => i !== id);
        this.renderWeaponComparison(newIds);
    }

    renderQuests() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">NPC Quest Tracker</h2>`;

        const grid = document.createElement('div');
        grid.className = 'card-grid';

        this.data.quests.forEach(quest => {
            const completedSteps = this.questProgress[quest.id] || [];
            const isFinished = completedSteps.length === quest.steps.length;

            const card = document.createElement('div');
            card.className = `quest-card ${isFinished ? 'finished' : ''}`;
            card.innerHTML = `
                <div class="quest-header">
                    <img src="${this.getProxiedUrl(quest.image, quest.name)}" crossorigin="anonymous" onerror="window.app.handleImageError(this, '${quest.name.replace(/'/g, "\\'")}', 'quest')">
                    <div class="quest-info">
                        <h4>${quest.name}</h4>
                        <p class="reward">Reward: ${quest.reward}</p>
                        ${quest.missable ? '<span class="missable-tag">Missable</span>' : ''}
                    </div>
                </div>
                <ul class="quest-steps">
                    ${quest.steps.map((step, index) => `
                        <li class="${completedSteps.includes(index) ? 'completed' : ''}" onclick="window.app.toggleQuestStep('${quest.id}', ${index})">
                            <span class="step-check">${completedSteps.includes(index) ? '☑' : '☐'}</span>
                            <div class="step-text">
                                <span class="step-location">${step.location}</span>
                                <span class="step-action">${step.action}</span>
                            </div>
                        </li>
                    `).join('')}
                </ul>
                ${quest.notes ? `<p class="quest-notes">${this.escapeHtml(quest.notes)}</p>` : ''}
                ${quest.npc_id ? this.detailLink('npc-detail',this.data.npcs.find(npc=>npc.id===quest.npc_id),'Character details') : ''}
                ${this.referenceSection(quest)}
            `;
            container.appendChild(card);
        });
    }

    renderMechanics() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Game Mechanics Encyclopedia</h2>`;

        const grid = document.createElement('div');
        grid.className = 'mechanics-grid';

        this.data.mechanics.forEach(m => {
            const card = document.createElement('div');
            card.className = 'mechanics-card';
            card.innerHTML = `
                <div class="mech-header">
                    <span class="mech-icon">${m.icon}</span>
                    <h3>${m.name}</h3>
                </div>
                <p class="mech-desc">${m.description}</p>
                <div class="mech-details">
                    <h4>Deep Dive</h4>
                    <p>${m.details}</p>
                </div>
            `;
            container.appendChild(card);
        });
    }

    renderFavorites() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Your Favorites</h2>`;

        if (this.favorites.length === 0) {
            container.innerHTML += `<p class="empty-msg">You haven't added any favorites yet.</p>`;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'card-grid';

        this.favorites.forEach(fav => {
            let item;
            if (fav.type === 'enemy') item = this.data.enemies.find(e => e.id === fav.id) || this.data.bosses.find(b => b.id === fav.id);
            else if (fav.type === 'weapon') item = this.data.weapons.find(w => w.id === fav.id);
            else if (fav.type === 'magic') item = this.data.magic.find(w => w.id === fav.id);
            else if (fav.type === 'npc') item = this.data.npcs.find(w => w.id === fav.id);
            else if (fav.type === 'item') item = this.data.items.find(w => w.id === fav.id);
            else if (fav.type === 'armor') item = this.data.armor.find(w => w.id === fav.id);

            if (item) {
                const card = document.createElement('div');
                card.className = 'item-card';
                card.innerHTML = `
                    <img src="${this.getProxiedUrl(item.image, item.name)}" crossorigin="anonymous" onerror="window.app.handleImageError(this, '${item.name.replace(/'/g, "\\'")}', '${fav.type}')">
                    <h4>${item.name}</h4>
                    <p>${fav.type === 'enemy' ? item.title : item.type}</p>
                `;
                card.onclick = () => this.renderView(`${fav.type}-detail`, { id: item.id });
                grid.appendChild(card);
            }
        });

        container.appendChild(grid);
    }

    renderItemList(category = 'items') {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">${category === 'magic' ? 'Magic' : 'Items & Consumables'}</h2>`;
        const results=this.renderCatalogControls(category,this.data[category]);
        if(category === 'magic')container.insertAdjacentHTML('afterbegin','<p class="data-note">Sorceries, miracles, pyromancies and hexes. Cast counts show the minimum of the documented attunement range.</p>');
        const grid = document.createElement('div');
        grid.className = 'card-grid';
        results.forEach(item => {
            const card = document.createElement('div');
            card.className = 'item-card';
            card.innerHTML = `
                <div class="card-image placeholder-item">
                    <img src="${this.getProxiedUrl(item.image, item.name)}" onerror="window.app.handleImageError(this, '${item.name.replace(/'/g, "\\'")}', 'item')">
                </div>
                <h4>${item.name}</h4>
                <p>${item.type}</p>
            `;
            card.dataset.recordId=item.id;
            card.insertAdjacentHTML('beforeend',this.catalogCardMetric(category,item));
            card.onclick = () => this.renderView(category === 'magic' ? 'magic-detail' : 'item-detail', { id: item.id });
            grid.appendChild(card);
        });
        container.appendChild(grid);
    }

    // Which enemies/bosses list this item in their drop table.
    renderItemSources(item, view = 'item-detail') {
        const holders = this.dropSources(item, view);
        if (!holders.length) return ''; // Purchased, found and traded items use their acquisition references.
        const links = holders.map(e => this.detailLink('enemy-detail', e, e.name)).join('');
        return `<section class="sources"><h3>Dropped By (${holders.length})</h3><div class="xlink-list">${links}</div></section>`;
    }

    renderItemDetail(id, type = 'item') {
        const item=(type === 'magic' ? this.data.magic : this.data.items).find(i=>i.id===id);
        if (!item) return;
        const refs=item.acquisition_refs || [];
        document.getElementById('view-container').innerHTML=`<div class="detail-view item-detail">${this.detailHeader(item,type)}<div class="detail-grid"><section><h3>Purpose and use</h3><p>${this.escapeHtml(item.description || item.usage || 'Purpose has not yet been verified.')}</p>${item.usage && item.usage!==item.description ? `<p>${this.escapeHtml(item.usage)}</p>` : ''}</section>${this.facts('Combat properties',item.combat_stats,{base_physical_damage:'Base physical damage',dex_scaling_percent:'Dexterity scaling (%)',poison_buildup:'Poison buildup per hit',poise_damage:'Poise damage',posture_damage:'Posture damage'})}${item.damage_formulas?.length ? `<section><h3>Damage mechanics</h3><ul>${item.damage_formulas.map(x=>`<li>${this.escapeHtml(x)}</li>`).join('')}</ul></section>` : ''}${this.facts('Ring equipment',item.equipment_stats)}${this.facts('Spell properties',item.spell_stats)}${item.mechanics_notes ? `<section><h3>Effects and mechanics</h3><p>${this.escapeHtml(item.mechanics_notes)}</p></section>` : ''}${item.soul_value!==undefined ? `<section><h3>Consume soul</h3><p class="soul-value">${Number(item.soul_value).toLocaleString()} souls</p><p>${this.escapeHtml(item.soul_warning || 'Using this item consumes it. Keep it if you want a trade reward instead.')}</p></section>` : ''}${item.trades?.length ? `<section><h3>Soul trades</h3>${item.trades.map(t=>`<div class="trade-card"><p><strong>Trader:</strong> ${this.namedReference(t.merchant)}</p><div class="xlink-list">${t.products.map(name=>this.namedReference(name)).join('')}</div><p><strong>Cost:</strong> this soul + ${this.escapeHtml(t.cost)} souls</p></div>`).join('')}</section>` : ''}<section><h3>Where to obtain</h3><p>${this.escapeHtml(item.obtaining || 'See the linked acquisition references.')}</p><div class="xlink-list">${refs.map(r=>this.namedReference(r.name,r.source_url)).join('')}</div></section>${item.direct_drop===false ? '' : this.renderItemSources(item,`${type}-detail`)}${this.referenceSection(item)}${item.combat_source ? `<section><h3>Damage notes</h3><p>Base damage is before Dexterity scaling and enemy defenses. Status buildup is separate from health damage.</p></section>` : ''}</div></div>`;
    }

    renderCovenants() {
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Covenants</h2>`;
        
        this.data.covenants.forEach(cov => {
            const section = document.createElement('div');
            section.className = 'detail-view covenant-detail';
            section.innerHTML = `
                <div class="detail-header">
                    <div class="detail-image">
                        <img src="${this.getProxiedUrl(cov.image, cov.name)}" onerror="window.app.handleImageError(this, '${cov.name.replace(/'/g, "\\'")}', 'covenant')">
                    </div>
                    <div class="detail-title-box">
                        <h1>${cov.name}</h1>
                        <p class="subtitle">${cov.purpose}</p>
                        <p>See the rank requirements and joining reward below.</p>
                        </div>
                    </div>
                </div>

                <div class="detail-grid">
                    <section class="rewards">
                        <h3>Rewards</h3>${cov.join_notes ? `<p><strong>How to join:</strong> ${this.escapeHtml(cov.join_notes)}</p>` : ''}
                        <ul class="drop-list">
                            ${cov.rewards.map(r => `
                                <li class="${r.received ? 'received' : ''}">
                                    <span class="rank">Rank ${r.rank} (${r.requirement})</span>
                                    <span class="drop-name">${this.escapeHtml(r.name)}</span>
                                    <span class="status-icon">${r.received ? '✓' : '✗'}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </section>

                    <section class="farming">
                        <h3>Best Farming Spots</h3>
                        ${cov.farming.map(f => `
                            <div class="farming-spot">
                                <p><strong>${f.area}</strong> - ${f.enemy}</p>
                                <p class="notes">${f.notes}</p>
                                <div class="difficulty">Efficiency: ${'★'.repeat(f.efficiency)}${'☆'.repeat(5-f.efficiency)}</div>
                            </div>
                        `).join('<hr>')}
                    </section>
                </div>
                ${this.referenceSection(cov)}
            `;
            container.appendChild(section);
        });
    }

    handleSearch(query) {
        query = String(query).toLowerCase();
        const catalogs = [['Bosses', 'enemy-detail', this.data.bosses], ['Enemies', 'enemy-detail', this.data.enemies], ['Areas', 'area-detail', this.data.areas], ['Weapons', 'weapon-detail', this.data.weapons], ['Magic', 'magic-detail', this.data.magic], ['Items', 'item-detail', this.data.items], ['Armor', 'armor-detail', this.data.armor], ['NPCs', 'npc-detail', this.data.npcs], ['Guide entries', 'article-detail', this.data.articles || []]];
        const container = document.getElementById('view-container');
        container.innerHTML = `<h2 class="view-title">Search results for “${this.escapeHtml(query)}”</h2>`;
        let count = 0;
        for (const [title, view, records] of catalogs) {
            const hits = records.filter(record => [record.name, record.title, ...(record.aliases || [])].some(text => String(text || '').toLowerCase().includes(query)));
            if (!hits.length) continue;
            count += hits.length;
            const section = document.createElement('section');
            section.innerHTML = `<h3>${title} (${hits.length})</h3><div class="xlink-list">${hits.map(record => this.detailLink(view, record, record.name)).join('')}</div>`;
            container.appendChild(section);
        }
        if (!count) container.insertAdjacentHTML('beforeend', '<p class="empty-msg">No matching entries found.</p>');
    }

}

Object.assign(CodexApp.prototype, referenceMethods);
Object.assign(CodexApp.prototype, blacksmithMethods);
Object.assign(CodexApp.prototype, characterMethods);

