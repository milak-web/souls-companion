from import_ds1 import *
import math
p=json.loads((OUT/'parameters.json').read_text());records=json.loads((OUT/'catalog.json').read_text(encoding='utf-8'));pathids={'Basic':0,'Normal':0,'Regular':0,'Crystal':100,'Lightning':200,'Raw':300,'Magic':400,'Enchanted':500,'Divine':600,'Occult':700,'Fire':800,'Chaos':900,'Upgrades':0};issues=[];checked=0
for entry in records:
 if entry['category']!='weapons' or not entry.get('param_id'):continue
 ident=entry['param_id'];w=p['param']['EquipParamWeapon'];reinf=p['param']['ReinforceParamWeapon']
 for table in entry['tables']:
  heads=table['rows'][0]
  if 'Damage'not in heads or 'Name'not in heads or table['heading']not in pathids:continue
  path=pathids[table['heading']]
  for row in table['rows'][1:]:
   if len(row)!=len(heads):continue
   level=re.search(r'\+(\d+)',row[heads.index('Name')]);level=int(level[1])if level else 0
   damage=row[heads.index('Damage')];match=re.match(r'^(\d+)/(\d+)/(\d+)/(\d+)(?:\s|$)',damage)
   if not match:continue
   item=p['EquipParamWeapon'].get(str(ident+path if ident not in [1330000,1332000]else ident+100*level))
   if not item:continue
   reinforce=p['ReinforceParamWeapon'].get(str(item[w['REINFORCE_ID']]+(level if ident not in [1330000,1332000]else 0)))
   if not reinforce:continue
   expected=list(map(int,match.groups()));actual=[math.floor(round(item[w[k+'_ATK']]*reinforce[reinf[k+'_ATK_CORRECT']],4))for k in ['PHYSICAL','MAGIC','FIRE','LIGHTNING']];checked+=1
   if expected!=actual:issues.append({'weapon':entry['id'],'path':table['heading'],'level':level,'wiki':expected,'parameters':actual})
report={'checked_rows':checked,'differences':issues,'sources':['https://darksouls.wikidot.com/weapons','https://soulsplanner.com/darksouls/weaponatk'],'notes':'A difference is a reference disagreement, not automatically an implementation error. Numerical parameter data drives the calculator.'}
(CACHE/'weapon-values.json').write_text(json.dumps(report,indent=2));print('Compared',checked,'rows; differences',len(issues));print(issues[:20])
