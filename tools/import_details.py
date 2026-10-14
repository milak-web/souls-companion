"""Import mechanical facts and relationships from cached, linked DSII reference pages."""
from pathlib import Path
from collections import defaultdict
import re,json,csv,html
from bs4 import BeautifulSoup
P=Path(__file__).resolve().parents[1];A=P/'audit';D=P/'database'
load=lambda n:json.loads((D/f'{n}.json').read_text(encoding='utf-8-sig'))
def save(n,x):(D/f'{n}.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def key(s):return re.sub('[^a-z0-9]+',' ',str(s).lower().replace('`',"'")).strip().removeprefix('the ')
def cleanname(s):return re.sub(r'\s*\((?:weapon|shield|helm)\)$','',s,flags=re.I)
def find(records,name):
 k=key(cleanname(name));hits=[x for x in records if k in {key(cleanname(x.get('name',''))),key(x.get('id','')),*[key(a) for a in x.get('aliases',[])]}];return hits[0] if len(hits)==1 else None
def soup(href):
 slug=href.strip('/').split('#')[0].replace('/','_');f=A/('reference-'+slug+'.html');f=f if f.exists() else A/(slug+'.html')
 if not f.exists():return None
 c=BeautifulSoup(f.read_bytes(),'html.parser');return c.select_one('#page-content') or c
def text(n):
 copy=BeautifulSoup(str(n),'html.parser')
 for sup in copy.select('sup.footnoteref'):sup.decompose()
 return re.sub(r'\s+',' ',copy.get_text(' ',strip=True)).strip()
def numbers(s):return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',s)]
def slash(s,count):
 m=re.match(r'\s*((?:\d+(?:\.\d+)?\s*/\s*){'+str(count-1)+r'}\d+(?:\.\d+)?)',s);return numbers(m[1]) if m else None
def section(c,label):
 h=next((h for h in c.select('h1,h2,h3') if text(h).lower()==label.lower()),None)
 if not h:return []
 out=[]
 for n in h.next_siblings:
  if getattr(n,'name',None) in ['h1','h2'] or (h.name=='h3' and getattr(n,'name',None)=='h3'):break
  if getattr(n,'name',None):out.append(n)
 return out
W=load('weapons');I=load('items');ARM=load('armor');AREAS=load('areas');B=load('bosses');NPC=load('npcs');UP=load('upgrades')
channels=['physical','magic','fire','lightning','dark'];scales=['str','dex','magic','fire','lightning','dark'];attrs=['str','dex','int','fth']
# Build a source index from actual reference links; a URL slug is never guessed from a name.
refs={}
for f in list(A.glob('reference-*.html')) + [A/(slug+'.html') for slug in ['weapons','shields','spell-tools','areas','consumables','rings','keys','ammo','bonfire-items','multiplayer-items'] if (A/(slug+'.html')).exists()]:
 c=BeautifulSoup(f.read_bytes(),'html.parser');c=c.select_one('#page-content') or c
 for a in c.select('a[href]'):
  h=a['href'];name=text(a)
  if h.startswith('/') and name and not h.startswith('//'):refs.setdefault(key(name),h.split('#')[0])
weapon_count=0
for w in W:
 href=next((refs.get(key(n)) for n in [cleanname(w['name']),*w.get('aliases',[])] if refs.get(key(n))),None)
 if not href:continue
 c=soup(href)
 if not c:continue
 table=next((t for t in c.select('table') if t.select('tr') and 'Stats Needed Stat Bonuses' in [text(x) for x in t.select('tr')[0].find_all(['td','th'],recursive=False)] and 'Damage' in [text(x) for x in t.select('tr')[0].find_all(['td','th'],recursive=False)]),None)
 if not table:continue
 rows=table.select('tr');head=[text(x) for x in rows[0].find_all(['td','th'],recursive=False)];cells=rows[1].find_all(['td','th'],recursive=False)
 if len(cells)!=len(head):continue
 row=dict(zip(head,map(text,cells)));needed=row['Stats Needed Stat Bonuses'];parts=needed.split();req=slash(parts[0],4);bonus=re.findall(r'[SABCDE-]',parts[-1])
 if req:w['requirements']=dict(zip(attrs,req))
 if len(bonus)==6:w['scaling']=dict(zip(scales,bonus))
 damage=slash(row['Damage'],5)
 if damage:w['attack']=dict(zip(channels,damage));w['base_damage']=damage[0];w['physical_ar']=damage[0]
 for src,dst in [('Weight','weight'),('Durability','durability'),('Counter Strength','counter_strength'),('Poise Damage','poise_damage'),('Stability','stability')]:
  if src in row and numbers(row[src]):w[dst]=numbers(row[src])[0]
 aux=slash(row.get('Aux Effects',''),2)
 if aux:w['auxiliary']={'poison':aux[0],'bleed':aux[1]}
 match=re.search(r'\(([^)]+)\)',row['Damage'])
 if match:w['damage_type']=match[1]
 w['source_url']='https://darksouls2.wikidot.com'+href
 w['description']=f"{w.get('type') or 'Weapon'} dealing {w.get('damage_type') or 'the listed damage types'}. Its attack rating and scaling change with reinforcement and infusion."
 w['upgrade_stats']=[]
 for t in c.select('table'):
  rs=t.select('tr')
  if not rs:continue
  hd=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)]
  if 'Name' not in hd or 'Damage' not in hd or 'Stat Bonuses' not in hd:continue
  for r in rs[1:]:
   cs=r.find_all(['td','th'],recursive=False)
   if len(cs)!=len(hd):continue
   vals=dict(zip(hd,map(text,cs)));m=re.match(r'(.+?)\s*\+(\d+)$',vals['Name'])
   if not m:continue
   dmg=slash(vals['Damage'],5);grades=re.findall('[SABCDE-]',vals['Stat Bonuses'])
   if not dmg or len(grades)!=6:continue
   path=m[1].removesuffix(cleanname(w['name'])).strip() or 'Normal'
   w['upgrade_stats'].append({'path':path,'level':int(m[2]),'attack':dict(zip(channels,dmg)),'scaling':dict(zip(scales,grades))})
 u=find(UP,w['name'])
 normal=[x for x in w['upgrade_stats'] if x['path']=='Normal']
 if u and normal:
  for ch,old in zip(channels,['phys','magic','fire','lightning','dark']):u[old]={str(x['level']):x['attack'][ch] for x in normal}
  u['maxLevel']=max(x['level'] for x in normal)
 weapon_count+=1
# Exact coefficients are published for fully reinforced, uninfused weapons. No extrapolation to lower levels.
coeff_rows=list(csv.DictReader((A/'18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY.csv').read_text(encoding='utf-8-sig').splitlines()))
for row in coeff_rows:
 if row['Infusion']!='Uninfused':continue
 w=find(W,row['Name']);u=find(UP,row['Name'])
 if not w or not u:continue
 try:coef=dict(zip(scales,[float(row['Scaling '+label]) for label in ['STR','DEX','Magic','Fire','Lightning','Dark']]))
 except ValueError:continue
 # Match the published maximum base AR to the individual weapon page before enabling the coefficients.
 published=dict(zip(channels,[float(row['Base '+label]) for label in ['Physical','Magic','Fire','Lightning','Dark']]))
 normal=next((x for x in w.get('upgrade_stats',[]) if x['path']=='Normal' and x['level']==u['maxLevel']),None)
 if normal and all(abs(published[ch]-normal['attack'][ch])<1.1 for ch in channels):
  w['max_scaling_percent']=coef;w['coefficient_level']=u['maxLevel'];w['scaling_source']='https://docs.google.com/spreadsheets/d/18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY/edit#gid=0'
# Elemental attribute bonus curves, with exact 1..99 values from the reference tables.
SC=load('scaling');SC.setdefault('bns',{})
for name,ch in [('magic-atk-bonus','magic'),('lightning-atk-bonus','lightning'),('fire-atk-bonus','fire'),('dark-atk-bonus','dark')]:
 c=soup('/'+name);curve={}
 for r in c.select('table tr'):
  vals=[text(x) for x in r.find_all(['td','th'],recursive=False)]
  for i in range(0,len(vals)-1,2):
   if vals[i].isdigit() and vals[i+1].isdigit():curve[vals[i]]=int(vals[i+1])
 if len(curve)==99:SC['bns'][ch]=curve
# Armor maximum tables are embedded JS datasets, not HTML tables.
armor_max=0
for f in A.glob('reference-*html_*.html'):
 slot=f.name.split('-')[1].split('_')[0];raw=f.read_text(encoding='utf-8');rows=defaultdict(dict)
 pattern=r"data\.setCell\(\s*(\d+)\s*,\s*(\d+)\s*,\s*((?:'[^']*')|[-\d.]+)\s*,\s*'((?:\\.|[^'])*)'"
 for m in re.finditer(pattern,raw,re.S):rows[int(m[1])][int(m[2])]=(m[3].strip("'"),m[4])
 for row in rows.values():
  if 0 not in row or 12 not in row:continue
  name=row[0][0];a=find(ARM,name)
  if not a:continue
  label=BeautifulSoup(row[0][1],'html.parser').get_text(' ',strip=True);level=re.search(r'\+(\d+)',label)
  if not level:continue
  vals=slash(row[1][1],4)
  defense=dict(zip(['physical','strike','slash','thrust'],vals)) if vals else {}
  for idx,ch in enumerate(['magic','fire','lightning','dark','poise','poison','bleed','petrify','curse','durability','weight'],2):
   if idx in row:
    try:defense[ch]=float(row[idx][0])
    except ValueError:pass
  a['slot']=slot;a['defenses_max']=defense;a['max_level']=int(level[1]);a['source_url']='https://darksouls2.wikidot.com/'+slot
  if 17 in row:
   fragment=BeautifulSoup(row[17][1],'html.parser');p=fragment.select_one('[title]');info=html.unescape(p['title']).replace('\r','; ') if p else ''
   a['requirements']={}
   for val,stat in re.findall(r'(\d+)\s*(STR|DEX|INT|FTH)',info) if 'required' in info.lower() else []:a['requirements'][stat.lower()]=int(val)
   a['special_effect']=info if 'e' in row[17][0].lower() else 'No special effect is listed in the source table.'
   a['equipment_note']=info
  armor_max+=1
# Per-set pages provide baseline defenses, set membership and acquisition references.
armor_base=0
for f in A.glob('reference-*.html'):
 c=BeautifulSoup(f.read_bytes(),'html.parser');c=c.select_one('#page-content') or c
 for t in c.select('table'):
  rows=t.select('tr')
  if not rows:continue
  hd=[text(x) for x in rows[0].find_all(['td','th'],recursive=False)]
  if not all(x in hd for x in ['Name','Physical Defense','Elemental Defense','Resistance','Weight']):continue
  members=[]
  for r in rows[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)!=len(hd):continue
   vals=dict(zip(hd,map(text,cells)));a=find(ARM,vals['Name'])
   if not a:continue
   physical=slash(vals['Physical Defense'],4);elemental=slash(vals['Elemental Defense'],4);resist=slash(vals['Resistance'],4)
   if not all([physical,elemental,resist]):continue
   defense=dict(zip(['physical','strike','slash','thrust'],physical));defense.update(zip(['magic','fire','lightning','dark'],elemental));defense.update(zip(['poison','bleed','petrify','curse'],resist))
   for name in ['Poise','Weight','Durability']:
    if numbers(vals.get(name,'')):defense[name.lower()]=numbers(vals[name])[0]
   a['defenses_base']=defense;members.append(a['id']);a['source_url']='https://darksouls2.wikidot.com/'+f.stem.removeprefix('reference-')
   a['description']=f"{a.get('slot','Armor').capitalize()} armor. Weight: {defense.get('weight','not recorded')}; physical defense at +0: {defense['physical']}.";armor_base+=1
  if members:
   setrec=next((x for x in ARM if x['id']==f.stem.removeprefix('reference-')),None)
   if setrec:setrec['pieces']=members;setrec['source_url']='https://darksouls2.wikidot.com/'+f.stem.removeprefix('reference-');setrec['description']='Armor set comprising '+', '.join(next(a['name'] for a in ARM if a['id']==id) for id in members)+'.'
# Compact mechanical item descriptions and source relationships from index columns.
for source in ['consumables','rings','keys','ammo','bonfire-items','multiplayer-items','sorceries','hexes','pyromancies','miracles']:
 c=soup('/'+source)
 for t in c.select('table'):
  rs=t.select('tr')
  if not rs:continue
  hd=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)]
  if 'Name' not in hd:continue
  for r in rs[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)!=len(hd):continue
   vals=dict(zip(hd,map(text,cells)));a=cells[hd.index('Name')].select_one('a[href]')
   if not a:continue
   item=find(I,text(a))
   if not item:continue
   item['source_url']='https://darksouls2.wikidot.com'+a['href'].split('#')[0]
   kind={'rings':'Ring','keys':'Key','ammo':'Ammunition','bonfire-items':'Bonfire item','multiplayer-items':'Multiplayer item','sorceries':'Sorcery','hexes':'Hex','pyromancies':'Pyromancy','miracles':'Miracle'}.get(source,'Consumable')
   item['type']=kind;use=vals.get('Use',vals.get('Description',vals.get('Effect','')))
   if use:item['usage']=use;item['description']=kind+' — '+use
   availability=vals.get('Availability',vals.get('Location',''))
   if availability:item['obtaining']=availability
   # Structured locations and merchant references remain navigable even when prose is long.
   item['acquisition_refs']=[]
   for col in ['Availability','Location']:
    if col in hd:
     for link in cells[hd.index(col)].select('a[href]'):
      if link['href'].startswith('/'):item['acquisition_refs'].append({'name':text(link),'source_url':'https://darksouls2.wikidot.com'+link['href'].split('#')[0]})
   if kind in ['Sorcery','Hex','Pyromancy','Miracle']:
    item['spell_stats']={h:vals[h] for h in hd if any(word in h.lower() for word in ['uses','slots','int','fth','faith','type /'])}
# Detailed item pages: soul consumption and trades, mechanical formulas, sellers and location links.
for item in I:
 href=item.get('source_url','').removeprefix('https://darksouls2.wikidot.com') if item.get('source_url','').startswith('https://darksouls2.wikidot.com/') else refs.get(key(item['name']))
 if not href:continue
 c=soup(href)
 if not c:continue
 item['source_url']='https://darksouls2.wikidot.com'+href
 use_nodes=section(c,'Use') or section(c,'Usage');use=' '.join(text(n) for n in use_nodes if n.name!='table')
 if use and not item.get('usage'):item['usage']=use;item['description']=f"{item.get('type') or 'Item'} — {use}"
 if not item.get('type'):item['type']='Soul' if 'soul' in item['name'].lower() else 'Item'
 if not item.get('description') and item.get('usage'):item['description']=item['type']+' — '+item['usage']
 availability=section(c,'Availability');avtext=' '.join(text(n) for n in availability)
 if avtext and (not item.get('obtaining') or item['obtaining'].startswith('See the reference')):item['obtaining']=avtext
 if availability:
  item.setdefault('acquisition_refs',[])
  for n in availability:
   for a in n.select('a[href]'):
    if a['href'].startswith('/'):
     ref={'name':text(a),'source_url':'https://darksouls2.wikidot.com'+a['href'].split('#')[0]}
     if ref not in item['acquisition_refs']:item['acquisition_refs'].append(ref)
 item['trades']=[]
 for t in c.select('table'):
  rs=t.select('tr')
  if not rs:continue
  hd=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)]
  if 'Give Soul To' not in hd or 'Player Receives' not in hd:continue
  for r in rs[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)!=len(hd):continue
   vals=dict(zip(hd,map(text,cells)))
   if vals['Give Soul To'].lower()=='consume':
    amounts=numbers(vals['Player Receives'].replace(',',''))
    if amounts:item['soul_value']=int(amounts[0])
   else:
    products=[text(a) for a in cells[hd.index('Player Receives')].select('a')]
    item['trades'].append({'merchant':vals['Give Soul To'],'products':products or [vals['Player Receives']],'cost':vals.get('Cost','')})
 if item.get('soul_value') is not None:
  item['type']='Soul';item['usage']=f"Consume to gain {item['soul_value']:,} souls. Trade it instead if you want one of its listed rewards.";item['description']='A soul item that can be consumed for souls or exchanged for the rewards listed below.'
 formulas=re.findall(r'(?:\d+(?:\.\d+)?\s*(?:\+|[x×])\s*)+[^.\n]{0,55}(?:Bonus|BNS|damage)',use,flags=re.I)
 if formulas:item['damage_formulas']=formulas
 if item['id']=='ancient-dragon-soul':item['direct_drop']=False;item['description']='Recovered from the dragon corpse in Dragon Memories. The Ancient Dragon boss does not drop this soul.'
 if item['id']=='soul-of-the-king':item['direct_drop']=False
# Combat facts from the separately checked wiki.gg projectile entries.
for id,physical,poison in [('throwing-knife',180,0),('poison-throwing-knife',120,40)]:
 item=next(x for x in I if x['id']==id);item['combat_stats']={'base_physical_damage':physical,'dex_scaling_percent':26,'poison_buildup':poison,'poise_damage':15,'posture_damage':0};item['combat_source']='https://darksouls2.wiki.gg/wiki/'+item['name'].replace(' ','_');item['usage']='Equip in a quick-item slot and throw at a target. Actual physical damage depends on Dexterity and the target’s defenses.'
 if poison:item['usage']+=' Each hit applies 40 poison buildup; poison starts damaging health only when the target’s poison meter fills.'
 item['description']='Ranged consumable projectile'+(' that builds up poison.' if poison else ' that inflicts physical damage.')
# Area roster is restricted to playable map locations; keep redirects for removed duplicate/lore entries.
lore={'Eastern Land','Catarina','Lindelt','Melfia','Lanafir','Northern Sea','Olaphis','Forossa','Mirrah','Jugo'};redirects=load('redirects');area_redirects={};lore_records=load('lore_locations') if (D/'lore_locations.json').exists() else []
AREAS=[x for x in AREAS if not (x['name'] in lore and not lore_records.append({'id':x['id'],'name':x['name']}))]
# Filter above intentionally keeps gameplay areas; merge duplicate Lost Bastille explicitly.
old=next((x for x in AREAS if x['id']=='the-lost-bastille'),None)
if old:AREAS.remove(old)
main=next(x for x in AREAS if x['id']=='lost_bastille');main['name']='The Lost Bastille';main['aliases']=['Lost Bastille'];area_redirects=load('area_redirects') if (D/'area_redirects.json').exists() else {};area_redirects['the-lost-bastille']=main['id']
for a in AREAS:
 if a['name']=="Sinners' Rise":a['aliases']=[a['name']];a['name']="Sinner's Rise"
# The Pit is a traversable sub-area rather than a foreign kingdom.
if not find(AREAS,'The Pit'):AREAS.append({'id':'the-pit','name':'The Pit','image':'assets/areas/Majula.png','recommended_level':'','bonfires':[],'bosses':[],'enemies':[],'npcs':[],'items':[],'description':'The vertical route beneath Majula, connecting the hub to the Grave of Saints and the Gutter.'})
index=soup('/areas');indexrows=index.select('table')[0].select('tr')[1:]
for r in indexrows:
 cells=r.find_all(['td','th'],recursive=False)
 if len(cells)!=6:continue
 link=cells[0].select_one('a[href]')
 if not link:continue
 a=find(AREAS,text(link))
 if not a:continue
 a['source_url']='https://darksouls2.wikidot.com'+link['href'];a['connections']=[text(x) for x in cells[1].select('a')];a['bosses']=[text(x) for x in cells[2].select('a')];a['mini_bosses']=[text(x) for x in cells[3].select('a')]
 a['bonfires']=[s.strip() for s in cells[5].get_text('\n',strip=True).split('\n') if s.strip()!='None'];a['overview_notes']=text(cells[4])
# Per-area quick tables supply accurate inhabitants, loot and version notes.
for area in AREAS:
 href=area.get('source_url','').removeprefix('https://darksouls2.wikidot.com') or refs.get(key(area['name']))
 if not href:continue
 c=soup(href)
 if not c:continue
 area['source_url']='https://darksouls2.wikidot.com'+href;area['region']='DLC' if any(t in href for t in ['shulva','sanctum','brume','eleum','frigid','old-chaos','iron-passage','cave-of-the-dead','old-iron-king','dragon-s-rest']) else 'Drangleic'
 for t in c.select('table'):
  rs=t.select('tr')
  if len(rs)<2:continue
  hd=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)]
  if 'Enemies' not in hd:continue
  cells=rs[1].find_all(['td','th'],recursive=False)
  if len(cells)!=len(hd):continue
  for col,dst in [('Enemies','enemies'),('NPCs','npcs'),('Boss','bosses'),('Notable Loot','items')]:
   if col in hd:area[dst]=list(dict.fromkeys(text(x) for x in cells[hd.index(col)].select('a') if text(x)))
  area['version_notes']=text(cells[hd.index('Enemies')])
  break
 area['bonfire_details']=[]
 for block in section(c,'Bonfires'):
  nodes=block.select('li') or ([block] if block.name=='p' else [])
  for node in nodes:
   title=node.select_one('strong,b')
   if not title:continue
   name=text(title).rstrip(':');location=text(node).removeprefix(text(title)).strip()
   if not location:continue
   images=[{'url':im['src'],'caption':im.get('alt','')} for im in node.select('img[src]')]
   area['bonfire_details'].append({'name':name,'location':location,'source_url':area['source_url'],'screenshot_candidates':images,'screenshots':[]})
 # Do not let a narrative heading inflate the actual fast-travel bonfire count.
 known=area.get('bonfires',[])
 if not known and area['bonfire_details']:known=[x['name'] for x in area['bonfire_details']]
 detail={key(x['name']):x for x in area['bonfire_details']}
 area['bonfire_details']=[detail.get(key(name),{'name':name,'location':'Location details are linked in the area reference.','source_url':area['source_url'],'screenshots':[]}) for name in known]
 area['bonfires']=known
 if not area.get('description'):area['description']=f"{area['name']} is a playable {area['region']} location. Its bonfires, inhabitants, bosses and connected areas are listed below."
# Canonical boss area links take precedence over ambiguous miniature encounters.
for area in AREAS:
 boss=[b['name'] for b in B if any(key(place)==key(area['name']) for place in b.get('areas',[]))]
 area['bosses']=list(dict.fromkeys(area.get('bosses',[])+boss))
# Merge the bonfire overview landmarks where individual pages omit details, including DLC routes.
current=None
for r in soup('/bonfires').select('table')[0].select('tr')[1:]:
 cells=r.find_all(['td','th'],recursive=False)
 if len(cells)==5:current=find(AREAS,text(cells[0]));name=text(cells[1]);landmark=text(cells[2]);notes=text(cells[3])
 elif len(cells)==4:name=text(cells[0]);landmark=text(cells[1]);notes=text(cells[2])
 else:continue
 if not current:continue
 bonfire=next((x for x in current['bonfire_details'] if key(x['name'])==key(name)),None)
 if not bonfire:bonfire={'name':name,'location':landmark or 'See the area reference for the approach route.','source_url':'https://darksouls2.wikidot.com/bonfires','screenshots':[]};current['bonfire_details'].append(bonfire);current['bonfires'].append(name)
 if landmark and bonfire['location'].startswith('Location details'):bonfire['location']=landmark
 bonfire['landmark']=landmark;bonfire['notes']=notes
for armor_record in ARM:
 if armor_record.get('pieces')==[armor_record['id']]:armor_record.pop('pieces')
for name,data in [('weapons',W),('items',I),('armor',ARM),('areas',AREAS),('upgrades',UP),('scaling',SC),('area_redirects',area_redirects),('lore_locations',lore_records)]:save(name,data)
summary={'areas':len(AREAS),'removed_lore_locations':lore_records,'bonfire_details':sum(len(a['bonfire_details']) for a in AREAS),'weapons_with_complete_scaling':weapon_count,'weapons_with_exact_max_coefficients':sum(bool(w.get('max_scaling_percent')) for w in W),'armor_base_imports':armor_base,'armor_with_max_stats':armor_max,'armor_sets':sum(bool(a.get('pieces')) for a in ARM),'items_with_usage':sum(bool(i.get('usage')) for i in I),'souls_with_consumption_value':sum('soul_value' in i for i in I),'souls_with_trades':sum(bool(i.get('trades')) for i in I)}
(A/'detail-import.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
