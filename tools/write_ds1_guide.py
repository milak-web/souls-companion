"""Authored DS1 guidance plus factual bonfire and progression records."""
from import_ds1 import *
def section(title,text,ids=[]):return {'title':title,'paragraphs':[text],'ids':ids}
guide={'entries':{},'areas':{},'quests':{}}
guide['progression']=[
 {'text':'Escape the Undead Asylum, rest at Firelink Shrine, and explore the Burg and Parish. Ring the upper Bell of Awakening.','ids':['undead-asylum','firelink-shrine','undead-burg','undead-parish','bell-gargoyles']},
 {'text':'Reach Blighttown through the Depths or the Valley shortcut. Defeat Quelaag and ring the lower bell to open Sen’s Fortress.','ids':['depths','blighttown','chaos-witch-quelaag','sen-s-fortress']},
 {'text':'Cross Sen’s Fortress and reach Anor Londo. Defeat Ornstein and Smough, then obtain the Lordvessel from Gwynevere.','ids':['iron-golem','anor-londo','dragon-slayer-ornstein-executioner-smough','lordvessel']},
 {'text':'After placing the Lordvessel, obtain the four Lord Souls from Seath, Nito, the Four Kings, and the Bed of Chaos.','ids':['seath-the-scaleless','gravelord-nito','the-four-kings','the-bed-of-chaos']},
 {'text':'Optional: rescue Dusk from the golden golem in Darkroot Basin, collect the Broken Pendant in the Archives, then return to the basin portal to enter the DLC.','ids':['dusk-of-oolacile','broken-pendant','sanctuary-garden','knight-artorias','manus-father-of-the-abyss']},
 {'text':'Offer the Lord Souls at the Firelink Altar, enter the Kiln, and confront Gwyn. Finishing the ending starts the next playthrough, so finish optional content first.','ids':['firelink-altar','kiln-of-the-first-flame','gwyn-lord-of-cinder','new-game-plus']}]
guide['paths']=[
 {'name':'Normal +15','text':'Any smith can reinforce to +5. Give Andre the Large Ember from the Depths for +6–10 and the Very Large Ember from drained New Londo for +11–15. Standard progression uses 9 Titanite Shards, 9 Large Shards, 7 Chunks and 1 Slab.','ids':['andre-of-astora','large-ember','very-large-ember','titanite-shard','large-titanite-shard','titanite-chunk','titanite-slab']},
 {'name':'Raw +5','text':'Andre ascends a Normal +5 weapon with the Large Ember. Raw increases base physical attack while reducing scaling. Uses Large Titanite Shards.','ids':['andre-of-astora','raw','large-ember']},
 {'name':'Crystal +5','text':'The Giant Blacksmith ascends Normal +10 with the Crystal Ember from the Duke’s Archives. Crystal increases physical attack but cannot be repaired normally; reinforcement restores durability while upgrade levels remain.','ids':['giant-blacksmith','crystal-ember','crystal']},
 {'name':'Lightning +5','text':'The Giant Blacksmith ascends Normal +10 without an ember. Adds lightning attack and removes attribute scaling. Uses Titanite Chunks and a Slab.','ids':['giant-blacksmith','lightning']},
 {'name':'Magic +10 / Enchanted +5','text':'Rickert makes Magic from Normal +5. The Large Magic Ember unlocks Magic +6–10; the Enchanted Ember permits Enchanted ascension from Magic +5. These paths use green shards, then blue chunks and a blue slab, and favor Intelligence.','ids':['rickert-of-vinheim','large-magic-ember','enchanted-ember','magic','enchanted']},
 {'name':'Divine +10 / Occult +5','text':'Andre uses the Divine Ember to ascend Normal +5. The Large Divine Ember unlocks Divine +6–10; the Dark Ember unlocks Occult from Divine +5. Divine defeats skeleton revival while a necromancer survives. These paths favor Faith.','ids':['andre-of-astora','divine-ember','large-divine-ember','dark-ember','divine','occult']},
 {'name':'Fire +10 / Chaos +5','text':'Vamos ascends Normal +5 to Fire. The Large Flame Ember unlocks Fire +6–10; the Chaos Flame Ember permits Chaos from Fire +5. Fire removes attribute scaling. Chaos also scales with carried humanity, capped at 10.','ids':['vamos','large-flame-ember','chaos-flame-ember','fire','chaos']},
 {'name':'Unique, boss, dragon and spell tools','text':'Special weapons generally use a fixed +5 path with Twinkling Titanite, Demon Titanite, or Dragon Scales and cannot take ordinary elemental ascensions. Catalysts and talismans generally cannot be reinforced. Pyromancy Flame reaches +15 before Quelana ascends it to a separate +0–5 flame. Check the selected weapon’s material table.','ids':['twinkling-titanite','demon-titanite','dragon-scale','pyromancy-flame','pyromancy-flame-ascended','quelaana-of-izalith']}]
