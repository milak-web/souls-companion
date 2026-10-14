"""Build local blacksmith tables from cached per-weapon reference pages.
No formulas or endpoint interpolation are used for equipment stats.
"""
from pathlib import Path
import json,re,csv
from reference_audit import load,doc,text,save,key,A
CHANNELS=['physical','magic','fire','lightning','dark'];SCALES=['str','dex','magic','fire','lightning','dark'];STATUS=['poison','bleed','petrify','curse']
STONES={'Magic':'Faintstone','Fire':'Firedrake Stone','Lightning':'Boltstone','Dark':'Darknight Stone','Poison':'Poison Stone','Bleed':'Bleed Stone','Raw':'Raw Stone','Enchanted':'Magic Stone','Mundane':'Old Mundane Stone'}
MATERIALS=['Titanite Shard','Large Titanite Shard','Titanite Chunk','Titanite Slab','Twinkling Titanite','Petrified Dragon Bone','Fire Seed']
def number(v):
 v=str(v).strip().replace(',','');return float(v) if re.fullmatch(r'\d+(\.\d+)?',v) else None
def values(v,n):
 parts=str(v).split('/');out=[number(x) for x in parts]
 if len(out)>n and all(x==0 for x in out[n:]):out=out[:n]
 return out if len(out)==n else None
def grid(table):
 spans={};out=[]
 for tr in table.select('tr'):
  cells=tr.find_all(['td','th'],recursive=False);row=[];col=0
  def carry():
   nonlocal col
   while col in spans:
    val,left=spans[col];row.append(val)
    if left==1:del spans[col]
    else:spans[col]=(val,left-1)
    col+=1
  for cell in cells:
   carry();v=text(cell);span=int(cell.get('colspan',1));height=int(cell.get('rowspan',1))
   for _ in range(span):
    row.append(v)
    if height>1:spans[col]=(v,height-1)
    col+=1
  carry();out.append(row)
 return out
