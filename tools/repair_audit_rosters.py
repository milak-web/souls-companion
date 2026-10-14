"""Repair confirmed roster gaps and source-backed mechanics. Run from the guide root."""
from reference_audit import *
from collections import defaultdict
import concurrent.futures,urllib.parse
from PIL import Image
import io
I=load('items');W=load('weapons');ARM=load('armor');E=load('enemies');B=load('bosses');N=load('npcs');C=load('covenants');AREAS=load('areas');ART=load('articles');changes=[];images=[]
backup=A/'before-full-audit';backup.mkdir(exist_ok=True)
for n in ['items','weapons','armor','enemies','bosses','npcs','covenants','articles']:
 f=backup/(n+'.json')
 if not f.exists():f.write_bytes((D/(n+'.json')).read_bytes())
def note(kind,name,detail):changes.append({'kind':kind,'name':name,'detail':detail})
def short(nodes,limit=150):return ' '.join(' '.join(text(n) for n in nodes if n.name in ['p','ul','ol']).split()[:limit])
def picture(record,c,category,cell=None):
 img=(cell or c).select_one('img[src]')
 if not img or not img['src'].startswith(('http:','https:','//')):return
 u=urllib.parse.urljoin(BASE+'/',img['src']).replace('http://','https://');images.append((record,u,category))
def refs(nodes):
 pairs=[]
 for n in nodes:pairs+=list_pairs(n)
 return [{'name':n,'source_url':u} for n,u in dict.fromkeys(pairs)]
# Actual item pages, not navigation headings or duplicate armor.
for name in ['Carvings','Weapon Buff']:
 r=find(I,name)
 if r:
  ident=r['id'];ART=[a for a in ART if a['id']!=ident];ART.append({'id':ident,'name':name,'aliases':[],'blocks':[{'heading':'Overview','type':'text','lines':[r.get('usage') or r.get('description') or 'See related items for their individual effects.']}],'related':[]});I.remove(r);note('classification',name,'Moved an overview heading to local guide entries')
r=find(I,'Crown of the Ivory King (helm)')
if r:I.remove(r);note('classification',r['name'],'Armor remains in the armor catalog; removed duplicate item entry')
for n,kind in [('sorceries','Sorcery'),('hexes','Hex'),('pyromancies','Pyromancy'),('miracles','Miracle')]:
 for row in named_rows('/'+n):
  r=find(I,row['name'],row['url']);new=r is None
  if new:r={'id':slug(row['name']),'name':row['name'],'image':'assets/ui/menu-item.webp'};I.append(r)
  r.update(type=kind,source_url=row['url']);v=row['values'];usage=v.get('Description','');r['usage']=usage;r['description']=kind+' - '+usage;r['obtaining']=v.get('Location',v.get('Availability',''));r['acquisition_refs']=refs([row['cells'][k] for k in ['Location','Availability'] if k in row['cells']]);r['spell_stats']={re.sub(r'\s+\d+$','',k):val for k,val in v.items() if any(w in k.lower() for w in ['uses','slots','int','fth','faith','type /'])}
  c=doc(row['url']);r['mechanics_notes']=short(sections(c,'Use') or sections(c,'Usage'),140)
  for h,rows in tables(c):
   if not any('Required' in k for k in h):continue
   if len(rows)!=1 or len(rows[0][1])!=len(h):continue
   for key_,cell in zip(h,rows[0][1]):
    if any(w in key_.lower() for w in ['required','duration','spell type']):r['spell_stats'][key_]=text(cell)
  if new:picture(r,c,'items',row['cells'].get('Icon'));note('spell',r['name'],'Added locally with uses, requirements, slots and acquisition')
for row in named_rows('/materials'):
 r=find(I,row['name'],row['url'])
 if not r:r={'id':slug(row['name']),'name':row['name'],'image':'assets/ui/menu-item.webp'};I.append(r);note('item',r['name'],'Added reinforcement/infusion material')
 r['type']='Upgrade Material';r['source_url']=BASE+'/materials'
# Known source-backed aliases, rather than broad substring matching.
armor_alias={'Forlorn Armor':'Armor of the Forlorn','Helm of Aurous (T)':'Helm of Aurous (transparent)','Leggings of Aurous (T)':'Leggings of Aurous (transparent)'}
for old,new in armor_alias.items():
 r=find(ARM,new)
 if r and old not in r.get('aliases',[]):r.setdefault('aliases',[]).append(old)
for r in ARM:
 if r['name'].endswith(' (helm)'):r.setdefault('aliases',[]).append(r['name'].removesuffix(' (helm)'))
for slot in ['head','chest','hands','legs']:
 for name,u in roster()['armor-'+slot]['entries']:
  r=find(ARM,name,u)
  if r and r.get('slot')!=slot:r['slot']=slot;note('armor-slot',r['name'],slot)
