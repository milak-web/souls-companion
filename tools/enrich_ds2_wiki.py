"""Fill DS2 reference gaps from collected wiki facts, retaining source disagreements."""
import argparse
import concurrent.futures
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from ds2_wiki_facts import body, text, rows, numeric, section_title, fex_enemy, wikidot_enemy, reference_facts, reference_tables, section_links
from research_ds2_wiki import key, BASE, CATALOGS

ROOT = Path(__file__).resolve().parents[1]


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def attacks(article):
    found = []
    for node in article.select('li'):
        heading = section_title(node)
        if not re.search(r'move.?set|attack', heading, re.I): continue
        value = text(node, False)
        name = value.split(':',1)[0].strip()
        if len(name.split()) > 7 or len(name) > 70 or re.match(r'can |physical damage|magic damage|inflicts |grapple', name, re.I): continue
        if not name or name.lower() in ['yes','no']: continue
        item = {'name':name}
        if re.search(r'can be parried', value, re.I): item['parry'] = 'Yes'
        if re.search(r'(?:can.?t|cannot) be parried', value, re.I): item['parry'] = 'No'
        if re.search(r'can be blocked', value, re.I): item['block'] = 'Yes'
        if re.search(r'(?:can.?t|cannot) be blocked', value, re.I): item['block'] = 'No'
        kinds = [word for word in ['Physical','Magic','Fire','Lightning','Dark','Poison','Bleed','Petrification','Curse'] if re.search(r'\b'+word+r'\b', value, re.I)]
        if kinds: item['damage'] = ', '.join(kinds)
        found.append(item)
    for table in article.select('table'):
        if not re.search(r'move.?set|attack', section_title(table), re.I): continue
        data=rows(table);headers=[]
        for row in data:
            if row and all(cell.name=='th' for cell in row):headers=[text(cell,False).lower() for cell in row];continue
            if not row:continue
            name = text(row[0],False)
            if name.lower().strip() in ['move','attack','description','move description','?','--','tba','two hit combo','two-handed attack']:continue
            if name and len(name.split()) <= 7 and len(name) < 70:
                item={'name':name}
                for i,header in enumerate(headers):
                    if i<len(row):
                        value=text(row[i],False).strip('; ')
                        if 'parri' in header or 'parry' in header:item['parry']=value
                        if 'block' in header:item['block']=value
                        if header in ['damage type','status effect']:item['damage']=', '.join(filter(None,[item.get('damage'),value]))
                found.append(item)
    return list({item['name']:item for item in found}.values())[:30]


def mech_facts(article):
    """Read short numeric effects, requirements and action affordances as facts."""
    found = []
    for node in article.select('li,p'):
        if node.find_parent('table') or node.find('ul') or node.find('ol'): continue
        heading = section_title(node)
        if not re.search(r'effect|use|usage|note|location|obtain|acquir|require|tip|spell', heading, re.I): continue
        value = text(node,False)
        if len(value)>600 or not re.search(r'\d', value): continue
        # Factual clauses, not full narrative paragraphs or in-game lore quotations.
        for sentence in re.split(r'(?<=[.!?])\s+|;\s+',value):
            if re.search(r'\bprobably\b|\baround \d|pretty similar|\bI (?:have|was|think|use)|needs? (?:testing|confirmation)|\bmaybe\b|not confirmed',sentence,re.I):continue
            if 0 < len(sentence.split()) <= 22 and re.search(r'\d',sentence) and re.search(r'HP|second|damage|soul|slot|cast|attun|durab|weight|intelligen|faith|strength|dexter|poison|bleed|stamina|resist|health|purchase|bought|sold|cost|\+\d|%',sentence,re.I):
                found.append(sentence.strip())
    return list(dict.fromkeys(found))[:8]