out=[];gaps=[];stats={'weapons':0,'rows':0,'steps':0,'coefficients':0}
for w in load('weapons'):
 c=doc(w.get('source_url',''),False) if w.get('source_url') else None
 equipment={'id':w['id'],'source_url':w.get('source_url'),'paths':{},'steps':{}}
 if c:
  for t in c.select('table'):
   rows=grid(t)
   if not rows:continue
   heads=rows[0]
   if not all(h in heads for h in ['Name','Damage','Stat Bonuses']):continue
   for cells in rows[1:]:
    d=dict(zip(heads,cells));m=re.match(r'(.+?)\s*\+\s*(\d+)$',d.get('Name',''))
    if not m:continue
    dmg=values(d.get('Damage',''),5)
    if not dmg:
     gaps.append({'weapon':w['id'],'row':d['Name'],'field':'malformed attack','source':d.get('Damage')});dmg=[None]*5
    elif any(v is None for v in dmg):gaps.append({'weapon':w['id'],'row':d['Name'],'field':'unknown attack','source':d.get('Damage')})
    prefix=m[1];suffix=next((n for n in [w['name'],*w.get('aliases',[])] if key(prefix)==key(n) or prefix.lower().endswith(n.lower())),None)
    if not suffix:continue
    path=prefix[:-len(suffix)].strip() or 'Normal';path={'Lacerating':'Bleed','Basic':'Normal'}.get(path,path)
    if path not in ['Normal',*STONES]:continue
    if 'shield' in w['type'].lower() and path in ['Raw','Enchanted','Mundane']:continue
    if w['type'] in ['Bow','Greatbow','Crossbow'] and path in ['Poison','Bleed']:continue
    if w['type'] in ['Hammer','Great Hammer'] and path=='Bleed':continue
    level=int(m[2]);row={'level':level,'attack':dict(zip(CHANNELS,dmg))}
    grades=d.get('Stat Bonuses','').replace(' ','').split('/');scale={};coef={}
    for k,v in zip(SCALES,grades):
     g=re.fullmatch(r'([SABCDE-])(?:\((\d+(?:\.\d+)?)%\))?',v)
     scale[k]=g[1] if g else '?'
     if g and g[2]:coef[k]=float(g[2])
    row['scaling']=scale
    if coef:row['scaling_percent']=coef
    aux=values(d.get('Aux Effects',d.get('Aux. Effects','')),2)
    if aux:row['auxiliary']=dict(zip(STATUS[:2],aux))
    block=values(d.get('Damage Reduction',''),5)
    if block:row['block_reduction']=dict(zip(CHANNELS,block))
    resist=values(d.get('Aux Effects Reduction',''),4)
    if resist:row['status_reduction']=dict(zip(STATUS,resist))
    stability=number(d.get('Stability'))
    if stability is not None:row['stability']=stability
    pathrec=equipment['paths'].setdefault(path,{'rows':[]});pathrec['rows'].append(row)
    if path!='Normal':
     pathrec['stone']=STONES[path]
     h=t.find_previous(['h1','h2','h3','h4']);nodes=[]
     if h:
      for node in h.next_siblings:
       if node is t or getattr(node,'name',None) in ['h1','h2','h3','h4']:break
       if getattr(node,'name',None):nodes.append(text(node))
     context=' '.join(nodes);fee=re.search(r'(\d[\d,]*)\s+souls',context,re.I)
     pathrec['souls']=int(fee[1].replace(',','')) if fee else None
    else:
     soul=number(d.get('Souls',d.get('Souls Cost')))
     material=next((d[h] for h in ['Materials Cost','Material Costs','Material Cost','Material','Upgrade Requirements'] if h in d),'');mat=None;count=None
     for name in sorted(MATERIALS,key=len,reverse=True):
      if name in material:
       mat=name;q=re.match(r'(\d+)\s*[x×]?',material);count=int(q[1]) if q else None;break
      if name in d:
       mat=name;count=number(d[name]);break
     if level>0:equipment['steps'][str(level)]={'material':mat,'quantity':count,'souls':soul}
  for path,p in equipment['paths'].items():
   p['rows']=sorted({r['level']:r for r in p['rows']}.values(),key=lambda r:r['level'])
  normal=equipment['paths'].get('Normal',{}).get('rows',[])
  if normal and not any(r['level']==0 for r in normal):
   base={'level':0,'attack':w.get('attack',{}),'scaling':w.get('scaling',{}),'source_note':'Base stats from the individual general-information table.'}
   for src in ['auxiliary','block_reduction']:
    if w.get(src):base[src]=w[src]
   if w.get('stability') is not None:base['stability']=w['stability']
   normal.insert(0,base)
  equipment['max_level']=max((r['level'] for r in normal),default=0)
  for path,p in equipment['paths'].items():
   p['missing_levels']=[n for n in range(equipment['max_level']+1) if not any(r['level']==n for r in p['rows'])]
   if p['missing_levels']:gaps.append({'weapon':w['id'],'path':path,'missing_levels':p['missing_levels']})
 if not equipment['paths']:equipment['unavailable_reason']={'fists':'Bare fists cannot be reinforced or infused.','key-to-the-embedded':'This key weapon cannot be reinforced or infused.','torch':'Torches cannot be reinforced or infused.'}.get(w['id'],'Reinforcement data has not been verified.')
 stats['weapons']+=bool(equipment['paths']);stats['rows']+=sum(len(p['rows']) for p in equipment['paths'].values());stats['steps']+=len(equipment['steps']);out.append(equipment)
# Add independently measured maximum coefficients only where the published base values agree.
for r in csv.DictReader((A/'18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY.csv').read_text(encoding='utf-8-sig').splitlines()):
 e=next((e for e in out if key(e['id'])==key(r['Name'])),None)
 if not e:continue
 path={'Uninfused':'Normal'}.get(r['Infusion'],r['Infusion']);rows=e['paths'].get(path,{}).get('rows',[]);row=next((row for row in rows if row['level']==e['max_level']),None)
 if not row:continue
 try:
  base={k:float(r['Base '+k.title()]) for k in CHANNELS};coef={k:float(r['Scaling '+n]) for k,n in zip(SCALES,['STR','DEX','Magic','Fire','Lightning','Dark'])}
 except ValueError:continue
 if all(row['attack'].get(k) is not None and abs(base[k]-row['attack'][k])<1.1 for k in CHANNELS):
  row['scaling_percent']=coef;row['coefficient_source']='https://docs.google.com/spreadsheets/d/18ZicqVD0x92DVjjB4ZzpmjhQ0F5suNnzF4zws2q9nOY/edit';stats['coefficients']+=1
save('blacksmith',{'equipment':out,'infusions':STONES,'source_url':'https://darksouls2.wikidot.com/upgrade','remove_infusion':{'stone':'Palestone','souls':1000,'source_url':'https://steamcommunity.com/sharedfiles/filedetails/?id=522307217'}})
missingcost=[{'weapon':e['id'],'level':l,'step':s} for e in out for l,s in e['steps'].items() if any(s[k] is None for k in ['material','quantity','souls'])]
(A/'blacksmith-data-check.json').write_text(json.dumps({'stats':stats,'gaps':gaps,'missing_costs':missingcost},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'stats':stats,'gaps':gaps[:12],'gap_count':len(gaps),'missing_cost_count':len(missingcost),'missing_costs':missingcost[:15]},indent=2))
