"""Read-only catalog, local-image and reference-coverage audit. Run from the project root."""
from pathlib import Path
from collections import Counter, defaultdict
import json,re,hashlib
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'database';AUDIT=ROOT/'audit'
DATA={p.stem:json.loads(p.read_text(encoding='utf-8-sig')) for p in DB.glob('*.json')}
def key(s):return re.sub('[^a-z0-9]+',' ',str(s).lower()).strip().removeprefix('the ')
def match(records,name):
 hits=[x for x in records if key(name) in {key(x.get('name','')),key(x.get('id','')),*[key(a) for a in x.get('aliases',[])]}]
 return hits[0] if len(hits)==1 else None
def content(name):return BeautifulSoup((AUDIT/f'{name}.html').read_bytes(),'html.parser').select_one('#page-content')
coverage={}
for name,catalog in [('weapons','weapons'),('shields','weapons'),('spell-tools','weapons')]:
 pairs={(a.get_text(' ',strip=True),a['href']) for a in content(name).select('table p a[href], table li a[href]') if a['href'].startswith('/') and a.get_text(' ',strip=True) != 'Boss Souls'}
 coverage[name]={'reference_count':len(pairs),'missing':[{'name':n,'url':'https://darksouls2.wikidot.com'+url} for n,url in sorted(pairs) if not match(DATA[catalog],n) and not (name == 'weapons' and match(DATA['items'],n))]}
# Restrict references to the three inventory headings, before area-by-area lists.
c=content('enemies')
pairs={(a.get_text(' ',strip=True),a['href']) for a in c.select('a[href]') if a['href'].startswith('/') and a.find_previous('h1') and a.find_previous('h1').get_text(' ',strip=True) in ['Enemies','Invaders','Roaming Souls']}
coverage['enemies']={'reference_count':len(pairs),'missing':[{'name':n,'url':'https://darksouls2.wikidot.com'+url} for n,url in sorted(pairs) if not match(DATA['enemies'],n) and not match(DATA['bosses'],n) and not any(b.get('source_url') == 'https://darksouls2.wikidot.com'+url for b in DATA['bosses'])]}
for name in ['consumables','rings','keys','ammo','bonfire-items','multiplayer-items']:
 pairs=set()
 for t in content(name).select('table'):
  rows=t.select('tr');headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['td','th'],recursive=False)]
  if 'Name' not in headers:continue
  i=headers.index('Name')
  for r in rows[1:]:
   cells=r.find_all(['td','th'],recursive=False)
   if len(cells)<=i:continue
   a=cells[i].select_one('a[href]')
   if a:pairs.add((a.get_text(' ',strip=True),a['href']))
 coverage[name]={'reference_count':len(pairs),'missing':[{'name':n,'url':'https://darksouls2.wikidot.com'+url} for n,url in sorted(pairs) if not match(DATA['items'],n)]}
images={};broken=[]
def walk(value,record,catalog):
 if isinstance(value,dict):
  for field,x in value.items():
   if field in ['image','icon'] and isinstance(x,str) and re.search(r'\.(png|jpg|jpeg|webp|svg)$',x,re.I) and not x.startswith(('http','data:')):
    path=ROOT/x
    if x not in images:
     try:
      if path.suffix=='.svg':
       import xml.etree.ElementTree as ET
       ET.parse(path)
      else:
       with Image.open(path) as im:im.verify()
      images[x]={'valid':True}
     except Exception as ex:images[x]={'valid':False,'problem':str(ex)}
    if not images[x]['valid']:broken.append({'catalog':catalog,'record':record,'path':x})
   else:walk(x,record,catalog)
 elif isinstance(value,list):
  for x in value:walk(x,record,catalog)
for catalog,records in DATA.items():
 if isinstance(records,list):
  for x in records:
   if isinstance(x,dict):walk(x,x.get('name',x.get('id','')),catalog)
# Check explicitly emitted UI/icon asset strings as well as catalog images.
for f in [ROOT/'index.html',ROOT/'js/app.js']:
 for path in set(re.findall(r'assets/[A-Za-z0-9_./-]+\.(?:webp|png|jpg|svg)',f.read_text(encoding='utf-8'))):
  if not(ROOT/path).is_file():broken.append({'catalog':'UI','record':f.name,'path':path})
unresolved=[]
for enemy in DATA['enemies']+DATA['bosses']:
 for drop in enemy.get('drops',[]):
  if not any(match(DATA[k],drop['name']) for k in ['items','magic','weapons','armor']):unresolved.append({'enemy':enemy['name'],'drop':drop['name']})
