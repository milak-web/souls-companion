from import_ds1 import *
params=json.loads((OUT/'parameters.json').read_text());records=json.loads((OUT/'catalog.json').read_text());guide=json.loads((OUT/'guide.json').read_text());byid={r['id']:r for r in records}
# Wiki folders and warp destinations are not ordinary inventory objects.
exclude={'offensive-items','hostile-npcs'}
for r in records:
 if r['id']in ['altar-of-sunlight','altar-of-the-gravelord','chamber-of-the-princess','darkmoon-tomb']:r['category']='bonfires';r['type']='Warp destination'
 if r['id']=='humanity':r['category']='items';r['type']='Consumables';r['param_id']=500
records=[r for r in records if r['id']not in exclude];ids={r['id']for r in records}
for r in records:
 r['relations']={h:[x for x in refs if x['id']in ids]for h,refs in r['relations'].items()}
 # Numeric parameters, names and terse classifications are the reference tables.
 # Remove explanatory "Key" tables and article-sized cells, which are not data.
 r['tables']=[t for t in r['tables']if t['heading'].lower()not in ['key','walkthrough','dialogue','dialogues','trivia']]
 for t in r['tables']:
  for row in t['rows']:
   for i,cell in enumerate(row):
    if len(cell.split())>14 and not re.fullmatch(r'[\d\s.,/%+()\-A-Z]+',cell):row[i]='—'
    else:row[i]=cell.replace('\ufffd','').strip()
 # Inventory references support boss soul consumption and transposition-like recipes.
 if r['category']=='items':
  c=BeautifulSoup(fetch(r['id']),'html.parser').select_one('#page-content');h=next((h for h in c.select('h1,h2,h3')if txt(h)in ['Use','Usage']),None)
  use=[]
  if h:
   for n in h.next_siblings:
    if getattr(n,'name',None)in ['h1','h2','h3']:break
    if getattr(n,'name',None):use.append(n)
  content=' '.join(txt(n)for n in use)
  consumption=re.search(r'(?:[Pp]rovides|[Cc]onsumed for|[Gg]rants)\s+([\d,]+)\s+souls',content)
  if not consumption:consumption=re.search(r'([\d,]+)\s+souls\s+when consumed',content)
  if consumption:
   r['soul_value']=int(consumption[1].replace(',',''));existing=guide['entries'].setdefault(r['id'],{'summary':'A soul consumable. Using it grants souls; special souls may also be exchanged for equipment.'})
   paragraphs=[f"Consumption reward: {r['soul_value']:,} souls."]
   recipes=[]
   for n in use:
    text=txt(n)
    if not any(k in text.lower()for k in ['craft','trade','acquire','offer']):continue
    named=[a['href'].strip('/')for a in n.select('a[href]')if a['href'].strip('/')in ids]
    output=[i for i in named if byid[i]['category']in ['weapons','magic']]
    inputs=[i for i in named if byid[i]['category']in ['weapons']and i not in output]
    if output:
     recipes+=output
     if 'craft'in text.lower():paragraphs.append('Boss weapon recipe: '+', '.join(byid[i]['name']for i in output)+'. Requires the indicated compatible +10 weapon or shield and this soul at the Giant Blacksmith. '+('Base equipment: '+', '.join(byid[i]['name']for i in inputs)+'.'if inputs else 'See the equipment entry for its eligible base classes.'))
     elif 'ciaran'in text.lower():paragraphs.append('Ciaran exchange: give this soul to receive both tracers. This spends the soul instead of crafting the boss weapon.')
     elif 'sunlight'in text.lower():paragraphs.append('Covenant offering: a rank +1 Warrior of Sunlight can exchange this soul at the Sunlight Altar for Sunlight Spear.')
   if recipes:existing.setdefault('sections',[]).append({'title':'Consume or exchange','paragraphs':paragraphs,'ids':recipes+(['giant-blacksmith']if any('Boss weapon'in p for p in paragraphs)else[])})
   else:existing.setdefault('sections',[]).append({'title':'Consumption','paragraphs':paragraphs,'ids':[]})