area_notes={
 'undead-asylum':'Your starting prison. Escape the first demon encounter through the left-hand doorway, collect equipment, and return through the upper fog. A later return reveals the Stray Demon, Rusted Iron Ring and Peculiar Doll.',
 'firelink-shrine':'The early game hub connects the Burg, Catacombs and New Londo. Rescued merchants gather here. Anastacia reinforces Estus; Lautrec’s quest can temporarily extinguish the bonfire.',
 'undead-burg':'The upper route leads to Taurus Demon and the Hellkite bridge. The lower route requires the Basement Key and leads to Capra Demon and the Depths. Unlock the ladder back to the main bonfire.',
 'undead-parish':'Defeat the church Channeler, open the Firelink elevator, and find Andre below the church. The Bell Gargoyles guard the upper Bell of Awakening. Lautrec can be freed from his cell.',
 'darkroot-garden':'An optional forest with the Moonlight Butterfly, Divine Ember and the path to Sif. The Crest of Artorias opens the forest gate; the basin ladder provides an alternate entrance.',
 'darkroot-basin':'The lower forest connects to the Valley of Drakes. The Hydra and a golden crystal golem are tied to Dusk’s rescue and the DLC entrance. Avoid the deep water edge.',
 'depths':'The Key to the Depths opens this sewer area. Find the Large Ember beside the first butcher, rescue Laurentius, and avoid basilisk curse clouds. The Gaping Dragon gives the Blighttown Key.',
 'blighttown':'The upper platforms connect from the Depths; the waterwheel connects to the Valley of Drakes. Bring poison and toxic cures. The lower swamp leads to Quelaag and the Great Hollow.',
 'quelaag-s-domain':'Quelaag guards the lower Bell of Awakening. Past the bell, an illusory wall conceals the Fair Lady’s bonfire and the Chaos Servant covenant.',
 'sen-s-fortress':'The gate opens after both bells are rung. Pendulums, pressure plates and rolling boulders dominate the route. The rooftop bonfire is reached by dropping over a broken wall. Iron Golem opens the way to Anor Londo.',
 'anor-londo':'Cross the rafters and archer ledge to the cathedral. The residence bonfire anchors the boss approach; open the interior shortcut. Ornstein and Smough guard Gwynevere and the Lordvessel. Gwyndolin is optional.',
 'painted-world-of-ariamis':'Carry the Peculiar Doll from the revisited Asylum and touch the large painting in Anor Londo. Open the central courtyard shortcut. Priscilla is optional; the exit is beyond her arena.',
 'new-londo-ruins':'There is no local bonfire. Transient Curse, being cursed, or a cursed weapon lets you attack ghosts. Ingward holds the seal key. Drain the water, collect the Very Large Ember, and wear the Covenant of Artorias for the Four Kings.',
 'valley-of-drakes':'A connecting zone between New Londo, Blighttown and Darkroot Basin. Its drakes and undead dragon are optional. It has no bonfire; use the basin cave or Firelink approach.',
 'the-catacombs':'Necromancers revive local skeletons until killed; Divine weapons can prevent individual revivals. Turn the bridges, find Vamos, and defeat Pinwheel for the Rite of Kindling. The Vamos bonfire is a Remastered addition.',
 'tomb-of-the-giants':'A dark descent beyond Pinwheel. A Skull Lantern, Cast Light, or Sunlight Maggot helps navigation. Rescue Rhea and approach Nito only after the Lordvessel removes the golden barrier.',
 'the-duke-s-archives':'The Lordvessel opens the Archives approach from Anor Londo. The initial Seath encounter leads to prison. Escape, unlock the revolving stairs, rescue Logan and locate the path to Crystal Cave.',
 'crystal-cave':'Watch falling crystal flakes to reveal the invisible bridges. Break Seath’s crystal before attacking him in the final arena. His tail cut yields the Moonlight Greatsword.',
 'demon-ruins':'Defeating Ceaseless Discharge drains the lava. The regular route then passes Demon Firesage and Centipede Demon; the Chaos Servant shortcut can bypass them. The Lordvessel opens the golden barrier.',
 'lost-izalith':'Use the Orange Charred Ring to cross lava. The ruins lead to the Bed of Chaos. The shortcut route matters for Solaire’s survival; Siegmeyer’s encounter takes place above the Chaos Eater pit.',
 'the-great-hollow':'Two illusory walls in the large Blighttown tree reveal this descent. Falling is the main hazard. Crystal lizards carry upgrade materials, and the bottom leads to Ash Lake.',
 'ash-lake':'An optional shore reached through the Great Hollow. A second Hydra inhabits the lake, and the Stone Dragon grants access to the Path of the Dragon covenant. Cut its tail for the Dragon Greatsword without making it hostile.',
 'firelink-altar':'Place the Lordvessel here to open the golden barriers. Offering the four Lord Souls unlocks the Kiln. Choosing Frampt or Kaathe affects their availability and covenant access.',
 'kiln-of-the-first-flame':'The final area contains five Black Knights and Gwyn. Finish optional bosses and DLC before choosing an ending, because the original game and Remastered immediately enter NG+ afterward.',
 'the-abyss':'The Four Kings arena requires the Covenant of Artorias ring before victory. The bonfire appears after the fight. Kaathe appears here when his quest conditions have been preserved.',
 'sanctuary-garden':'The entrance to Artorias of the Abyss. Sanctuary Guardian guards the route to Oolacile Sanctuary. Later returns can reveal two lesser guardians.',
 'oolacile-sanctuary':'A safe DLC hub with Elizabeth. The route onward leads into the Royal Wood, with a later shortcut back from the Township.',
 'royal-wood':'Explore the woodland and ruins toward Artorias’s colosseum. Kalameet occupies the ravine; Hawkeye Gough must shoot him down for the normal ground fight. Chester trades near the boss approach.',
 'oolacile-township':'The area beyond Artorias leads through corrupted inhabitants and dark sorcerers toward the dungeon. Find the Crest Key and unlock Gough’s tower; the arena at the start also connects to PvP.',
 'chasm-of-the-abyss':'Follow the dungeon into the humanity-filled chasm. Rescue the young Sif behind an illusory wall for a summon option, then face Manus. The Silver Pendant can deflect his dark magic.',
 'battle-of-stoicism-gazebo':'The DLC PvP arena entrance beside Artorias’s arena. Match modes are accessed here rather than through a normal exploration route.',
 'battle-of-stoicism':'The DLC arena provides competitive duels and team modes. Matchmaking availability differs by edition and online population.'}
