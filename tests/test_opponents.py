import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'tools/opponents.py'
spec=importlib.util.spec_from_file_location('opponents',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class OpponentsTest(unittest.TestCase):
    def fixture(self):
        return {'runs':[{'id':'demo','gameVersion':'1','days':[
            {'day':1,'outcome':'win','before':'我方燃烧装备','after':'敌人信息未读','images':[]},
            {'day':2,'outcome':'loss','after':'失败','images':[]},
            {'day':3,'outcome':'unknown','after':'尚未结算','images':[]}]}],'opponentStudies':[]}
    def test_keep_both_outcomes_exclude_unknown(self):
        rows=m.make_cases(self.fixture(),{})
        self.assertEqual([r['ownOutcome'] for r in rows],['win','loss'])
    def test_own_mentions_are_not_enemy_traits(self):
        row=m.make_cases(self.fixture(),{})[0]
        self.assertEqual(row['enemyMechanisms'],[])
        self.assertEqual(m.search([row],mechanism='燃烧'),[])
    def test_missing_stats_not_zero(self):
        row=m.make_cases(self.fixture(),{})[0]
        self.assertIsNone(row['stats'])
        self.assertIsNone(row['enemyName'])
    def test_explicit_snapshot_preserves_time_and_null(self):
        snap={'demo-d01':{'opponent':'A','enemyTech':['禁用'], 'damage':{'enemy':{'hand':None}},'enemyEquipment':[{'cdObserved':2}], 'firstHitSeconds':None}}
        row=m.make_cases(self.fixture(),snap)[0]
        self.assertEqual(row['stats']['damage']['enemy']['hand'],None)
        self.assertEqual(row['snapshotTiming'],'postbattle')
        self.assertEqual(row['enemyEquipment'][0]['cdObserved'],2)
    def test_search_evidence_text_not_win_probability(self):
        rows=m.make_cases(self.fixture(),{})
        self.assertEqual(len(m.search(rows,query='燃烧')),1)
        self.assertNotIn('winProbability',rows[0])

if __name__=='__main__':unittest.main()
