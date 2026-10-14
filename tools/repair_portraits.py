from pathlib import Path
import sys,json,urllib.request,hashlib,io
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
sys.path.insert(0,'tools');from reference_audit import doc,load,save
R=Path('.');placeholder='assets/ui/portrait-unavailable.svg'
(R/placeholder).write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><rect width="400" height="400" fill="#191b1e"/><circle cx="200" cy="130" r="52" fill="#44484d"/><path d="M95 290c0-90 35-110 105-110s105 20 105 110" fill="#44484d"/><text x="200" y="345" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#c5a059">Portrait unavailable</text></svg>''',encoding='utf-8')
names={
'npcs': ['Abbess Feeva','Ashen Knight Boyd','Devotee Scarlett','Drifter Swordsman Aidel','Felicia the Brave','Lone Hunter Schmidt',"Manhunter O'harrah",'Rapacious Andrei','Ruined Aflis','Sellsword Luet','Steel-willed Lorrie','Steelheart Ellie','Transcendent Edde','Twiggy Shei','Jester Thomas'],
'enemies':['Blue-eyed Durgo','Castaway Witch Donna','Bowman Guthry','Forest Spirit','Jester Thomas','Looking Glass Phantom','Greatsword of the Forlorn','Wall Watchman','Woodland Child Victor','Woodland Child Gully']}
# These source assets themselves are removed-image banners or unrelated equipment.
missing=['Armored Skeleton','Greatsword Foreigner Phantom','Invisible Hollow','Crescent Sickle Phantom','Elite Knight Phantom','Greatbow Phantom','Prisoned Sinner','Royal Infantry','Royal Soldier','Syan Knight Phantom']
lore_wrong=['Alva the Wayfarer','Aurous','Azal, Sage of Forossa','Caffrey, Goddess of Fortune','Evil Eye','Evlana, Goddess of the Hunt','Fabian, Knight of Eleum Loyce','Fiorenza','Flynn','Galib, God of Disease','Gordin, Wandering Knight','Knight King Rendal','Llewellyn','Olenford','Quella, God of Dream','Shieldless Lothian','Sir Syan','Sir Yorgh','War God Faraam','Zandroe, God of Greed','Zinder, God of Desire','Zullie the Witch']
data={n:load(n) for n in names};tasks=[];report=[]
# Reject the known Imgur removed-image banner even though it returns HTTP 200.
removed={hashlib.sha256(Image.open(R/r['image']).convert('RGB').resize((64,64)).tobytes()).hexdigest() for r in data['enemies'] if r['name'] in missing and 'stat-' not in r['image']}
for cat,recs in data.items():
 for r in recs:
  if r['name'] in names[cat]:tasks.append((cat,r))
  elif cat=='enemies' and r['name'] in missing or cat=='npcs' and r['name'] in lore_wrong:
   r.update(image=placeholder,image_verified=False,image_note='No verified character portrait available. Equipment artwork is not used as a portrait.');report.append({'category':cat,'name':r['name'],'result':'portrait unavailable'})
def repair(task):
 cat,r=task;result='portrait unavailable'
 try:
  c=doc(r['source_url'],False);imgs=c.select('img') if c else []
  if not imgs:raise ValueError('No image in source')
  u=imgs[0]['src'].replace('http://','https://');raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();im=Image.open(io.BytesIO(raw)).convert('RGB')
  if hashlib.sha256(im.resize((64,64)).tobytes()).hexdigest() in removed or im.width<70 or im.height<70:raise ValueError('Unavailable image')
  p=f'assets/{cat}/portrait-{r["id"]}.png';im.save(R/p);r.update(image=p,image_source=u,image_verified=True);r.pop('image_note',None);result='downloaded portrait; awaiting visual check'
 except Exception as e:
  r.update(image=placeholder,image_verified=False,image_note='No verified character portrait available. Equipment artwork is not used as a portrait.')
 return {'category':cat,'name':r['name'],'result':result}
with ThreadPoolExecutor(max_workers=6) as pool:report+=list(pool.map(repair,tasks))
for cat,recs in data.items():save(cat,recs)
(R/'audit/portrait-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