records=json.loads((OUT/'catalog.json').read_text());byid={r['id']:r for r in records}
c=BeautifulSoup(fetch('bonfires'),'html.parser').select_one('#page-content');bonfires={};current=''
for tr in c.select('table tr'):
 cells=tr.find_all(['td','th'],recursive=False)
 if len(cells)<3 or 'Area Name' in txt(cells[0]):continue
 if txt(cells[0]):current=txt(cells[0])
 name=txt(cells[1]);location=txt(cells[2]);
 bonfires.setdefault(current,[]).append({'name':name,'location':location or ('Appears after defeating the area boss.' if name in ['Crystal Cave','Altar of the Gravelord','The Abyss','Chasm of the Abyss'] else 'Along the main approach through the area.')})
aliases={'The Catacombs':'Catacombs'}
for r in records:
 if r['category']!='areas':continue
 bosses=[]
 for t in r['tables']:
  if t['heading'].lower()=='quick reference':
   for row in t['rows'][1:]:
    for boss in records:
     if boss['category']=='bosses'and boss['name']in row[0]:bosses.append(boss['id'])
 bosses+= [b['id']for b in records if b['category']=='bosses'and any(x['id']==r['id']for h,refs in b['relations'].items()if h=='Location'for x in refs)]
 guide['areas'][r['id']]={'description':area_notes.get(r['id'],''),'bonfires':bonfires.get(aliases.get(r['name'],r['name']),[]),'bosses':sorted(set(bosses))}
 # Bonfire-to-area facts are exposed even where the original area page has no bonfire table.
 guide['entries'][r['id']]={'summary':area_notes.get(r['id'],'')}
