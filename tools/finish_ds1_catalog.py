from import_ds1 import *
from PIL import Image
from io import BytesIO
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower()).replace('armour','armor')
def describe(c):
 # One short, explicitly identified reference excerpt per source page.
 hs=c.select('h1,h2,h3,h4')
 h=next((h for h in hs if txt(h).lower() in ['description','use','usage','effect','effects']),None)
 if not h:h=next((h for h in hs if 'description' in txt(h).lower()),None)
 if h:
  for n in h.next_siblings:
   if getattr(n,'name',None) in ['h1','h2','h3','h4']:break
   if getattr(n,'name',None) in ['p','ul','ol'] and txt(n):return ' '.join(txt(n).split()[:24])
 return ''
def image(record):
 candidates=record.pop('image_candidates',[])
 candidates.sort(key=lambda i:(0 if '/local--files/'in i['url'] else 1))
 for candidate in candidates:
  url=candidate['url'].replace('http://','https://'); digest=hashlib.sha256(url.encode()).hexdigest()[:16];p=ROOT/'images/ds1'/ (digest+'.webp')
  try:
   if not p.exists():
    b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://darksouls.fandom.com/' if 'wikia' in url else BASE+'/'}),timeout=20).read()
    im=Image.open(BytesIO(b));im.load()
    if im.width<30 or im.height<30:continue
    im.thumbnail((1000,850)); im.convert('RGBA').save(p,'WEBP',quality=86)
   with Image.open(p) as im:
    if im.width<30 or im.height<30:continue
   record['image']='images/ds1/'+p.name;record['image_source']=url;return record
  except Exception:continue
 record['image']='';return record
def main():
 records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'));params=json.loads((OUT/'parameters.json').read_text())
 excluded={'ending','chest-max','head-max','hands-max','legs-max','shields-tabview','spell-tools-tabview','miracle-synergy','lordran'}
 records=[r for r in records if r['id']not in excluded]
 records.append(parse({'id':'gwyn-lord-of-cinder','name':'Gwyn, Lord of Cinder','category':'bosses','type':'Final boss','source':BASE+'/gwyn-lord-of-cinder'}))
 for r in records:
  if r['id']in ['hydra','parasitic-wall-hugger','undead-dragon']:r['category']='enemies';r['type']='Mini-bosses'
  raw=fetch(r['id']);c=BeautifulSoup(raw,'html.parser').select_one('#page-content')
  r['excerpt']=describe(c)
  # Never bulk-republish article prose or walkthroughs embedded in tables.
  for t in r['tables']:
   t['rows']=[[cell if len(cell.split())<=24 else '[See related entries below]' for cell in row] for row in t['rows']]
  r['tables']=[t for t in r['tables'] if any(re.search(r'\d',cell) for row in t['rows'] for cell in row) or len(t['rows'][0])>=3 and all(len(cell.split())<12 for row in t['rows'] for cell in row)]
  if r['category']in ['weapons','armor','rings','magic','items']:
   key={'weapons':'weapons','armor':'protectors','rings':'rings','magic':'spells','items':'items'}[r['category']]
   matches=[int(i) for i,v in params[key].items() if norm(v['name'])==norm(r['name'])]
   if matches:r['param_id']=matches[0]
  if r['category']=='armor' and 'param_id'in r:
   row=params['EquipParamProtector'][str(r['param_id'])];r['type']=['Head','Chest','Hands','Legs'][row[0]]
  if r['category']=='weapons'and'param_id'in r:r['type']=params['weaponGroups'].get(str(params['weapons'][str(r['param_id'])].get('group','')),r['type'])
  if r['category']=='magic'and'param_id'in r:r['type']=['Sorceries','Miracles','Pyromancies'][params['Magic'][str(r['param_id'])][0]]
 ids={r['id']for r in records}
 for r in records:r['relations']={h:[ref for ref in refs if ref['id']in ids] for h,refs in r['relations'].items()}
 (ROOT/'images/ds1').mkdir(parents=True,exist_ok=True);done=[]
 with ThreadPoolExecutor(max_workers=6)as pool:
  for i,f in enumerate(as_completed([pool.submit(image,r)for r in records]),1):
   done.append(f.result())
   if i%50==0:print('Images',i,'/',len(records),flush=True)
 done.sort(key=lambda r:(r['category'],r['name'].lower()))
 (OUT/'catalog.json').write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding='utf-8')
 report={'count':len(done),'categories':{cat:sum(r['category']==cat for r in done)for cat in sorted({r['category']for r in done})},'missing_images':[r['id']for r in done if not r['image']],'unmatched_parameters':{cat:[r['id']for r in done if r['category']==cat and 'param_id'not in r]for cat in ['weapons','armor','rings','magic']},'excluded_indexes':sorted(excluded),'retrieved':'2026-10-11'}
 (CACHE/'coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
