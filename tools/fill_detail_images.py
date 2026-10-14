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

import urllib.request,concurrent.futures,io
from PIL import Image
ARM=load('armor');I=load('items');jobs={};cache={}
def cached(slug):
 if slug not in cache:cache[slug]=soup(slug)
 return cache[slug]
for kind,records in [('armor',ARM),('items',I)]:
 for a in records:
  if a.get('image') or a.get('content_status'):continue
  slug=a.get('source_url','').split('/')[-1];c=cached(slug) if slug else None
  if not c:continue
  for t in c.select('table'):
   rs=t.select('tr');hd=[text(x).replace('_',' ') for x in rs[0].find_all(['th','td'],recursive=False)] if rs else []
   if 'Name' not in hd:continue
   for r in rs[1:]:
    cs=r.find_all(['td','th'],recursive=False)
    if len(cs)!=len(hd) or key(text(cs[hd.index('Name')])) not in [key(a['name']),*[key(n) for n in a.get('aliases',[])]]:continue
    im=r.select_one('img[src]')
    if im:jobs[(kind,a['id'])]=im['src'].replace('http://','https://');break
   if (kind,a['id']) in jobs:break
  if (kind,a['id']) not in jobs:
   if kind=='items' and slug==a['id']:
    im=c.select_one('img[src]')
    if im:jobs[(kind,a['id'])]=im['src'].replace('http://','https://')
   elif a.get('pieces'):
    im=next((i for i in c.select('img[src]') if key(a['name']) in key(i.get('alt',''))),None)
    if im:jobs[(kind,a['id'])]=im['src'].replace('http://','https://')
# Items without their own detail page also have exact icons in the mechanics indices.
for slug in ['ammo','consumables','boss-soul-items','materials']:
 c=cached(slug)
 if not c:continue
 for r in c.select('table tr'):
  for a in I:
   if a.get('image') or ('items',a['id']) in jobs:continue
   cs=r.find_all(['td','th'],recursive=False)
   if any(key(text(cell))==key(a['name']) for cell in cs):
    im=r.select_one('img[src]')
    if im:jobs[('items',a['id'])]=im['src'].replace('http://','https://')
def fetch(pair):
 (kind,id),url=pair
 try:
  raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read();im=Image.open(io.BytesIO(raw));im.verify();im=Image.open(io.BytesIO(raw));dest=P/'assets'/kind/(id+'-reference.png');im.save(dest);return kind,id,dest.as_posix(),url,None
 except Exception as e:return kind,id,None,url,str(e)
results=list(concurrent.futures.ThreadPoolExecutor(5).map(fetch,jobs.items()))
for kind,id,path,url,error in results:
 if not error:
  a=next(a for a in (ARM if kind=='armor' else I) if a['id']==id);a['image']=path;a['image_source']=url;a['image_verified']=True
save('armor',ARM);save('items',I)
(A/'image-import.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps({'downloaded':sum(not r[-1] for r in results),'failed':[r for r in results if r[-1]],'remaining_armor':sum(not a.get('image') and not a.get('content_status') for a in ARM),'remaining_items':sum(not a.get('image') for a in I)}))
