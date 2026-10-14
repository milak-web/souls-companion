"""Build the offline DS1 factual catalog from independently cached wiki pages."""
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re,json,urllib.request,time,hashlib
ROOT=Path(__file__).resolve().parents[1]; CACHE=ROOT/'audit/ds1'; OUT=ROOT/'database/ds1'; BASE='https://darksouls.wikidot.com'
CACHE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
def txt(n):return re.sub(r'\s+',' ',n.get_text(' ',strip=True)).strip()
def fetch(slug):
 p=CACHE/(slug+'.html')
 if p.exists():return p.read_bytes()
 for attempt in range(3):
  try:
   data=urllib.request.urlopen(urllib.request.Request(BASE+'/'+slug,headers={'User-Agent':'SoulsOfflineGuide/2.0'}),timeout=35).read();p.write_bytes(data);return data
  except Exception:
   time.sleep(1+attempt)
 return None
def roster():
 s=BeautifulSoup(fetch('sitemap'),'html.parser').select_one('#page-content'); records={}
 groups={'areas':'areas','bosses':'bosses','enemies':'enemies','npcs':'npcs','covenants':'covenants','weapons':'weapons','shields':'weapons','spell-tools':'weapons','head':'armor','chest':'armor','hands':'armor','legs':'armor','armor':'sets','rings':'rings','sorceries':'magic','miracles':'magic','pyromancies':'magic','consumables':'items','bonfire-items':'items','miscellaneous-items':'items','keys':'items','multiplayer-items':'items','ammo':'items','souls':'items','materials':'items','embers':'items','game-mechanics':'mechanics','stats':'mechanics','upgrade':'mechanics','classes':'classes'}
 skip={'armor-all-max','armor-all-min','weapons-tabview','miracles-sortable','lordvessel-lore','gwyn-lore','elite-cleric-set','mage-smith-set','old-pendant','unused-content','upgrade-chart','farming','weapon-upgrades','boss-soul-items'}
 for slug,cat in groups.items():
  a=next((a for a in s.select('a') if a.get('href')=='/'+slug and a.parent.find('ul',recursive=False)),None)
  if not a:continue
  for link in a.parent.find('ul',recursive=False).select('li > a'):
   ident=link.get('href','').strip('/')
   if not ident or ':' in ident or ident in skip or ident in groups or '#' in ident:continue
   # Intermediate folders are indexes, except real covenants.
   if link.parent.find('ul',recursive=False) and cat not in ('covenants',):continue
   if cat=='covenants' and link.parent.parent!=a.parent.find('ul',recursive=False):continue
   if cat=='mechanics' and any(x in ident for x in ['soul-of','large-soul','core-of','fire-keeper-soul','guardian-soul']):continue
   family=slug
   parent=link.parent.parent.parent
   if parent.name=='li':
    parent_a=parent.find('a',recursive=False)
    if parent_a:family=txt(parent_a)
   if ident not in records or cat!='mechanics':records[ident]={'id':ident,'name':txt(link),'category':cat,'type':family,'source':BASE+'/'+ident}
 return records
def parse(record):
 raw=fetch(record['id'])
 if not raw:return {**record,'error':'Source unavailable'}
 s=BeautifulSoup(raw,'html.parser'); c=s.select_one('#page-content')
 if not c:return {**record,'error':'Page content unavailable'}
 for n in c.select('.toc,.footnotes-footer,.page-rate-widget-box,.collapsible-block-link,.code,.wiki-content-table .footnoteref'):n.decompose()
 tables=[]
 for t in c.select('table'):
  rows=[[txt(cell) for cell in tr.find_all(['th','td'],recursive=False)] for tr in t.select('tr')]
  rows=[r for r in rows if any(r)]
  if rows:tables.append({'heading':txt(t.find_previous(['h1','h2','h3','h4'])) if t.find_previous(['h1','h2','h3','h4']) else 'Statistics','rows':rows})
 record['tables']=tables
 # Structured names and relations are factual; prose is authored separately.
 relations={}
 for a in c.select('a[href]'):
  href=a['href'].split('#')[0]
  if not href.startswith('/') or href.startswith('//') or ':' in href:continue
  ident=href.strip('/')
  if ident==record['id']:continue
  h=a.find_previous(['h1','h2','h3','h4'])
  label=txt(h) if h else 'Related entries'
  if txt(a):relations.setdefault(label,{})[ident]=txt(a)
 record['relations']={k:[{'id':i,'name':n} for i,n in v.items()] for k,v in relations.items()}
 images=[]
 for img in c.select('img[src]'):
  src=img['src']; low=src.lower()
  if not any(x in low for x in ['.png','.jpg','.jpeg','.webp']):continue
  if any(x in low for x in ['icon','wiki-logo','damage','strength','dexterity','intelligence','faith','placeholder']):continue
  if src.startswith('//'):src='https:'+src
  if src.startswith('/'):src=BASE+src
  images.append({'url':src,'alt':img.get('alt','')})
 record['image_candidates']=images
 return record
def main():
 records=roster();print('Roster',len(records),flush=True);done=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  futures={pool.submit(parse,r):r for r in records.values()}
  for i,f in enumerate(as_completed(futures),1):
   try:done.append(f.result())
   except Exception as e:done.append({**futures[f],'error':str(e)})
   if i%40==0:print('Imported',i,'/',len(records),flush=True)
 done.sort(key=lambda r:(r['category'],r['name'].lower()))
 (OUT/'catalog.json').write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({cat:sum(r['category']==cat for r in done) for cat in sorted({r['category'] for r in done})}),flush=True)
 print('Failures',[(r['id'],r['error']) for r in done if 'error'in r],flush=True)
if __name__=='__main__':main()
