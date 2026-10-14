from finish_ds1_catalog import *
from urllib.parse import urlencode
def api(args):
 u='https://darksouls.fandom.com/api.php?'+urlencode({'action':'query','format':'json',**args})
 return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read())
records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
aliases={'the-duke-s-archives':"The Duke's Archives",'dark-sun-gwyndolin':'Dark Sun Gwyndolin','chasm-of-the-abyss':'Chasm of the Abyss','battle-of-stoicism':'Battle of Stoicism','battle-of-stoicism-gazebo':'Battle of Stoicism','firelink-altar':'Firelink Altar','the-abyss':'Abyss','the-great-hollow':'The Great Hollow','the-catacombs':'The Catacombs','chaos-servant':'Chaos Servant','path-of-the-dragon':'Path of the Dragon','crystal-lizard':'Crystal Lizard','pharis':'Pharis'}
targets=[r for r in records if not r.get('image')and r['category']in ['areas','bosses','covenants','enemies']and r['id']!='hostile-npcs']
def one(r):
 try:
  data=api({'titles':aliases.get(r['id'],r['name']),'prop':'pageimages','pithumbsize':1000,'redirects':1});page=next(iter(data['query']['pages'].values()));candidate=page.get('thumbnail',{}).get('source')
  if candidate:
   candidate=candidate.split('/revision/')[0]
   r['image_candidates']=[{'url':candidate,'alt':page['title']}];r=image(r);r['image_reference']='https://darksouls.fandom.com/wiki/'+page['title'].replace(' ','_')
   print(r['id'],bool(r.get('image')),flush=True)
 except Exception as e:print(r['id'],str(e),flush=True)
 return r
with ThreadPoolExecutor(max_workers=3)as pool:
 updated={r['id']:r for r in pool.map(one,targets)}
records=[updated.get(r['id'],r)for r in records]
(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
