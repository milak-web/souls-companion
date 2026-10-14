from finish_ds1_catalog import *
def retry(r):
 if r.get('image'):return r
 for attempt in range(3):
  candidates=parse({'id':r['id']}).get('image_candidates',[])
  if not candidates:return r
  r['image_candidates']=candidates;r=image(r)
  if r.get('image'):return r
  time.sleep(2+attempt*3)
 return r
records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))
records=[r for r in records if not r['id'].startswith(('elite-cleric-','mage-smith-'))]
for r in records:
 if r['id']=='pyromancy-flame-ascended':r['param_id']=1332000
with ThreadPoolExecutor(max_workers=3)as pool:
 done=[]
 for i,f in enumerate(as_completed([pool.submit(retry,r)for r in records]),1):
  done.append(f.result())
  if i%100==0:print('Checked',i,flush=True)
done.sort(key=lambda r:(r['category'],r['name'].lower()));(OUT/'catalog.json').write_text(json.dumps(done,ensure_ascii=False,indent=2),encoding='utf-8')
print('Remaining',[(r['category'],r['id'])for r in done if not r.get('image')],flush=True)
