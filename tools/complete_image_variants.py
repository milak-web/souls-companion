import json,urllib.request,urllib.parse,io
from pathlib import Path
from PIL import Image
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
def load(n):return json.loads((R/'database'/f'{n}.json').read_text(encoding='utf-8'))
def fetch(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'DS2OfflineGuideImageAudit/1.9.1'}),timeout=25).read()
def save(n,d):(R/'database'/f'{n}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
enemies=load('enemies');items=load('items');report=[]
for id in ['looking-glass-phantom','prisoned-sinner','royal-infantry','royal-soldier','armored-skeleton']:
 r=next(x for x in enemies if x['id']==id)
 p=json.loads((R/'audit'/f'image-page-{id}.json').read_text(encoding='utf-8'))['parse']
 s=BeautifulSoup(p['text']['*'],'html.parser');images=[i for i in s.select('img') if int(i.get('data-file-width',0))>=100 and 'Defense' not in i.get('alt','')]
 if id=='armored-skeleton':images=[i for i in images if i.get('alt')=='Skeleton Falchions.png']
 if not images:report.append({'id':id,'error':'No specific portrait'});continue
 image=images[0];url=urllib.parse.urljoin('https://darksouls2.wiki.gg',image['src']);im=Image.open(io.BytesIO(fetch(url)));im.verify();im=Image.open(io.BytesIO(fetch(url)))
 dest=R/'assets/enemies'/f'verified-{id}.png';im.save(dest)
 r.update(image=dest.relative_to(R).as_posix(),image_source=url,image_verified=True,image_kind='game-reference',image_reference='https://darksouls2.wiki.gg/wiki/'+urllib.parse.quote(p['title'].replace(' ','_')))
 r.pop('image_note',None);report.append({'id':id,'image':r['image'],'source':url})
durgo=next(x for x in enemies if x['id']=='blue-eyed-durgo');greatbow=next(x for x in enemies if x['id']=='greatbow-phantom')
if greatbow.get('image_verified'):
 durgo.update(image=greatbow['image'],image_source=greatbow['image_source'],image_verified=True,image_kind='game-reference',image_reference='https://darksouls.fandom.com/wiki/Blue-eyed_Durgo',image_note='Blue-eyed Durgo is also called the Greatbow Phantom; their portrait is shared.')
 report.append({'id':durgo['id'],'image':durgo['image'],'alias_of':greatbow['id']})
for id,hash in [('hello-carving','sPee28p'),('thank-you-carving','U0QFyVG'),('i-m-sorry-carving','hlyl9PM'),('very-good-carving','OIQNs25')]:
 r=next(x for x in items if x['id']==id);u='https://i.imgur.com/'+hash+'.png'
 try:
  raw=fetch(u);im=Image.open(io.BytesIO(raw));im.verify();im=Image.open(io.BytesIO(raw));dest=R/'assets/items'/f'verified-{id}.png';im.save(dest)
  r.update(image=dest.relative_to(R).as_posix(),image_source=u,image_verified=True,image_kind='game-reference',image_reference='https://darksouls2.wikidot.com/multiplayer-items');r.pop('image_note',None);report.append({'id':id,'image':r['image'],'source':u})
 except Exception as e:report.append({'id':id,'error':str(e)})
save('enemies',enemies);save('items',items)
(R/'audit/image-variants.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