boss_tactics={
 'asylum-demon':('Escape the first encounter unless pursuing the special hammer drop. Return with your equipment and use the balcony plunging attack.','Stay behind him, attack after his hammer swings, and step away from the butt slam. Killing him on the first meeting gives the Demon’s Great Hammer; the normal encounter gives the key.'),
 'taurus-demon':('Clear the tower archers before entering the bridge fight. Climb the ladder for a plunging attack.','Bait his overhead attack and move past his legs. Avoid being trapped at the bridge edge; repeated tower plunges are possible if you create enough distance.'),
 'bell-gargoyles':('The second gargoyle joins while the first is still alive. Keep enough damage pressure to limit the time fighting both.','Cut the first gargoyle’s tail for the Gargoyle Tail Axe. Move away from fire breath and strike its side; Solaire and Lautrec can help if their conditions are met.'),
 'capra-demon':('The two dogs and cramped entrance are the immediate threat. Kill the dogs and use the stairs to create space.','Block or evade the opening rush, climb to the upper ledge and attack after Capra finishes a combo. The Key to the Depths is the progression reward.'),
 'gaping-dragon':('Kill the Channeler above the arena before entering so it cannot buff the boss.','Bait the head slam, wait for the charge to end, then attack from the side. Avoid standing directly behind the tail sweep. A tail cut awards the Dragon King Greataxe.'),
 'chaos-witch-quelaag':('Her lava pools can cut off retreat paths. Avoid relying on fire damage.','Attack the spider’s side and retreat when Quelaag folds forward for the large explosion. Maneater Mildred’s summon becomes available after defeating her invasion.'),
 'moonlight-butterfly':('The boss spends much of the fight airborne; ranged attacks or Witch Beatrice’s summon help.','Evade the magic volleys, then punish when it lands to feed on the bridge. The corpse beyond the arena holds the Divine Ember and Watchtower Basement Key.'),
 'sif-the-great-grey-wolf':('Sif guards the ring needed to survive the Four Kings arena.','Move under or close to Sif’s body to evade broad sword sweeps. Watch the double spin and backward leap. Sif slows and limps at low health.'),
 'iron-golem':('Kill the bomb-throwing giant above the arena before the fight. The narrow platform makes positioning essential.','Attack the legs repeatedly to stagger and topple the golem. Avoid grabs and the arena edge. Black Iron Tarkus can be summoned from the nearby side tower.'),
 'dragon-slayer-ornstein-executioner-smough':('You fight both first, then an empowered survivor. The second boss killed determines the boss soul, purchasable armor and Leo Ring opportunity.','Use pillars to separate them. Kill Smough first for empowered Ornstein and the Leo Ring; kill Ornstein first for empowered Smough. Retreat from the lightning butt slam in phase two.'),
 'dark-sun-gwyndolin':('The Darkmoon Seance Ring opens access to his tomb; attacking Gwynevere also exposes the route but has additional consequences.','Hide behind pillars for small magic volleys, then dodge the large projectile that passes through them. Close distance between casts and strike before he teleports.'),
 'crossbreed-priscilla':('This Painted World boss is optional: walk past her to leave peacefully.','If attacked, she turns invisible. Track her footprints in the snow and stagger her to reveal her. Cutting her small tail gives Priscilla’s Dagger.'),
 'stray-demon':('On returning to the Asylum, the main floor collapses into this optional encounter. Heal after the fall.','Stay behind him and leave the explosion radius after his magic attacks. Avoid locking on if it makes retreat awkward. His reward includes a Titanite Slab.'),
 'pinwheel':('Pinwheel unlocks the Rite of Kindling, allowing bonfires to supply up to 20 Estus.','Close distance and attack quickly before clones accumulate. Paladin Leeroy’s summon lies on the approach. Pinwheel drops one of the three masks.'),
 'gravelord-nito':('Prepare for the entry fall and the delayed ground sword attack. Divine weapons help control the small skeletons.','Stay in the near part of the arena to avoid waking the giant skeletons. Evade or block the explosion and let it scatter his escorts, then punish Nito’s recovery.'),
 'seath-the-scaleless':('The first Archives encounter is unwinnable through normal attacks. The final cave fight requires destroying the regenerating crystal.','Protect against curse buildup and move away from crystal breath. To obtain Moonlight Greatsword, cut the tip of the large rear tail rather than the small side tails.'),
 'the-four-kings':('Wear the Covenant of Artorias ring before dropping into the Abyss. New kings appear over time, making sustained damage essential.','Fight close to reduce the danger of sword strikes, heal through safe openings, and evade the grab and explosion. Removing the ring before victory is fatal.'),
 'ceaseless-discharge':('Picking up the Gold-Hemmed Black Set provokes the boss. The lava below drains after his defeat.','You can fight by baiting the arm slam and attacking recovery. The entrance ledge strategy requires first triggering his arm-release animation near the altar before retreating to the fog.'),
 'demon-firesage':('This demon resembles the Stray Demon and uses large magical explosions despite its fiery appearance.','Stay near its rear, attack after swings, and withdraw from area explosions. The tree roots can obstruct movement; keep a clear retreat lane.'),
 'centipede-demon':('The initial safe platform is small; look for the larger solid area along the right-hand side of the arena.','Avoid prolonged lava exposure. Cutting an appendage can obtain the Orange Charred Ring during the fight; equipping it allows safer movement through lava.'),
 'the-bed-of-chaos':('Destroy the two side cores, then reach the central insect. Core destruction persists across deaths.','Watch collapsing floor sections and sweeping arms. After both side cores are gone, drop onto the central root, enter the tunnel and destroy the insect; ordinary boss HP damage is not the objective.'),
 'gwyn-lord-of-cinder':('Gwyn is the final boss. Finish DLC and other optional objectives before triggering an ending.','Gwyn can be parried. Without parries, use pillars to gain healing windows and punish finished combos. His fire damage makes suitable defensive equipment useful.'),
 'sanctuary-guardian':('The DLC guardian combines aerial attacks, lightning projectiles and a poisonous tail.','Dodge the wind blast and punish its recovery. Stay ready for follow-up swipes. A tail cut gives Guardian Tail; later two-guardian encounters are separate from the main boss.'),
 'knight-artorias':('Artorias can stack his damage buff if his charging animation completes.','Interrupt a charge with sufficient stagger damage. Dodge the leaping slams and wait for the full combo to end before committing to a short punish. Long recovery weapons need careful openings.'),
 'manus-father-of-the-abyss':('Manus combines long melee chains with dark magic. The Silver Pendant can repel dark projectiles when timed correctly.','Keep enough distance to read the frenzy combo, then punish the extended arm slam. Learn the different magic patterns rather than spending every opening attacking. Young Sif can be summoned inside the arena after rescue.'),
 'black-dragon-kalameet':('Speak to Hawkeye Gough after encountering Kalameet in the ravine so Gough can ground him.','Avoid breath sweeps and the calamity grab, which amplifies incoming damage. Bait the tail slam and cut the tail for the Obsidian Greatsword. Healing requires a clear opening, not merely distance.')}
