"""Merge structured wiki.gg weapon templates into the local smith catalog.
Absent damage columns are zero; absent values in active columns remain unknown.
Material schedules are read from the downloaded template, not guessed.
"""
from pathlib import Path
import json,re,hashlib,urllib.parse
from reference_audit import load,save,A
CACHE=A/'wiki-gg';B=load('blacksmith');W=load('weapons');changes=[];used=[];unparsed=[]
def numeric(s):
 s=str(s).strip().replace(',','');return float(s) if re.fullmatch(r'\d+(\.\d+)?',s) else None
def blocks(s):
 for m in re.finditer(r'\{\{(Weapon (?:Standard|Special|Boss|Pyro) Upgrade)\b',s,re.I):
  start=m.start();i=start;depth=0
  while i<len(s)-1:
   if s[i:i+2]=='{{':depth+=1;i+=2
   elif s[i:i+2]=='}}':
    depth-=1;i+=2
    if depth==0:
     tabs=re.findall(r'\|-\|([^=\n]+)=',s[:start]);yield m[1],s[start+2:i-2],tabs[-1].strip() if tabs else None;break
   else:i+=1
def template_materials(kind):
 f=CACHE/(hashlib.sha256(('Template:'+kind).encode()).hexdigest()[:20]+'.json');d=json.loads(f.read_text(encoding='utf-8'));s=d['parse']['wikitext']['*'];out={}
 for level,chunk in re.findall(r'\|\s*\+(\d+)\s*\n(.*?)(?=\n\|-|\n\|\})',s,re.S):
  m=re.search(r'\[\[([^]]+)\]\]\s*x(\d+)',chunk)
  if m:out[int(level)]={'material':m[1],'quantity':int(m[2])}
 return out
