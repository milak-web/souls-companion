// Locally stored reference facts. Source pages are credits, never required navigation.
export const referenceMethods = {
    enemyDrops(enemy) {
        const drops=[...(enemy.drops||[])], seen=new Set(drops.map(drop=>this.normalizeImageKey(drop.name)));
        for(const ref of enemy.wiki_reference?.drops || []) {
            const cacheKey='wiki-drop:'+ref.name+'|'+ref.source_url;
            if(!this.dropTargetCache.has(cacheKey))this.dropTargetCache.set(cacheKey,this.localReferenceTarget(ref.name,ref.source_url));
            const target=this.dropTargetCache.get(cacheKey);
            if(!target || !['item-detail','weapon-detail','armor-detail','magic-detail'].includes(target.view))continue;
            const key=this.normalizeImageKey(target.record.name);
            if(seen.has(key))continue;
            seen.add(key);drops.push({name:target.record.name,icon:target.record.image,chance:'Rate not published'});
        }
        return drops;
    },
    referenceRecord(view, id) {
        const names = {'enemy-detail':['bosses','enemies'],'area-detail':['areas'],'weapon-detail':['weapons'],'item-detail':['items'],'magic-detail':['magic'],'armor-detail':['armor'],'npc-detail':['npcs'],'article-detail':['articles']};
        for (const name of names[view] || []) {
            const record = this.data[name]?.find(record => record.id === id);
            if (record) return record;
        }
    },
    referenceLabel(value) {
        return String(value).replace(/\.(?:png|webp)$/ig,'').replace(/icon[-_ ]*/ig,'').replace(/wp[-_ ]*/ig,'').replace(/physicaldef/ig,'Physical defense').replace(/strikedef/ig,'Strike defense').replace(/slashdef/ig,'Slash defense').replace(/thrustdef/ig,'Thrust defense').replace(/magicdef/ig,'Magic defense').replace(/firedef/ig,'Fire defense').replace(/lightningdef/ig,'Lightning defense').replace(/darkdef/ig,'Dark defense').replace(/poisedef/ig,'Poise').replace(/poisonres/ig,'Poison resistance').replace(/bleedres/ig,'Bleed resistance').replace(/petrifyres/ig,'Petrification resistance').replace(/curseres/ig,'Curse resistance').replace(/durabilitiy/ig,'Durability').replace(/;\s*$/,'').trim();
    },
    renderWikiReference(view, params, container) {
        const record = this.referenceRecord(view, params.id), wiki = record?.wiki_reference;
        if (!wiki) return;
        const esc = value => this.escapeHtml(value), linked = value => this.namedReference(String(value));
        const properties = (wiki.properties || []).flatMap(group => group.facts).filter(fact => !['HP','Weakness','Resistance','Respawns'].includes(fact.label));
        const unique = [...new Map(properties.map(fact => [fact.label+'\0'+fact.value,fact])).values()];
        const section = document.createElement('section');
        section.className = 'wiki-reference-facts';
        section.innerHTML = `<h2>Reference details</h2>${wiki.mechanics?.length ? `<div class="wiki-mechanics"><h3>Effects and conditions</h3><ul>${wiki.mechanics.map(fact => `<li>${esc(fact)}</li>`).join('')}</ul></div>` : ''}
            ${unique.length ? `<details class="wiki-properties"><summary>Properties (${unique.length})</summary><dl class="fact-grid">${unique.map(fact => `<div><dt>${esc(this.referenceLabel(fact.label))}</dt><dd>${linked(fact.value)}</dd></div>`).join('')}</dl></details>` : ''}
            ${wiki.attacks?.length ? `<details class="wiki-attacks" open><summary>Attacks and openings (${wiki.attacks.length})</summary><div class="table-scroll"><table class="ds-table"><thead><tr><th>Attack</th><th>Damage / buildup</th><th>Parry</th><th>Block</th></tr></thead><tbody>${wiki.attacks.map(attack => `<tr><td>${esc(attack.name)}</td><td>${esc(attack.damage || '—')}</td><td>${esc(attack.parry || '—')}</td><td>${esc(attack.block || '—')}</td></tr>`).join('')}</tbody></table></div><p class="data-note">A dash means the source does not describe that property for this attack. Parry timing and unblockable moves vary by attack.</p></details>` : ''}
            ${(wiki.tables || []).map(table => `<details><summary>${esc(table.heading)} (${table.rows.length})</summary><div class="table-scroll"><table class="ds-table"><thead><tr>${table.headers.map(header => `<th>${esc(this.referenceLabel(header))}</th>`).join('')}</tr></thead><tbody>${table.rows.map(row => `<tr>${row.map(value => `<td>${linked(value)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`).join('')}
            ${wiki.acquisition?.length ? `<div class="wiki-acquisition"><h3>Locations and acquisition references</h3><div class="xlink-list">${wiki.acquisition.map(ref => this.namedReference(ref.name,ref.source_url)).join('')}</div></div>` : ''}
            ${wiki.related?.length ? `<details><summary>Related equipment and mechanics</summary><div class="xlink-list">${wiki.related.map(ref => this.namedReference(ref.name,ref.source_url)).join('')}</div></details>` : ''}
            <p class="data-note">Reviewed ${esc(wiki.checked_on)} · ${esc(wiki.reference || 'Fextralife')} reference facts, stored in this guide. Source-specific variants remain separate.</p>`;
        if (!unique.length && !wiki.mechanics?.length && !wiki.tables?.length && !wiki.attacks?.length && !wiki.acquisition?.length && !wiki.related?.length) return;
        const credits=container.querySelector('.detail-view > .source-credit');
        if(credits)credits.before(section);else container.querySelector('.detail-view')?.append(section);
    },
    enemyStatProfiles(enemy) {
        const profiles=enemy.stat_profiles||[],modifiers=enemy.damage_modifiers||[];
        return `${profiles.length ? `<section><details class="enemy-stat-profiles"><summary>Stats by variant, location and game cycle</summary><div class="table-scroll"><table class="ds-table"><thead><tr><th>Context / variant</th><th>Game cycle</th><th>HP</th><th>Souls</th><th>Reference</th></tr></thead><tbody>${profiles.map(row => `<tr><td>${this.escapeHtml(row.context)}</td><td>${row.cycle == null ? this.escapeHtml('Intensity '+row.intensity) : row.cycle === 0 ? 'NG' : row.cycle === 1 ? 'NG+' : 'NG+'+this.escapeHtml(row.cycle)}</td><td>${this.escapeHtml(row.hp || '—')}</td><td>${this.escapeHtml(row.souls || '—')}</td><td>${this.escapeHtml(row.reference || 'Wikidot')}</td></tr>`).join('')}</tbody></table></div><p class="data-note">Each row preserves its source and variant. A dash is an unpublished value, not zero. NG+ and local Bonfire Ascetics raise the encounter’s intensity.</p></details></section>` : ''}
        ${modifiers.length ? `<section><h3>Published damage modifiers</h3><dl class="fact-grid">${modifiers.map(row=>`<div><dt>${this.escapeHtml(row.channel)} · ${this.escapeHtml(row.kind)}</dt><dd>${this.escapeHtml(row.value)}</dd></div>`).join('')}</dl><p class="data-note">Wikidot reference values. Physical percentages describe damage multipliers; elemental percentages describe resistance. They use different scales.</p></section>` : ''}`;
    },
    enemyQuickFacts(enemy) {
        const result = [];
        for (const [key,name,icon] of [['hp','HP','stat-hp'],['souls','Souls','stat-souls']]) {
            const cycle=enemy.fact_cycles?.[key]||0,label=name+' ('+(cycle===0?'NG':cycle===1?'NG+':'NG+'+cycle)+')';
            if (enemy[key] != null && enemy[key] !== '') result.push(`<div class="stat"><img class="ico" src="assets/ui/stat/${icon}.webp" alt=""><span>${label}:</span> ${this.escapeHtml(enemy[key])}</div>`);
        }
        for (const [key,label] of [['can_parry','Parry'],['can_backstab','Backstab']]) {
            if (enemy[key] != null) result.push(`<div class="stat"><span>${label}:</span> ${enemy[key] ? 'Yes' : 'No'}${enemy.critical_notes?.[key] ? ` <span class="data-note">(${this.escapeHtml(enemy.critical_notes[key])})</span>` : ''}</div>`);
        }
        if(enemy.stat_notes)result.push(`<p class="data-note">${[...new Set(Object.values(enemy.stat_notes))].map(note=>this.escapeHtml(note)).join(' · ')}</p>`);
        if(enemy.can_parry===true)result.push('<p class="data-note">Parry means at least one documented attack can be deflected. It does not guarantee a riposte; jumping, ranged and special attacks can be exceptions.</p>');
        return result.join('');
    }
};
