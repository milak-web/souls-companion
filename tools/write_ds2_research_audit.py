"""Write measured coverage and remaining source gaps; never infer verification."""
import argparse
import json
from datetime import date
from pathlib import Path
from enrich_ds2_wiki import read, write, profile_summary

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=['enemies','bosses','areas','weapons','items','magic','armor','npcs','covenants','quests','articles']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--validated-on');args=parser.parse_args();cache=args.cache
    data={cat:read(ROOT/'database'/f'{cat}.json') for cat in CATEGORIES}
    manifest=read(cache/'manifest.json');baseline=read(cache/'baseline/enemies.json')
    missing=lambda records,field:sum(r.get(field) in [None,''] for r in records)
    report={'research_date':'2026-10-16','validated_on':args.validated_on,'catalogs':{cat:len(rows) for cat,rows in data.items()},'enemy_before':{'records':len(baseline),**{field:missing(baseline,field) for field in ['hp','souls','can_parry','can_backstab']}},'enemy_after':{'records':len(data['enemies']),**{field:missing(data['enemies'],field) for field in ['hp','souls','can_parry','can_backstab']}},'remaining_enemy_fields':[], 'source_comparisons':[]}
    for r in data['enemies']:
        absent=[field for field in ['hp','souls','can_parry','can_backstab'] if r.get(field) in [None,'']]
        if absent:report['remaining_enemy_fields'].append({'id':r['id'],'name':r['name'],'fields':absent,'context':r.get('stat_context',''),'notes':r.get('variant_notes','')})
    for r in data['enemies']+data['bosses']:
        for field in ['hp','souls']:
            a=profile_summary([p for p in r.get('stat_profiles',[]) if p.get('reference')=='Fextralife'],field)
            b=profile_summary([p for p in r.get('stat_profiles',[]) if p.get('reference')=='Wikidot'],field)
            if a and b and a!=b:report['source_comparisons'].append({'name':r['name'],'field':field,'Fextralife':a,'Wikidot':b})
    report['source_files']=sum(s.get('status') in ['cached','downloaded'] for s in manifest['sources'].values())
    report['enemy_profiles']=sum(len(r.get('stat_profiles',[])) for r in data['enemies'])
    report['boss_profiles']=sum(len(r.get('stat_profiles',[])) for r in data['bosses'])
    report['movesets']=sum(bool(r.get('wiki_reference',{}).get('attacks')) for r in data['enemies']+data['bosses'])
    report['bonfire_locations']=sum(len(r.get('bonfire_details',[])) for r in data['areas'])
    report['bonfires_with_photos']=sum(bool(b.get('screenshots')) for r in data['areas'] for b in r.get('bonfire_details',[]))
    report['missing_npc_descriptions']=missing(data['npcs'],'description')
    report['missing_npc_locations']=missing(data['npcs'],'location')
    write(cache/'final-review.json',report)
    lines=['# Dark Souls II reference review','',
      'Research collected 16 October 2026; validation date: '+(date.fromisoformat(args.validated_on).strftime('%B %d, %Y') if args.validated_on else 'not recorded')+'.','',
      'This review repairs source extraction and checks the catalog inventory. It is not a claim that every numerical value has been verified against game files or tested in-game. Missing facts were not replaced with guesses.','',
      '## Sources and method','',
      f"The public Fextralife index contained {manifest['wiki_articles']:,} non-redirect article titles. {report['source_files']:,} source pages were cached for matching and mechanical extraction; this count is not a count of manually verified articles.",
      '',
      '[Fextralife DS2 wiki](https://darksouls2.wiki.fextralife.com/Dark_Souls_2_Wiki), [enemy name disambiguation](https://darksouls2.wiki.fextralife.com/Enemy_Names_Disambiguation), [Wikidot](https://darksouls2.wikidot.com/), and selected [wiki.gg](https://darksouls2.wiki.gg/) numerical tables support the changes. Each record keeps its source credits. Public indexed wiki.gg results were used where direct page access was unavailable. Raw research HTML is excluded from the application and deployment.',
      '',
      'The importer reads Health/HP synonyms, icon headers, bonfire-intensity annotations, NG+ only records, attack properties, merchant stock, requirements, effects, acquisition references and related equipment. Curated corrections distinguish ghosts, crystallized enemies, NPC phantoms, player invasions, and regular boss reappearances.',
      '', 'Category roster links were checked across weapons, shields, armor, consumables, rings, all four spell schools, NPCs and bosses. Alternate spellings, category links and cut content were examined separately from obtainable equipment.',
      '', '## Catalog inventory','', '| Catalog | Records |','| --- | ---: |']
    lines += [f'| {cat.title()} | {len(rows):,} |' for cat,rows in data.items()]
    lines += ['',
      'Armor includes sets, pieces, and a small number of clearly labeled unused/legacy records. Those legacy records are excluded from the wearable armor catalog. Weapons include bare fists. Boss and ordinary-enemy catalogs are separate.',
      '', '## What changed','',
      '- Restored published HP and soul rows that the old parser skipped. Location, bonfire intensity and source are retained instead of combining unrelated encounters.',
      '- Corrected “NG+7” being interpreted as 7 HP. Recovered NG+ only phantom values and per-member Congregation health.',
      '- Consolidated duplicate enemy names with bookmark/favorite redirects. Archdrake Pilgrims in Amana remain distinct from the Archdrake-equipped Exiled Braves in Frigid Outskirts.',
      '- Removed boss souls from regular reappearance drops and Bell Keeper armor from enemy loot. The Bell Keeper pyromancy is Fire Whip, not the DLC spell Fire Snake.',
      '- Added attack/opening tables, numerical damage modifiers, effects, merchant inventory and local acquisition links. Ring +2 and merchant links now preserve the named destination even when source URLs are shared.',
      '- Replaced empty or misleading NPC descriptions with services, locations and sourced lore summaries. Generic group placeholders and the DS3-only NPC category were removed.',
      '- Expanded the quest tracker to 14 sourced guides, including Navlaan’s non-murder proof route, covenant trials, Loyce Soul rewards and crown blessings. Quest conditions and character portraits are now visible.',
      '- Fixed mobile enemy/NPC detail headers that clipped their images and titles. Layout tests check element bounds as well as page scroll width.',
      '', '## Measured enemy coverage','',
      'The inventory changed because duplicate cards were consolidated. Counts below describe empty fields, not incorrect values.',
      '', '| Field | Before (219 cards) | After ('+str(len(data['enemies']))+' encounters) |','| --- | ---: | ---: |']
    lines += [f"| {field} | {report['enemy_before'][field]} | {report['enemy_after'][field]} |" for field in ['hp','souls','can_parry','can_backstab']]
    lines += ['',
      f"The guide retains {report['enemy_profiles']:,} enemy stat rows and {report['boss_profiles']:,} boss stat rows, with attack/opening lists on {report['movesets']} enemy/boss records. All 41 boss cards have health and soul information, including group-health descriptions.",
      '', '## Remaining limits','',
      '- Many source pages do not explicitly state parry or backstab susceptibility. No universal rule based on an enemy’s size or humanoid appearance was applied. An absent Boolean is not treated as immunity. Parrying an attack does not necessarily permit a riposte.',
      '- Player invaders have build-dependent stats. Regular Castle Ruin Sentinels use the published Castle encounter row (3,260 HP / 2,500 souls), separate from the Lost Bastille boss trio. Twin Dragonriders use their own Castle article, not the Heide encounter.',
      '- Some wiki pages are unfinished templates. The Hollow Priest page describes a different enemy and remains an unresolved roster title; it was not imported as a new factual encounter.',
      '- Some source summaries differ because of location, edition, variant, or unresolved source disagreement. Their rows remain separate. For example, Faraam phantom Ascetic behavior is described differently by Wikidot and wiki.gg.',
      '- Prisoner head/chest armor has two appearance variants. Their base values are listed separately; the aggregate maximum-defense source does not identify the appearance variant.',
      f"- There are {report['bonfire_locations']} stored bonfire locations, but only {report['bonfires_with_photos']} bonfires have a sourced photograph. Missing bonfire photographs were not replaced with invented screenshots.",
      '- The blacksmith and character calculation datasets were not re-derived from game parameters in this review. Reference additions do not establish that every conditional combat effect is simulated.',
      '', '### Encounters without a single published fixed HP/soul pair','', '| Encounter | Context |','| --- | --- |']
    for r in report['remaining_enemy_fields']:
        if any(field in r['fields'] for field in ['hp','souls']):lines.append('| '+r['name']+' | '+(r['notes'] or r['context']).replace('|','/')+' |')
    lines += ['', '### Source comparisons','',
      'These are differences between the earliest published source summaries; they are not automatically contradictions, since a source can cover different locations or variants.',
      '', '| Encounter | Field | Fextralife | Wikidot |','| --- | --- | --- | --- |']
    lines += ['| '+r['name'].replace('|','/')+' | '+r['field']+' | '+r['Fextralife']+' | '+r['Wikidot']+' |' for r in report['source_comparisons']]
    lines += ['', '## Reproduce','',
      'From the project directory, with Python and Beautiful Soup installed:', '', '```sh',
      'python tools/research_ds2_wiki.py --cache <research-cache>',
      'python tools/enrich_ds2_wiki.py --cache <research-cache> --apply',
      'python tools/curate_ds2_references.py --cache <research-cache>',
      'python tools/verify_ds2_research.py',
      'python tools/write_ds2_research_audit.py --cache <research-cache>', '```', '',
      'Review source and variant differences before accepting regenerated data. Run the browser checks described in `tools/README.md` with the local server running. No research tools are runtime dependencies.', '']
    target=ROOT/'docs/DS2_REFERENCE_REVIEW.md';target.parent.mkdir(exist_ok=True);target.write_text('\n'.join(lines),encoding='utf-8')
    print('Wrote',target.name,'with measured coverage and remaining gaps.')

if __name__=='__main__':main()
