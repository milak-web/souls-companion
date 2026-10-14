from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request,concurrent.futures,json
P=Path('DarkSouls-Guide');A=P/'audit';jobs={}
for n in ['areas','weapons','shields','spell-tools','armor','consumables','rings','keys','ammo','multiplayer-items','sorceries','hexes','pyromancies','miracles']:
 c=BeautifulSoup((A/f'{n}.html').read_bytes(),'html.parser').select_one('#page-content')
 if n=='areas':
  for r in c.select('table tr')[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)==6:
    a=cells[0].select_one('a[href]')
    if a:jobs[a['href'].split('#')[0]]=n
 elif n in ['weapons','shields','spell-tools']:
  for a in c.select('table p a[href], table li a[href]'):
   if a['href'].startswith('/') and a.get_text(' ',strip=True)!='Boss Souls':jobs[a['href'].split('#')[0]]=n
 elif n=='armor':
  for a in c.select('a[href]'):
   if a['href'].startswith('/') and a['href'] not in ['/head','/chest','/hands','/legs','/unused-content#toc1']:jobs[a['href'].split('#')[0]]=n
 else:
  for t in c.select('table'):
   rows=t.select('tr');headers=[x.get_text(' ',strip=True) for x in rows[0].find_all(['td','th'],recursive=False)]
   if 'Name' not in headers:continue
   idx=headers.index('Name')
   for r in rows[1:]:
    cells=r.find_all(['td','th'],recursive=False)
    if len(cells)>idx:
     a=cells[idx].select_one('a[href]')
     if a and a['href'].startswith('/'):jobs[a['href'].split('#')[0]]=n
for name in ['head','chest','hands','legs']:
 c=BeautifulSoup((A/f'{name}.html').read_bytes(),'html.parser').select_one('#page-content')
 for frame in c.select('iframe[src]'):jobs[frame['src']]=name+'-table'
for slug in ['memory-of-the-king','grand-cathedral','upgrades','special-effects','scaling','magic-atk-bonus','fire-atk-bonus','lightning-atk-bonus','dark-atk-bonus']:
 jobs['/'+slug]='supplement'
(A/'reference-jobs.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
def get(job):
 href,category=job;slug=href.strip('/').replace('/','_');f=A/('reference-'+slug+'.html')
 try:
  cached=A/(slug+'.html')
  if not f.exists():
   if cached.exists():f.write_bytes(cached.read_bytes())
   else:f.write_bytes(urllib.request.urlopen('https://darksouls2.wikidot.com'+href,timeout=12).read())
  return href,True
 except Exception as e:return href,str(e)
results={};print('References queued:',len(jobs),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for count,(href,result) in enumerate(pool.map(get,jobs.items()),1):
  results[href]=result
  if count%40==0:print('Checked',count,'/',len(jobs),'failures',sum(v is not True for v in results.values()),flush=True)
(A/'reference-download.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print('Finished. Failed:',{k:v for k,v in results.items() if v is not True},flush=True)
