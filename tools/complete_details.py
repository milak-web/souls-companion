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
W=load('weapons');ARM=load('armor');I=load('items');AREAS=load('areas');B=load('bosses');UP=load('upgrades');RED=load('redirects');ARED=load('area_redirects')
# Category/navigation pages are not wearable armor.
nav={'custom-armor-set-comparison','heavy-armor-sets','light-armor-sets','medium-armor-sets','portal-dark-souls-ii','starting-armor-sets','unique-armor'}
removed=[x for x in ARM if x['id'] in nav];ARM=[x for x in ARM if x['id'] not in nav]
# Alternate names from the old catalog for the same pieces.
aliases={'Defender Helm':'Throne Defender Helm','Defender Mail':'Throne Defender Armor',"Defender's Gauntlet":'Throne Defender Gauntlets',"Defender's Leggings":'Throne Defender Leggings','Wanderer Manchettes':'Wanderer Manchette','Tattered Set':'Tattered Cloth Set'}
armor_redirects={}
for old,new in aliases.items():
 a=find(ARM,old);b=find(ARM,new)
 if a and b and a is not b:b.setdefault('aliases',[]).append(old);armor_redirects[a['id']]=b['id'];ARM.remove(a)
# Read base armor tables with both older Magic Defense and Elemental Defense headers.
for f in A.glob('reference-*-set.html'):
 c=soup(f.name.removeprefix('reference-').removesuffix('.html'));members=[]
 for t in c.select('table'):
  rows=t.select('tr');heads=[text(x).replace('_',' ') for x in rows[0].find_all(['th','td'],recursive=False)] if rows else []
  if not all(x in heads for x in ['Name','Physical Defense','Resistance','Weight']):continue
  for row in rows[1:]:
   cells=row.find_all(['td','th'],recursive=False)
   if len(cells)!=len(heads):continue
   vals=dict(zip(heads,map(text,cells)));a=find(ARM,vals['Name'])
   if not a:continue
   phy=nums(vals['Physical Defense']);elm=nums(vals.get('Elemental Defense',vals.get('Magic Defense','')));res=nums(vals['Resistance'])
   if len(phy)!=4 or len(elm)!=4 or len(res)!=4:continue
   stats=dict(zip(['physical','strike','slash','thrust'],phy));stats.update(zip(['magic','fire','lightning','dark'],elm));stats.update(zip(['poison','bleed','petrify','curse'],res))
   for k in ['Poise','Weight','Durability']:
    if nums(vals.get(k,'')):stats[k.lower()]=nums(vals[k])[0]
   a['defenses_base']=stats;members.append(a['id']);a['source_url']='https://darksouls2.wikidot.com/'+f.stem.removeprefix('reference-')
   loc=section(c,'Location');a['obtaining']=' '.join(text(n) for n in loc if n.name in ['p','ul'])
  if members:break
 setrec=find(ARM,f.stem.removeprefix('reference-'))
 if setrec and members and members!=[setrec['id']]:
  setrec['pieces']=list(dict.fromkeys(members));setrec['description']='Armor set comprising '+', '.join(next(x['name'] for x in ARM if x['id']==id) for id in members)+'.';setrec['source_url']='https://darksouls2.wikidot.com/'+f.stem.removeprefix('reference-')
  setrec['obtaining']=' '.join(text(n) for n in section(c,'Location') if n.name in ['p','ul'])
  effects=' '.join(text(n) for n in section(c,'Effects') if n.name in ['ul','p'])
  if effects:setrec['special_effect']=effects
# Slot table already contains verified piece-specific effects.
for a in ARM:
 if a.get('defenses_max') and not a.get('description'):a['description']=f"{a.get('slot','Armor').capitalize()} armor. Open its defense tables for equipment properties."