bosses={
 'anor-londo':['dragon-slayer-ornstein-executioner-smough','dark-sun-gwyndolin'],'undead-asylum':['asylum-demon','stray-demon'],'undead-burg':['taurus-demon','capra-demon'],'undead-parish':['bell-gargoyles'],'darkroot-garden':['moonlight-butterfly','sif-the-great-grey-wolf'],'depths':['gaping-dragon'],'quelaag-s-domain':['chaos-witch-quelaag'],'sen-s-fortress':['iron-golem'],'painted-world-of-ariamis':['crossbreed-priscilla'],'the-catacombs':['pinwheel'],'tomb-of-the-giants':['gravelord-nito'],'the-duke-s-archives':['seath-the-scaleless'],'crystal-cave':['seath-the-scaleless'],'demon-ruins':['ceaseless-discharge','demon-firesage','centipede-demon'],'lost-izalith':['the-bed-of-chaos'],'new-londo-ruins':['the-four-kings'],'the-abyss':['the-four-kings'],'kiln-of-the-first-flame':['gwyn-lord-of-cinder'],'sanctuary-garden':['sanctuary-guardian'],'royal-wood':['knight-artorias','black-dragon-kalameet'],'chasm-of-the-abyss':['manus-father-of-the-abyss']}
for id,a in guide['areas'].items():a['bosses']=bosses.get(id,[])
guide['areas']['chasm-of-the-abyss']['notes']='Sif encountered here is the rescued young summon, not a second fight against the Darkroot Garden boss.'
guide['areas']['new-londo-ruins']['notes']='The Four Kings are fought in the connected Abyss. No bonfire exists within New Londo itself.'
guide['areas']['the-duke-s-archives']['notes']='Seath’s first encounter takes place in the Archives. The final killable encounter is in Crystal Cave.'
guide['entries']['rotten-pine-resin']['sections'][0]['paragraphs'][0]='Coats a compatible right-hand weapon with poison for 60 seconds. It is a temporary coating; DS1 has no generic Poison ascension path.'
for r in records:
 if r['category']=='rings':
  e=params['EquipParamAccessory'][str(r['param_id'])]; row=params['SpEffectParam'].get(str(e[0]));sp=params['param']['SpEffectParam'];facts=[]
  if row:
   for key,label in [('HP_CORRECT','Max HP'),('STAMINA_CORRECT','Max stamina'),('EQUIPMENT_LOAD_CORRECT','Equip capacity'),('BLEED_RES_CORRECT','Bleed resistance'),('POISON_RES_CORRECT','Poison resistance'),('CURSE_RES_CORRECT','Curse resistance'),('PHYSICAL_ATK_CORRECT','Physical attack'),('MAGIC_ATK_CORRECT','Magic attack'),('FIRE_ATK_CORRECT','Fire attack'),('LIGHTNING_ATK_CORRECT','Lightning attack')]:
    v=row[sp[key]]
    if abs(v-1)>.0001:facts.append(f'{label}: {(v-1)*100:+.0f}%.')
   for key,label in [('POISE_CORRECT','Poise'),('ATTUNEMENT_SLOT_COUNT_CORRECT','Attunement slots'),('STAMINA_REGEN_SPEED_CORRECT','Stamina recovery per second'),('PHYSICAL_DEF','Physical defense'),('MAGIC_DEF','Magic defense'),('FIRE_DEF','Fire defense'),('LIGHTNING_DEF','Lightning defense')]:
    v=row[sp[key]]
    if abs(v)>.0001:facts.append(f'{label}: {v:+g}.')
   if facts:
    if row[0]==20:facts.insert(0,'These modifiers apply only at or below 20% HP.')
    guide['entries'].setdefault(r['id'],{'summary':'Ring equipment; occupies one of two ring slots.'}).setdefault('sections',[]).append({'title':'Equipment effects','paragraphs':[' '.join(facts)],'ids':[]})
(OUT/'catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8')
print('Enriched',len(records),'entries')