# Fill missing set records and preserve explicit membership only from real tables.
for name,u in roster()['armor-sets']['entries']:
 c=doc(u);r=find(ARM,name,u)
 if not r:r={'id':slug(name),'name':name,'type':'Armor Set','image':'assets/ui/menu-chest-armor.webp','source_url':u,'requirements':{},'special_effect':'See individual pieces for effects.'};ARM.append(r);note('armor-set',name,'Added the missing set page');picture(r,c,'armor')
 members=[]
 for h,rows in tables(c):
  if 'Name' not in h or 'Physical Defense' not in h:continue
  for _,cells in rows:
   if len(cells)!=len(h):continue
   member=find(ARM,text(cells[h.index('Name')]))
   if member and member is not r:members.append(member['id'])
 if members:r['pieces']=list(dict.fromkeys(members));r['type']='Armor Set';r['description']='Armor set. Open individual pieces for their properties.'
# Link NPC aliases explicitly documented by the index.
npc_alias={'Maughlin the Armourer':'Maughlin the Armorer','Housekeeper Milibeth':'Milibeth the Housekeeper','Saulden, the Crestfallen Warrior':'Crestfallen Saulden','Sparkling Sisters Dyna and Tillo':'Dyna & Tillo','Mild Mannered Pate':'Mild-Mannered Pate','Belfry Guard':'Bell Keeper of Alken','The Rat King':'Rat King (character)'}
for old,new in npc_alias.items():
 r=find(N,new)
 if r and old not in r.get('aliases',[]):r.setdefault('aliases',[]).append(old)
npc_roster=roster()['npcs']['entries'];canonical=set()
for name,u in npc_roster:
 r=find(N,name,u)
 if not r:
  other=find(E,name,u) or find(B,name,u);r={'id':slug(name),'name':name,'image':other['image'] if other else 'assets/ui/menu-item.webp','description':''};N.append(r);note('npc',name,'Added interactable character or summon from the wiki index')
 c=doc(u);r['source_url']=u;canonical.add(r['id']);r['role']='Character / summon';r['location']=short(sections(c,'Location'),100) or r.get('location','');r['use_notes']=short(sections(c,'Use') or sections(c,'Usage'),140)
 if not r.get('description'):r['description']='Dark Souls II character. See locations and interactions below.'
 if r['image'].startswith('assets/ui/'):picture(r,c,'npcs')
for r in N:
 if r['id'] not in canonical:r['role']='Lore figure'
# Enemies missing under their published wiki names, plus baseline stats with area/intensity context.
for name,u in roster()['enemies']['entries']:
 r=find(E,name,u)
 if not r and find(B,name,u):continue
 if not r:r={'id':slug(name),'name':name,'title':'','image':'assets/ui/stat/stat-physical-attack.webp','areas':[],'hp':None,'souls':None,'despawn':'Not verified','respawn':'Not verified','can_parry':None,'can_backstab':None,'weaknesses':{},'status_effects':{},'drops':[],'farming':{'difficulty':0,'bonfire':'Not verified','gear':[],'notes':''},'ai_notes':''};E.append(r);note('enemy',name,'Added published enemy/invader entry');picture(r,doc(u),'enemies')
 r['source_url']=u
# Existing exact names also obtain source provenance from the area-by-area enemy table.
for name,u in list_pairs(doc('/enemies')):
 r=find(E,name)
 if r and not r.get('source_url') and u.rsplit('/',1)[-1] not in ['enemies','bosses']:r['source_url']=u
