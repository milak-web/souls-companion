"""Copy generated assets into the offline project and mark their provenance."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'audit/generated-lore-manifest.json').read_text(encoding='utf-8'))
records=json.loads((R/'database/npcs.json').read_text(encoding='utf-8'));report=[]
for entry in manifest:
 r=next(x for x in records if x['id']==entry['id']);source=Path(entry['source']);dest=R/'assets/npcs'/('illustration-'+r['id']+'.png')
 if not source.is_file():raise FileNotFoundError(source)
 shutil.copyfile(source,dest)
 r.update(image=dest.relative_to(R).as_posix(),image_kind='generated',image_verified=False,image_generator='imagegen',image_generated_on='2026-10-11',image_note='Interpretive artwork based on the figure’s name and associated lore. Appearance is not canonical; this is not an in-game screenshot.')
 r.pop('image_source',None);report.append({'id':r['id'],'name':r['name'],'image':r['image'],'kind':'generated','canonical':False})
(R/'database/npcs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(R/'audit/generated-lore-images.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'copied':len(report),'generator':'imagegen'},indent=2))
