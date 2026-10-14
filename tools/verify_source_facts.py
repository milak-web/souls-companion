"""Compare and optionally repair published weapon/armor numeric tables, without inferring missing values."""
from reference_audit import *
from collections import defaultdict,Counter
import sys,html
repair='--repair' in sys.argv
W=load('weapons');ARM=load('armor');UP=load('upgrades');checked=[];changes=[];unverified=[]
channels=['physical','magic','fire','lightning','dark'];scales=['str','dex','magic','fire','lightning','dark'];attrs=['str','dex','int','fth']
def put(record,field,value,source):
 old=record.get(field)
 checked.append({'name':record['name'],'field':field,'source':source,'matches':old==value})
 if old!=value:
  changes.append({'name':record['name'],'field':field,'old':old,'published':value,'source':source})
  if repair:record[field]=value
for w in W:
 u=w.get('source_url')
 if not u:unverified.append({'name':w['name'],'fields':'weapon stats','reason':'No source URL'});continue
 c=doc(u);found=False
 for h,rows in tables(c):
  if 'Damage' not in h or 'Stats Needed Stat Bonuses' not in h or not rows:continue
  cells=rows[0][1]
  if len(cells)!=len(h):continue
  v=dict(zip(h,map(text,cells)));needed=v['Stats Needed Stat Bonuses'].split();required=needed[0].split('/') if needed else [];grade=needed[-1].split('/') if needed else []
  if len(required)==4 and all(re.fullmatch(r'\d+(?:\.\d+)?|-',x) for x in required):put(w,'requirements',dict(zip(attrs,[float(x) if x!='-' else 0 for x in required])),u)
  if len(grade)==6 and all(x in ['S','A','B','C','D','E','-'] for x in grade):put(w,'scaling',dict(zip(scales,grade)),u)
  attacks=nums(v['Damage'])
  if len(attacks)>=5:put(w,'attack',dict(zip(channels,attacks[:5])),u)
  for src,dst in [('Weight','weight'),('Durability','durability'),('Counter Strength','counter_strength'),('Poise Damage','poise_damage'),('Stability','stability')]:
   val=nums(v.get(src,''))
   if len(val)==1:put(w,dst,val[0],u)
  for src,dst,keys in [('Damage Reduction','block_reduction',channels),('Aux Effects','auxiliary',['poison','bleed'])]:
   val=nums(v.get(src,''))
   if len(val)==len(keys):put(w,dst,dict(zip(keys,val)),u)
  found=True;break
 if not found:unverified.append({'name':w['name'],'fields':'baseline weapon stats','reason':'No supported individual table layout'})
 published=[]
 for h,rows in tables(c):
  if not {'Name','Damage','Stat Bonuses'}.issubset(h):continue
  for _,cells in rows:
   if len(cells)!=len(h):continue
   v=dict(zip(h,map(text,cells)));m=re.match(r'(.+?)\s*\+(\d+)$',v['Name']);damage=nums(v['Damage']);grade=v['Stat Bonuses'].replace(' ','').split('/')
   if not m or len(damage)<5 or len(grade) not in [5,6]:continue
   # Normal upgrade rows must identify this exact weapon, not a suffix match.
   names=[w['name'].removesuffix(' (weapon)').removesuffix(' (shield)'),*(w.get('aliases') or [])]
   if not any(key(m[1])==key(n) for n in names):continue
   if len(grade)==5:grade.append(w.get('scaling',{}).get('dark','?') if damage[4]==0 else '?')
   if not all(x in ['S','A','B','C','D','E','-','?'] for x in grade):continue
   if int(m[2])>0 and v.get('Materials Cost')=='-' and v.get('Souls')=='-':continue
   published.append({'path':'Normal','level':int(m[2]),'attack':dict(zip(channels,damage[:5])),'scaling':dict(zip(scales,grade))})
 existing=[r for r in w.get('upgrade_stats',[]) if r['path']=='Normal']
 for row in published:
  old=next((x for x in existing if x['level']==row['level']),None)
  checked.append({'name':w['name'],'field':'normal +'+str(row['level']),'source':u,'matches':old==row})
  if old!=row:
   changes.append({'name':w['name'],'field':'normal +'+str(row['level']),'old':old,'published':row,'source':u})
   if repair:w.setdefault('upgrade_stats',[]);w['upgrade_stats']=[r for r in w['upgrade_stats'] if not(r['path']=='Normal' and r['level']==row['level'])]+[row]
 if not published:unverified.append({'name':w['name'],'fields':'normal reinforcement rows','reason':'No supported exact-name rows'})
 if repair and w.get('attack'):w['base_damage']=w['attack']['physical'];w['physical_ar']=w['attack']['physical']
