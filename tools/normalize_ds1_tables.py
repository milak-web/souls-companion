from import_ds1 import *
import math
p=json.loads((OUT/'parameters.json').read_text());records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'));guide=json.loads((OUT/'guide.json').read_text(encoding='utf-8'))
pathids={'Basic':0,'Normal':0,'Regular':0,'Crystal':100,'Lightning':200,'Raw':300,'Magic':400,'Enchanted':500,'Divine':600,'Occult':700,'Fire':800,'Chaos':900,'Upgrades':0};corrected=[]
for entry in records:
 if entry['category']!='weapons' or not entry.get('param_id'):continue
 ident=entry['param_id'];w=p['param']['EquipParamWeapon'];reinf=p['param']['ReinforceParamWeapon'];count=0
 for table in entry['tables']:
  heads=table['rows'][0]
  if 'Damage'not in heads or 'Name'not in heads or table['heading']not in pathids:continue
  path=pathids[table['heading']]
  for row in table['rows'][1:]:
   if len(row)!=len(heads):continue
   level=re.search(r'\+(\d+)',row[heads.index('Name')]);level=int(level[1])if level else 0
   damage=row[heads.index('Damage')];match=re.match(r'^(\d+)/(\d+)/(\d+)/(\d+)(?:\s|$)',damage)
   if not match:continue
   item=p['EquipParamWeapon'].get(str(ident+path if ident not in [1330000,1332000]else ident+100*level))
   if not item:continue
   reinforce=p['ReinforceParamWeapon'].get(str(item[w['REINFORCE_ID']]+(level if ident not in [1330000,1332000]else 0)))
   if not reinforce:continue
   expected=list(map(int,match.groups()));actual=[math.floor(round(item[w[k+'_ATK']]*reinforce[reinf[k+'_ATK_CORRECT']],4))for k in ['PHYSICAL','MAGIC','FIRE','LIGHTNING']]
   if expected!=actual:
    count+=1;row[heads.index('Damage')]='/'.join(map(str,actual))+damage[match.end(4):]
    corrected.append({'weapon':entry['id'],'path':table['heading'],'level':level,'original':expected,'corrected':actual})
 if count:entry['reinforcement_note']='Reinforcement attack figures follow the archived DS1 parameter tables. Older wiki cells that disagreed were corrected; the original comparison remains in the local audit.'
# Soul recipe outputs are the entries after "craft", not their precursor weapons.
for id,entry in guide['entries'].items():
 if id not in {r['id']for r in records}:continue
 sections=entry.get('sections',[])
 if not any(s['title']=='Consume or exchange'for s in sections):continue
 c=BeautifulSoup(fetch(id),'html.parser').select_one('#page-content');outputs=[];recipes=[]
 for n in c.select('li,p'):
  text=txt(n);index=text.lower().find('craft')
  if index<0 or len(text)>600:continue
  named=[a['href'].strip('/')for a in n.select('a[href]')if a['href'].strip('/')in {r['id']for r in records}]
  after=[rid for rid in named if next(r for r in records if r['id']==rid)['category']=='weapons'and text.rfind(next(r for r in records if r['id']==rid)['name'])>=index]
  if after:
   outputs+=after;recipes.append('Equipment result: '+', '.join(next(r for r in records if r['id']==rid)['name']for rid in after)+'. The Giant Blacksmith combines this soul with a compatible +10 precursor; check each equipment entry for its base weapon class.')
 if recipes:
  s=next(s for s in sections if s['title']=='Consume or exchange');s['paragraphs']=[f"Consumption reward: {next(r for r in records if r['id']==id)['soul_value']:,} souls."]+recipes+[p for p in s['paragraphs']if p.startswith(('Ciaran','Covenant'))];s['ids']=outputs+['giant-blacksmith']+[rid for rid in s['ids']if any(k in rid for k in ['tracer','sunlight-spear'])]
(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
(CACHE/'table-corrections.json').write_text(json.dumps({'corrected_cells':len(corrected),'rows':corrected,'cross_checks':['https://darksouls.wikidot.com/reinforcement-formulas','https://darksouls.fandom.com/wiki/Balder_Shield'],'notes':'Parameter values are retained rather than silently copying older wiki shield tables.'},indent=2))
print('Corrected',len(corrected),'attack cells')
