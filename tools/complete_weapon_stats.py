from pathlib import Path
import json,re,html
from bs4 import BeautifulSoup
P=Path('.');D=P/'database';A=P/'audit'
load=lambda n:json.loads((D/(n+'.json')).read_text(encoding='utf-8-sig'))
def save(n,x):(D/(n+'.json')).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(n):
 for sup in n.select('sup.footnoteref'):sup.decompose()
 return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def key(s):return re.sub('[^a-z0-9]+',' ',s.lower().replace('`',"'")).strip().removeprefix('the ')
def find(d,n):return next((x for x in d if key(n) in [key(x['name']),key(x['id']),*[key(y) for y in x.get('aliases',[])]]),None)
def soup(slug):
 p=A/('reference-'+slug+'.html');p=p if p.exists() else A/(slug+'.html');return BeautifulSoup(p.read_bytes(),'html.parser').select_one('#page-content') if p.exists() else None
def section(c,label):
 h=next((h for h in c.select('h1,h2,h3') if text(h).lower()==label.lower()),None);out=[]
 if not h:return out
 for n in h.next_siblings:
  if getattr(n,'name',None) in ['h1','h2']:break
  if getattr(n,'name',None):out.append(n)
 return out
def nums(s):return [float(x) for x in re.findall(r'\d+(?:\.\d+)?',s)]

import csv
W=load('weapons');UP=load('upgrades');jobs=load('weapons')
linked=json.loads((A/'reference-jobs.json').read_text(encoding='utf-8'));channels=['physical','magic','fire','lightning','dark'];scales=['str','dex','magic','fire','lightning','dark']
for w in W:
 # A cached page linked by the reference index and matching the record's own slug wins over shorthand hyperlinks.
 href='/'+w['id']
 if href not in linked:href=w.get('source_url','').removeprefix('https://darksouls2.wikidot.com')
 c=soup(href.strip('/')) if href else None
 if not c:continue
 w['source_url']='https://darksouls2.wikidot.com'+href
 for t in c.select('table'):
  rs=t.select('tr');hd=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)] if rs else []
  if 'Damage' not in hd or 'Stats Needed Stat Bonuses' not in hd:continue
  cells=rs[1].find_all(['td','th'],recursive=False) if len(rs)>1 else [];vals=dict(zip(hd,map(text,cells)))
  reqtext=vals.get('Stats Needed Stat Bonuses','');parts=reqtext.split();req=parts[0].split('/') if parts else []
  if len(req)==4:w['requirements']=dict(zip(['str','dex','int','fth'],[float(x) if x not in ['-',''] else 0 for x in req]))
  grades=parts[-1].split('/') if parts else []
  if len(grades)==6:w['scaling']=dict(zip(scales,grades))
  dmg=nums(vals.get('Damage',''))
  if len(dmg)>=5:w['attack']=dict(zip(channels,dmg[:5]));w['base_damage']=dmg[0];w['physical_ar']=dmg[0]
  for src,dst in [('Weight','weight'),('Durability','durability'),('Counter Strength','counter_strength'),('Poise Damage','poise_damage'),('Stability','stability')]:
   v=nums(vals.get(src,''))
   if v:w[dst]=v[0]
  if 'Enchantable? Items/Spells' in vals:w['buffable']=vals['Enchantable? Items/Spells']
  elif 'Enchantable' in vals:w['buffable']=vals['Enchantable']
  blocks=nums(vals.get('Damage Reduction',''))
  if len(blocks)>=5:w['block_reduction']=dict(zip(channels,blocks[:5]))
  aux=nums(vals.get('Aux Effects',''))
  if len(aux)>=2:w['auxiliary']=dict(zip(['poison','bleed'],aux[:2]))
  break
 rows=[]
 for t in c.select('table'):
  rs=t.select('tr');hd=[text(x) for x in rs[0].find_all(['th','td'],recursive=False)] if rs else []
  if not all(k in hd for k in ['Name','Damage','Stat Bonuses']):continue
  for r in rs[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)!=len(hd):continue
   d=dict(zip(hd,map(text,cells)));m=re.match(r'(.+?)\s*\+(\d+)$',d['Name']);v=nums(d['Damage']);g=d['Stat Bonuses'].replace(' ','').split('/')
   if not m or len(v)<5 or len(g) not in [5,6]:continue
   if len(g)==5:g.append(w.get('scaling',{}).get('dark','?') if v[4]==0 else '?')
   if any(grade not in ['S','A','B','C','D','E','-','?'] for grade in g):continue
   prefix=m[1]
   # Restrict each row to this weapon, preventing similar suffix names from being assigned to the wrong weapon.
   suffix=next((n for n in [w['name'],*w.get('aliases',[])] if key(prefix)==key(n) or prefix.lower().endswith(n.lower())),None)
   if not suffix:continue
   path=prefix[:len(prefix)-len(suffix)].strip() or 'Normal'
   rows.append({'path':path,'level':int(m[2]),'attack':dict(zip(channels,v[:5])),'scaling':dict(zip(scales,g))})
 if rows:w['upgrade_stats']=list({(r['path'],r['level']):r for r in rows}.values())
 normal=[r for r in w.get('upgrade_stats',[]) if r['path']=='Normal'];u=find(UP,w['name'])
 if normal and u:
  u['maxLevel']=max(r['level'] for r in normal)
  for ch,old in zip(channels,['phys','magic','fire','lightning','dark']):u[old]={str(r['level']):r['attack'][ch] for r in normal}
 # Functional availability, effects and notes belong on the weapon card.
 w['obtaining']=' '.join(text(n) for n in section(c,'Availability') if n.name in ['p','ul'])
 effect=' '.join(text(n) for n in section(c,'Effects') if n.name in ['p','ul'])
 if effect:w['special_effect']=effect
 notes=' '.join(text(n) for n in section(c,'Notes') if n.name in ['p','ul'])
 if notes:w['mechanics_notes']=notes
 w.pop('max_scaling_percent',None);w.pop('coefficient_level',None)
for row in csv.DictReader((A/'18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY.csv').read_text(encoding='utf-8-sig').splitlines()):
 if row['Infusion']!='Uninfused':continue
 w=find(W,row['Name']);u=find(UP,row['Name'])
 if not w or not u:continue
 try:coef=dict(zip(scales,[float(row['Scaling '+label]) for label in ['STR','DEX','Magic','Fire','Lightning','Dark']]));damage=dict(zip(channels,[float(row['Base '+ch]) for ch in ['Physical','Magic','Fire','Lightning','Dark']]))
 except ValueError:continue
 normal=next((r for r in w.get('upgrade_stats',[]) if r['path']=='Normal' and r['level']==u['maxLevel']),None)
 if normal and all(abs(damage[ch]-normal['attack'][ch])<1.1 for ch in channels):w['max_scaling_percent']=coef;w['coefficient_level']=u['maxLevel'];w['scaling_source']='https://docs.google.com/spreadsheets/d/18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY/edit#gid=0'
save('weapons',W);save('upgrades',UP)
print(json.dumps({'weapons':len(W),'complete_scaling':sum(len(w.get('scaling',{}))==6 for w in W),'normal_reinforcement_rows':sum(any(r['path']=='Normal' for r in w.get('upgrade_stats',[])) for w in W),'verified_max_coefficients':sum(bool(w.get('max_scaling_percent')) for w in W),'greatsword':find(W,'Greatsword')['attack']}))
