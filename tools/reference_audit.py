"""Source helpers for the 10 October audit; no runtime network dependency."""
from pathlib import Path
from bs4 import BeautifulSoup
import json,re,hashlib,urllib.request
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'audit';D=ROOT/'database';BASE='https://darksouls2.wikidot.com'
def load(n):return json.loads((D/(n+'.json')).read_text(encoding='utf-8-sig'))
def save(n,data):(D/(n+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(n):
 c=BeautifulSoup(str(n),'html.parser')
 for sup in c.select('sup.footnoteref'):sup.decompose()
 return re.sub(r'\s+',' ',c.get_text(' ',strip=True)).strip()
def key(s):return re.sub('[^a-z0-9]+',' ',str(s).lower()).strip().removeprefix('the ')
def slug(s):return re.sub('[^a-z0-9]+','-',s.lower()).strip('-')
def url(href):return (BASE+href if href.startswith('/') else href).replace('http://darksouls2.wikidot.com','https://darksouls2.wikidot.com').split('#')[0].rstrip('/')
@lru_cache(maxsize=1400)
def doc(href,download=True):
 u=url(href);f=A/'fresh-sources'/(hashlib.sha256(u.encode()).hexdigest()[:20]+'.html')
 if not f.exists() and download:
  f.parent.mkdir(exist_ok=True);f.write_bytes(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'DS2LocalGuideAudit/1.0'}),timeout=20).read())
 if not f.exists():return None
 c=BeautifulSoup(f.read_bytes(),'html.parser');return c.select_one('#page-content') or c
def find(records,name,href=None):
 matches=[x for x in records if key(name) in {key(x['name']),key(x['id']),*[key(a) for a in x.get('aliases',[])]}]
 if len(matches)==1:return matches[0]
 if href:
  matches=[x for x in records if x.get('source_url') and url(x['source_url'])==url(href)]
  if len(matches)==1:return matches[0]
 return None
def tables(c):
 for t in c.select('table'):
  rs=t.select('tr')
  if not rs:continue
  h=[text(x) for x in rs[0].find_all(['td','th'],recursive=False)]
  yield h,[(r,r.find_all(['td','th'],recursive=False)) for r in rs[1:]]
def named_rows(href,column='Name'):
 out=[]
 for heads,rs in tables(doc(href)):
  if column not in heads:continue
  i=heads.index(column)
  for r,cells in rs:
   if len(cells)!=len(heads):continue
   a=cells[i].select_one('a[href]')
   if not a or not a['href'].startswith('/') or a['href'].startswith('//'):continue
   out.append({'name':text(a),'url':url(a['href']),'values':dict(zip(heads,map(text,cells))),'cells':dict(zip(heads,cells))})
 return out
def sections(c,label):
 h=next((h for h in c.select('h1,h2,h3,h4') if text(h).lower()==label.lower()),None);out=[]
 if not h:return out
 level=int(h.name[1])
 for n in h.next_siblings:
  if getattr(n,'name',None) in ['h1','h2','h3','h4'] and int(n.name[1])<=level:break
  if getattr(n,'name',None):out.append(n)
 return out
def nums(s):
 out=[]
 for token in re.findall(r'\d+(?:[.,]\d+)*',str(s)):
  if token.count(',')==1 and '.' not in token and len(token.split(',')[1])!=3:token=token.replace(',','.')
  else:token=token.replace(',','')
  out.append(float(token))
 return out
def list_pairs(c):return [(text(a),url(a['href'])) for a in c.select('a[href]') if a['href'].startswith('/') and not a['href'].startswith('//') and text(a)]
def roster():
 out={}
 for n,cat,col in [('weapons','weapons',''),('shields','weapons',''),('spell-tools','weapons',''),('consumables','items','Name'),('rings','items','Name'),('keys','items','Name'),('ammo','items','Name'),('bonfire-items','items','Name'),('multiplayer-items','items','Name'),('sorceries','magic','Name'),('hexes','magic','Name'),('pyromancies','magic','Name'),('miracles','magic','Name'),('bosses','bosses','Boss'),('areas','areas','Area Name'),('covenants','covenants','Covenant')]:
  pairs=[(r['name'],r['url']) for r in named_rows('/'+n,col) if n!='bosses' or 'Souls' in r['values']] if col else [(text(a),url(a['href'])) for a in doc('/'+n).select('table p a[href],table li a[href]') if a['href'].startswith('/') and text(a)!='Boss Souls']
  out[n]={'catalog':cat,'entries':sorted(set(pairs))}
 c=doc('/enemies');pairs=[]
 for a in c.select('a[href]'):
  h=a.find_previous('h1')
  if a['href'].startswith('/') and h and text(h) in ['Enemies','Invaders','Roaming Souls']:pairs.append((text(a),url(a['href'])))
 out['enemies']={'catalog':'enemies','entries':sorted(set(pairs))}
 c=doc('/npcs');pairs=[(text(a),url(a['href'])) for a in c.select('h2 a[href]') if a['href'].startswith('/')]
 if not pairs:pairs=list_pairs(c)
 pairs=[(n,u) for n,u in pairs if not u.endswith('/gravestones')]
 # Summons are additionally listed under NPC Summons, rather than in the first headings.
 h=next((h for h in c.select('h2,h3') if text(h)=='NPC Summons'),None)
 if h:
  for n in h.next_siblings:
   if getattr(n,'name',None) in ['h2','h3']:break
   if getattr(n,'name',None):pairs+=list_pairs(n)
 out['npcs']={'catalog':'npcs','entries':sorted(set(pairs))}
 out['armor-sets']={'catalog':'armor','entries':sorted(set((n,u) for n,u in list_pairs(doc('/armor')) if u.rsplit('/',1)[-1] not in ['head','chest','hands','legs','unused-content'] and ('set' in n.lower() or u.endswith('-set'))))}
 for slot in ['head','chest','hands','legs']:
  pairs=[]
  for frame in doc('/'+slot).select('iframe[src]'):
   raw=str(doc(frame['src']));
   for match in re.finditer(r"data\.setCell\(\s*\d+\s*,\s*0\s*,\s*'([^']*)'\s*,\s*'((?:\\.|[^'])*)'",raw,re.S):
    n=match[1];frag=BeautifulSoup(match[2].replace('\\\"','"'),'html.parser');a=frag.select_one('a[href]');pairs.append((n,url(a['href']) if a else BASE+'/'+slot))
  out['armor-'+slot]={'catalog':'armor','entries':sorted(set(pairs))}
 return out
if __name__=='__main__':
 data={n:load(n) for n in ['weapons','items','magic','armor','enemies','bosses','areas','npcs','covenants']};out={}
 for n,r in roster().items():
  missing=[{'name':a,'url':b} for a,b in r['entries'] if not find(data[r['catalog']],a,b) and not(n=='enemies' and find(data['bosses'],a,b)) and not(n=='weapons' and find(data['items'],a,b))]
  out[n]={'compared':len(r['entries']),'missing':missing}
 (A/'full-roster-check.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({n:{'compared':v['compared'],'missing':len(v['missing'])} for n,v in out.items()},indent=2))
