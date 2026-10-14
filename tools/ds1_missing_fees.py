from import_ds1 import *
from urllib.parse import urlencode
records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'));params=json.loads((OUT/'parameters.json').read_text());targets=[r for r in records if r['category']=='weapons'and r.get('param_id')and params['EquipParamWeapon'][str(r['param_id'])][2]>0 and not any('Souls'in t['rows'][0]or'Cost (souls)'in t['rows'][0]for t in r['tables'])]
def one(r):
 try:
  cache=CACHE/('fee-'+r['id']+'.json')
  if cache.exists():data=json.loads(cache.read_text(encoding='utf-8'))
  else:
   u='https://darksouls.fandom.com/api.php?'+urlencode({'action':'parse','page':'Four-Pronged Plow'if r['id']=='four-pronged-plow'else r['name'],'prop':'text','format':'json','redirects':1})
   data=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read());cache.write_text(json.dumps(data),encoding='utf-8')
  c=BeautifulSoup(data.get('parse',{}).get('text',{}).get('*',''),'html.parser');text=txt(c)
  fees={int(m.replace(',',''))for m in re.findall(r'([\d,]+)\s+souls per upgrade',text,re.I)}
  if not fees:fees={int(m.replace(',',''))for m in re.findall(r'Requires:[^.\n]{0,150}?([\d,]+)\s+[Ss]ouls\s+and\s+(?:Twinkling|Demon)',text)}
  if len(fees)==1:r['upgrade_fee']=next(iter(fees));r['upgrade_fee_source']='https://darksouls.fandom.com/wiki/'+data['parse']['title'].replace(' ','_');print(r['id'],r['upgrade_fee'],flush=True)
  else:print(r['id'],'unverified fee',fees,flush=True)
 except Exception as e:print(r['id'],str(e),flush=True)
 return r
with ThreadPoolExecutor(max_workers=3)as pool:updates={r['id']:r for r in pool.map(one,targets)}
records=[updates.get(r['id'],r)for r in records];(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');print('Researched',len(targets),'fee gaps')