for name in ['Lion Mage Robe','Lion Mage Cuffs','Lion Mage Skirt']:
 a=find(ARM,name)
 if a:a['special_effect']='Increases casting speed by approximately 5%. The three pieces stack.';a['effect_source']='https://darksouls2.wikidot.com/casting-speed'
# Item purposes for reinforcement and infusion materials come from a dedicated mechanics index.
c=soup('materials')
for row in c.select('table tr'):
 cells=row.find_all(['td','th'],recursive=False)
 if len(cells)!=3:continue
 a=find(I,text(cells[1]))
 if not a:continue
 purpose=text(cells[2]);a['description']=purpose;a['usage']=purpose+(' Give the Dull Ember to Steady Hand McDuff, then choose Infuse Weapon. Consumes one stone and souls.' if 'stone' in a['name'].lower() else ' Choose Reinforce Weapon or Reinforce Armor at a suitable smith; materials and souls are consumed.');a['source_url']='https://darksouls2.wikidot.com/materials'
for slug in ['fire-seed','soul-of-a-giant','binoculars','key-to-the-embedded','petrified-dragon-bone','twinkling-titanite']:
 a=find(I,slug);c=soup(slug)
 if not a or not c:continue
 use=' '.join(text(n) for n in section(c,'Use') if n.name in ['p','ul'])
 if use:a['usage']=use;a['description']=use
 a['source_url']='https://darksouls2.wikidot.com/'+slug
 avail=section(c,'Availability');a['obtaining']=' '.join(text(n) for n in avail if n.name in ['p','ul'])
 a['acquisition_refs']=[{'name':text(link),'source_url':'https://darksouls2.wikidot.com'+link['href']} for n in avail for link in n.select('a[href]') if link['href'].startswith('/')]
 if slug=='soul-of-a-giant':a['soul_value']=10000;a['soul_warning']='Keep up to five in your inventory for the Vendrick fight: each halves his resistance multiplier, down from 32× to 1×.'
# Index variants have their full functional effect; avoid the old empty cards.
for name,purpose in [('Carvings','Equip a carving as a quick item and use it to play its corresponding voice phrase. These reusable multiplayer communication items do not deal damage.'),('Weapon Buff','A category of temporary weapon enchantments. Open a resin or spell entry for its individual effect and duration.'),('Crown of the Ivory King (helm)','Armor headpiece. See Crown of the Ivory King in the armor catalog for defenses and its regeneration effect.')]:
 a=find(I,name)
 if a:a['description']=purpose;a['usage']=purpose
# Shield source layouts occasionally omit cells or include notes. Use their explicit upgrade rows for attack and grades.
for slug in ['greatshield-of-glory','havel-s-greatshield','gyrm-greatshield']:
 w=find(W,slug);c=soup(slug)
 if not w or not c:continue
 w['source_url']='https://darksouls2.wikidot.com/'+slug;rows=[]
 for t in c.select('table'):
  rs=t.select('tr');hd=[text(x) for x in rs[0].find_all(['th','td'],recursive=False)] if rs else []
  if 'Name' not in hd or 'Damage' not in hd or 'Stat Bonuses' not in hd:continue
  for r in rs[1:]:
   cs=r.find_all(['td','th'],recursive=False)
   if len(cs)!=len(hd):continue
   d=dict(zip(hd,map(text,cs)));m=re.match(r'(.+?)\s*\+(\d+)$',d['Name']);v=nums(d['Damage']);g=re.findall('[SABCDE-]',d['Stat Bonuses'])
   if not m or len(v)<5 or len(g)!=6:continue
   path=m[1].removesuffix(w['name']).strip() or 'Normal';row={'path':path,'level':int(m[2]),'attack':dict(zip(['physical','magic','fire','lightning','dark'],v[:5])),'scaling':dict(zip(['str','dex','magic','fire','lightning','dark'],g))};rows.append(row)
   if path=='Normal' and row['level']==0:
    w['attack']=row['attack'];w['scaling']=row['scaling'];w['block_reduction']=dict(zip(['physical','magic','fire','lightning','dark'],nums(d.get('Damage Reduction',d.get('Damage Reduction %','')))[:5]));w['stability']=nums(d.get('Stability','0'))[0]
 if rows:w['upgrade_stats']=rows
 w['description']='Greatshield for blocking attacks; its attack rating describes shield bashes. Stability governs stamina loss when blocking.'
 normal=[r for r in rows if r['path']=='Normal'];u=find(UP,w['name'])
 if u and normal:
  u['maxLevel']=max(r['level'] for r in normal)
  for ch,old in zip(['physical','magic','fire','lightning','dark'],['phys','magic','fire','lightning','dark']):u[old]={str(r['level']):r['attack'][ch] for r in normal}
