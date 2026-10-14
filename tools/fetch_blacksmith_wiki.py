"""Cache the current wiki.gg equipment wikitext and upgrade-template defaults."""
import json,urllib.request,urllib.parse,hashlib,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];A=R/'audit/wiki-gg';A.mkdir(exist_ok=True)
W=json.loads((R/'database/weapons.json').read_text(encoding='utf-8'));manifest=[]
def fetch(title):
 f=A/(hashlib.sha256(title.encode()).hexdigest()[:20]+'.json')
 if f.exists():return json.loads(f.read_text(encoding='utf-8'))
 u='https://darksouls2.wiki.gg/api.php?'+urllib.parse.urlencode({'action':'parse','page':title,'prop':'wikitext','format':'json','redirects':1})
 raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'DS2LocalGuideAudit/1.0'}),timeout=25).read();j=json.loads(raw);f.write_text(json.dumps(j,ensure_ascii=False),encoding='utf-8');return j
def work(w):
 title=w['name'].replace(' (weapon)','').replace(' (shield)','')
 try:
  j=fetch(title)
  if 'parse' not in j:
   for alt in w.get('aliases',[]):
    j=fetch(alt)
    if 'parse' in j:break
  return {'id':w['id'],'requested':title,'title':j.get('parse',{}).get('title'),'file':hashlib.sha256((j.get('parse',{}).get('title') or title).encode()).hexdigest()[:20]+'.json','cache_file':hashlib.sha256(title.encode()).hexdigest()[:20]+'.json','error':j.get('error')}
 except Exception as e:return {'id':w['id'],'requested':title,'error':str(e)}
with ThreadPoolExecutor(max_workers=6) as pool:
 futures=[pool.submit(work,w) for w in W]
 for i,f in enumerate(as_completed(futures),1):
  manifest.append(f.result())
  if i%50==0:print('Cached',i,'/',len(W),flush=True)
for title in ['Template:Weapon Standard Upgrade','Template:Weapon Special Upgrade','Template:Weapon Boss Upgrade','Infusions','Scaling']:
 try:fetch(title)
 except Exception as e:print(title,str(e))
(A/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Completed',len(manifest),'errors',sum(bool(m.get('error')) for m in manifest),flush=True)
