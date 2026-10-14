from pathlib import Path
import json,re,urllib.request,concurrent.futures,hashlib
P=Path(__file__).resolve().parents[1];A=P/'audit';F=A/'fresh-sources';F.mkdir(exist_ok=True)
base='https://darksouls2.wikidot.com/'
indexes=['weapons','shields','spell-tools','armor','head','chest','hands','legs','enemies','bosses','areas','consumables','rings','keys','ammo','bonfire-items','multiplayer-items','sorceries','hexes','pyromancies','miracles','materials','npcs','covenants','gestures']
urls={base+n for n in indexes}
def collect(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if isinstance(v,str) and ('source' in k or k=='url') and v.startswith(base):urls.add(v.split('#')[0].rstrip('/'))
   else:collect(v)
 elif isinstance(x,list):
  for a in x:collect(a)
for p in (P/'database').glob('*.json'):collect(json.loads(p.read_text(encoding='utf-8-sig')))
from bs4 import BeautifulSoup
for slot in ['head','chest','hands','legs']:
 for f in [A/(slot+'.html')]:
  if f.exists():
   for frame in BeautifulSoup(f.read_bytes(),'html.parser').select('iframe[src]'):
    if frame['src'].startswith('/'):urls.add(base.rstrip('/')+frame['src'])
manifest={};total=len(urls)
def fetch(url):
 target=F/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
 try:
  if not target.exists():
   data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'DS2LocalGuideAudit/1.0'}),timeout=18).read();target.write_bytes(data)
  return url,{'file':str(target.relative_to(P)).replace('\\','/'),'bytes':target.stat().st_size,'status':'downloaded'}
 except Exception as e:return url,{'status':'failed','error':str(e)}
print('Fresh reference pages:',total,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for i,(url,result) in enumerate(pool.map(fetch,sorted(urls)),1):
  manifest[url]=result
  if i%100==0:print('Checked',i,'/',total,'failed',sum(x['status']=='failed' for x in manifest.values()),flush=True)
(A/'fresh-source-manifest.json').write_text(json.dumps({'checked_on':'2026-10-10','sources':manifest},indent=2)+'\n',encoding='utf-8')
print('Finished',len(manifest),'failures',[(u,r.get('error')) for u,r in manifest.items() if r['status']=='failed'],flush=True)
