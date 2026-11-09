# Dark Souls II reference review

Research collected 16 October 2026; validation date: November 09, 2026.

This review repairs source extraction and checks the catalog inventory. It is not a claim that every numerical value has been verified against game files or tested in-game. Missing facts were not replaced with guesses.

## Sources and method

The public Fextralife index contained 2,794 non-redirect article titles. 1,649 source pages were cached for matching and mechanical extraction; this count is not a count of manually verified articles.

[Fextralife DS2 wiki](https://darksouls2.wiki.fextralife.com/Dark_Souls_2_Wiki), [enemy name disambiguation](https://darksouls2.wiki.fextralife.com/Enemy_Names_Disambiguation), [Wikidot](https://darksouls2.wikidot.com/), and selected [wiki.gg](https://darksouls2.wiki.gg/) numerical tables support the changes. Each record keeps its source credits. Public indexed wiki.gg results were used where direct page access was unavailable. Raw research HTML is excluded from the application and deployment.

The importer reads Health/HP synonyms, icon headers, bonfire-intensity annotations, NG+ only records, attack properties, merchant stock, requirements, effects, acquisition references and related equipment. Curated corrections distinguish ghosts, crystallized enemies, NPC phantoms, player invasions, and regular boss reappearances.

Category roster links were checked across weapons, shields, armor, consumables, rings, all four spell schools, NPCs and bosses. Alternate spellings, category links and cut content were examined separately from obtainable equipment.

## Catalog inventory

| Catalog | Records |
| --- | ---: |
| Enemies | 188 |
| Bosses | 41 |
| Areas | 49 |
| Weapons | 325 |
| Items | 335 |
| Magic | 106 |
| Armor | 547 |
| Npcs | 95 |
| Covenants | 9 |
| Quests | 14 |
| Articles | 187 |

Armor includes sets, pieces, and a small number of clearly labeled unused/legacy records. Those legacy records are excluded from the wearable armor catalog. Weapons include bare fists. Boss and ordinary-enemy catalogs are separate.

## What changed

- Restored published HP and soul rows that the old parser skipped. Location, bonfire intensity and source are retained instead of combining unrelated encounters.
- Corrected “NG+7” being interpreted as 7 HP. Recovered NG+ only phantom values and per-member Congregation health.
- Consolidated duplicate enemy names with bookmark/favorite redirects. Archdrake Pilgrims in Amana remain distinct from the Archdrake-equipped Exiled Braves in Frigid Outskirts.
- Removed boss souls from regular reappearance drops and Bell Keeper armor from enemy loot. The Bell Keeper pyromancy is Fire Whip, not the DLC spell Fire Snake.
- Added attack/opening tables, numerical damage modifiers, effects, merchant inventory and local acquisition links. Ring +2 and merchant links now preserve the named destination even when source URLs are shared.
- Replaced empty or misleading NPC descriptions with services, locations and sourced lore summaries. Generic group placeholders and the DS3-only NPC category were removed.
- Expanded the quest tracker to 14 sourced guides, including Navlaan’s non-murder proof route, covenant trials, Loyce Soul rewards and crown blessings. Quest conditions and character portraits are now visible.
- Fixed mobile enemy/NPC detail headers that clipped their images and titles. Layout tests check element bounds as well as page scroll width.

## Measured enemy coverage

The inventory changed because duplicate cards were consolidated. Counts below describe empty fields, not incorrect values.

| Field | Before (219 cards) | After (188 encounters) |
| --- | ---: | ---: |
| hp | 84 | 7 |
| souls | 84 | 6 |
| can_parry | 211 | 137 |
| can_backstab | 214 | 149 |

The guide retains 1,278 enemy stat rows and 316 boss stat rows, with attack/opening lists on 131 enemy/boss records. All 41 boss cards have health and soul information, including group-health descriptions.

## Remaining limits

- Many source pages do not explicitly state parry or backstab susceptibility. No universal rule based on an enemy’s size or humanoid appearance was applied. An absent Boolean is not treated as immunity. Parrying an attack does not necessarily permit a riposte.
- Player invaders have build-dependent stats. Regular Castle Ruin Sentinels use the published Castle encounter row (3,260 HP / 2,500 souls), separate from the Lost Bastille boss trio. Twin Dragonriders use their own Castle article, not the Heide encounter.
- Some wiki pages are unfinished templates. The Hollow Priest page describes a different enemy and remains an unresolved roster title; it was not imported as a new factual encounter.
- Some source summaries differ because of location, edition, variant, or unresolved source disagreement. Their rows remain separate. For example, Faraam phantom Ascetic behavior is described differently by Wikidot and wiki.gg.
- Prisoner head/chest armor has two appearance variants. Their base values are listed separately; the aggregate maximum-defense source does not identify the appearance variant.
- There are 78 stored bonfire locations, but only 2 bonfires have a sourced photograph. Missing bonfire photographs were not replaced with invented screenshots.
- The blacksmith and character calculation datasets were not re-derived from game parameters in this review. Reference additions do not establish that every conditional combat effect is simulated.

### Encounters without a single published fixed HP/soul pair

| Encounter | Context |
| --- | --- |
| Dark Spirit | Player-controlled encounter: health, defenses, equipment and attack options depend on the summoned or invading character. |
| Bell Keeper (Dark Spirit) | Player-controlled encounter: health, defenses, equipment and attack options depend on the summoned or invading character. |
| Arbiter Spirit | Player-controlled encounter: health, defenses, equipment and attack options depend on the summoned or invading character. |
| Frost Hound | Frozen Eleum Loyce variant of the Stray Dog, also called Rampart Stray Dog or Frozen Hound. Its dedicated Fextralife page does not publish HP or souls. |
| Curse Jar | Environmental curse hazard. Break the jar or use curse immunity; a combat HP/soul template is not applicable. |
| Invisible Hollow | Non-attacking hidden Hollow. Any damaging hit reveals and kills it; carry a light to see its shadow. |
| Pagan Tree | Non-hostile repair tree. Strike it with a whip to release equipment-repairing mist; killing it removes that service until it respawns. |

### Source comparisons

These are differences between the earliest published source summaries; they are not automatically contradictions, since a source can cover different locations or variants.

| Encounter | Field | Fextralife | Wikidot |
| --- | --- | --- | --- |
| Hollow Infantry | hp | 270 | ~210–310 |
| Hollow Infantry | souls | 50 | 50–70 |
| Hollow Soldier | hp | 290 | ~250–330 |
| Old Ironclad Soldier | hp | 525–900 | 540–2,000 |
| Old Ironclad Soldier | souls | 250 | 250–937 |
| Old Knight | hp | 520–850 | ~520–1,600 |
| Old Knight | souls | 400 | 400–700 |
| Heide Knight | hp | ~1,250 | ~1,100–1,300 |
| Heide Knight | souls | 3,000 | 600–5,500 |
| Bell Keeper | hp | 2,100 | 800–2,800 |
| Bell Keeper | souls | 350 | 350–701 |
| Manikin | hp | ~290–825 | ~500 |
| Manikin | souls | 160–170 | 160 |
| Alonne Knight | hp | 590–1,350 | 590 |
| Alonne Knight | souls | 450–800 | 700 |
| Falconer | hp | 588 | 420–460 |
| Falconer | souls | 700 | 260 |
| Syan Knight | hp | 960 | 960–1,018 |
| Syan Knight | souls | 900 | 900–1,300 |
| Drakekeeper | hp | 1,061–1,380 | 1,050–1,300 |
| Ogre | hp | 1,300 | 1,300–2,750 |
| Ogre | souls | 1,000 | 1,000–2,200 |
| Basilisk | hp | 270–360 | 260–360 |
| Mimic | hp | 720 | ~720–1,150 |
| Mimic | souls | 1,500 | 1,500–2,500 |
| Sanctum Soldier | hp | 850 | 860 |
| Possessed Armor | hp | 1,300 | 1,200 |
| Kobold | souls | 30 | 30–180 |
| Leydia Pyromancer | hp | 360 | ~360 |
| Leydia Pyromancer | souls | 380 | 750 |
| Skeleton | hp | 290–600 | ~240–600 |
| Skeleton | souls | 110 | 0–700 |
| The Imperfect | hp | ~4,500 | 2,530 |
| Undead Laborer | hp | 180–240 | 180–330 |
| Undead Laborer | souls | 40 | 40–150 |
| Grave Warden | souls | 380 | 380–1,000 |
| Bonewheel Skeleton | souls | 380 | 0 |
| Dark Stalker | hp | 620 | ~620–1,050 |
| Alonne Knight Captain | hp | 840–1,075 | 840–1,280 |
| Alonne Knight Captain | souls | 1,500 | 1,500–1,600 |
| Aslatiel of Mirrah | hp | 2,300 | 2,250 |
| Cask Runner | hp | 590 | 550 |
| Bowman Guthry | souls | 450 | 1,052 |
| Flame Salamander | hp | 3,325 | 1,400–3,325 |
| Enslaved Pig | souls | 20 | 0–20 |
| Goblin | hp | 160 | ~340–440 |
| Goblin | souls | 30–40 | 90 |
| Enhanced Undead | souls | 1,600 | 1,600–2,200 |
| Giant Acid Horn Beetle | souls | 1,200 | 1,200–3,400 |
| Elite Giant | souls | 4,000 | 2,200–4,000 |
| Hollow Mage | hp | 430 | ~430 |
| Giant Undead Boar | hp | 2,000 | 950 |
| Giant Undead Boar | souls | 1,700 | 800 |
| Forest Spirit | souls | 380 | 600–1,500 |
| Ironclad Soldier | hp | 525–900 | 780 |
| Ironclad Soldier | souls | 250 | 850 |
| Mad Warrior | hp | 1,870 | ~1,980 |
| Lindelt Cleric | souls | 450 | 550 |
| Lion Clan Warrior | hp | 160–665 | ~665–850 |
| Lion Clan Warrior | souls | 40–400 | 400 |
| Necromancer | hp | 600 | 320–500 |
| Leydia Witch | hp | 900 | ~900 |
| Hunting Dog | hp | 1,100 | ~1,100–1,550 |
| Hunting Dog | souls | 660 | 660–720 |
| Undead Jailer | hp | 290 | 780 |
| Undead Jailer | souls | 1,100 | 540 |
| Undead Citizen | hp | 80 | 80–130 |
| Undead Citizen | souls | 260–340 | 260–350 |
| Suspicious Shadow | hp | 330 | 330–700 |
| Rhoy the Explorer | hp | 2,700 | 1,420 |
| Rhoy the Explorer | souls | 5,200 | 2,600 |
| Undead Boar | hp | 330 | 640 |
| Undead Boar | souls | 20 | 350 |
| Vorgel the Sinner | souls | 20 | 1,150 |
| Undead Traveler | hp | 160 | 160–180 |
| Executioner Phantom | hp | 3,050 | ~3,050 |
| Greatbow Phantom | hp | 3,600 | ~3,600 |
| The Last Giant | souls | 0–10 | 10,000 |
| Belfry Gargoyles | hp | 1,400 | ~3,000–7,000 |
| Scorpioness Najka | hp | 5,911 | 5,741 |
| Mytha, the Baneful Queen | hp | 3,570 | 3,650 |
| Guardian Dragon | hp | 2,249 | ~1,653–5,300 |
| Throne Watcher and Defender | hp | 2,760–3,910 | 6,670 |
| Ancient Dragon | souls | 0–120 | 120,000 |
| Velstadt, the Royal Aegis | hp | 6,290 | 2,600–6,290 |

## Reproduce

From the project directory, with Python and Beautiful Soup installed:

```sh
python tools/research_ds2_wiki.py --cache <research-cache>
python tools/enrich_ds2_wiki.py --cache <research-cache> --apply
python tools/curate_ds2_references.py --cache <research-cache>
python tools/verify_ds2_research.py
python tools/write_ds2_research_audit.py --cache <research-cache>
```

Review source and variant differences before accepting regenerated data. Run the browser checks described in `tools/README.md` with the local server running. No research tools are runtime dependencies.
