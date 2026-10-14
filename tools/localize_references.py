"""Bundle missing guide references as inert local JSON, never remote HTML."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json,re,urllib.request,concurrent.futures
P=Path(__file__).resolve().parents[1];A=P/'audit';D=P/'database'
def load(n):return json.loads((D/(n+'.json')).read_text(encoding='utf-8-sig'))
def key(s):return re.sub('[^a-z0-9]+',' ',str(s).lower().replace('`',"'")).strip().removeprefix('the ')
records=[r for n in ['bosses','enemies','areas','items','weapons','armor','npcs','covenants'] for r in load(n)]
known_names={key(n) for r in records for n in [r.get('name',''),r.get('id',''),*r.get('aliases',[])]};known_urls={r.get('source_url','').split('#')[0].rstrip('/') for r in records if r.get('source_url')}
needed={};missing_names=set();links={}
def add(name,url):
 url=url.split('#')[0].rstrip('/')
 if key(name) in known_names or url in known_urls:return
 if url.startswith('https://darksouls2.wikidot.com/') and not any(t in url for t in ['local--files','system:','javascript:']):needed.setdefault(url,set()).add(name)
for item in load('items'):
 for r in item.get('acquisition_refs',[]):add(r['name'],r.get('source_url',''))
 for t in item.get('trades',[]):missing_names.update(n for n in [t['merchant'],*t['products']] if key(n) not in known_names)
for area in load('areas'):
 for field in ['connections','bosses','enemies','npcs','mini_bosses','items']:
  missing_names.update(n for n in area.get(field,[]) if key(n) not in known_names)
for f in A.glob('reference-*.html'):
 c=BeautifulSoup(f.read_bytes(),'html.parser');c=c.select_one('#page-content') or c
 for a in c.select('a[href]'):
  if a['href'].startswith('/') and not a['href'].startswith('//'):
   name=a.get_text(' ',strip=True)
   if name:links.setdefault(key(name),set()).add('https://darksouls2.wikidot.com'+a['href'].split('#')[0])
for name in missing_names:
 urls=links.get(key(name),set())
 if len(urls)==1:add(name,next(iter(urls)))
def file(url):return A/('reference-'+urlparse(url).path.strip('/').replace('/','_')+'.html')
def fetch(url):
 p=file(url)
 if p.exists():return url,None
 try:
  p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read());return url,None
 except Exception as e:return url,str(e)
fetches=list(concurrent.futures.ThreadPoolExecutor(5).map(fetch,needed))
articles=[];unavailable=[]
allowed={'use','effects','effect','location','locations','availability','drops','notes','general information','description','connections','strategies','strategy','bonfires','quick reference','general','effectiveness','attacks','starting items','soul memory ranges','online play','tier list','multiplayer item ranges','stats'}
for url,error in fetches:
 if error:unavailable.append({'url':url,'names':sorted(needed[url]),'reason':error});continue
 s=BeautifulSoup(file(url).read_bytes(),'html.parser');c=s.select_one('#page-content')
 if not c:continue
 title=s.select_one('#page-title');name=title.get_text(' ',strip=True) if title else sorted(needed[url])[0]
 blocks=[];related={};budget=190
 for h in c.select('h1,h2,h3,h4,h5'):
  heading=h.get_text(' ',strip=True)
  if heading.lower() not in allowed and key(heading) not in known_names:continue
  if heading.lower()=='description' and ('In-Game Description' in c.get_text(' ',strip=True) or 'Description'==heading and url.endswith('-soul')):continue
  for n in h.next_siblings:
   if getattr(n,'name',None) in ['h1','h2','h3','h4','h5']:break
   if getattr(n,'name',None) not in ['p','ul','ol','table']:continue
   # Strip page chrome, script code, and footnote markers before importing facts.
   for bad in n.select('script,style,iframe,sup.footnoteref'):bad.decompose()
   if heading.lower()=='general' and n.name=='p' and n.select_one('em'):continue
   if n.name=='table':
    rows=[]
    for tr in n.select('tr'):
     cells=[td.get_text(' ',strip=True) for td in tr.find_all(['th','td'],recursive=False)]
     if not cells or sum(len(x.split()) for x in cells)>budget:break
     budget-=sum(len(x.split()) for x in cells);rows.append(cells)
    if rows:blocks.append({'heading':heading,'type':'table','rows':rows})
   else:
    lines=[li.get_text(' ',strip=True) for li in n.find_all('li',recursive=False)] if n.name in ['ul','ol'] else [n.get_text(' ',strip=True)]
    kept=[]
    for line in lines:
     words=line.split()
     if not words or len(words)>budget:continue
     budget-=len(words);kept.append(line)
    if kept:blocks.append({'heading':heading,'type':'list' if n.name in ['ul','ol'] else 'text','lines':kept})
   for a in n.select('a[href]'):
    if a['href'].startswith('/') and a.get_text(strip=True):related[a.get_text(' ',strip=True)]='https://darksouls2.wikidot.com'+a['href'].split('#')[0]
  if budget<12:break
 if not blocks:unavailable.append({'url':url,'names':sorted(needed[url]),'reason':'No usable factual section in cached page'});continue
 articles.append({'id':urlparse(url).path.strip('/'),'name':name,'aliases':sorted(needed[url]-{name}),'source_url':url,'blocks':blocks,'related':[{'name':n,'source_url':u} for n,u in related.items() if key(n) in known_names or u in known_urls or u in needed]})
(D/'articles.json').write_text(json.dumps(articles,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'local-content-import.json').write_text(json.dumps({'local_articles':len(articles),'unavailable':unavailable},indent=2),encoding='utf-8')
print(json.dumps({'local_articles':len(articles),'unavailable':unavailable},indent=2))
