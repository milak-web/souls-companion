"""Fetch explicitly associated wiki images; keep failures for visual review."""
import json, time, urllib.request, urllib.parse, io
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
R=Path(__file__).resolve().parents[1]
def load(n):return json.loads((R/'database'/f'{n}.json').read_text(encoding='utf-8'))
def fetch(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'DS2OfflineGuideImageAudit/1.9.1'}),timeout=25).read()
data={n:load(n) for n in ['items','enemies','npcs']};report=[]
for cat,records in data.items():
 for r in records:
  if r.get('image_verified') is not False:continue
  if cat=='npcs' and r.get('role')=='Lore figure':continue
  title='Forlorn' if cat=='enemies' and r['id']=='greatsword-of-the-forlorn' else r['name'];url='https://darksouls2.wiki.gg/api.php?'+urllib.parse.urlencode({'action':'parse','page':title,'prop':'text|images','format':'json','redirects':1})
  try:
   cache=R/'audit'/('image-page-'+r['id']+('-enemy' if title=='Forlorn' else '')+'.json')
   if cache.exists():d=json.loads(cache.read_text(encoding='utf-8'))
   else:d=json.loads(fetch(url));cache.write_text(json.dumps(d),encoding='utf-8');time.sleep(1.2)
   page=d.get('parse',{});html=BeautifulSoup(page.get('text',{}).get('*',''),'html.parser')
   img=html.select_one('.druid-main-image img') or html.select_one('.infobox img')
   if title=='Forlorn':img=next((i for i in html.select('img') if i.get('alt')=='Forlorn Greatsword.png'),None)
   elif cat in ['enemies','npcs'] and html.select_one('.druid-container-Weapons, .druid-container-Rings, .druid-container-Armor'):raise ValueError('Equipment page rejected as a character portrait')
   if not img:raise ValueError('No associated infobox image')
   src=urllib.parse.urljoin('https://darksouls2.wiki.gg',img['src']);raw=fetch(src);im=Image.open(io.BytesIO(raw));im.verify();im=Image.open(io.BytesIO(raw))
   if min(im.size)<20:raise ValueError('Image too small')
   dest=R/'assets'/cat/('verified-'+r['id']+'.png');dest.parent.mkdir(exist_ok=True);im.save(dest)
   r.update(image=dest.relative_to(R).as_posix(),image_source=src,image_verified=True,image_kind='game-reference',image_reference='https://darksouls2.wiki.gg/wiki/'+urllib.parse.quote(page['title'].replace(' ','_')))
   r.pop('image_note',None);report.append({'category':cat,'id':r['id'],'name':r['name'],'image':r['image'],'source':src,'result':'downloaded; needs visual review'})
   print(cat,r['name'],'downloaded',flush=True)
  except Exception as ex:report.append({'category':cat,'id':r['id'],'name':r['name'],'result':str(ex)});print(cat,r['name'],str(ex),flush=True)
for n,d in data.items():(R/'database'/f'{n}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'audit/image-completion-downloads.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