materials={k:template_materials(k) for k in ['Weapon Standard Upgrade','Weapon Special Upgrade','Weapon Boss Upgrade','Weapon Pyro Upgrade']}
letters=list('ABCDEF');channels=['physical','magic','fire','lightning','dark'];scales=['str','dex','magic','fire','lightning','dark'];aux=['poison','bleed'];statuses=['poison','bleed','petrify','curse']
for e in B['equipment']:
 w=next(w for w in W if w['id']==e['id']);title={'claws-weapon':'Claws(weapon)'}.get(w['id'],w['name'].replace(' (weapon)','').replace(' (shield)',''));f=CACHE/(hashlib.sha256(title.encode()).hexdigest()[:20]+'.json')
 if not f.exists():continue
 j=json.loads(f.read_text(encoding='utf-8'))
 if 'parse' not in j:continue
 source='https://darksouls2.wiki.gg/wiki/'+urllib.parse.quote(j['parse']['title'].replace(' ','_'),safe="_'()")
 paths={};steps={}
 for kind,body,tab in blocks(j['parse']['wikitext']['*']):
  d=dict((m[1].strip(),m[2].strip()) for m in re.finditer(r'^\|([^=\n]+)=(.*)$',body,re.M));path=tab if tab in ['Standard','Special','Boss','Basic','Normal',*B['infusions']] else d.get('UpgradeType','Standard');path={'Standard':'Normal','Special':'Normal','Boss':'Normal','Basic':'Normal'}.get(path,path)
  if path not in ['Normal',*B['infusions']]:unparsed.append({'weapon':w['id'],'template':kind,'path':path});continue
  levels=sorted({int(m[1]) for k in d for m in [re.match(r'Damage(\d+)(?: [A-E])?$',k)] if m});rows=[]
  active_fields={}
  for field in d:
   fm=re.fullmatch(r'(.+?)(\d+) ([A-F])',field)
   if fm:active_fields.setdefault(fm[1],set()).add(fm[3])
  def channel_values(prefix,keys,level):
   out={}
   for letter,key in zip(letters,keys):
    active=letter in active_fields.get(prefix,set())
    out[key]=(0 if d.get(f'{prefix}{level} {letter}') in ['-',''] else numeric(d.get(f'{prefix}{level} {letter}'))) if active else 0
   return out
  for level in levels:
   if kind=='Weapon Pyro Upgrade':
    attack=dict.fromkeys(channels,0);attack['fire']=numeric(d.get(f'Damage{level}'));scale=dict.fromkeys(scales,'-');scale['fire']=d.get(f'Bonus{level}','?');coef=dict.fromkeys(scales,0);coef['fire']=numeric(d.get(f'BonusPercent{level}'))
   else:
    attack=channel_values('Damage',channels,level);scale={k:(d.get(f'Bonus{level} {letter}') or '-') for letter,k in zip(letters,scales)};coef=channel_values('BonusPercent',scales,level)
    for letter,key in zip(letters,scales):
     if scale[key] not in ['-','?'] and f'BonusPercent{level} {letter}' not in d:coef[key]=None
   row={'level':level,'attack':attack,'auxiliary':channel_values('Aux',aux,level),'scaling':scale,'scaling_percent':coef,'aux_scaling_percent':channel_values('Bonus Aux',aux,level),'source_url':source}
   for prefix,key,keys in [('Damage Reduction','block_reduction',channels),('Status Buildup Reduction','status_reduction',statuses)]:
    if any(k.startswith(prefix+str(level)+' ') for k in d):row[key]=channel_values(prefix,keys,level)
   if f'Stability{level}' in d:row['stability']=numeric(d[f'Stability{level}'])
   rows.append(row)
   if path=='Normal' and level>0:
    steps[str(level)]={**materials[kind].get(level,{'material':None,'quantity':None}),'souls':numeric(d.get(f'Soul Cost{level}')),'source_url':source}
  if rows:
   paths[path]={'rows':rows,'source_url':source,'missing_levels':[]}
   if path!='Normal':paths[path].update(stone=B['infusions'][path],souls=2000)
 if 'Normal' not in paths:unparsed.append({'weapon':w['id'],'reason':'No normal template rows'});continue
 for p,pr in paths.items():
  for row in pr['rows']:
   old=next((r for r in w.get('upgrade_stats',[]) if r['level']==row['level'] and {'Lacerating':'Bleed'}.get(r['path'],r['path'])==p),None)
   if old:
    for field in ['attack','scaling']:
     if old.get(field) is not None and old[field]!=row[field]:changes.append({'weapon':w['id'],'path':p,'level':row['level'],'field':field,'older':old[field],'current':row[field]})
 e['older_source_url']=w.get('source_url');e.update(source_url=source,paths=paths,steps=steps,max_level=max(r['level'] for r in paths['Normal']['rows']))
 e.pop('unavailable_reason',None);used.append(w['id'])
 # Real game infusability is supplied independently of buffability.
 m=re.search(r'\|Can Be Infused\?\s*=([^\n]+)',j['parse']['wikitext']['*'])
 if m:e['infusion_note']=m[1].strip()
 for p,pr in e['paths'].items():pr['missing_levels']=[n for n in range(e['max_level']+1) if not any(r['level']==n for r in pr['rows'])]
save('blacksmith',B)
stats={'structured_weapons':len(used),'rows':sum(len(p['rows']) for e in B['equipment'] for p in e['paths'].values()),'fully_documented_coefficients':sum(all(v is not None for v in row.get('scaling_percent',{}).values()) and len(row.get('scaling_percent',{}))==6 for e in B['equipment'] for p in e['paths'].values() for row in p['rows']), 'missing_attack_rows':sum(any(v is None for v in row['attack'].values()) for e in B['equipment'] for p in e['paths'].values() for row in p['rows']), 'missing_cost_steps':sum(any(s.get(k) is None for k in ['material','quantity','souls']) for e in B['equipment'] for s in e['steps'].values())}
(A/'blacksmith-structured-check.json').write_text(json.dumps({'stats':stats,'used':used,'source_differences':changes,'unparsed':unparsed},indent=2)+'\n',encoding='utf-8');print(json.dumps({'stats':stats,'source_difference_count':len(changes),'unparsed':unparsed},indent=2))