for r in E:
 if not r.get('source_url'):continue
 c=doc(r['source_url']);loc=sections(c,'Location');areas=[a['name'] for a in AREAS if any(key(text(link))==key(a['name']) for node in loc for link in node.select('a[href]'))]
 if areas:r['areas']=list(dict.fromkeys(areas))
 profiles=[]
 for t in c.select('table'):
  rs=t.select('tr');h=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)] if rs else []
  if not {'HP','Souls'}.issubset(h):continue
  context=t.find_previous(['h2','h3','h4','p']);context=text(context)[:200] if context else 'Location variants'
  for row in rs[1:]:
   cells=row.find_all(['td','th'],recursive=False)
   if len(cells)!=len(h):continue
   vals=dict(zip(h,map(text,cells)));profiles.append({'context':context,'intensity':vals.get('Bonfire Intensity','Not specified'),'hp':vals['HP'],'souls':vals['Souls']})
 if profiles:
  r['stat_profiles']=profiles
  for field in ['hp','souls']:
   vals={p[field] for p in profiles if p['intensity']=='1'}
   newval=next(iter(vals)) if len(vals)==1 else 'Varies by location'
   if r.get(field)!=newval:note('enemy-stat',r['name'],field+' corrected to '+str(newval))
   r[field]=newval
  r['stat_context']='Bonfire intensity 1 shown when identical across published variants. See location/intensity rows for differences.'
 else:r['hp']=None;r['souls']=None
 effect=short(sections(c,'Effectiveness'));resist=short(sections(c,'Resistance'));r['effectiveness_notes']=' '.join([effect,resist]).strip()
 # Preserve only physical weakness evidence explicitly published as a damage multiplier.
 r['weaknesses']={ch:'weak' if float(v)>100 else 'resistant' if float(v)<100 else 'neutral' for ch,v in re.findall(r'(Strike|Slash|Thrust):\s*~?(\d+(?:\.\d+)?)%',effect,re.I) for ch in [ch.lower()]}
 r['status_effects']={}
 notes=short(sections(c,'Notes'));r['can_parry']=True if re.search(r'can be parried',notes,re.I) else False if re.search(r'cannot be parried|can.t be parried',notes,re.I) else None;r['can_backstab']=True if re.search(r'can be backstabbed',notes,re.I) else False if re.search(r'cannot be backstabbed|can.t be backstabbed',notes,re.I) else None
 r['ai_notes']=short(sections(c,'Strategy'),140) or r.get('ai_notes','');dropnodes=sections(c,'Drops');droptext=' '.join(text(n) for n in dropnodes)
 if dropnodes:
  drops=[]
  for name_,u in dict.fromkeys((n,u) for node in dropnodes for n,u in list_pairs(node)):
   target=next((find(d,name_,u) for d in [I,W,ARM] if find(d,name_,u)),None)
   if not target:continue
   line=next((text(li) for node in dropnodes for li in node.select('li') if key(name_) in key(text(li))),name_)
   rate=re.search(r'(very rare|rare|uncommon|common|guaranteed|\d+(?:\.\d+)?%)',line,re.I)
   drops.append({'name':target['name'],'chance':rate[0].capitalize() if rate else 'Rate not specified','icon':target['image']})
  if drops:r['drops']=drops
 for d in r.get('drops',[]):
  if '%' in d.get('chance','') and d['chance'] not in droptext:d['chance']='Rate not verified';note('drop-rate',r['name'],d['name']+' unsupported percentage removed')
# Correct all covenant reward rows from their published rank tables.
for row in named_rows('/covenants','Covenant'):
 r=find(C,row['name']);c=doc(row['url']);r['source_url']=row['url'];r['purpose']=row['values']['Summary'];r['join_notes']=short(sections(c,'How to Join'),100)
 for h,rows in tables(c):
  if 'Rank' not in h or 'Reward' not in h:continue
  rewards=[]
  for _,cells in rows:
   if len(cells)!=len(h):continue
   vals=dict(zip(h,map(text,cells)));rank=nums(vals['Rank']);req=next((vals[k] for k in h if k not in ['Rank','Reward']),None)
   if rank:rewards.append({'rank':int(rank[0]),'requirement':req,'name':vals['Reward'],'received':False})
  if rewards and r['rewards']!=rewards:r['rewards']=rewards;note('covenant',r['name'],'Replaced rank requirements/rewards with published table including joining reward')
 r['rank_progress']['item']='rank requirements (see below)';r['rank_progress']['target']=max([nums(str(x['requirement']))[0] for x in r['rewards'] if nums(str(x['requirement']))]+[1])
for name,kind in [('Archdrake Chime','Sacred Chime'),('Old Whip','Whip'),('Torch','Tool'),('Varangian Shield','Medium Shield'),('Tower Shield','Greatshield')]:
 r=find(W,name)
 if r and not r.get('type'):r['type']=kind;note('weapon-type',name,kind)
# Download source-associated art; unavailable exact images remain explicitly labelled.
def get_image(job):
 r,u,cat=job
 try:
  data=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=12).read();im=Image.open(io.BytesIO(data));im.verify();ext=Image.open(io.BytesIO(data)).format.lower();ext={'jpeg':'jpg'}.get(ext,ext);f=ROOT/'assets'/cat/('audit-'+r['id']+'.'+ext);f.write_bytes(data);r['image']=str(f.relative_to(ROOT)).replace('\\','/');r['image_source']=u;r['image_verified']=True;return True
 except Exception as e:r['image_verified']=False;return {'name':r['name'],'source':u,'error':str(e)}
print('Artwork queued',len(images),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:art_results=list(pool.map(get_image,images))
for n,data in [('items',I),('weapons',W),('armor',ARM),('enemies',E),('bosses',B),('npcs',N),('covenants',C),('articles',ART)]:save(n,data)
(A/'full-audit-repairs.json').write_text(json.dumps({'changes':changes,'image_success':sum(x is True for x in art_results),'image_unavailable':[x for x in art_results if x is not True]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Repairs',len(changes),'records',{'items':len(I),'enemies':len(E),'npcs':len(N),'armor':len(ARM)},flush=True)
