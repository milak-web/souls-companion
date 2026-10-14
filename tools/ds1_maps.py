from finish_ds1_catalog import *
from urllib.parse import urlencode
def api(args):
 u='https://darksouls.fandom.com/api.php?'+urlencode({'action':'query','format':'json',**args})
 return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read())
records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'));guide=json.loads((OUT/'guide.json').read_text(encoding='utf-8'))
areas=[r for r in records if r['category']=='areas'];titles='|'.join(r['name']for r in areas)
result=api({'titles':titles,'prop':'images','imlimit':500,'redirects':1});(CACHE/'area-map-sources.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
selected={}
for page in result['query']['pages'].values():
 record=next((r for r in areas if r['name'].lower()==page.get('title','').lower()),None)
 if not record:continue
 files=[i['title']for i in page.get('images',[])if re.match(r'File:\d+\s.*\.png$',i['title'])]
 if record['id']=='firelink-shrine':files+=['File:DS1 Promotional screenshot (bonfire 3).jpg']
 if files:selected[record['id']]=files
filenames=sorted({f for files in selected.values()for f in files}|{'File:Crystal lizard vanashing.jpg'})
infos=api({'titles':'|'.join(filenames),'prop':'imageinfo','iiprop':'url','redirects':1})
urls={p['title']:p['imageinfo'][0]['url']for p in infos['query']['pages'].values()if p.get('imageinfo')}
for id,files in selected.items():
 maps=[]
 for file in files:
  if file not in urls:continue
  url=urls[file].split('/revision/')[0];data=image({'id':id,'image_candidates':[{'url':url}]})
  if data.get('image'):maps.append({'image':data['image'],'caption':file.removeprefix('File:').rsplit('.',1)[0],'source':url,'kind':'Screenshot'if'Promotional'in file else'Location map'})
 if maps:guide['areas'][id]['gallery']=maps
 print(id,len(maps),flush=True)
r=next(x for x in records if x['id']=='crystal-lizard');url=urls.get('File:Crystal lizard vanashing.jpg')
if url:r.update(image({'id':r['id'],'image_candidates':[{'url':url.split('/revision/')[0]}]}))
(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
