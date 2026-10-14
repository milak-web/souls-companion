"""Import factual parameter tables from the wiki-linked combat research workbook.

Run read_combat_reference.py first. Never evaluate workbook formulas as code.
Only known formula families are translated; unresolved effects remain descriptive.
"""
import json, re, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'database'
SOURCE = 'https://docs.google.com/spreadsheets/d/1EJq2GUJxTxsezAOz_RPllRWMg1lJNE3Xdc6HWhh7Fnc/edit'
cells = json.loads((ROOT/'audit/combat-reference-cells.json').read_text(encoding='utf-8'))
def load(name): return json.loads((D/(name+'.json')).read_text(encoding='utf-8'))
def save(name,obj): (D/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(sheet):
    return [{re.sub(r'\d+', '', k): v for k,v in r.items()} for r in cells[sheet]]
def val(r,c,default=None): return r.get(c,{}).get('v',default)
def num(r,c,default=0):
    try:return float(val(r,c))
    except (ValueError,TypeError):return default
def key(s):return re.sub('[^a-z0-9]','',s.lower().replace(' (weapon)','').replace(' (shield)','').replace(' (helm)',''))
def col(n):
    out=''
    while n: n,a=divmod(n-1,26);out=chr(65+a)+out
    return out
def ci(s):
    n=0
    for c in s:n=n*26+ord(c)-64
    return n
stats=['vgr','end','vit','atn','str','dex','adp','int','fth']
levelcols=dict(zip(['hp','other_hp','stamina_x10','slots','agility','backstep_frames','roll_frames','landing_frames','load','swap_speed','item_speed','guard_speed','str','dex','magic','lightning','fire','dark','poison','bleed','mundane','element_defense','unarmored_defense','armor_bonus','poise','cast_time'],[col(i) for i in range(2,28)]))
levels={str(int(num(r,'A'))):{k:val(r,c) if k=='agility' else num(r,c) for k,c in levelcols.items()} for r in rows('PlayerLevels')[2:] if 1<=num(r,'A')<=99}
classes={val(rows('StarterClasses')[0],c):dict(zip(stats,[int(num(r,c)) for r in rows('StarterClasses')[1:10]])) for c in 'BCDEFGHI'}
weapons=load('weapons');armor=load('armor');items=load('items');smith=load('blacksmith')
virtual=[{'id':'vanquisher_fists','name':"Vanquisher's Seal"},{'id':'majestic_left','name':'Majestic Greatsword L'},{'id':'santier_unbroken','name':"Santier's Spear (Unbroken)"}]
aliases={'majesticgreatsword':'majesticgreatswordr','santiersspear':'santiersspearbroken','wanderermanchette':'wanderermanchettes'}
for a in armor:
    k=key(a['name'])
    if 'ofaurous' in k:aliases[k]=key(a['name'].replace(' (transparent)','')+(' (Invisible)' if 'transparent' in k else ' (Visible)'))
aliases.update({'prisonershood':'prisonershooda','prisonershoodeyecover':'prisonershoodb','prisonerstatters':'prisonerstatter sa'.replace(' ',''),'prisonerst attersrightshoulder'.replace(' ',''):'prisonerstattersb'})
def match(cat,name):
    target=key(name)
    return next((a for a in cat if aliases.get(key(a['name']),key(a['name']))==target),None)
params={};name=None
scale_starts={'str':'CC','dex':'CN','magic':'CY','lightning':'DJ','fire':'DU','dark':'EF','poison':'EQ','bleed':'FB','enchanted':'FM'}
channels=['physical','magic','lightning','fire','dark','poison','bleed']
for r in rows('Weapons')[2:]:
    if val(r,'GQ'):name=val(r,'GQ')
    w=match(weapons+virtual,name or '')
    if not w or val(r,'G') not in ['Base','Magic','Lightning','Fire','Dark','Poison','Bleed','Raw','Enchanted','Mundane']:continue
    path=val(r,'G');path='Normal' if path=='Base' else path
    p={'max_level':int(num(r,'I')),'scaling':{ch:[num(r,col(ci(c)+lv),None) for lv in range(int(num(r,'I'))+1)] for ch,c in scale_starts.items()},'flags':dict(zip(channels,[num(r,col(ci('AW')+i)) for i in range(7)])),'innate':dict(zip(channels,[num(r,col(ci('AP')+i))/100 for i in range(7)])),'base':dict(zip(channels,[num(r,col(ci('BE')+i)) for i in range(7)])),'increment':dict(zip(channels,[num(r,col(ci('BL')+i)) for i in range(7)])),'base_multiplier':num(r,'BS',1),'infusion_multiplier':num(r,'BU'),'element_count':num(r,'BT'),'damage_multiplier':dict(zip(channels,[num(r,col(ci('BV')+i),1) for i in range(7)])),'mundane':num(r,'FX'),'blades':[num(r,c) for c in ['FY','FZ','GA']],'oath':num(r,'GB'),'clutch':{ch:num(r,c) for ch,c in [('magic','GD'),('lightning','GE'),('fire','GF'),('dark','GH')]},'king_ring':num(r,'GG'),'status_ring':{'poison':num(r,'GJ'),'bleed':num(r,'GK')},'buff_correction':num(r,'GO'),'resin':val(r,'AE')=='Y','spell_buff':val(r,'AF')=='Y','requirements':dict(zip(['str','dex','int','fth'],[num(r,c) for c in ['AA','AB','AC','AD']])),'source_row':int(num(r,'B'))}
    p.update(weight=num(r,'N'),durability=num(r,'O'))
    params.setdefault(w['id'],{})[path]=p
# The workbook contains #REF! cells for Varangian Shield. Do not turn those into zero.
varangian=next(e for e in smith['equipment'] if e['id']=='varangian-shield')
varangian_weapon=next(w for w in weapons if w['id']=='varangian-shield')
params['varangian-shield']={}
for path,data in varangian['paths'].items():
    rows_by_level=sorted(data['rows'],key=lambda x:x['level']);first=rows_by_level[0]
    values={**first['attack'],**first['auxiliary']}
    params['varangian-shield'][path]={'max_level':varangian['max_level'],'scaling':{**{ch:[r['scaling_percent'][ch]/100 for r in rows_by_level] for ch in ['str','dex','magic','fire','lightning','dark']},**{ch:[(r['aux_scaling_percent'][ch] or 0)/100 for r in rows_by_level] for ch in ['poison','bleed']},'enchanted':[0]*11},'flags':{ch:200 if v else 0 for ch,v in values.items()},'innate':{ch:1 if v else 0 for ch,v in values.items()},'base':values,'increment':dict.fromkeys(values,0),'base_multiplier':1,'infusion_multiplier':0,'element_count':0,'damage_multiplier':dict.fromkeys(values,1),'mundane':0,'blades':[0,0,0],'oath':0,'clutch':dict.fromkeys(['magic','fire','lightning','dark'],0),'king_ring':0,'status_ring':{'poison':0,'bleed':0},'buff_correction':0,'resin':False,'spell_buff':False,'requirements':varangian_weapon['requirements'],'weight':3,'durability':70,'source_url':varangian['source_url'],'source_note':'Varangian Shield uses the wiki’s individually published percentages because the combat workbook contains broken references. Precision beyond those rounded values and its ring/buff affinity are not verified.'}
armor_models={};unmatched=[]
for r in rows('Armors')[2:433]:
    name=val(r,'AX')
    if not name:continue
    a=match(armor,name)
    if not a:unmatched.append(name);continue
    effect={k:num(r,c) for k,c in zip(['vgr','end','vit','str','dex','adp','int','fth'],'DEFGHIJK') if num(r,c) and not r.get(c,{}).get('f')}
    model={'max_level':int(num(r,'T')),'base':dict(zip(['strike','slash','thrust','magic','fire','lightning','dark','poison','bleed'],[num(r,c) for c in ['U','V','W','X','Y','Z','AA','AB','AC']])),'increment':dict(zip(['strike','slash','thrust','magic','fire','lightning','dark','poison','bleed'],[num(r,c) for c in ['AD','AE','AF','AG','AH','AI','AJ','AK','AL']])),'scaling':num(r,'AM'),'poise':num(r,'AN'),'weight':num(r,'AO'),'stats':effect,'requirements':dict(zip(['str','dex','int','fth'],[num(r,c) for c in ['AQ','AR','AS','AT']]))}
    armor_models[a['id']]=model
# The combat workbook omits this obtainable set. Import its explicitly published rows.
hollow_source=ROOT/'audit/wiki-gg/Hollow Soldier Set.txt'
if hollow_source.exists():
    raw=hollow_source.read_text(encoding='utf-8')
    for i,(name,block) in enumerate(re.findall(r'\|-\|([^=]+)=\s*\{\{Armor upgrade table \+10(.*?)\}\}',raw,re.S)):
        a=match(armor,name.strip())
        if not a:continue
        vals={k.strip():float(v) for k,v in re.findall(r'\|\s*([^=\n]+?)\s*=\s*([\d.]+)',block)}
        channels=['strike','slash','thrust','magic','fire','lightning','dark','poison','bleed','petrify','curse']
        explicit={str(lv):{ch:vals[ch.capitalize()+' Reduction'+str(lv)] for ch in channels} for lv in range(11)}
        armor_models[a['id']]={'max_level':10,'rows':explicit,'base':explicit['0'],'increment':{},'scaling':.53 if a['slot']=='chest' else .26,'poise':a['defenses_base']['poise'],'weight':a['defenses_base']['weight'],'stats':{},'requirements':{},'source_url':'https://darksouls2.wiki.gg/wiki/Hollow_Soldier_Set'}
effects={}
for sheet,colname,cat in [('Armors','AX',armor),('Rings','AI',items),('Offhand','Z',weapons),('Items','A',items)]:
    for r in rows(sheet)[1:]:
        n=val(r,colname)
        if not n or n in ['English','Consumables']:continue
        a=match(cat,n)
        if not a:continue
        e={'stats':{},'defense':{},'source_url':SOURCE,'description':a.get('usage') or a.get('special_effect') or a.get('special_effect', '')}
        if sheet in ['Armors','Rings','Offhand']:
            e['stats']={k:num(r,c) for k,c in zip(['vgr','end','vit','str','dex','adp','int','fth'],'DEFGHIJK') if num(r,c) and not r.get(c,{}).get('f')}
        if sheet=='Rings':
            e['weight']=num(r,'O',a.get('equipment_stats',{}).get('weight',0))
            e['defense']={ch:num(r,c) for ch,c in zip(['strike','slash','thrust','magic','fire','lightning','dark','poison','bleed'],'PQRSTUVWX') if num(r,c)}
            for k,c in [('hp_mult','L'),('load_mult','M')]:
                f=r.get(c,{}).get('f','') or '';m=re.search(r',\s*(1\.\d+)\s*,\s*1\)',f)
                if m:e[k]=float(m[1])
            for label,field,values in [('Life Ring','hp_mult',[1.05,1.075,1.125,1.15]),('Royal Soldier\'s Ring','load_mult',[1.1,1.15,1.2]),('Chloranthy Ring','regen',[.15,.20,.25]),('Ring of Giants','poise',[10,20,30]),('Clear Bluestone Ring','cast_time_mult',[.8,.65,.6]),('Southern Ritual Band','slots',[1,2,3]),('Northern Ritual Band','hp_mult',[.8,.65,.5])]:
                if n.startswith(label):lv=int(n[-1]) if re.search(r'\+[123]$',n) else 0;e[field]=values[lv]
            for dragon,hp,stam,capacity in [('First',1.03,1.05,1.05),('Second',1.05,1.1,1.1),('Third',1.075,1.125,1.125)]:
                if n==dragon+' Dragon Ring':e.update(hp_mult=hp,stamina_mult=stam,load_mult=capacity,family='Dragon Ring')
            for name,stat in [('Strength Ring','str'),('Dexterity Ring','dex'),('Ring of Knowledge','int'),('Ring of Prayer','fth'),('Simpleton\'s Ring','adp')]:
                if n==name:e['stats'][stat]=5
            if n=='Blue Seal':e['hp_mult']=1.03
            if n=='Ring of the Embedded':e['embedded']=True
            if n=='Stone Ring':e['poise_damage']=30
            e.setdefault('family',a.get('ring_family') or re.sub(r'\s*\+\d+$','',n))
        if sheet=='Items':
            e['stats']={k:num(r,c) for k,c in zip(['str','dex','int','fth'],'DEFG') if num(r,c)}
            e['defense']={ch:num(r,c) for ch,c in zip(['magic','lightning','fire','dark','poison','bleed','petrify'],'HIJKLMN') if num(r,c)}
            if e['stats']:e['duration']=45
            if e['defense']:e['duration']=90
            if n=='Green Blossom':e.update(regen=.15,duration=60)
            if n=='Brightbug':e.update(damage_mult=1.2,damage_taken_mult=.8,duration=120)
            m=re.search(r'(?:Heals|cures) (\d+) HP over ([\d.]+)s',val(r,'C',''))
            if m:e.update(heal=int(m[1]),heal_duration=float(m[2]))
            if n=='Divine Blessing':e['full_heal']=True
            if n=='Human Effigy':e['human']=True
        if sheet=='Offhand':
            e['defense']={ch:num(r,c) for ch,c in zip(['magic','lightning','fire','dark','poison','bleed'],'MNOPQR') if num(r,c)}
            if n in ['Blossom Kite Shield','Slumbering Dragon Shield','Shield of the Insolent']:e['regen']=.05
        # These rows contain aggregates, never per-item values.
        if sheet=='Armors' and n=='Alonne Captain Helm':e['stats']={}
        if sheet=='Armors':
            ident=int(num(r,'B'))
            if ident in {46:1.01,84:1.03,127:1.015,263:1.01,385:1.015}:e['load_mult']={46:1.01,84:1.03,127:1.015,263:1.01,385:1.015}[ident]
            if ident in [10,18,179,285,388]:e['cast_time_mult']=.9 if ident==10 else .95
            if ident==12:e['slots']=1
            if ident==11:
                e.update(hp_mult=.85,spell_damage_mult=1.03)
                e['source_note']='Domino Mask: uses the individually documented 15% HP reduction; the combat workbook description says 10%.'
            if ident==302:e['pyromancy_damage_mult']=1.075
        effects[a['id']]=e
buffs=[]
for r in rows('Buffs'):
    if num(r,'D',None) is None or val(r,'A')=='None':continue
    name=val(r,'A');kind=int(num(r,'E'));ch={2:'magic',3:'lightning',4:'fire',5:'dark',6:'poison',7:'bleed',0:'special'}.get(int(num(r,'D')))
    if not name or not ch:continue
    record=match(items+load('magic')+weapons,name)
    buffs.append({'name':name,'id':record['id'] if record else 'resonant-weapon','flat':num(r,'B'),'multiplier':num(r,'C'),'channel':ch,'type':['resin','spell','special'][kind],'duration':90 if kind==0 else None})
for buff in buffs:
    for r in rows('Widgets'):
        if val(r,'Q')==buff['name'] and val(r,'S') in ['Int','Fth']:
            buff['duration_model']={'stat':val(r,'S').lower(),'minimum_stat':12 if val(r,'S')=='Fth' else 10,'cap':num(r,'W'),'minimum':num(r,'U'),'maximum':num(r,'V'),'base':num(r,'X')}
# Per-level costs are direct game parameter table values; index is the target level.
costs={str(int(num(r,'A'))):int(num(r,'B')) for r in rows('LevelCosts')[1:] if 1<=num(r,'A')<=838}
out={'source_url':SOURCE,'reference_version':'Combat calculator 4.0','levels':levels,'classes':classes,'weapons':params,'armor':armor_models,'effects':effects,'buffs':buffs,'level_costs':costs,'notes':['Published community parameter tables; not compared to a local game executable.','Per-level armor uses the published base plus per-level parameter increment, with physical attribute scaling applied separately. Hollow Soldier armor uses the separately published wiki reinforcement rows.','Agility and i-frames use the investment table, including hidden tiers with identical displayed agility.','Flynn and base Chloranthy have conflicting published descriptions. This model follows the combat research formulas (Flynn maximum-load curve; Chloranthy 15%).','Northern Ritual Band +1 uses the corroborated 35% HP reduction, correcting the combat spreadsheet’s contradictory 25% formula.']}
# The wiki's single Majestic table describes the left-hand variant. Keep it,
# but make default cards and Blacksmith consistently show the right-hand variant.
majestic=next(e for e in smith['equipment'] if e['id']=='majestic-greatsword')
for path,pr in majestic['paths'].items():
    p=params['majestic-greatsword'][path]
    for row in pr['rows']:
        row.setdefault('left_hand_attack',dict(row['attack']))
        row['attack']={ch:math.floor((p['base'][ch]+p['increment'][ch]*row['level'])*p['base_multiplier']*p['damage_multiplier'][ch]+1e-9) if p['flags'][ch] else 0 for ch in row['attack']}
majestic['variant_note']='Default values are for the right hand. The published wiki table describes the stronger left-hand variant; Character Lab switches automatically with the selected hand.'
majestic['parameter_source']=SOURCE
save('blacksmith',smith)
save('character',out)
# One canonical published reinforcement table for cards, comparisons and Blacksmith.
changed=0
for w in weapons:
    e=next((x for x in smith['equipment'] if x['id']==w['id']),None)
    if not e or not e.get('paths'):continue
    normal=e['paths'].get('Normal',{}).get('rows',[])
    if not normal:continue
    w['upgrade_stats']=[{'path':path,'level':r['level'],'attack':r['attack'],'scaling':r['scaling']} for path,p in e['paths'].items() for r in p['rows']]
    w.update(attack=normal[0]['attack'],base_damage=normal[0]['attack']['physical'],physical_ar=normal[0]['attack']['physical'],scaling=normal[0]['scaling'],auxiliary=normal[0]['auxiliary'])
    p=params.get(w['id'],{}).get('Normal')
    if p:w['requirements']=p['requirements'];w['weight']=p['weight'];w['durability']=p['durability']
    last=normal[-1]
    w['max_scaling_percent']=last['scaling_percent'];w['coefficient_level']=last['level'];w['scaling_source']=e['source_url']
    if p:
        lv=last['level'];w['max_scaling_percent']={ch:p['scaling'][ch][lv]*100 if ch in ['str','dex'] or p['flags'][ch] else 0 for ch in ['str','dex','magic','fire','lightning','dark']}
    w['additional_sources']=list(dict.fromkeys(w.get('additional_sources',[])+[e['source_url'],SOURCE]));changed+=1
save('weapons',weapons)
report={'weapon_models':len(params),'armor_models':len(armor_models),'ring_models':sum(a['id'] in effects for a in items if a['type']=='Ring'),'reconciled_weapons':changed,'missing_weapon_models':[w['name'] for w in weapons if w['id'] not in params],'missing_armor_models':[a['name'] for a in armor if a.get('slot') and a['id'] not in armor_models],'missing_rings':[a['name'] for a in items if a['type']=='Ring' and a['id'] not in effects],'unmatched_reference_armor':unmatched}
(ROOT/'audit/character-data-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