stats={k:{'entries':len(DATA[k])} for k in ['enemies','bosses','weapons','items','magic','armor','areas','npcs','quests','articles']}
stats['enemies'].update(empty_weaknesses=sum(not x.get('weaknesses') for x in DATA['enemies']),empty_drop_tables=sum(not x.get('drops') for x in DATA['enemies']))
stats['bosses'].update(combat_guides=sum(bool(x.get('combat')) for x in DATA['bosses']),physical_tables=sum(bool(x.get('combat',{}).get('physical')) for x in DATA['bosses']),empty_status_tables=sum(not x.get('status_effects') for x in DATA['bosses']))
stats['weapons'].update(missing_base_damage=sum(x.get('base_damage') in ['',None] for x in DATA['weapons']),empty_tactical_notes=sum(not x.get('notes') and not x.get('mechanics_notes') for x in DATA['weapons']))
stats['items'].update(empty_descriptions=sum(not x.get('description') for x in DATA['items']),empty_usage=sum(not x.get('usage') for x in DATA['items']),empty_obtaining=sum(not x.get('obtaining') for x in DATA['items']))
stats['armor'].update(empty_descriptions=sum(not x.get('description') for x in DATA['armor']))
unavailable=[x['name'] for x in DATA['items'] if x.get('image_verified') is False]
result={'checked_on':'2026-10-10','coverage':coverage,'stats':stats,'broken_local_assets':broken,'local_images_checked':len(images),'unavailable_exact_icons':unavailable,'unresolved_loot_references':unresolved,'scope':'Both original DSII and Scholar of the First Sin, including DLC; version differences retained where verified. Reference index coverage does not certify all variants, stats or image identity.'}
(AUDIT/'catalog-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Dark Souls II guide audit — 10 October 2026','', 'The navigation and boss-detail repairs are implemented. The guide is **not yet a complete, fully fact-checked encyclopedia**. This report distinguishes roster coverage from detailed-content and artwork verification.','', '## Implemented repairs','', '- Replaced fuzzy substring links with exact names and explicit aliases; unresolved references stay labelled text.', '- Preserved selected entries through search clearing, favorites, refresh and browser Back; added actual NPC detail destinations.', '- Fixed 322 weapon-detail crashes caused by a string being treated as an array.', '- Added the Drangleic Castle Dragonriders encounter: 41 boss fights, each with a sourced combat guide and elemental defenses; 32 also have physical effectiveness tables.', '- Added 71 base rings, 4 keys, 4 carvings and 9 distinct +2 boss-reward ring variants.', '- Fixed missing enemy artwork paths and quest portraits, merged six enemy-name aliases while preserving old IDs, and removed exact-ID boss duplicates from the enemy roster.', '- Corrected Sanctum Soldier loot (the gauntlet, rather than a nonexistent full soldier set) and repaired mismatched loot names/icons.', '- Reclassified binoculars and three keys as items, and removed a category heading that was masquerading as an item.','', '## Catalog and data quality','', '| Catalog | Entries | Outstanding detail gaps |','|---|---:|---|']
for name,s in stats.items():
 gaps=', '.join(f'{v} {k.replace("_"," ")}' for k,v in s.items() if k!='entries') or 'No detailed-field audit performed for this catalog'
 lines.append(f'| {name} | {s["entries"]} | {gaps} |')
details=json.loads((AUDIT/'detail-coverage.json').read_text(encoding='utf-8')) if (AUDIT/'detail-coverage.json').exists() else {}
lines+=['','## Area, item and equipment repairs (version 1.5.0)','',
 '- Removed ten lore-only lands from playable areas, merged the duplicate Lost Bastille and removed seven armor category/navigation records.',
 '- 49 playable areas now show inhabitants, bosses, connected areas, notable loot and 78 individually described resting/fast-travel bonfires. Primal bonfires are identified in overview notes rather than counted as resting/fast-travel bonfires.',
 '- Added two visually verified bonfire screenshots (The Far Fire and Cardinal Tower). The remaining 76 bonfire screenshots are still missing; video metadata is retained for provenance but no longer linked from the app.',
 '- Weapon cards and comparisons expose STR, DEX, INT and FTH requirements plus all six scaling channels. 314 weapons have explicit normal reinforcement rows. Shields include block reductions and stability where sourced.',
 '- The builder applies Magic/INT, Lightning/FTH, Fire/(INT+FTH)/2 and Dark/min(INT,FTH) bonus curves. 199 maximum reinforcement coefficient sets were cross-checked against weapon attack tables. Other levels/weapons are clearly labelled as partial subtotals; missing elemental coefficients are not fabricated.',
 '- All 320 items have descriptions and uses. 56 soul items have consumption values; 44 have structured trader/reward/cost records and links. Projectile damage is separated from poison buildup.',
 '- Armor has 432 baseline defense records and 425 maximum reinforcement records, equipment requirements, special effects and 106 set-to-piece groups. Self-referencing piece links were removed. Two alternate Prisoner designs still lack assigned full defenses; their common equipment properties and effects are shown.',
 '- 103 missing source-associated item/armor icons were downloaded and image-decoded. No active armor or item record now has an empty image path. Nineteen other exact variant icons remain unavailable and labelled generic.',
 '- Five unused or identity-unverified legacy armor records are excluded from the normal armor list and explicitly labelled on their direct pages.',
 '- Reduced oversized equipment images so purpose, use and stats are visible sooner; fixed mobile equipment headers.','']
