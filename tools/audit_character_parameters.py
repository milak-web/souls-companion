"""Compare independently published wiki rows and the wiki-linked parameter workbook."""
import json, math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(n):return json.loads((R/'database'/f'{n}.json').read_text(encoding='utf-8'))
character=load('character');smith=load('blacksmith');attack_diffs=[];scale_diffs=[];missing=[];rows=0;rounded=0
for e in smith['equipment']:
 for path,pr in e['paths'].items():
  p=character['weapons'].get(e['id'],{}).get(path)
  if not p:missing.append([e['id'],path]);continue
  for row in pr['rows']:
   rows+=1;lv=row['level']
   if p.get('source_note'):continue
   for ch in ['physical','magic','fire','lightning','dark','poison','bleed']:
    published=row['attack'].get(ch,row['auxiliary'].get(ch,0))
    computed=math.floor((p['base'][ch]+p['increment'][ch]*lv)*p['base_multiplier']*p['damage_multiplier'][ch]+1e-9) if p['flags'][ch] else 0
    if published!=computed:
     if abs(published-computed)<=1:rounded+=1
     else:attack_diffs.append({'id':e['id'],'path':path,'level':lv,'channel':ch,'wiki':published,'parameters':computed})
   factor=1-p['infusion_multiplier']/max(1,p['element_count'])
   for ch in ['str','dex','magic','fire','lightning','dark']:
    raw=p['scaling'][ch][lv]
    effective=(raw*(factor if p['flags']['physical']==100 else 1)*100 if ch in ['str','dex'] else raw*(p['innate'][ch]+p['infusion_multiplier'] if p['flags'][ch]==200 else factor)*100 if p['flags'][ch] else 0)
    if path=='Mundane' and ch in ['str','dex']:continue
    published=row['scaling_percent'].get(ch)
    if published is not None and abs(effective-published)>1.01:scale_diffs.append({'id':e['id'],'path':path,'level':lv,'channel':ch,'wiki':published,'effective_parameters':round(effective,4)})
warnings={}
for diff in attack_diffs+scale_diffs:
 warnings.setdefault(diff['id'],{}).setdefault(diff['path'],set()).add('base attack' if 'parameters' in diff else 'scaling coefficients')
character['source_disagreements']={id:{path:'Published references disagree on '+', '.join(sorted(kinds))+'. Base attack follows the individual wiki reinforcement rows; scaling follows the combat parameter table. This preview has not been verified against the game executable.' for path,kinds in paths.items()} for id,paths in warnings.items()}
for path in character['source_disagreements'].get('ruler-s-sword',{}):
 character['source_disagreements']['ruler-s-sword'][path]='The wiki scaling table includes the maximum souls-held modifier. Character Lab applies the combat parameter coefficient and your selected souls held separately.'
(R/'database/character.json').write_text(json.dumps(character,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report={'checked_rows':rows,'missing_paths':missing,'one_point_rounding_differences':rounded,'base_attack_disagreements':attack_diffs,'coefficient_disagreements':scale_diffs,'policy':'Individual wiki reinforcement rows remain canonical for base attack except the explicitly identified Majestic right-hand variant. Combat parameter coefficients include infusion affinity and keep their precision; source disagreements are reported in the affected previews. No local executable validation was performed.'}
(R/'audit/character-parameter-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'checked_rows':rows,'missing_paths':missing,'rounding_differences':rounded,'base_attack_disagreements':len(attack_diffs),'affected_weapons':sorted(set(x['id'] for x in attack_diffs)),'coefficient_disagreements':len(scale_diffs),'coefficient_weapons':sorted(set(x['id'] for x in scale_diffs))},indent=2))