for id,(summary,tactics)in boss_tactics.items():guide['entries'][id]={'summary':summary,'sections':[section('Fight strategy',tactics)]}
quests={
 'solaire-of-astora':('Solaire of Astora','The Lost Izalith outcome depends on stopping the red-eyed Chaos Bug before Solaire reaches it.',[
 'Speak to Solaire beyond the Taurus Demon and accept his offer to receive the White Sign Soapstone.',
 'Meet him at the Anor Londo residence bonfire and continue his dialogue.',
 'Follow his journey through the Sunlight Altar and Demon Ruins.',
 'Before his final Lost Izalith encounter, kill the red-eyed Chaos Bug in the shortcut corridor. Chaos Servant rank +2 opens the door from the Demon Ruins side; other routes exist.',
 'If saved, speak to the despairing Solaire in the corridor. His summon sign can then appear for Gwyn. If infected, he becomes hostile.']),
 'siegmeyer-of-catarina':('Siegmeyer of Catarina','In Lost Izalith, his remaining HP after the fight determines whether the quest continues.',[
 'Meet Siegmeyer outside or inside Sen’s Fortress and resolve the rolling boulder obstruction.',
 'In Anor Londo, defeat the Silver Knights in the room beside him and speak again for the Tiny Being’s Ring.',
 'At Firelink, answer that you opened the gate to receive Emit Force.',
 'In Blighttown, give him three Purple Moss Clumps.',
 'At Lost Izalith, weaken the Chaos Eaters before speaking to him, then help him fight. He must survive with more than half his HP for the continuing outcome.',
 'Complete Sieglinde’s encounters, then meet the family at Ash Lake for the final reward.']),
 'sieglinde-of-catarina':('Sieglinde of Catarina','Her progress is tied to Siegmeyer’s quest.',[
 'Free Sieglinde from the golden crystal golem in the Duke’s Archives garden.',
 'Speak to her at Firelink and confirm that you have seen her father.',
 'Continue her Firelink dialogue as Siegmeyer’s journey advances.',
 'If the successful Lost Izalith outcome was preserved, meet her at Ash Lake for a Titanite Slab.']),
 'knight-lautrec-of-carim':('Knight Lautrec of Carim','His scripted actions can extinguish Firelink’s bonfire until Anastacia is restored.',[
 'Free Lautrec from the Undead Parish cell, or allow his later automatic escape.',
 'Meet him at Firelink for the rescue reward.',
 'After Anastacia’s death, collect the Black Eye Orb and her clothing from the cell.',
 'Use the vibrating Black Eye Orb in Anor Londo’s cathedral to invade Lautrec and defeat his party.',
 'Bring Anastacia’s particular Fire Keeper Soul back to her cell to revive her. Do not consume or spend that soul on Estus.',
 'Collect Lautrec’s armor in the upper boss chamber after resolving the invasion.']),
 'anastacia-of-astora':('Anastacia of Astora','Her recovered soul is needed for revival; a different Fire Keeper Soul cannot substitute.',[
 'Find Anastacia beneath the Firelink bonfire. Give ordinary Fire Keeper Souls to reinforce Estus.',
 'If Lautrec kills her, recover the Black Eye Orb from the cell.',
 'Defeat Lautrec’s Anor Londo invasion and return her unique soul to the cell.',
 'Speak after revival; later Lordvessel progress restores her speech.']),
 'big-hat-logan':('Big Hat Logan','Buy his available sorceries and exhaust dialogue to advance later stages.',[
 'Rescue Logan from the cage in Sen’s Fortress using the Cage Key or Master Key.',
 'Meet him at Firelink; the early shop has an Intelligence requirement.',
 'Find him imprisoned in the Duke’s Archives and free him using the Archive Tower Giant Cell Key.',
 'Buy his Archives sorceries and continue speaking after defeating Seath.',
 'Find the hollowed Logan in Seath’s first arena. His final drops and the chest in his former study complete the rewards.']),
 'griggs-of-vinheim':('Griggs of Vinheim','The lower Burg room is opened with the Residence Key.',[
 'Rescue Griggs from the locked room in the lower Undead Burg.',
 'Visit his Firelink sorcery shop and buy the spells and rings you want.',
 'After his shop and Logan-related conditions are exhausted, his later hollow encounter can appear in Sen’s Fortress.']),
 'laurentius':('Laurentius of the Great Swamp','Telling him where you found advanced pyromancy can lead to his hollowing in Blighttown.',[
 'Free Laurentius from a barrel in the Depths; roll into the barrel to avoid striking him.',
 'Meet him at Firelink and use his pyromancy shop and flame reinforcement service.',
 'If asked about advanced Chaos pyromancy, decline to reveal the location to preserve his Firelink availability.',
 'If he leaves, his hostile form can be found in the Blighttown swamp.']),
 'quelaana-of-izalith':('Quelana of Izalith','Meet her before defeating the Bed of Chaos; her appearance and rewards can be missed.',[
 'Obtain a Pyromancy Flame +10 and look for Quelana beside a stone pillar in Blighttown’s swamp.',
 'Buy her pyromancies and ascend a +15 Pyromancy Flame.',
 'Accept her request concerning the Bed of Chaos and defeat that boss.',
 'Return to receive Fire Tempest while she remains available.']),
 'rhea-of-thorolund':('Rhea of Thorolund','After her rescue, buy the desired miracles promptly; Petrus can kill her if left alive.',[
 'Meet Rhea and her companions at Firelink, then follow their departure into the Catacombs.',
 'In Tomb of the Giants, defeat her hollowed bodyguards and speak to Rhea to receive Replenishment.',
 'Find her at the Undead Parish church and purchase her miracles.',
 'Her later fate depends on Petrus and shop progress; exhausting her shop can lead to a hollow encounter in the Archives.']),
 'patches':('Patches','Answering that you are a cleric affects his hostility.',[
 'Patches can be encountered in the Catacombs if his earlier encounter is still available.',
 'In Tomb of the Giants, investigate his suggested treasure to trigger the pit event.',
 'Escape, confront him, and spare him if you want his later merchant service.',
 'After Nito, find his shop at Firelink.']),
 'dusk-of-oolacile':('Dusk of Oolacile','DLC entry requires Dusk’s rescue and the Broken Pendant.',[
 'Defeat the Hydra in Darkroot Basin. Reload the area and find the golden crystal golem at the rear of the lake.',
 'Kill the golem and agree to help Dusk. Her summon sign appears near the lake.',
 'Obtain the Broken Pendant from the crystal golem near the start of the Duke’s Archives.',
 'Return to the location of Dusk’s rescued golem and interact with the dark portal.',
 'Defeat Manus to resolve the DLC rescue.']),
 'hawkeye-gough':('Hawkeye Gough','The Crest Key is in Oolacile Township.',[
 'Find the Crest Key and unlock the tower near Artorias’s arena.',
 'Speak to Gough and visit Kalameet’s ravine to encounter the flying dragon.',
 'Ask Gough for help; his arrow grounds Kalameet for the normal boss fight.',
 'After defeating Kalameet, return to Gough for his greatbow reward.']),
 'lord-s-blade-ciaran':('Lord’s Blade Ciaran','Giving away Artorias’s soul prevents using that same soul for another reward.',[
 'Defeat Artorias and reload the arena to find Ciaran at the grave.',
 'Decide whether to give her Artorias’s soul in exchange for Gold Tracer and Dark Silver Tracer.',
 'Killing her yields her equipment but ends the peaceful encounter.']),
 'darkstalker-kaathe':('Darkstalker Kaathe','Do not place the Lordvessel with Frampt before meeting Kaathe if you want the Darkwraith covenant.',[
 'Obtain the Lordvessel while preserving the option to meet Kaathe.',
 'Defeat Sif, drain New Londo, and defeat the Four Kings wearing the Covenant of Artorias.',
 'Speak to Kaathe in the Abyss and follow his Lordvessel placement route.',
 'Join the Darkwraith covenant and offer humanity for its rank rewards.']),
 'kingseeker-frampt':('Kingseeker Frampt','Following Frampt’s Lordvessel route can close off Kaathe for the playthrough.',[
 'Ring both Bells of Awakening to awaken Frampt at Firelink.',
 'Obtain the Lordvessel, then let him transport you to the Firelink Altar if choosing his route.',
 'Use his feeding service to exchange equipment for souls or break down certain upgrade materials.',
 'Collect and offer the four Lord Souls to open the Kiln.']),
 'shiva-of-the-east':('Shiva of the East','Shiva’s merchant availability depends on remaining a Forest Hunter.',[
 'Join Alvina’s Forest Hunter covenant and speak to Shiva in Darkroot Garden.',
 'Find his weapon shop by the Blighttown waterwheel while you remain in the covenant.',
 'His bodyguard carries the Dark Wood Grain Ring, but attacking covenant members incurs betrayal and hostility.']),
 'elizabeth':('Elizabeth','She becomes the DLC merchant after you reach Oolacile Sanctuary.',[
 'Speak to Elizabeth after defeating Sanctuary Guardian and accept the rescue request.',
 'Buy available sorceries and consumables as needed.',
 'Return after defeating Manus to receive Elizabeth’s Mushroom rewards.']),
 'oscar-knight-of-astora':('Oscar, Knight of Astora','He provides essential starting items in the Asylum.',[
 'Speak to the wounded Oscar after the rolling boulder opens his wall.',
 'Accept the mission and collect the Estus Flask and key.',
 'On returning to the Asylum, his hollowed encounter can yield the Crest Shield.'])}
