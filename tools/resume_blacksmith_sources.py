"""Resume source caching at one request per second, respecting rate limits."""
import json,urllib.request,urllib.parse,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'audit/wiki-gg';m=json.loads((A/'manifest.json').read_text(encoding='utf-8'))
def fetch(title):
 f=A/(hashlib.sha256(title.encode()).hexdigest()[:20]+'.json')
 if f.exists():return json.loads(f.read_text(encoding='utf-8'))
 u='https://darksouls2.wiki.gg/api.php?'+urllib.parse.urlencode({'action':'parse','page':title,'prop':'wikitext','format':'json','redirects':1})
 for attempt in range(4):
  try:
   time.sleep(1.1);raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'DS2LocalGuideAudit/1.0'}),timeout=20).read();j=json.loads(raw);f.write_text(json.dumps(j,ensure_ascii=False),encoding='utf-8');return j
  except urllib.error.HTTPError as e:
   if e.code!=429:raise
   print('Source rate limit; backing off 30 seconds',flush=True);time.sleep(30)
 raise RuntimeError('Rate limit still active')
for title in ['Template:Weapon Standard Upgrade','Template:Weapon Special Upgrade','Template:Weapon Boss Upgrade','Template:Weapon Pyro Upgrade','Infusions','Scaling']:
 try:fetch(title)
 except Exception as e:print(title,str(e),flush=True)
for i,entry in enumerate(m):
 if not entry.get('error'):continue
 title=entry['requested']
 try:
  j=fetch(title);entry.update(title=j.get('parse',{}).get('title'),cache_file=hashlib.sha256(title.encode()).hexdigest()[:20]+'.json',error=j.get('error'))
 except Exception as e:entry['error']=str(e)
 if i%20==0:print('Remaining',sum(bool(x.get('error')) for x in m),flush=True)
 (A/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Remaining errors',sum(bool(x.get('error')) for x in m),flush=True)
