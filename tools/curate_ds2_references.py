"""Reviewed entity/encounter corrections applied after the mechanical wiki import.

No universal humanoid/animal parry or backstab defaults are used. The maintained
overrides below record source-specific exceptions that a generic parser cannot
resolve. Raw research stays outside the distributable application.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from ds2_wiki_facts import body, text, section_title, numeric, wikidot_enemy, fex_enemy, section_links
from enrich_ds2_wiki import attacks, profile_summary, read, write

ROOT=Path(__file__).resolve().parents[1]
WD='https://darksouls2.wikidot.com/'
FEX='https://darksouls2.wiki.fextralife.com/'

# Same entity under competing wiki/guide names; encounter variants remain intact.
MERGES={
    'bell-keeper-enemy':'bell_keeper_gnome', 'royal-guard':'syan_knight',
    'parasitic_spider':'parasite-spider', 'ice-golem':'rampart_golem',
    'giant':'giant_warrior', 'amana-shrine-healer':'amana-shrine-maiden',
    'dark-spirit-catarina-knight':'catarina-knight',
    'dark-spirit-aurous-knight':'aurous-knight',
    'dark-spirit-blue-sentinel':'sentinel-phantom',
    'full-moon-sickle-phantom':'crescent-sickle-phantom',
    'the-painting-protector':'painting-guardian-phantom',
    'vorgol-the-sinner':'vorgel-the-sinner', 'blue-eyed-durgo':'greatbow-phantom',
    'archdrake-warrior':'exiled-brave', 'faraam-warrior':'exiled-brave',
    'greatsword-of-the-forlorn':'forlorn', 'vengarl-of-forossa':'vengarl-s-body',
    'nadalia-bride-of-ash':'ashen-idol', 'stray-hound':'stray-dog',
    'dark-spirit-syan-knight':'syan-knight-phantom',
    'dark-spirit-heide-sword-knight':'knight-phantom',
    'dark-spirit-executioner':'executioner-phantom',
    'dark-spirit-tattered-butcher':'butcher-phantom',
    'heavy-crossbow-dark-spirit':'foreign-wanderer-phantom',
    'bastard-sword-dark-spirit':'greatsword-foreigner-phantom',
    'coal-tar':'darksucker',
    'frozen-golem':'facsimile-giant', 'sand-basilisk':'basilisk',
    'acid-horn-beetle':'poison-horn-beetle',
    'looking-glass-phantom':'mirror-squire',
}

ROLES={
    'alsanna-silent-oracle':('Oracle / Loyce Soul rewards','Grand Cathedral'),
    'bell-keeper-of-alken':('Bell Keepers covenant steward','Belfry Luna; Belfry Sol'),
    'blacksmith-lenigrast':('Blacksmith','Majula'),
    'blue-sentinel-targray':('Blue Sentinels covenant leader / merchant','Cathedral of Blue'),
    'cale-the-cartographer':('Cartographer / mansion key','Forest of Fallen Giants; Majula'),
    'captain-drummond':('Captain / summon / quest reward','Memory of Vammar; Memory of Jeigh'),
    'carhillion-of-the-fold':('Sorcery merchant / pyromancy reinforcement',"No-man's Wharf; Majula"),
    'chancellor-wellager':('Merchant / Drangleic history','Drangleic Castle'),
    'crestfallen-saulden':('Way of Blue covenant leader','Majula'),
    'cromwell-the-pardoner':('Pardoner / merchant','Brightstone Cove Tseldora'),
    'darkdiver-grandahl':('Pilgrims of Dark covenant leader / merchant','Shaded Woods; Black Gulch; Drangleic Castle'),
    'dyna-tillo':('Item exchange','Things Betwixt'),
    'emerald-herald':('Leveling / Estus Flask upgrades','Majula; Drangleic Castle; Dragon Aerie; Undead Crypt; Throne of Want'),
    'felkin-the-outcast':('Hex merchant',"Huntsman's Copse"),
    'grave-warden-agdayne':('Merchant / summon','Undead Crypt'),
    'laddersmith-gilligan':('Ladder builder / merchant','Earthen Peak; Majula'),
    'licia-of-lindeldt':('Miracle merchant / rotunda access',"Heide's Tower of Flame; Majula"),
    'lonesome-gavlan':('Merchant / buys equipment',"No-man's Wharf; Harvest Valley; Doors of Pharros"),
    'magerold-of-lanafir':('Merchant / Dragon Remnants covenant leader','Iron Keep'),
    'manscorpion-tark':('Summon / quest rewards','Shaded Woods'),
    'maughlin-the-armorer':('Armor merchant','Majula'),
    'merchant-hag-melentia':('General merchant','Forest of Fallen Giants; Majula'),
    'milfanito':('Shrine singers / rescue rewards','Shrine of Amana; Drangleic Castle'),
    'milibeth-the-housekeeper':('Housekeeper / Handmaid’s Ladle reward','Things Betwixt'),
    'rat-king-character':('Rat King covenant leader','Grave of Saints; Doors of Pharros'),
    'rosabeth-of-melfia':('Pyromancy merchant / pyromancy reinforcement','Shaded Woods entrance; Majula'),
    'steady-hand-mcduff':('Blacksmith / infusions','The Lost Bastille'),
    'stone-trader-chloanne':('Upgrade material merchant','Harvest Valley; Majula'),
    'straid-of-olaphis':('Boss soul trades / spell merchant','The Lost Bastille'),
    'sweet-shalquoir':('Ring merchant / covenant services','Majula'),
    'titchy-gren':('Brotherhood of Blood covenant leader / merchant','Undead Purgatory'),
    'weaponsmith-ornifex':('Boss soul weapon trades / blacksmith','Shaded Woods; Brightstone Cove Tseldora'),
    'aldia-scholar-of-the-first-sin':('Story character / optional final boss','Final primal bonfire; Undead Crypt; Dragon Shrine; Throne of Want'),
    'griant':('Retired Fire Keeper','Things Betwixt'),
    'morrel':('Retired Fire Keeper','Things Betwixt'),
    'strowen':('Retired Fire Keeper / character respec','Things Betwixt'),
    'head-of-vengarl':('Merchant / summon / quest reward','Shaded Woods'),
    'loyce-knight':('Allied knights for the Old Chaos encounter','Frozen Eleum Loyce; The Old Chaos'),
    'royal-sorcerer-navlaan':('Assassination quest / spell merchant',"Aldia's Keep"),
    'vendrick':('Fallen king / boss / crown blessing','Undead Crypt; Memory of the King'),
    'benhart-of-jugo':('Summon / equipment quest','Majula; Drangleic Castle; Memory of Orro'),
    'lucatiel-of-mirrah':('Summon / equipment quest',"No-man's Wharf; Lost Bastille; Earthen Peak; Black Gulch; Aldia's Keep"),
    'mild-mannered-pate':('Summon / Pate and Creighton quest','Forest of Fallen Giants; Earthen Peak; Brightstone Cove Tseldora'),
    'creighton-the-wanderer':('Pate and Creighton quest',"Huntsman's Copse; Shaded Woods; Brightstone Cove Tseldora"),
}

SERVICES={
    'alsanna-silent-oracle':'Collect Loyce Souls from Charred Loyce Knights to unlock her rewards. Speaking to her after Aava clears the ice in Eleum Loyce.',
    'bell-keeper-of-alken':'Speak to the seated keeper to join the Bell Keepers. Covenant ranks reward invasions rather than ordinary enemy kills.',
    'cale-the-cartographer':'Exhaust his dialogue to receive the House Key. Clear the Majula mansion basement so he can move there.',
    'crestfallen-saulden':'Speak to him beside the monument to join the Way of Blue.',
    'dyna-tillo':'Leave one eligible trade item in the nest and pick up the exchanged reward. Outcomes depend on the item; dropping a stack wastes its extra units.',
    'milibeth-the-housekeeper':'Return after defeating both nearby Ogres to receive the Handmaid’s Ladle.',
    'loyce-knight':'Find the three frozen knights after Alsanna melts the ice. They join the initial ally and help seal the Old Chaos portals.',
    'strowen':'Bring a Soul Vessel to redistribute attributes. Starting-class minimums still apply.',
    'manscorpion-tark':'Equip the Ring of Whispers to understand him. Exhaust his dialogue to unlock his summon sign for Scorpioness Najka.',
    'royal-sorcerer-navlaan':'Speak to him while hollow to pursue his assassination requests. Keeping his barrier closed preserves the quest; proof items can be obtained without murdering the targets.',
}

# Authored summaries of named item lore, with the actual supporting item page.
# These figures are not presented as NPCs the player can visit.
LORE={
 'alva-the-wayfarer':('Alva Set','A wandering knight who sought a cure for Saint Serreta. His armor describes his failure and his later companionship with Zullie.'),
 'aurous':('Aurous Set','Legendary founder of Jugo, remembered through the armor that bears his name.'),
 'azal-sage-of-forossa':("Azal's Staff",'A sage of Forossa associated with the unusually demanding catalyst named Azal’s Staff.'),
 'bearer-of-the-curse':('Story','The player character: a cursed Undead who travels to Drangleic seeking a remedy for the curse.'),
 'caffrey-goddess-of-fortune':('Name-Engraved Ring','Goddess of Fortune, one of the selectable deities on the Name-Engraved Ring. This is a multiplayer matching choice.'),
 'caitha-goddess-of-tears':('Blue Tearstone Ring','Goddess of Tears associated with the tearstones described by the Blue Tearstone Ring.'),
 'elizabeth':('Elizabeth Mushroom','Saint Elizabeth is remembered for medicines and potions made to help those in need. Elizabeth Mushrooms preserve that association.'),
 'evil-eye':('Ring of the Evil Eye','An unsettling presence associated with the Ring of the Evil Eye. The ring restores HP when enemies die; there is no separate visitable DS2 NPC by this name.'),
 'evlana-goddess-of-the-hunt':("Hunter's Blackbow",'The Hunter’s Blackbow describes Evlana as a skilled huntress whose memory became worship of a goddess.'),
 'eygil':('Fire Snake','A magus loyal to the Old Iron King. Fire Snake and Dance of Fire attribute their pyromancies to him.'),
 'fabian-knight-of-eleum-loyce':('Ivory Straight Sword','A knight who led Eleum Loyce’s warriors into Chaos. The Ivory Straight Sword records that the expedition did not return.'),
 'fiorenza':('Avelyn','A wealthy Volgen merchant and collector. Avelyn attributes the recreation of its unusual design to him.'),
 'flynn':("Flynn's Ring",'A legendary small warrior commemorated by Flynn’s Ring, whose damage bonus favors low maximum equipment load.'),
 'galib-god-of-disease':('Leydia Black Set','God of Disease worshipped by the Leydia apostles of the Undead Crypt.'),
 'gordin-wandering-knight-of-forossa':('Majestic Greatsword','A wandering knight of Forossa and the last named inheritor of the Majestic Greatsword, which was lost after his death.'),
 'gower':("Gower's Ring of Protection",'An assassin remembered for killing kings and clerics. His protective ring is associated with defending the wearer’s back.'),
 'knight-king-rendal':('Ring of Steel Protection','A forgotten Knight King associated with the Ring of Steel Protection. DS2’s item description does not give his name.'),
 'llewellyn':('Royal Dirk','A skilled blacksmith from Mirrah. Vendrick ordered Wellager to secure his services and bring his metalworking to Drangleic.'),
 'nahr-alma-god-of-blood':('Scythe of Nahr Alma','God of Blood worshipped by Titchy Gren and the Brotherhood of Blood. His followers use the scythe bearing his name.'),
 'olenford':("Olenford's Staff",'A sorcerer remembered through the catalyst named Olenford’s Staff. No living NPC encounter is documented.'),
 'pharros-the-vagabond':("Pharros' Lockstone",'A legendary travelling inventor associated with hidden contraptions. His reputation led later generations to credit him with other inventors’ work.'),
 'quella-god-of-dream':('Grand Spirit Tree Shield','God of Dream associated with the spirit-tree allegory and with shields capable of deflecting spells.'),
 'santier':("Santier's Spear",'A walking statue from local legend. Santier’s Spear is said to be the weapon used to defeat it.'),
 'shieldless-lothian':("Dragonslayer's Crescent Axe",'A renowned Forossan warrior who abruptly left the battlefield. His axe and several rings preserve his name.'),
 'sir-syan':("Syan's Set",'Vendrick’s loyal knight, killed while leading the advance against the Giants. Replicas of his armor were later issued to other knights.'),
 'sir-yorgh':("Yorgh's Spear",'Leader of the Sanctum City invasion. His spear pierced Sinh after the Sunken King’s defeat, releasing the dragon’s poisonous fog.'),
 'sunken-king':("Yorgh's Spear",'Former ruler of the Sanctum City, defeated by Sir Yorgh before Sinh awakened and devastated the city.'),
 'war-god-faraam':('Faraam Helm','War god worshipped by the Lion Knights of Forossa, as described by the Faraam armor.'),
 'zandroe-god-of-greed':('Covetous Silver Serpent Ring','God of Greed associated with the snake depicted on the Covetous Silver Serpent Ring.'),
 'zinder-god-of-desire':('Covetous Gold Serpent Ring','God of Desire associated with the snake depicted on the Covetous Gold Serpent Ring.'),
 'zullie-the-witch':('Black Witch Set','A witch who first sought to undermine Alva’s devotion to Saint Serreta, then became his companion and supported his journey.'),
}

QUESTS=[
 ('navlaan','Royal Sorcerer Navlaan',"Aldia's Keep",[
  'Stay hollow and leave the barrier lever untouched. Speak to Navlaan to begin his requests.',
  'Show a Ladder Miniature bought from Gilligan to receive a Dispelling Ring.',
  'Show Cale’s Helm, earned by completing Cale’s map objectives, to receive Simpleton’s Spice.',
  'Show the Sunset Staff: Felkin gives one at 20 base INT and 20 base FTH; another is found outside Aldia’s Keep. Receive Forbidden Sun.',
  'Show the Aged Feather given by the Emerald Herald in Dragon Aerie. Receive Unleash Magic, then talk again for the Chaos Set.'
 ],'Dispelling Ring; Simpleton’s Spice; Forbidden Sun; Unleash Magic; Chaos Set',True,'All four proof items can be obtained without killing the requested NPCs. Releasing Navlaan ends the quest and Bonfire Ascetics do not reset the lever.','royal-sorcerer-navlaan'),
 ('rosabeth','Rosabeth of Melfia','Shaded Woods entrance; Majula',[
  'Use a Fragrant Branch of Yore on the petrified woman blocking the gatehouse switch.',
  'Give her at least one piece of wearable clothing and exhaust her dialogue.',
  'Meet her in Majula to buy pyromancies and reinforce Pyromancy Flames with Fire Seeds.'
 ],'Pyromancy merchant and reinforcement service',False,'Clothing given to Rosabeth is not returned.','rosabeth-of-melfia'),
 ('ornifex','Weaponsmith Ornifex','Shaded Woods; Brightstone Cove Tseldora',[
  'Obtain the Fang Key from the petrified Lion Warrior near the Shaded Ruins bonfire.',
  'Unlock Ornifex’s cell in the underground cave and exhaust her dialogue.',
  'Meet her in her workshop in Lower Brightstone Cove to exchange boss souls for equipment.'
 ],'Boss soul trades; the first weapon trade has its soul fee waived',True,'The boss soul itself is still required for the first trade. Keep nearby enemies away from her.','weaponsmith-ornifex'),
 ('grandahl','Darkdiver Grandahl','Shaded Woods; Black Gulch; Drangleic Castle',[
  'Find Grandahl at all three locations and accept membership in the Pilgrims of Dark.',
  'Explore each of the three Dark Chasm of Old branches, light its brazier and defeat its enemies before leaving.',
  'Complete the covenant trials and defeat Darklurker, then speak to Grandahl for the final rewards.'
 ],'Covenant ranks; Dragon Chime; Xanthous Set',False,'Re-entry normally costs a Human Effigy. Bring a flame source to light the braziers.','darkdiver-grandahl'),
 ('vengarl','Head of Vengarl','Shaded Woods',[
  'Find the disembodied head in the foggy woods and listen to his full story for Vengarl’s Helm.',
  'Defeat his hostile body: after Freja in original DS2, or behind a petrified Lion Warrior in Shaded Woods in Scholar.',
  'Return to the head to unlock additional weapon stock and his summon availability.'
 ],'Vengarl’s Helm; body armor drops; expanded stock and summons',False,'Head and body are different encounters. Killing the friendly head is not required.','head-of-vengarl'),
 ('alsanna','Alsanna, Silent Oracle','Grand Cathedral; The Old Chaos',[
  'Defeat Aava and speak to Alsanna so the blizzard ends and frozen routes reopen.',
  'Recruit the three scattered Loyce Knights, then defeat the Burnt Ivory King with their help.',
  'Collect 5 Loyce Souls for gauntlets and leggings, 15 for the armor, and 35 for the helm.',
  'At 50 Loyce Souls, the stairs clear completely. Speak to her for her soul; Maughlin can then sell the Ivory King Set.'
 ],'Loyce Set; Soul of Alsanna; Ivory King Set purchase unlocked',False,'Keep the Loyce Souls for her progression; killing Alsanna is not equivalent to completing her collection rewards.','alsanna-silent-oracle'),
 ('cale','Cale the Cartographer','Forest of Fallen Giants; Majula',[
  'Exhaust Cale’s dialogue in the cave for the House Key. Defeat the Last Giant and clear the mansion basement so he can move in.',
  'Defeat the Last Giant, Lost Sinner, Old Iron King, the Rotten and the Duke’s Dear Freja.',
  'Obtain the King’s Ring and Ashen Mist Heart, then defeat Throne Watcher and Throne Defender.',
  'Return to Cale after all eight map flames are lit to receive his equipment.'
 ],'Cale’s Set; Curious Map achievement',False,'Cale’s Helm also serves as proof for Navlaan’s second request.','cale-the-cartographer'),
 ('tark','Manscorpion Tark','Shaded Woods',[
  'Wear the Ring of Whispers to understand Tark and exhaust his dialogue.',
  'Defeat Scorpioness Najka and return to him for a Fragrant Branch of Yore.',
  'Return after defeating the Duke’s Dear Freja for the Second Dragon Ring.'
 ],'Fragrant Branch of Yore; Second Dragon Ring',False,'Speaking to him before Najka unlocks his summon sign.','manscorpion-tark'),
 ('crown-blessing','Vendrick — crown blessing','Undead Crypt; Memory of the King',[
  'Obtain the Ashen Mist Heart and use Vendrick’s discarded armor to enter the Memory of the King.',
  'Defeat Vendrick and acquire his crown, plus the crowns of the Sunken King, Old Iron King and Ivory King.',
  'Return to the memory with all four crowns and speak to Vendrick for the blessing.'
 ],'Blessed crowns prevent hollowing and curse while worn',False,'The blessing is for the current playthrough and must be earned again in NG+.','vendrick'),
]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True)
    args=parser.parse_args();cache=args.cache
    data={cat:read(ROOT/'database'/f'{cat}.json') for cat in ['enemies','bosses','npcs','areas','items','weapons','armor','magic','quests']}
    original_notes={r['id']:r.get('ai_notes','') for r in read(cache/'baseline/enemies.json')}
    enemies={r['id']:r for r in data['enemies']};redirects=read(ROOT/'database/redirects.json')
    if 'guardian-dragon-field' not in enemies:
        portrait=next(r['image'] for r in data['bosses'] if r['id']=='guardian-dragon')
        url=FEX+'Dragon';a=body((cache/(hashlib.sha256(b'Dragon').hexdigest()[:20]+'.html')).read_bytes());facts=fex_enemy(a,'Field dragon',url)
        enemies['guardian-dragon-field']={
            'id':'guardian-dragon-field','name':'Guardian Dragon (field encounters)','title':'Aerie dragons / Scholar bridge dragon',
            'aliases':['Dragon','Aerie Dragon'],'areas':['Dragon Aerie',"Heide's Tower of Flame"],
            'image':portrait,'image_source':url,'image_verified':True,'hp':'5,300','souls':'4,000',
            'respawn':'No','despawn':'One defeat per encounter','source_url':url,
            'weaknesses':facts['weaknesses'],'status_effects':{},'can_parry':None,'can_backstab':None,
            'drops':[],'farming':{'bonfire':'Dragon Aerie','gear':[],'difficulty':0,'notes':'Use cover and lightning damage; leave room to retreat from fire breath.'},
            'ai_notes':'Three field dragons guard Dragon Aerie. Scholar also places a dragon on the approach to the Cathedral of Blue.',
            'stat_context':'Field encounters, separate from the Guardian Dragon boss. Headline values are the wiki’s general NG reference; it does not distinguish every location in the infobox.',
            'stat_profiles':facts['profiles'],'fact_sources':{'hp':url,'souls':url},
            'wiki_reference':{'source_url':url,'title':'Dragon','checked_on':'2026-10-16','properties':[], 'mechanics':[], 'attacks':attacks(a),'drops':section_links(a,['drops'])},
        }
        for area in data['areas']:
            if area['name'] in ['Dragon Aerie',"Heide's Tower of Flame"]:
                area['enemies']=[n for n in area['enemies'] if n not in ['Guardian Dragon','Dragon']]
                if enemies['guardian-dragon-field']['name'] not in area['enemies']:area['enemies'].append(enemies['guardian-dragon-field']['name'])
    changes=[]
    for old,new in MERGES.items():
        if old not in enemies:continue
        old_record=enemies.pop(old);canonical=enemies[new]
        canonical['aliases']=list(dict.fromkeys([*canonical.get('aliases',[]),old_record['name'],*old_record.get('aliases',[])]))
        canonical['areas']=list(dict.fromkeys([*canonical['areas'],*old_record['areas']]))
        for field in ['source_url','wiki_reference','hp','souls','can_parry','can_backstab','stat_profiles']:
            if not canonical.get(field) and canonical.get(field) is not False and old_record.get(field):canonical[field]=old_record[field]
        canonical['additional_sources']=list(dict.fromkeys([*canonical.get('additional_sources',[]),*old_record.get('additional_sources',[]),*filter(None,[old_record.get('source_url')])]))
        redirects[old]=new;changes.append({'old':old,'canonical':new,'reason':'Duplicate name or encounter alias'})
    # These were duplicate boss cards, rather than separate regular enemies.
    for old,new in [('smelter_demon_enemy','smelter-demon'),('ancient_dragon_enemy','ancient-dragon')]:
        if old in enemies:enemies.pop(old);redirects[old]=new;changes.append({'old':old,'canonical':new,'reason':'Boss duplicated in regular enemy list'})
    redirects['archdrake_pilgrim']='lindelt-cleric'
    for old in list(redirects):
        seen={old};target=redirects[old]
        while target in redirects and target not in seen:seen.add(target);target=redirects[target]
        redirects[old]=target

    # The boss article also publishes the Castle reappearance. Move those rows
    # to the regular enemy rather than treating 3,260 / 2,500 as boss values.
    ruin_boss=next(r for r in data['bosses'] if r['id']=='ruin-sentinels')
    castle_rows=[p for p in ruin_boss.get('stat_profiles',[]) if p.get('reference')=='Fextralife' and 'Drangleic Castle' in p['context']]
    regular=enemies['ruin_sentinel_enemy']
    regular['stat_profiles']=list({(p.get('source'),p['context'],p.get('cycle'),p.get('hp'),p.get('souls')):p for p in [*regular.get('stat_profiles',[]),*castle_rows]}.values())

    # A regular reappearance is not assigned the boss's HP or soul reward.
    encounters={
        'ruin_sentinel_enemy':('ruin-sentinel','Drangleic Castle'),
        'pursuer_enemy':('the-pursuer','Repeat encounters outside the Forest boss arena'),
        'dragonrider_enemy':('dragonrider',"Shrine of Amana; Undead Crypt"),
    }
    for id,(slug,context) in encounters.items():
        r=enemies[id];r['stat_profiles']=[p for p in r.get('stat_profiles',[]) if (p['reference']=='Wikidot' or id=='ruin_sentinel_enemy' and 'Drangleic Castle' in p['context']) and p['context'] not in [r['name'],"Heide's Tower of Flame",'The Lost Bastille','Forest of Fallen Giants']]
        if id=='dragonrider_enemy':r['stat_profiles']=[p for p in r['stat_profiles'] if re.search('Amana|Crypt',p['context'],re.I)]
        for field in ['hp','souls']:
            r[field]=profile_summary(r['stat_profiles'],field)
            if not r[field]:r.setdefault('stat_notes',{})[field]='Published boss values do not establish the value for this repeat encounter.'
            else:
                r.get('stat_notes',{}).pop(field,None)
                evidence=next(p for p in r['stat_profiles'] if p.get(field))
                r.setdefault('fact_sources',{})[field]=evidence['source']
        r['stat_context']='Regular reappearance: '+context+'. Boss arena values are kept on the boss card.'
    enemies['ruin_sentinel_enemy']['areas']=['Drangleic Castle']
    enemies['dragonrider_enemy']['areas']=['Shrine of Amana','Undead Crypt']
    for id in ['pursuer_enemy','dragonrider_enemy']:
        r=enemies[id];r['drops']=[d for d in r['drops'] if d['name'] not in ['Soul of the Pursuer','Dragonrider Soul']]
        r['wiki_reference']['drops']=[]
    enemies['pursuer_enemy']['drops']=[d for d in enemies['pursuer_enemy']['drops'] if d['name']!='Ring of Blades']
    equipment_icons={r['name']:r.get('image','') for cat in ['items','weapons','armor','magic'] for r in data[cat]}
    for name,condition in [('Ring of Blades +1','Iron Keep reappearance'),('Ring of Blades +2','Defeat the Drangleic Castle pair at NG+ intensity')]:
        if not any(d['name']==name for d in enemies['pursuer_enemy']['drops']):enemies['pursuer_enemy']['drops'].append({'name':name,'icon':equipment_icons.get(name,''),'chance':condition})
    for d in enemies['dragonrider_enemy']['drops']:
        if d['name']=='Titanite Slab':d['chance']='Shrine of Amana encounter (Scholar)'
    enemies['pursuer_enemy']['variant_notes']='Repeat Pursuers have encounter-specific rewards: Ring of Blades +1 in Iron Keep, +2 from the Drangleic Castle NG+ pair, and Twinkling Titanite from Scholar encounters. The boss soul belongs to the Forest boss encounter.'
    enemies['ruin_sentinel_enemy']['drops']=[d for d in enemies['ruin_sentinel_enemy']['drops'] if 'soul' not in d['name'].lower()]
    enemies['ruin_sentinel_enemy']['wiki_reference']['drops']=[d for d in enemies['ruin_sentinel_enemy']['wiki_reference'].get('drops',[]) if 'soul' not in d['name'].lower()]
    enemies['exiled-brave']['variant_notes']='Frigid Outskirts has Faraam and Archdrake equipment variants. The latter is unrelated to the Archdrake Pilgrims in Shrine of Amana.'
    r=enemies['exiled-brave'];r['aliases']=[n for n in dict.fromkeys([*r.get('aliases',[]),'Faraam Warrior','Archdrake Warrior']) if n not in ['Archdrake Pilgrim','Lindelt Cleric']]
    r['areas']=['Frigid Outskirts'];url=WD+'exiled-brave'
    a=body((cache/'wikidot'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')).read_bytes(),'wikidot');facts=wikidot_enemy(a,r['name'],url)
    r.update({'source_url':url,'hp':profile_summary(facts['profiles'],'hp'),'souls':profile_summary(facts['profiles'],'souls'),'stat_profiles':facts['profiles'],'weaknesses':facts['weaknesses'],'status_effects':facts['status_effects']})
    r['additional_sources']=[u for u in r.get('additional_sources',[]) if 'Archdrake_Pilgrim' not in u]
    r['wiki_reference']={'source_url':url,'title':'Exiled Brave','checked_on':'2026-10-16','reference':'Wikidot','properties':[],'attacks':attacks(a),'drops':section_links(a,['drops'],base=WD.rstrip('/'))}
    r['fact_sources']={'hp':url,'souls':url};r['fact_cycles']={'hp':0,'souls':0}
    for field in ['can_parry','can_backstab']:
        r[field]=facts['criticals'].get(field,{}).get('value')
    r.pop('critical_notes',None)
    extra_aliases={
        'prowling-magus':['Aldia Warlock'], 'goblin':['Dark Spirit - Forrest Grotesque'],
        'executioner-phantom':['Chariot Lance Executioner'], 'elite-knight-phantom':['Elite Knight'],
        'giant-undead-boar':['Grand Tusk'], 'spellsword':['Rampart Soldier','Rampart Spearman'],
        'frost-hound':['Rampart Stray Dog'], 'retainer':['Retainer Rogue'],
        'foreign-wanderer-phantom':['Roaming Soul - Foreign Wanderer'],
    }
    for id,aliases in extra_aliases.items():enemies[id]['aliases']=list(dict.fromkeys([*enemies[id].get('aliases',[]),*aliases]))
    enemies['retainer']['variant_notes']='Staff and short-sword variants share this entry. They become hostile after Alsanna ends the blizzard; the sword variant can backstab the player.'
    enemies['retainer']['can_backstab']=True
    enemies['retainer'].setdefault('critical_notes',{})['can_backstab']='The Retainer Rogue / sword variant is explicitly documented as vulnerable.'
    enemies['retainer'].setdefault('fact_sources',{})['can_backstab']=FEX+'Retainer_Rogue'
    enemies['retainer']['additional_sources']=list(dict.fromkeys([*enemies['retainer'].get('additional_sources',[]),FEX+'Retainer_Rogue']))
    enemies['spellsword']['variant_notes']='Also called Rampart Soldiers or Spearmen. Regular and crystallized variants have different health and critical susceptibility.'
    enemies['greatbow-phantom']['variant_notes']='Original Dark Souls II only; appears at bonfire intensity 2+ after obtaining the King’s Ring. Removed in Scholar of the First Sin.'
    enemies['bell_keeper_gnome']['drops']=[d for d in enemies['bell_keeper_gnome']['drops'] if 'Set' not in d['name']]
    icons={r['name']:r.get('image','') for cat in ['items','weapons','armor','magic'] for r in data[cat]}
    enemies['bell_keeper_gnome']['drops']=[{'name':name,'icon':icons.get(name,''),'chance':condition} for name,condition in [
        ('Rusted Coin','Published drop; rate varies by variant'),('Flame Swathe','Belfry Sol'),('Fire Whip','Belfry Sol'),
        ('Bell Keeper Bow','Scholar; matching weapon wielder'),('Bell Keeper Shield','Scholar; matching shield wielder'),('Awestone','Company of Champions'),
    ]]
    enemies['bell_keeper_gnome']['wiki_reference']['drops']=[]
    enemies['bell_keeper_gnome']['variant_notes']='Bell Keeper armor is a covenant rank reward. Enemy drops differ between Luna, Sol and the red phantom, and between original DS2 and Scholar.'
    r=enemies['vorgel-the-sinner'];r['stat_profiles']=[p for p in r.get('stat_profiles',[]) if not (p.get('reference')=='Fextralife' and p.get('hp')=='7')]
    r['hp']=profile_summary(r['stat_profiles'],'hp');r['souls']=profile_summary(r['stat_profiles'],'souls');r.pop('stat_notes',None)
    for id in ['old_ironclad_soldier','enslaved-pig','undead-boar']:
        r=enemies[id];specific=[p for p in r.get('stat_profiles',[]) if p.get('reference')=='Wikidot']
        for field in ['hp','souls']:
            value=profile_summary(specific,field)
            if value:r[field]=value;r.setdefault('fact_sources',{})[field]=r['source_url']
    # Additional published numerical tables, available from the indexed wiki.gg
    # article even where Fextralife has no entry and Wikidot has blank cells.
    gg='https://darksouls2.wiki.gg/wiki/'
    for id,title,hps,rewards,first in [
        ('hollow-pyromancer','Hollow_Pyromancer',[1830,2196,2636,3075,3294,3514,3734,4173],[450,900,1125,1237,1350,1462,1575,1800],0),
        ('faraam-knight-phantom','Faraam_Knight_Phantom',[1700,3230,3876,4522,4845,5168,5491,6137],[1000,2000,2500,2750,3000,3250,3500,4000],1),
    ]:
        r=enemies[id];url=gg+title
        r.update({'hp':f'{hps[first]:,}','souls':f'{rewards[first]:,}','fact_cycles':{'hp':first,'souls':first},'fact_sources':{'hp':url,'souls':url}})
        r['stat_profiles']=[{'context':'Scholar of the First Sin','cycle':i,'intensity':str(i+1),'hp':f'{h:,}','souls':f'{s:,}','source':url,'reference':'wiki.gg'} for i,(h,s) in enumerate(zip(hps,rewards)) if i>=first]
        r['additional_sources']=list(dict.fromkeys([*r.get('additional_sources',[]),url]))
    r=enemies['hollow-pyromancer'];r['source_url']=WD+'hollow-pyromancer'
    r['encounter_notes']=['Scholar-only pyromancers beyond the Rise of the Dead hollow-only door in Shrine of Amana.','They cast Acid Surge, Chaos Storm, Great Chaos Fireball, Great Combustion and Lingering Flame.']
    r['wiki_reference']={'source_url':gg+'Hollow_Pyromancer','title':'Hollow Pyromancer','reference':'wiki.gg','checked_on':'2026-10-16','properties':[{'heading':'Combat properties','facts':[{'label':'Poise','value':'22'},{'label':'Posture','value':'21,978'}]}],'attacks':[{'name':n,'damage':'Fire' if n!='Acid Surge' else 'Equipment durability'} for n in ['Acid Surge','Chaos Storm','Great Chaos Fireball','Great Combustion','Lingering Flame']]}
    r['drops']=[{'name':'Bonfire Ascetic','chance':'2% base drop rate (wiki.gg)','icon':'assets/items/Bonfire_Ascetic.webp'}]
    enemies['hollow_infantry']['can_backstab']=True
    enemies['hollow_infantry'].setdefault('fact_sources',{})['can_backstab']='https://www.reddit.com/r/DarkSouls2/comments/iku66t/'
    enemies['hollow_infantry']['title']='Drangleic Foot Soldier'
    for r in enemies.values():
        url=r.get('source_url','');path=cache/'wikidot'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
        a=body(path.read_bytes(),'wikidot') if path.exists() else None
        if a is None:continue
        tips=[];words=0
        for node in a.select('p,li'):
            if node.find('ul') or node.find('ol') or node.find_parent('table'):continue
            if not re.search(r'strateg|notes|attack',section_title(node),re.I):continue
            value=text(node,False)
            if not 15<len(value)<700:continue
            for sentence in re.split(r'(?<=[.!?])\s+|;\s+',value):
                if 3<len(sentence.split())<=25 and words+len(sentence.split())<=75 and sentence not in tips:
                    tips.append(sentence);words+=len(sentence.split())
        if tips:r['encounter_notes']=tips

    for id in ['dark-spirit','bell-keeper-dark-spirit','arbiter-spirit']:
        r=enemies[id]
        r['stat_context']='Player-controlled encounter: health, defenses, equipment and attack options depend on the summoned or invading character.'
        r['stat_notes']={'hp':'Player build dependent','souls':'Multiplayer reward rules apply'}
        r['can_backstab']=True;r.setdefault('critical_notes',{})['can_backstab']='Subject to the player’s equipment and current animation; backstab-protection armor is an exception.'
        r.setdefault('fact_sources',{})['can_backstab']=WD+'critical-damage'
    r=enemies['mirror-squire'];url=WD+'mirror-squire'
    r['stat_profiles']=[{'context':context,'cycle':cycle,'intensity':str(cycle+1),'hp':f'{hp:,}','souls':f'{souls:,}','source':url,'reference':'Wikidot'} for context,hps,rewards in [("King's Passage",[1100,1550,2900],[0,0,0]),("Aldia's Keep",[2250,3000,5650],[1200,2400,4800])] for cycle,hp,souls in zip([0,1,7],hps,rewards)]
    r['hp']='1,100–2,250';r['souls']='0–1,200';r['fact_cycles']={'hp':0,'souls':0};r['fact_sources']={'hp':url,'souls':url}
    r['variant_notes']='The NPC squires have different stats in the Looking Glass Knight encounter and Aldia’s Keep. A human player summoned through the boss shield uses their own build instead.'
    r['stat_context']='NPC mirror squires: headline NG values span both locations; each location is separated in the table.'
    r['can_backstab']=None;r.pop('critical_notes',None)
    for id,note in {
        'invisible-hollow':'Non-attacking hidden Hollow. Any damaging hit reveals and kills it; carry a light to see its shadow.',
        'pagan-tree':'Non-hostile repair tree. Strike it with a whip to release equipment-repairing mist; killing it removes that service until it respawns.',
        'curse-jar':'Environmental curse hazard. Break the jar or use curse immunity; a combat HP/soul template is not applicable.',
        'faraam-knight-phantom':'Grave of Saints phantom, available from NG+. Wikidot reports playthrough-only spawning; wiki.gg reports that Scholar can respawn it with a Grave Entrance Ascetic. Drops Soul of a Great Hero.',
        'frost-hound':'Frozen Eleum Loyce variant of the Stray Dog, also called Rampart Stray Dog or Frozen Hound. Its dedicated Fextralife page does not publish HP or souls.',
    }.items():enemies[id]['variant_notes']=note
    for r in enemies.values():
        r.pop('data_status',None)
        if r.get('variant_notes'):r['ai_notes']=' '.join(filter(None,[original_notes.get(r['id'],'').strip(),r['variant_notes']]))
    # Main boss infoboxes establish the boss reward. General enemy pages can
    # include several later reappearances with different HP and soul rewards.
    for r in data['bosses']:
        if r['id']=='dragonriders':continue
        main=[p for p in r.get('stat_profiles',[]) if p.get('reference')=='Wikidot' and p['context']==r['name']]
        for field in ['hp','souls']:
            value=profile_summary(main,field)
            if value:
                r[field]=value;r.setdefault('fact_sources',{})[field]=main[0]['source']
                r.setdefault('fact_cycles',{})[field]=min(p['cycle'] for p in main if p.get(field))
        if r['id']=='ruin-sentinels':r['stat_profiles']=[p for p in r['stat_profiles'] if 'Drangleic Castle' not in p['context']]
        if r['id']=='dragonrider':r['stat_profiles']=[p for p in r['stat_profiles'] if p['context'] in [r['name'],"Heide's Tower of Flame"]]
        if r['id']=='the-pursuer':r['stat_profiles']=[p for p in r['stat_profiles'] if p['context'] in [r['name'],'Forest of Fallen Giants']]
    for id,health,context in [
        ('ruin-sentinels','2,330 each (6,990 total)','Lost Bastille boss: three sentinels, with per-member and encounter-total health distinguished.'),
        ('belfry-gargoyles','1,400 each (7,000 encounter total)','NG health is per gargoyle; the encounter-total reference is separate from the health of an individual gargoyle.'),
        ('throne-watcher-and-defender','Defender: 3,910; Watcher: 2,760 (6,670 total)','Two separate boss health bars; the table distinguishes per-member values and the combined reference total.'),
    ]:
        r=next(r for r in data['bosses'] if r['id']==id);r['hp']=health;r['stat_context']=context
        for p in r.get('stat_profiles',[]):
            if p.get('reference')=='Wikidot' and p['context']==r['name'] and p.get('hp'):p['context']='Encounter total'
    r=next(r for r in data['bosses'] if r['id']=='belfry-gargoyles');r['souls']='25,000';r['fact_cycles']['souls']=0
    r=next(r for r in data['bosses'] if r['id']=='throne-watcher-and-defender');r['stat_profiles']=[p for p in r['stat_profiles'] if p.get('reference')!='Fextralife']
    source=FEX+'Throne_Watcher_and_Throne_Defender'
    r['stat_profiles'] += [{'context':member,'cycle':cycle,'intensity':str(cycle+1),'hp':f'{hp:,}','souls':None,'source':source,'reference':'Fextralife'} for member,values in [('Throne Defender',[3910,4692]),('Throne Watcher',[2760,3312])] for cycle,hp in enumerate(values)]
    r=next(r for r in data['bosses'] if r['id']=='afflicted-graverobber-ancient-soldier-varg-and-cerah-the-old-explorer')
    r['hp']='Graverobber: 3,350; Varg: 3,310; Cerah: 2,540';r['stat_context']='NG health is listed per member. The soul reward is for the encounter.'
    # The Castle pair has its own article and is not the Heide Dragonrider.
    r=next(r for r in data['bosses'] if r['id']=='dragonriders');title='DragonRider(Second Encounter)';source=FEX+'DragonRider(Second_Encounter)'
    a=body((cache/(hashlib.sha256(title.encode()).hexdigest()[:20]+'.html')).read_bytes())
    r['hp']='Archer: 1,470; Warrior: 3,670';r['souls']='26,000';r['stat_context']='Drangleic Castle boss pair. The archer and halberd warrior have different health; Heide and regular reappearances are separate entries.'
    r['fact_sources']={'hp':source,'souls':source};r['fact_cycles']={'hp':0,'souls':0}
    r['stat_profiles']=[p for p in r.get('stat_profiles',[]) if p.get('reference')=='Wikidot' and p['context']=='Drangleic Castle']
    r['stat_profiles'] += [{'context':member,'cycle':cycle,'intensity':str(cycle+1),'hp':f'{hp:,}','souls':'26,000' if cycle==0 else '52,000','source':source,'reference':'Fextralife'} for member,values in [('Archer',[1470,2352]),('Halberd warrior',[3670,5872])] for cycle,hp in enumerate(values)]
    r['wiki_reference']={'source_url':source,'title':'Twin Dragonriders','checked_on':'2026-11-08','properties':[],'attacks':attacks(a),'drops':section_links(a,['drops'])}
    r['additional_sources']=list(dict.fromkeys([*r.get('additional_sources',[]),source]))
    source_aliases=read(ROOT/'tools/ds2_entity_aliases.json');source_aliases['Dragonriders']=title;write(ROOT/'tools/ds2_entity_aliases.json',source_aliases)
    # Group HP is per member, rather than a fabricated single boss HP value.
    boss=next(r for r in data['bosses'] if r['id']=='prowling-magus-and-congregation')
    boss['hp']='1,100 Magus; 900 × 2 clerics; 300 × 3 standing; 280 × 5 crawling'
    boss['stat_context']='NG health is listed per member; the congregation contains several distinct enemy types.'
    boss['fact_sources']['hp']=FEX+'Prowling_Magus_and_Congregation'
    boss['can_backstab']=True
    boss.setdefault('critical_notes',{})['can_backstab']='Magus and clerics can be backstabbed; susceptibility varies among congregation members.'
    junk_moves={'move','attack','description','move description','?','--','tba','two hit combo','two-handed attack'}
    for r in [*enemies.values(),*data['bosses']]:
        wiki=r.get('wiki_reference',{})
        if 'attacks' in wiki:wiki['attacks']=[a for a in wiki['attacks'] if a['name'].lower().strip() not in junk_moves]

    # Recover NPC location/interaction facts missed by generic character templates.
    area_names={r['name'].lower():r['name'] for r in data['areas']}
    for r in data['npcs']:
        if r.get('role')=='Lore figure':continue
        url=r.get('source_url','');path=cache/'wikidot'/(hashlib.sha256(url.encode()).hexdigest()[:20]+'.html')
        a=body(path.read_bytes(),'wikidot') if path.exists() else None
        if r['id'] in ROLES:
            role,locations=ROLES[r['id']];r['role']=role
            if not r.get('location'):r['location']=locations
            r['description']=r['name']+' — '+role.lower()+'.'
        else:
            r['role']='Summon / co-op ally'
            r['description']=r['name']+' is an NPC ally available through a summon sign. Availability depends on location, game edition and encounter progress.'
        if a is not None:
            if not r.get('location'):
                locations=[]
                for node in a.select('p,li'):
                    if re.search(r'location',section_title(node),re.I):
                        value=text(node,False)
                        if 0<len(value)<500:locations.append(value)
                r['location']=' '.join(locations[:4])
            clauses=[];word_count=0
            for node in a.select('p,li'):
                if node.find('ul') or node.find('ol') or node.find_parent('table'):continue
                heading=section_title(node)
                if not re.search(r'use|interact|quest|event|note|require|reward|summon',heading,re.I):continue
                value=text(node,False)
                if not 15<len(value)<650:continue
                for sentence in re.split(r'(?<=[.!?])\s+|;\s+',value):
                    if not 3<len(sentence.split())<=25 or not re.search(r'give|reward|summon|sell|buy|soul|speak|talk|defeat|kill|must|require|human|hollow|offer|trade|reinfor|upgrade|join',sentence,re.I):continue
                    if sentence in clauses or word_count+len(sentence.split())>85:continue
                    clauses.append(sentence);word_count+=len(sentence.split())
            if clauses:
                r['interaction_details']=clauses
                if not r.get('use_notes'):r['use_notes']=' '.join(clauses[:2])
            r['additional_sources']=list(dict.fromkeys([*r.get('additional_sources',[]),url]))
        if r['id'] in SERVICES:r['use_notes']=SERVICES[r['id']]
    summon_locations={
        'drifter-swordsman-aidel':'Iron Passage; Memory of the Old Iron King',
        'felicia-the-brave':'Shrine of Amana; The Lost Bastille (Scholar)',
        'rapacious-andrei':'Cave of the Dead',
        'jester-thomas':"Earthen Peak (ally for Mytha); Dragon's Sanctum (invader)",
        'melinda-the-butcher':"The Gutter (invader); Aldia's Keep (summon)",
    }
    for r in data['npcs']:
        if not r.get('location') and r['id'] in summon_locations:r['location']=summon_locations[r['id']]
    npc_redirects={'old-ladies':'strowen','fire-keeper':'strowen','knight-of-eleum-loyce':'loyce-knight'}
    for r in data['npcs']:
        if r['id'] in LORE:
            title,summary=LORE[r['id']];r['description']=summary;r['role']='Lore figure'
            r['location']='Item lore / historical reference; no separate visitable NPC encounter.'
            r['source_url']=FEX+title.replace(' ','_');r['use_notes']='Related reference: '+title+'.'
            r['related']=[{'name':title,'source_url':r['source_url']}]
            if r['id']=='knight-king-rendal':r['aliases']=list(dict.fromkeys([*r.get('aliases',[]),r['name'],'Knight King Rendal']));r['name']='Knight King'
    # Generic group placeholders and a DS3 category were imported as empty NPCs.
    data['npcs']=[r for r in data['npcs'] if r['id'] not in {*npc_redirects,'lords','lords-of-cinder','phantom'}]
    write(ROOT/'database/npc_redirects.json',npc_redirects)
    source_aliases=read(ROOT/'tools/ds2_entity_aliases.json')
    source_aliases.update({'Prowling Magus':'Aldia Warlock','Frost Hound':'Rampart Stray Dog','Exiled Brave':'Exiled Brave'})
    write(ROOT/'tools/ds2_entity_aliases.json',source_aliases)
    for id,name,location,actions,reward,missable,notes,slug in QUESTS:
        quest={'id':id,'name':name,'steps':[{'location':location,'action':a,'done':False} for a in actions], 'reward':reward,'missable':missable,'notes':notes,'source_url':WD+slug}
        data['quests']=[q for q in data['quests'] if q['id']!=id]+[quest]
    for q in data['quests']:
        if q['id']=='benhart':
            q['reward']='Bluemoon Greatsword; Benhart’s Set; Benhart’s Parma'
            q['notes']='Benhart must survive three qualifying boss victories before the final conversation in Memory of Orro. Prowling Magus and Congregation, Looking Glass Knight and Giant Lord count; repeated victories using Ascetics count. Elana does not count.'
            q['source_url']=WD+'benhart-of-jugo'
        if q['id']=='lucatiel':
            q['notes']='Lucatiel must survive three victories against Flexile Sentry, Lost Sinner, Smelter Demon or the Rotten before the final Aldia’s Keep conversation. Repeated victories using Ascetics count. Her meeting spots differ by edition.'
            q['steps'][0]['action']='Speak to her by the bonfire in original DS2, or in the first upper building in Scholar. Exhaust her dialogue.'
            q['source_url']=WD+'lucatiel-of-mirrah'
        if q['id']=='pate':q['source_url']=WD+'mild-mannered-pate'
        if q['id']=='creighton':q['source_url']=WD+'creighton-the-wanderer'
        if q['id']=='chloanne':q['source_url']=WD+'stone-trader-chloanne'
        npc=next((r for r in data['npcs'] if r.get('source_url')==q.get('source_url')),None)
        if npc:q['image']=npc['image'];q['npc_id']=npc['id']
    data['enemies']=list(enemies.values())
    reference_aliases={
        'weapons':{"Craftsman's Hammer":["Craftman's Hammer"]},
        'armor':{'Leather Set':['Hunter/Leather Set'],'Tattered Cloth Set':['Pyromancer Set']},
        'items':{'Scorpioness Najka Soul':['Scorpion Najka Soul'],'Old Dead One Soul':["Old Dead One's Soul"]},
        'npcs':{'Licia of Lindeldt':['Licia of Lindelt']},
        'bosses':{'Skeleton Lords':['The Skeleton Lords']},
        'enemies':{'Poison Horn Beetle':['Poisonous Horn Beetle','Poisonous Horn Beetles']},
    }
    for category,mapping in reference_aliases.items():
        for r in data[category]:
            if r['name'] in mapping:r['aliases']=list(dict.fromkeys([*r.get('aliases',[]),*mapping[r['name']]]))
    for r in data['weapons']:
        # Fextralife's unlabeled infobox mixes maximum and infused attack values.
        # The guide already has explicit base/level/path tables; do not duplicate
        # those values as though they were a second set of baseline stats.
        wiki=r.get('wiki_reference',{})
        for group in wiki.get('properties',[]):group['facts']=[f for f in group['facts'] if not re.search(r'^icon|^[*; ()SABCDE+-]+$|^\d',f['label'],re.I)]
        if r['id']=='fists':
            r.update({'source_url':WD+'fist','attack':{'physical':10,'magic':0,'fire':0,'lightning':0,'dark':0},'requirements':{'str':0,'dex':0,'int':0,'fth':0},'scaling':{'str':'C','dex':'D','magic':'-','fire':'-','lightning':'-','dark':'-'},'notes':'Bare fists cannot be reinforced, infused or buffed. Normal scaling is 50% STR bonus plus 15% DEX bonus. Vanquisher’s Seal changes base physical attack to 200 and scaling to 75% STR / 25% DEX.'})
    for r in data['armor']:
        if r['id']=='xanthous-overcoat':
            fields=['physical','strike','slash','thrust','magic','fire','lightning','dark','poison','bleed','petrify','curse','poise','durability','weight']
            r['defenses_base']=dict(zip(fields,[52,60,52,45,39,10,25,30,23,21,0,0,0,60,3.9]))
            r['defenses_base_source']='https://darksouls2.wiki.gg/wiki/Chests'
            r['additional_sources']=list(dict.fromkeys([*r.get('additional_sources',[]),r['defenses_base_source'],WD+'xanthous-set']))
            r['obtaining']='Reward for reaching rank 3 in Pilgrims of Dark; speak to Darkdiver Grandahl after completing the covenant.'
        if r['id'] in ['prisoner-s-hood','prisoner-s-tatters']:
            values=[['Left source image',4,4,4,4,4,4,6,5,5,4],['Right source image',4,5,4,4,4,4,6,5,5,3]] if r['id']=='prisoner-s-hood' else [['Left source image',11,12,10,10,11,12,16,13,13,10],['Right source image',11,12,11,11,11,11,17,13,13,10]]
            table={'heading':'Base defenses by appearance variant (Wikidot)','headers':['Appearance','Physical','Strike','Slash','Thrust','Magic','Fire','Lightning','Dark','Poison','Bleed'],'rows':[[str(v) for v in row] for row in values]}
            wiki=r.setdefault('wiki_reference',{'source_url':WD+'prisoner-s-set','title':"Prisoner's Set",'reference':'Wikidot','checked_on':'2026-11-08'})
            wiki['tables']=[t for t in wiki.get('tables',[]) if t['heading']!=table['heading']]+[table]
            r['equipment_note']='Two appearance variants have different base defenses; both are listed in the reference table. The maximum-defense source does not identify the appearance variant.'
            r['additional_sources']=list(dict.fromkeys([*r.get('additional_sources',[]),WD+'prisoner-s-set']))
    for name,records in data.items():write(ROOT/'database'/f'{name}.json',records)
    write(ROOT/'database/redirects.json',redirects)
    write(cache/'curation-audit.json',{'checked_on':'2026-10-16','entity_corrections':changes})
    print('Curated',len(changes),'duplicate/invalid enemy records; retained',len(enemies),'distinct encounters.')


if __name__=='__main__':main()