for id,(name,warning,steps)in quests.items():guide['quests'][id]={'name':name,'warning':warning,'steps':steps};guide['entries'].setdefault(id,{'summary':warning})
item_guides={
 'estus-flask':('Refillable healing received from Oscar. Resting restores charges according to the bonfire’s kindling level.','An unkindled fire gives 5 charges, then kindling raises this to 10, 15 and 20. The Rite of Kindling from Pinwheel is required beyond 10. Fire Keeper Souls upgrade healing through a living Fire Keeper: +0–7 heal 300, 400, 500, 600, 650, 700, 750 and 800 HP. Remastered allows phantom Estus with halved charges.'),
 'humanity':('A consumable humanity sprite; using one restores health and adds one carried humanity.','Carried humanity can reverse hollowing and kindle bonfires. It also affects item discovery, curse resistance and humanity-scaling weapons. Chaos weapon scaling and humanity’s discovery bonus cap at 10, while the humanity counter can reach 99.'),
 'twin-humanities':('Using this consumable restores health and adds two carried humanity.','Spend carried humanity at a bonfire to reverse hollowing or kindle. Holding it exposes the counter to loss on death until your bloodstain is recovered.'),
 'homeward-bone':('Returns you to the last rested bonfire while preserving carried souls and humanity.','Use it to leave a dangerous route without the losses associated with the Darksign. It does not replace unlocking shortcuts or Lordvessel warping.'),
 'darksign':('Returns you to the last rested bonfire but forfeits carried souls and humanity.','A Homeward Bone or the Homeward miracle is preferable when you want to preserve resources.'),
 'transient-curse':('Temporarily allows ordinary weapons to hit New Londo’s ghosts.','Its effect lasts five minutes. A genuine curse or a weapon that can damage ghosts provides another option. The effect is separate from the permanent curse status inflicted by basilisks.'),
 'purple-moss-clump':('Cures poison and removes accumulated poison buildup.','It does not cure toxic; use Blooming Purple Moss for that. Carry moss when exploring Blighttown or fighting poison-inflicting enemies.'),
 'blooming-purple-moss-clump':('Cures toxic as well as poison and clears their buildup.','Useful against Blighttown blowdart snipers. Removing buildup before the status triggers can prevent damage over time.'),
 'bloodred-moss-clump':('Clears accumulated bleed buildup.','Use before the bleed meter fills. It does not restore HP already lost to a bleed proc.'),
 'purging-stone':('Removes curse, restoring the maximum HP lost to that status.','Basilisk curse clouds and Seath’s crystals can inflict curse. Curse resistance helps prevent it; a Purging Stone removes an existing curse.'),
 'repair-powder':('Restores durability to the equipped weapon.','It cannot repair Crystal-path equipment. Reinforcement can restore a Crystal weapon only while an unspent upgrade level remains.'),
 'gold-pine-resin':('Temporarily adds lightning attack to a weapon that accepts buffs.','Adds 150 lightning attack for 60 seconds. Buff eligibility depends on the weapon and upgrade path; most elemental ascensions do not accept resin.'),
 'charcoal-pine-resin':('Temporarily adds fire attack to a buffable weapon.','Adds 80 fire attack for 60 seconds. It is ineffective on weapons that do not accept temporary buffs.'),
 'rotten-pine-resin':('Temporarily adds poison buildup to a buffable weapon.','This is a temporary weapon coating, not a permanent Poison infusion. The game does not offer a generic Poison ascension path.'),
 'poison-throwing-knife':('A ranged consumable that damages a target and applies poison buildup.','Purchased from the female Undead Merchant. If poison triggers, its damage ticks over time; the source documents 4 HP per second. A target’s poison resistance determines how many successful hits are needed.'),
 'throwing-knife':('A quick thrown projectile for pulling an enemy or finishing a distant target.','Lock-on can help direct it. Unlike bow ammunition it is thrown directly from the quick-item slot; actual damage depends on the target’s defenses.'),
 'firebomb':('A thrown fire-damage consumable.','Useful for enemies vulnerable to fire and for ranged pressure without a bow. The Black Firebomb variant is stronger. Actual HP damage depends on enemy fire defense.'),
 'black-firebomb':('A stronger thrown firebomb and one of the starting gifts.','The starting stack can be used to defeat Asylum Demon on the first encounter for the special hammer reward.'),
 'fire-keeper-soul':('Give this soul to a living Fire Keeper to increase Estus healing.','Consuming it instead grants humanity but loses the flask upgrade opportunity. Anastacia’s specific stolen soul must be returned to her cell for revival; do not spend it on Estus.'),
 'rite-of-kindling':('Pinwheel’s key reward unlocks additional bonfire kindling.','After obtaining it, kindle an individual bonfire beyond 10 Estus to 15 and then 20. Each kindling step costs carried humanity and requires human form.'),
 'lordvessel':('Gwynevere’s reward unlocks warping to eligible bonfires.','Placing it at Firelink Altar removes the golden barriers. Offering the four Lord Souls then opens the Kiln. Not every bonfire is a warp destination.'),
 'covenant-of-artorias':('Sif’s ring allows safe entry into the Four Kings’ Abyss.','Keep it equipped until the Four Kings are defeated. The ring has no weight but occupies one of DS1’s two ring slots.'),
 'orange-charred-ring':('Reduces damage taken while standing in lava.','Acquired from Centipede Demon, potentially during the fight through an appendage cut. It is the intended tool for crossing the lava toward Lost Izalith.'),
 'rusted-iron-ring':('Restores normal movement in obstructive terrain such as deep swamp water.','Found during the return to the Undead Asylum. It does not prevent poison buildup or lava damage.'),
 'silver-pendant':('A reusable DLC tool that repels dark projectiles with a timed activation.','Found behind an illusory wall in Oolacile Township. It is particularly useful against Manus’s dark magic; it does not provide continuous protection.'),
 'broken-pendant':('A key item required to open the Artorias of the Abyss portal.','Rescue Dusk in Darkroot Basin, obtain this from the Archives crystal golem, then return to the basin where her golden golem stood.'),
 'peculiar-doll':('Opens entry to the Painted World of Ariamis.','Collect it from your starting cell on returning to the Undead Asylum, then approach the large painting in Anor Londo.'),
 'black-eye-orb':('Invades Lautrec’s world to recover Anastacia’s soul.','The orb reacts in Anor Londo’s cathedral. Its quest invasion can be retried; it is separate from ordinary multiplayer invasion items.'),
 'crest-of-artorias':('Opens the sealed forest gate in Darkroot Garden.','Andre sells it for 20,000 souls. The unlocked route leads toward the Forest Hunters and Sif; the basin ladder is an alternate forest entrance.')}
