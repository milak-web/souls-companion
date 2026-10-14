"""Complete named ring variants and classify source-unreconciled legacy records explicitly."""
from reference_audit import *
import copy
I=load('items');E=load('enemies');N=load('npcs');changes=[];variant_names=[]
for row in named_rows('/rings'):
 base=find(I,row['name'],row['url'])
 if not base:continue
 c=doc(row['url']);availability=sections(c,'Availability')
 for h,rows in tables(c):
  if not {'Name','Use','Weight','Durability'}.issubset(h):continue
  for _,cells in rows:
   if len(cells)!=len(h):continue
   vals=dict(zip(h,map(text,cells)));name=vals['Name']
   if not key(name).startswith(key(base['name'])):continue
   r=find(I,name)
   if not r:
    r=copy.deepcopy(base);r['id']=slug(name);r['name']=name;r['aliases']=[];r.pop('direct_drop',None);r.pop('trades',None);I.append(r);changes.append({'kind':'ring-variant','name':name})
   r['type']='Ring';r['usage']=vals['Use'];r['description']='Ring - '+vals['Use'];r['source_url']=row['url'];r['equipment_stats']={k.lower():nums(vals[k])[0] for k in ['Weight','Durability'] if nums(vals[k])};r['ring_family']=base['name'];variant_names.append(name)
   # Match the variant heading or bullet in the source's availability section.
   version=re.search(r'\+(\d+)$',name);target=version[0] if version else 'Regular'
   nodes=[]
   for n in availability:
    for li in n.select('li'):
     own=text(li).split('+',1)[0] if not version else text(li)
     if (version and re.match(r'^'+re.escape(target)+r'\b',text(li))) or (not version and text(li).startswith('Regular')):nodes.append(li)
   if nodes:r['obtaining']=' '.join(text(n) for n in nodes);r['acquisition_refs']=[{'name':n,'source_url':u} for node in nodes for n,u in list_pairs(node)]
# Soul consumption is a distinct category, including ordinary found souls.
for r in I:
 if 'soul_value' in r:r['type']='Soul'
for r in E:
 if not r.get('source_url'):
  r['data_status']='Source not yet reconciled';r['hp']=None;r['souls']=None;r['weaknesses']={};r['status_effects']={};r['can_parry']=None;r['can_backstab']=None
  for drop in r.get('drops',[]):
   if '%' in drop.get('chance',''):drop['chance']='Rate not verified'
  r['stat_context']='This legacy name still needs reconciliation with the reference roster. Unverified stats are omitted.'
 # Safe, existing generic art for the three pages without a usable image.
 if r.get('image') and not(ROOT/r['image']).is_file():r['image']='assets/ui/stat/stat-physical-attack.webp';r['image_verified']=False
save('items',I);save('enemies',E)
(A/'ring-variant-repairs.json').write_text(json.dumps({'added':changes,'published_variants':sorted(set(variant_names))},indent=2)+'\n',encoding='utf-8');print('Ring variants added',len(changes),'published total',len(set(variant_names)),'items',len(I))