# Rebuild bonfire lists from individual area descriptions, preserving their source directions.
for area in AREAS:
 c=soup(area.get('source_url','').split('/')[-1]);details=[]
 if c:
  for n in section(c,'Bonfires'):
   for li in n.select('li'):
    title=li.select_one('strong,b')
    if title:
     name=text(title).rstrip(':');location=text(li).removeprefix(name).strip()
     if location:details.append({'name':name,'location':location,'source_url':area['source_url'],'screenshots':[]})
  if details:area['bonfires']=[f['name'] for f in details];area['bonfire_details']=details
 # Canonical aliases should not create duplicate bosses.
 aliases={'Prowling Magus & Congregation':'Prowling Magus and Congregation','Throne Defender & Throne Watcher':'Throne Watcher and Defender','King Vendrick':'Vendrick','Lost Sinner':'The Lost Sinner','Velstadt the Royal Aegis':'Velstadt, the Royal Aegis','Mytha the Baneful Queen':'Mytha, the Baneful Queen','Graverobber, Varg and Cerah':'Afflicted Graverobber, Ancient Soldier Varg, and Cerah the Old Explorer'}
 area['bosses']=list(dict.fromkeys(aliases.get(n,n) for n in area.get('bosses',[])))
 if area['id']=='lost_bastille':area['bosses']=['Ruin Sentinels']
 if area['id']=='iron-passage':area['bosses']=['Smelter Demon (Iron Passage)']
 if area['id']=='frigid-outskirts':area['bosses']=['Lud and Zallen, the King’s Pets'] if find(B,'Lud and Zallen, the King’s Pets') else [b['name'] for b in B if 'Lud' in b['name']]
for id,name,path,caption,source in [('majula','The Far Fire','assets/bonfires/far-fire.jpg','The Far Fire on the cliff overlooking Majula.','https://www.svg.com/939253/tragic-details-you-missed-in-dark-souls-2/'),('forest_of_fallen_giants','Cardinal Tower','assets/bonfires/cardinal-tower.jpg','Cardinal Tower bonfire, identified by its in-game bonfire menu.','https://steamcommunity.com/sharedfiles/filedetails/?id=254338375')]:
 a=next(a for a in AREAS if a['id']==id);f=next(f for f in a['bonfire_details'] if key(f['name'])==key(name));f['screenshots']=[{'image':path,'caption':caption,'source_url':source}]
for n,d in [('weapons',W),('items',I),('armor',ARM),('areas',AREAS),('upgrades',UP),('armor_redirects',armor_redirects)]:save(n,d)
summary={'areas':len(AREAS),'bonfires':sum(len(a['bonfires']) for a in AREAS),'bonfires_with_screenshots':2,'armor_records':len(ARM),'removed_armor_navigation':[a['name'] for a in removed],'armor_stat_gaps':[a['name'] for a in ARM if not a.get('pieces') and not a.get('defenses_base') and not a.get('defenses_max')],'item_use_gaps':[a['name'] for a in I if not a.get('usage')],'weapon_scaling_gaps':[w['name'] for w in W if len(w.get('scaling',{}))!=6]}
(A/'detail-coverage.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