for id,(summary,how)in item_guides.items():guide['entries'][id]={'summary':summary,'sections':[section('Purpose & use',how)]}
mechanics={
 'equipment-load':'Maximum equip load starts at 40 + Endurance and can be modified by equipment. Fast roll is at or below 25% load, medium at or below 50%, and heavy at or below 100%; above that you cannot roll normally. Every equipped weapon slot contributes weight, including inactive weapons. Rings have no weight.',
 'attunement':'Attunement unlocks slots at 10, 12, 14, 16, 19, 23, 28, 34, 41 and 50. Spells may occupy more than one slot. DS1 uses a limited number of casts per attuned copy rather than a Focus Point bar.',
 'strength':'Strength affects compatible physical weapon scaling and requirements. Two-handing applies an effective 1.5 multiplier, rounded down and capped for scaling. It does not increase Dexterity, Intelligence or Faith, and the displayed scaling letter alone does not specify the precise coefficient.',
 'dexterity':'Dexterity affects compatible physical weapon scaling. It can also shorten casting animations for supported spells at higher values; that animation effect is separate from spell attack power.',
 'intelligence':'Intelligence supplies magic scaling for relevant weapons and catalysts and meets sorcery requirements. A catalyst’s magic adjustment and the spell’s multiplier determine spell offense; displayed weapon physical AR is not a sorcery damage prediction.',
 'faith':'Faith meets miracle requirements and supplies scaling to relevant talismans and Divine/Occult equipment. Individual tools can use unusual scaling; check their data rather than assuming every catalyst uses Intelligence.',
 'endurance':'Endurance raises stamina up to its 40-point cap and continues raising equipment capacity afterward. It also contributes to bleed resistance. Choosing a lighter outfit can change roll speed without changing Endurance.',
 'vitality':'Vitality increases maximum HP using a nonlinear curve. Its major gains diminish after the early soft caps. Equipment such as Tiny Being’s Ring and Ring of Favor and Protection then modifies the resulting HP.',
 'resistance':'Resistance affects poison resistance and parts of physical and fire defense. Equipment offers alternative sources of protection; inspect the Character Lab’s actual changes before spending levels.',
 'bonfires':'Resting refills Estus, restores spell casts and respawns most normal enemies. Kindling permanently raises an individual fire’s Estus supply. Lordvessel warping works only to eligible destinations. The Remastered Catacombs adds a bonfire beside Vamos.',
 'poise':'Poise helps resist interruption before your poise is exhausted. It is an equipment and effect stat rather than the DS2 Adaptability attribute. Stagger behavior also depends on the enemy attack, so a single poise total does not guarantee immunity.',
 'new-game-plus':'Choosing an ending immediately begins the next playthrough. Enemy health, damage and rewards increase; some items and progression keys reset. Finish DLC and optional objectives before leaving Gwyn’s arena.',
 'humanity':'The counter and consumable Humanity items are separate. Carried humanity enables reversal and kindling, improves discovery up to 10, contributes curse resistance up to 30, and boosts humanity-scaling weapons up to 10. Death places carried souls and humanity in the recoverable bloodstain.',
 'parry':'Parry with an appropriate shield or weapon during the incoming attack, then perform a riposte if the enemy is vulnerable. Many large bosses cannot be parried; Gwyn is a notable exception. Blocking and parrying are different actions.',
 'bleed':'Hits build a bleed meter; filling it triggers burst damage. Bloodred Moss removes buildup, and bleed resistance raises the threshold. Weapon buildup and damage after a proc are distinct values.',
 'poison':'Poison buildup must cross the target’s resistance threshold before damage over time begins. Purple Moss cures it. Toxic is a separate status with a stronger effect and requires Blooming Purple Moss.',
 'toxic':'Toxic is a distinct damage-over-time status. Blooming Purple Moss removes it; ordinary Purple Moss is insufficient. Blighttown blowdart snipers are an early source of toxic.',
 'cursed-weapons':'Cursed weapons can strike ghosts without a Transient Curse. This property differs from the Divine auxiliary effect, which prevents necromancer-driven skeleton revival.',
 'critical-damage':'Backstabs and ripostes use attack-specific critical multipliers and the target’s defenses. A weapon’s critical stat and Hornet Ring affect supported critical attacks; regular AR is not the final critical damage.'}
for id,text in mechanics.items():guide['entries'][id]={'summary':text}
(OUT/'guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2),encoding='utf-8');print('Authored',len(guide['entries']),'entries;',len(guide['areas']),'areas;',len(guide['quests']),'questlines')
