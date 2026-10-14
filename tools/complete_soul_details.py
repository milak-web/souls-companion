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

I=load('items');ARM=load('armor');AREAS=load('areas');W=load('weapons')
for item in I:
 c=soup(item.get('source_url','').split('/')[-1])
 if not c:continue
 use=section(c,'Use');trades=[];consumption=None
 for n in use:
  for t in ([n] if n.name=='table' else n.select('table')):
   rows=t.select('tr');heads=[text(h).lower() for h in rows[0].find_all(['th','td'],recursive=False)] if rows else []
   if len(heads)!=3 or 'player receives' not in heads:continue
   for r in rows[1:]:
    cells=r.find_all(['td','th'],recursive=False)
    if len(cells)!=3:continue
    merchant=text(cells[0]);reward=text(cells[1]);cost=text(cells[2])
    if merchant.lower()=='consume':
     m=re.search(r'(\d[\d,]*)\s*souls?',reward,re.I)
     if m:consumption=int(m[1].replace(',',''))
    else:
     products=[text(a) for a in cells[1].select('a[href]') if a['href'].startswith('/')]
     if products:trades.append({'merchant':merchant,'products':products,'cost':cost})
 if consumption is None:
  use_text=' '.join(text(n) for n in use if n.name in ['p','ul'])
  m=re.search(r'Consume\s+to\s+(?:receive|acquire|gain)\s+(\d[\d,]*)\s*souls?',use_text,re.I)
  if m:consumption=int(m[1].replace(',',''))
 if consumption is not None:
  item['soul_value']=consumption
  if item['id']!='soul-of-a-giant':item['usage']=f"Consume to gain {consumption:,} souls."+(' Keep this soul instead to exchange it for one of the listed trade rewards.' if trades else '')
 if trades:item['trades']=trades
 if item['id']=='soul-of-the-king':item['direct_drop']=False;item['description']='Treasure in Shrine of Amana after defeating Vendrick. It is not looted directly from his body.';item['obtaining']='After defeating Vendrick, be human and open the door behind the roots near Shrine of Amana?s second bonfire. The soul is on the chair inside.'
 if item['id']=='ancient-dragon-soul':item['obtaining']='Recover it from the dragon corpse in Dragon Memories, accessed through the crystal in the Duke?s Dear Freja arena after obtaining the Ashen Mist Heart.'
for a in ARM:
 if a['id'] in ['despatcher-s-hood','despatcher-s-robes']:
  a['content_status']='Legacy entry ? identity unverified';a['description']='The original catalog contained this name, but it could not be matched to a confirmed obtainable armor piece. Its stats and availability remain unverified.';a['special_effect']='Unverified.'
for a in AREAS:
 if a['id']=='dragon-shrine':
  f=a['bonfire_details'][0];f['location']='At the entrance to Dragon Shrine, inside the small building on the left after crossing the bridge from Dragon Aerie.'
 # Visible visual route guides supplement the remaining screenshots without claiming they are photos.
 videos={'forest_of_fallen_giants':'fHkXSLde_Hs','heides_tower_of_flame':'nEQbov82x9Q','lost_bastille':'iUVp7KGTpq4','huntsman-s-copse':'CcMDhtGSf0A','harvest-valley':'Njm8_1bOjxs','earthen-peak':'Njm8_1bOjxs','iron-keep':'jpGw41qSTAo','shaded-woods':'4Ey8rBqLYZk','doors-of-pharros':'4Ey8rBqLYZk','brightstone-cove-tseldora':'kqDbmL0Rpuk','grave-of-saints':'n7wLGtNIE6A','the-gutter':'i8UTGPkj8Kk','black-gulch':'i8UTGPkj8Kk','drangleic-castle':'6gQzgZNlbmY','shrine-of-amana':'K5JVw6Ws7uc','undead-crypt':'K5JVw6Ws7uc','aldia-s-keep':'ILFLbH_f02E'}
 if a['id'] in videos:a['bonfire_video']='https://www.youtube.com/watch?v='+videos[a['id']];a['bonfire_video_source']='https://steamcommunity.com/sharedfiles/filedetails/?id=2108626487'
save('items',I);save('armor',ARM);save('areas',AREAS)
print(json.dumps({'souls_with_values':sum('soul_value' in i for i in I),'soul_trades':sum(bool(i.get('trades')) for i in I),'items_with_uses':sum(bool(i.get('usage')) for i in I)}))
