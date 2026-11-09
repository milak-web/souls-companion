"""Regression checks for actual importer failures and reviewed DS2 distinctions."""
import json
import unittest
from pathlib import Path
from ds2_wiki_facts import body, cycles, fex_enemy, wikidot_enemy, criticals, reference_facts, reference_tables
from enrich_ds2_wiki import profile_summary

ROOT=Path(__file__).resolve().parents[1]

class SourceParsing(unittest.TestCase):
    def test_cycle_labels_are_not_hit_points(self):
        self.assertEqual(cycles('NG: ? ; NG+: ? ; NG+7: ?'),{})
        self.assertEqual(cycles('NG: 590 ; NG+: 1,062 ; NG+7: 2,018'),{0:'590',1:'1,062',7:'2,018'})
        self.assertEqual(cycles('3,110 | 6,220 (NG+)'),{0:'3,110',1:'6,220'})

    def test_wikidot_health_and_intensity_annotation(self):
        article=body('<div id="page-content"><h2>Forest</h2><table><tr><th>Bonfire Intensity</th><th>Health</th><th>Souls</th></tr><tr><td>1 (NG)</td><td>270</td><td>50</td></tr><tr><td>2 (NG+)</td><td>570</td><td>100</td></tr></table></div>','wikidot')
        p=wikidot_enemy(article,'Hollow Infantry','source')['profiles']
        self.assertEqual([(r['cycle'],r['hp'],r['souls']) for r in p],[(0,'270','50'),(1,'570','100')])

    def test_ng_plus_only_is_not_missing(self):
        self.assertEqual(profile_summary([{'cycle':1,'hp':'3,400'},{'cycle':7,'hp':'6,540'}],'hp'),'3,400')

    def test_mixed_attack_table_is_not_universal_immunity(self):
        a=body('<div class="mw-parser-output"><h2>Attacks</h2><table><tr><th>Attack</th><th>Parryable?</th></tr><tr><td>Swing</td><td>Yes</td></tr><tr><td>Jump</td><td>No</td></tr></table></div>')
        result=criticals(a)['can_parry'];self.assertTrue(result['value']);self.assertTrue(result['conditional'])

    def test_critical_subject_and_crystallized_exception(self):
        a=body('<div class="mw-parser-output"><p>The enemy can backstab the player.</p></div>')
        self.assertNotIn('can_backstab',criticals(a))
        a=body('<div class="mw-parser-output"><p>The crystallized enemies cannot be backstabbed.</p></div>')
        result=criticals(a)['can_backstab'];self.assertTrue(result['value']);self.assertTrue(result['conditional'])

    def test_merchant_quantity_is_not_a_price_property(self):
        a=body('<div class="mw-parser-output"><h2>Inventory</h2><table><tr><th>Item</th><th>Quantity</th><th>Price</th></tr><tr><td>Longsword</td><td>Infinite</td><td>1,300</td></tr></table></div>')
        self.assertEqual(reference_facts(a),[])
        self.assertEqual(reference_tables(a)[0]['rows'][0],['Longsword','Infinite','1,300'])

class ReviewedCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data={n:json.loads((ROOT/'database'/f'{n}.json').read_text(encoding='utf-8')) for n in ['enemies','bosses','npcs','items','weapons','armor','magic','areas','quests']}
        cls.enemies={r['id']:r for r in cls.data['enemies']}

    def test_common_enemy_facts_and_alias_separation(self):
        infantry=self.enemies['hollow_infantry'];self.assertTrue(infantry['can_parry']);self.assertTrue(infantry['can_backstab'])
        alonne=self.enemies['alonne_knight'];self.assertTrue(alonne['can_parry']);self.assertTrue(alonne['can_backstab'])
        self.assertTrue(any(p['hp']=='590' for p in alonne['stat_profiles']))
        self.assertFalse(self.enemies['old_knight']['can_parry']);self.assertFalse(self.enemies['old_knight']['can_backstab'])
        brave=self.enemies['exiled-brave'];self.assertEqual(brave['hp'],'2,550');self.assertEqual(brave['areas'],['Frigid Outskirts'])
        self.assertNotIn('Lindelt Cleric',brave['aliases'])
        self.assertFalse(self.enemies['lindelt-cleric']['can_parry'])

    def test_no_boss_loot_on_repeat_enemy(self):
        self.assertNotIn('Soul of the Pursuer',[d['name'] for d in self.enemies['pursuer_enemy']['drops']])
        self.assertNotIn('Dragonrider Soul',[d['name'] for d in self.enemies['dragonrider_enemy']['drops']])
        bell=self.enemies['bell_keeper_gnome'];names=[d['name'] for d in bell['drops']]
        self.assertIn('Fire Whip',names);self.assertNotIn('Fire Snake',names);self.assertNotIn('Bell Keeper Set',names)

    def test_published_scholar_tables_and_criticals(self):
        pyro=self.enemies['hollow-pyromancer'];self.assertEqual(pyro['hp'],'1,830');self.assertEqual(len(pyro['stat_profiles']),8)
        phantom=self.enemies['faraam-knight-phantom'];self.assertEqual(phantom['hp'],'3,230');self.assertEqual(phantom['fact_cycles']['hp'],1)
        boss=next(r for r in self.data['bosses'] if r['id']=='prowling-magus-and-congregation')
        self.assertIn('Magus',boss['hp']);self.assertTrue(boss['can_backstab'])

    def test_boss_values_are_not_reappearance_values(self):
        bosses={r['id']:r for r in self.data['bosses']}
        self.assertIn('2,330 each',bosses['ruin-sentinels']['hp'])
        self.assertEqual(self.enemies['ruin_sentinel_enemy']['hp'],'3,260')
        self.assertEqual(self.enemies['ruin_sentinel_enemy']['souls'],'2,500')
        self.assertEqual(bosses['dragonrider']['souls'],'12,000')
        self.assertEqual(bosses['dragonriders']['souls'],'26,000')
        self.assertIn('Archer: 1,470',bosses['dragonriders']['hp'])
        self.assertIn('Warrior: 3,670',bosses['dragonriders']['hp'])

    def test_descriptions_quest_images_and_redirect_integrity(self):
        self.assertTrue(all(r.get('description') for r in self.data['npcs']))
        self.assertTrue(all(r.get('location') for r in self.data['npcs']))
        self.assertTrue(all(r.get('usage') for r in self.data['items']))
        self.assertGreaterEqual(len(self.data['quests']),14)
        for q in self.data['quests']:
            self.assertTrue((ROOT/q['image']).is_file(),q['name'])
            self.assertTrue(q.get('source_url'))
        ids={r['id'] for r in self.data['enemies']+self.data['bosses']}
        redirects=json.loads((ROOT/'database/redirects.json').read_text())
        self.assertTrue(all(target in ids for target in redirects.values()))
        self.assertEqual(redirects['archdrake_pilgrim'],'lindelt-cleric')

if __name__=='__main__':unittest.main(verbosity=2)