# Baseline armor tables; ambiguous same-name rows remain unassigned.
for source in sorted({r.get('source_url') for r in ARM if r.get('source_url')}):
 c=doc(source);candidates=defaultdict(list)
 for h,rows in tables(c):
  if not {'Name','Physical Defense','Resistance','Weight'}.issubset(h):continue
  elem='Elemental Defense' if 'Elemental Defense' in h else 'Magic Defense'
  if elem not in h:continue
  for _,cells in rows:
   if len(cells)!=len(h):continue
   v=dict(zip(h,map(text,cells)));r=find(ARM,v['Name'])
   if not r or r.get('pieces'):continue
   ph=nums(v['Physical Defense']);el=nums(v[elem]);rs=nums(v['Resistance'])
   if not(len(ph)==len(el)==len(rs)==4):continue
   stats=dict(zip(['physical','strike','slash','thrust'],ph));stats.update(zip(['magic','fire','lightning','dark'],el));stats.update(zip(['poison','bleed','petrify','curse'],rs))
   for k in ['Poise','Durability','Weight']:
    val=nums(v.get(k,''))
    if len(val)==1:stats[k.lower()]=val[0]
   candidates[r['id']].append(stats)
 for ident,values in candidates.items():
  r=next(r for r in ARM if r['id']==ident)
  if any(v!=values[0] for v in values[1:]):unverified.append({'name':r['name'],'fields':'baseline armor','reason':'Ambiguous published variant rows'});continue
  put(r,'defenses_base',values[0],source)
# Maximum armor is published as an embedded sortable Google-style table.
for slot in ['head','chest','hands','legs']:
 for frame in doc('/'+slot).select('iframe[src]'):
  source=url(frame['src']);raw=str(doc(source));rows=defaultdict(dict)
  for m in re.finditer(r"data\.setCell\(\s*(\d+)\s*,\s*(\d+)\s*,\s*((?:'[^']*')|[-\d.]+)\s*,\s*'((?:\\.|[^'])*)'",raw,re.S):rows[int(m[1])][int(m[2])]=(m[3].strip("'"),m[4])
  for row in rows.values():
   if 0 not in row or 12 not in row:continue
   r=find(ARM,row[0][0]);label=text(BeautifulSoup(row[0][1],'html.parser'));level=re.search(r'\+(\d+)',label)
   if not r or not level:continue
   ph=nums(text(BeautifulSoup(row[1][1],'html.parser')))
   if len(ph)!=4:continue
   stats=dict(zip(['physical','strike','slash','thrust'],ph))
   for i,k in enumerate(['magic','fire','lightning','dark','poise','poison','bleed','petrify','curse','durability','weight'],2):
    if i in row:
     try:stats[k]=float(row[i][0])
     except ValueError:pass
   put(r,'defenses_max',stats,source);put(r,'max_level',int(level[1]),source)
   if repair:r['defenses_max_source']=BASE+'/'+slot
   if repair and not r.get('slot'):r['slot']=slot
if repair:
 save('weapons',W);save('armor',ARM)
 # Keep the blacksmith's existing normal attack rows in agreement with verified catalogs.
 for w in W:
  u=find(UP,w['name']);rows=[r for r in w.get('upgrade_stats',[]) if r['path']=='Normal']
  if not u or not rows:continue
  for channel,out in zip(channels,['phys','magic','fire','lightning','dark']):u[out]={str(r['level']):r['attack'][channel] for r in rows}
 save('upgrades',UP)
report={'checked_on':'2026-10-10','fields_checked':len(checked),'mismatches':changes,'repaired':repair,'unverified':unverified,'checked':checked}
(A/('source-fact-repairs.json' if repair else 'source-fact-check.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'fields_checked':len(checked),'mismatches':len(changes),'unverified':len(unverified),'repair':repair},indent=2))