lines+=['','## Local-only guide repairs (version 1.5.1)','', '- Added 185 bundled supplemental entries with factual reference content and internal navigation.', '- Bundled fonts and licenses; removed wiki image lookup and external reference/video navigation.', '- Source credits are collapsible plain text. A local-only content security policy prevents remote runtime dependencies.', '- The app runs from its local server and files without Internet access; source import tools are optional maintenance utilities.', '']
lines+=['','## Reference coverage','', 'Compared the local catalogs with Wikidot indexes. “Missing” means no exact name or explicit alias match; some enemy names may be alternative names rather than genuinely absent enemies.','', '| Reference index | Entries compared | Missing / unresolved names |','|---|---:|---:|']
for name,c in coverage.items():lines.append(f'| [{name}](https://darksouls2.wikidot.com/{name}) | {c["reference_count"]} | {len(c["missing"])} |')
lines+=['','### Enemy names requiring reconciliation','']
lines += [f'- [{x["name"]}]({x["url"]})' for x in coverage['enemies']['missing']]
lines+=['','## Images and icons','',f'- {len(images)} distinct local image/icon paths were checked for existence and image decoding.',f'- {len(broken)} broken local asset references remain.',f'- {len(unavailable)} newly added items use a labelled generic icon because the reference image host returned HTTP 429.', '- Artwork identity is verified only where a source provenance URL was recorded. Existing readable images were not all compared visually with game/reference imagery; readable files alone do not prove correct artwork.', '- Shared images across soul tiers can be legitimate. Existing suspicious shared stone artwork was switched to matching original local PNGs; its identity still needs review.','', 'Unavailable exact icons: '+', '.join(unavailable)+'.','', '## Remaining convenience / accuracy concerns','', '- Enemy variants, drop tables, NPC details and version-specific placement still require further factual reconciliation. Item and armor cards now contain mechanical facts; full certification of every variant remains outstanding.', '- Existing enemy drop percentages have not been verified. Newly imported boss rewards and corrected soldier drops avoid invented rates.', '- NG, NG+ and Scholar/original enemy placements and defenses need explicit per-version profiles. Boss notes identify known differences, but the app has no global version selector.', '- Supplemental local guide entries cover named area and acquisition references absent from the main catalogs. Broad loot descriptions remain plain text rather than guessing a target.', '- Full builder output is verified only for the marked maximum reinforcement coefficient sets. Infusion calculations, two handing, requirement penalties and conditional buffs remain outside the calculation.', '- Guide data, fonts and images are bundled locally. Runtime image lookup and external navigation fallbacks have been removed.', '- Spell inventory, armor variants, promotional weapon reskins and every individual image identity were not independently certified.','', '### References without a specific loot entry','']
lines += [f'- {x["enemy"]}: {x["drop"]}' for x in unresolved]
lines+=['','## Validation','', 'See `runtime-check.json` for the final whole-catalog browser-render check and `interaction-check.json` for click, reverse-link, Back, refresh, favorites and search checks. `detail-check.json` records 14 additional mechanics, soul trade, armor set, area and mobile checks. The earlier checks blocked external requests. The new `local-only-check.json` covers 1,730 detail pages and 5,429 internal links, with zero external requests observed without blocking external requests; asset requests during the catalog sweep are served from their actual local files to avoid overloading the development server.','', '## Sources','', '- [Boss roster and encounter rewards](https://darksouls2.wikidot.com/bosses)', '- [Elemental resistance tiers, environment and DLC differences](https://darksouls2.wikidot.com/resistance)', '- Source URLs are retained as plain text in collapsible credits; guide cards no longer link out to reference websites.', '- [Armor tables](https://darksouls2.wikidot.com/armor)', '- [Materials and infusions](https://darksouls2.wikidot.com/materials)', '- [Boss soul uses and trades](https://darksouls2.wikidot.com/boss-soul-items)', '- [Bonus scaling and coefficient reference](https://darksouls2.wikidot.com/scaling)', '- [Bonfire route videos](https://steamcommunity.com/sharedfiles/filedetails/?id=2108626487)', '']
lines+=['','## Full audit and filters (version 1.6.0)','', 'See FULL_AUDIT.md for the refreshed wiki roster comparison, source-table verification, completed catalog additions, filter validation and remaining certification gaps. The historical repair sections above describe their original version scope.','']
(AUDIT/'AUDIT.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'stats':stats,'broken_assets':len(broken),'unavailable_icons':len(unavailable),'coverage':{k:{'compared':v['reference_count'],'missing':len(v['missing'])} for k,v in coverage.items()},'unresolved_loot':unresolved},indent=2))
