import importlib.util
import unittest
from pathlib import Path


class LoadoutTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name('loadout.py')
        self.assertTrue(path.exists(), 'offline loadout model not implemented')
        spec = importlib.util.spec_from_file_location('loadout', path)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def gear(self, id, ports, **kwargs):
        return dict(id=id, name=id, slot=id, ports=ports, tags=['firm'],
                    kind='attack', damage=100, hits=3, shield=0, element=10,
                    cooldown=5, price=0, **kwargs)

    def test_shapes_use_actual_ports_and_same_card_only_once(self):
        g = self.gear('a', [[0, 1], [2, 1]])
        part = dict(id='p', shape=[[0, 0], [2, 0]], price=0,
                    effect={'stat': 'damage_pct', 'value': 2})
        ps = self.m.placements([g], part, 4)
        self.assertEqual(len(ps), 1)
        result = self.m.evaluate([g], [part], [ps[0]], 0)
        self.assertEqual(result['equipment'][0]['damage'], 300)
        self.assertEqual(result['equipment'][0]['hits'], 3)
        part['shape'] = [[0, 0], [4, 0]]
        self.assertEqual(self.m.placements([g], part, 4), [])

    def test_shared_endpoints_and_body_overlap_are_distinct(self):
        a = {'points': [(0, 0), (4, 0)]}
        b = {'points': [(2, 0), (6, 0)]}
        c = {'points': [(4, 0), (8, 0)]}
        self.assertTrue(self.m.conflicts(a, b, 'solid'))
        self.assertFalse(self.m.conflicts(a, b, 'endpoints'))
        self.assertTrue(self.m.conflicts(a, c, 'endpoints'))

    def test_conditional_endpoint_and_cost(self):
        a = self.gear('a', [[2, 0]])
        b = self.gear('b', [[0, 0]])
        b.update(kind='defense', tags=['force'], damage=0, shield=200)
        p = dict(id='p', shape=[[0, 0], [2, 0]], price=16,
                 effect={'stat': 'damage_pct', 'value': 2, 'tag': 'firm', 'tagValue': 6})
        ps = self.m.placements([a, b], p, 4)
        r = self.m.evaluate([a, b], [p], ps[:1], 0)
        self.assertEqual(r['equipment'][0]['damage'], 700)
        self.assertEqual(r['equipment'][1]['shield'], 200)
        self.assertEqual(r['cost'], 16)
        self.assertEqual(r['placements'][0]['beneficiaries'], ['a'])

    def test_search_considers_replacement_permutations_and_budget(self):
        a = self.gear('a', [[2, 0]])
        b = self.gear('b', [[0, 0]])
        upgrade = dict(b, id='b2', name='upgrade', damage=200, price=10)
        d = {'stride': 4, 'gold': 9, 'mainBonus': 0,
             'equipment': [a, b, upgrade], 'parts': [], 'slots': ['a', 'b']}
        r = self.m.search(d, beam=4, limit=10)
        self.assertEqual(r['metrics']['equipmentOrders'], 2)
        self.assertTrue(all('b2' not in x['order'] for x in r['candidates']))
        d['gold'] = 10
        r = self.m.search(d, beam=4, limit=10)
        self.assertEqual(r['metrics']['equipmentOrders'], 4)
        self.assertTrue(any('b2' in x['order'] for x in r['candidates']))

    def test_recorded_day14_baseline_preserves_all_successful_connections(self):
        import json
        root = Path(__file__).resolve().parents[1]
        d = json.loads((root/'runs/run05/day14-loadout-input.json').read_text(encoding='utf-8'))
        order = [next(g for g in d['equipment'] if g['id'] == id) for id in d['currentOrder']]
        expected = {'main-long': [(2,1),(6,1)], 'damage-long': [(8,1),(12,1)],
                    'damage-short': [(6,2),(8,2)], 'firm-short': [(10,2),(12,2)],
                    'charge-short': [(10,0),(12,0)], 'cd-single': [(14,1)]}
        chosen = []
        for id, points in expected.items():
            part = next(p for p in d['parts'] if p['id'] == id)
            choices = self.m.placements(order, part, d['stride'])
            chosen.append(next(p for p in choices if p['points'] == points))
        self.assertTrue(all(not self.m.conflicts(a,b,'solid') for i,a in enumerate(chosen) for b in chosen[i+1:]))
        r = self.m.evaluate(order,d['parts'],chosen,d['mainBonus'])
        hand, shoulder = r['equipment'][3], r['equipment'][2]
        self.assertEqual((shoulder['damage'],shoulder['hits'],shoulder['element']), (7462,3,95))
        self.assertEqual((hand['damage'],hand['hits'],hand['element'],hand['cooldown']), (4615,4,13,4.5))

    def test_startup_proxy_distinguishes_core_charge_from_support_charge(self):
        order = [self.gear(str(i), [[0,0]]) for i in range(4)]
        order[0]['slot'], order[1]['slot'] = 'hand', 'shoulder'
        order[2]['kind'], order[3]['kind'] = 'defense', 'defense'
        p = dict(id='charge', shape=[[0,0],[4,0]], price=0, effect=dict(stat='charge',value=2))
        ps = self.m.placements(order,p,4)
        core = self.m.evaluate(order,[p],[ps[0]],0)
        support = self.m.evaluate(order,[p],[ps[-1]],0)
        self.assertGreater(self.m.scores(core)[2], self.m.scores(support)[2])


if __name__ == '__main__':
    unittest.main()