def profile_summary(profiles, field):
    available=[p for p in profiles if p.get(field) and numeric(p[field])]
    if not available:return None
    cycle=min(p['cycle'] for p in available)
    base = [p[field] for p in available if p['cycle']==cycle]
    if not base: return None
    vals = []
    for value in base:
        vals.extend(int(n.replace(',','')) for n in re.findall(r'\d[\d,]*',value))
    if not vals: return None
    result=f'{min(vals):,}' if min(vals) == max(vals) else f'{min(vals):,}–{max(vals):,}'
    return ('~' if any('~' in value for value in base) else '')+result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--categories',nargs='+',choices=CATALOGS,default=CATALOGS)
    args=parser.parse_args();cache=args.cache
    manifest=read(cache/'manifest.json')
    mappings={(r['category'],r['id']):r for r in manifest['records']}
    catalogs={name:read(ROOT/'database'/f'{name}.json') for name in CATALOGS if (ROOT/'database'/f'{name}.json').exists()}
    # Preserve a non-published baseline for a reproducible before/after audit.
    baseline=cache/'baseline';baseline.mkdir(exist_ok=True)
    for name, records in catalogs.items():
        if not (baseline/f'{name}.json').exists():write(baseline/f'{name}.json',records)
    wiki_sources=sorted({r.get('source_url') for name in ['enemies','bosses'] for r in catalogs[name] if str(r.get('source_url','')).startswith('https://darksouls2.wikidot.com/')})
    wd=cache/'wikidot';wd.mkdir(exist_ok=True)
    def obtain(url):
        target=wd/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
        if target.exists():return
        existing=ROOT/'audit'/'fresh-sources'/target.name
        if existing.exists():target.write_bytes(existing.read_bytes());return
        try:target.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SoulsCompanionReferenceAudit/2.3'}),timeout=25).read())
        except Exception:pass
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(obtain,wiki_sources))
    report={'checked_on':'2026-10-16','changes':[],'coverage':{},'critical_evidence':[],'source_conflicts':[],'unmatched':manifest['unmatched']}
    for category, records in catalogs.items():
        if category not in args.categories:continue
        enriched=0
        for record in records:
            match=mappings.get((category,record['id']));article=None;source=None
            if match:
                file=cache/(hashlib.sha256(match['title'].encode()).hexdigest()[:20]+'.html')
                if file.exists():article=body(file.read_bytes())
                source=BASE+'/'+urllib.parse.quote(match['title'].replace(' ','_'),safe='()_')
            if article is not None:
                record['wiki_reference']={'source_url':source,'title':match['title'],'checked_on':'2026-10-16','properties':reference_facts(article),'tables':reference_tables(article),'mechanics':mech_facts(article)}
                record['additional_sources']=list(dict.fromkeys([*record.get('additional_sources',[]),source]))
                if key(record['name']) != key(match['title']):record['aliases']=list(dict.fromkeys([*record.get('aliases',[]),match['title']]))
                acquisition=section_links(article,['location','acquir','obtain','where to','merchant','drop'])
                record['wiki_reference']['acquisition']=acquisition[:45]
                record['wiki_reference']['related']=section_links(article,['effect','use','note','require','trade','spell'])[:30]
                if category in ['items','magic','armor','weapons']:
                    if not record.get('obtaining') and acquisition:
                        record['obtaining']='Referenced locations, holders or vendors: '+', '.join(ref['name'] for ref in acquisition[:8])+'. See the linked acquisition references and source conditions below.'
                    if category in ['items','magic'] and not record.get('usage'):
                        facts=[fact for group in record['wiki_reference']['properties'] for fact in group['facts']]
                        use=next((fact['value'] for fact in facts if re.search(r'effect|usage|use|function',fact['label'],re.I)),None)
                        if use:record['usage']=use
                if category=='npcs':
                    names={key(name) for area in catalogs['areas'] for name in [area['name'],*area.get('aliases',[])]}
                    locations=[ref['name'] for ref in section_links(article,['location']) if key(ref['name']) in names]
                    merchant=any(re.search(r'price|cost|stock|souls',header,re.I) for table in record['wiki_reference']['tables'] for header in table['headers'])
                    role='merchant' if merchant else 'summon' if re.search(r'summon',record.get('role',''),re.I) else 'character'
                    if not record.get('description') or record.get('description','').startswith('Dark Souls II character.'):
                        record['description']=record['name']+' is a '+role+(' encountered in '+', '.join(dict.fromkeys(locations)) if locations else ' in Drangleic')+'.'
                    if not record.get('location') and locations:record['location']=', '.join(dict.fromkeys(locations))
                    if not record.get('use_notes') and record['wiki_reference']['mechanics']:record['use_notes']=' '.join(record['wiki_reference']['mechanics'][:3])
                if category not in ['enemies','bosses','areas','npcs','covenants','articles']:
                    record['acquisition_refs']=list({(r['name'],r['source_url']):r for r in [*record.get('acquisition_refs',[]),*acquisition]}.values())
                enriched+=1
            if category not in ['enemies','bosses']:continue
            existing_source=record.get('source_url','')
            oldfile=wd/(hashlib.sha256(existing_source.encode()).hexdigest()[:20]+'.html')
            wd_article=body(oldfile.read_bytes(),'wikidot') if oldfile.exists() else None
            other=wikidot_enemy(wd_article,record['name'],existing_source) if wd_article is not None else None
            primary=fex_enemy(article,record['name'],source) if article is not None else None
            new_profiles=[]
            for data in [primary,other]:
                if not data:continue
                new_profiles.extend(data['profiles'])
                for field,value in data['criticals'].items():
                    report['critical_evidence'].append({'name':record['name'],'field':field,'source':data['source'],**value})
                    if value.get('value') is not None:
                        if record.get(field)!=value['value']:report['changes'].append({'category':category,'id':record['id'],'field':field,'old':record.get(field),'new':value['value'],'source':data['source']})
                        record[field]=value['value']
                        record.setdefault('fact_sources',{})[field]=data['source']
                        if value.get('conditional'):record.setdefault('critical_notes',{})[field]=value.get('condition') or 'Some attacks or variants are exceptions; consult the attack list.'
            if new_profiles:
                record['stat_profiles']=list({(p['source'],p['context'],p['cycle'],p.get('hp'),p.get('souls')):p for p in new_profiles}.values())
                # Prefer the requested wiki for the headline; keep alternative source rows visible.
                for field in ['hp','souls']:
                    candidates=[d for d in [primary,other] if d and profile_summary(d['profiles'],field)]
                    selected=min(candidates,key=lambda d:min(p['cycle'] for p in d['profiles'] if p.get(field) and numeric(p[field]))) if candidates else None
                    if selected:
                        value=profile_summary(selected['profiles'],field)
                        if value:
                            if record.get(field)!=value:report['changes'].append({'category':category,'id':record['id'],'field':field,'old':record.get(field),'new':value,'source':selected['source']})
                            record[field]=value;record.setdefault('fact_sources',{})[field]=selected['source']
                            record.setdefault('fact_cycles',{})[field]=min(p['cycle'] for p in selected['profiles'] if p.get(field) and numeric(p[field]))
                record['stat_context']='Headline values use the earliest published cycle. Ranges distinguish encounter variants; the table retains location, cycle and source differences.'
                if primary and other:
                    for field in ['hp','souls']:
                        first=profile_summary(primary['profiles'],field);second=profile_summary(other['profiles'],field)
                        if first and second and first!=second:report['source_conflicts'].append({'name':record['name'],'field':field,'fextralife':first,'wikidot':second})
            for data in [primary,other]:
                if not data:continue
                record.setdefault('weaknesses',{}).update(data['weaknesses'])
                for channel,state in data['status_effects'].items():
                    if state=='resistant' and record.get('status_effects',{}).get(channel)=='immune':continue
                    record.setdefault('status_effects',{})[channel]=state
            if other and other.get('modifiers'):record['damage_modifiers']=other['modifiers']
            if article is not None:
                record['wiki_reference']['attacks']=attacks(article)
                drop_refs=section_links(article,['drops'])
                record['wiki_reference']['drops']=drop_refs[:35]
                if primary.get('respawn'):record['respawn']=primary['respawn']
            if wd_article is not None:
                if 'wiki_reference' not in record:record['wiki_reference']={'source_url':existing_source,'title':record['name'],'checked_on':'2026-10-16','properties':[],'mechanics':[],'reference':'Wikidot'}
                record['wiki_reference']['attacks']=list({row['name']:row for row in [*record['wiki_reference'].get('attacks',[]),*attacks(wd_article)]}.values())
            # Rates absent from a source are not estimated as percentages.
            for drop in record.get('drops',[]):
                if 'not verified' in str(drop.get('chance','')).lower():drop['chance']='Rate not published'
        report['coverage'][category]={'records':len(records),'fextralife_articles':enriched}
        print('Reviewed',category,len(records),'Fextralife matches',enriched,flush=True)
    for category in ['enemies','bosses']:
        if category not in report['coverage']:continue
        records=catalogs[category]
        report['coverage'][category]['missing']={field:sum(r.get(field) is None or r.get(field)=='' for r in records) for field in ['hp','souls','can_parry','can_backstab']}
    write(cache/'enrichment-audit.json',report)
    if args.apply:
        for name,records in catalogs.items():
            if name in args.categories:write(ROOT/'database'/f'{name}.json',records)
    print('Fact corrections:',len(report['changes']),'source disagreements retained:',len(report['source_conflicts']),flush=True)


if __name__=='__main__':main()
