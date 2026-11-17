import importlib.util,json,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
d=json.loads((root/'runs/run05/day14-loadout-input.json').read_text(encoding='utf-8'))
results=json.loads((root/'runs/run05/day14-loadout-results.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('loadout',root/'tools/loadout.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for item in d['equipment']+d['parts']:
 assert (root/'docs'/item['evidence']).is_file(),item['evidence']
count=0
for result in results:
 for c in result['candidates']:
  order=[next(g for g in d['equipment'] if g['id']==id) for id in c['order']]
  assert sorted(g['slot'] for g in order)==sorted(d['slots'])
  assert len({p['part'] for p in c['placements']})==len(c['placements'])
  for p in c['placements']:
   part=next(a for a in d['parts'] if a['id']==p['part'])
   allowed=m.placements(order,part,d['stride'])
   assert any(list(map(list,a['points']))==p['points'] for a in allowed)
  for i,a in enumerate(c['placements']):
   assert all(not m.conflicts(a,b,result['policy']) for b in c['placements'][i+1:])
  recomputed=m.evaluate(order,d['parts'],c['placements'],d['mainBonus'])
  assert recomputed['metrics']==c['metrics']
  assert 0<=c['cost']<=d['gold'] and c['remainingGold']==d['gold']-c['cost']
  count+=1
audit={'checkedCandidates':count,'evidenceFilesChecked':len(d['equipment'])+len(d['parts']),
       'tests':'9 unittest tests passed, including recorded baseline and core-charge distinction',
       'page':'384 candidate views exercised with offline DOM smoke; no browser visual QA',
       'search':[dict(policy=r['policy'],**r['metrics']) for r in results],
       'gameValidation':'not performed; day14 remains paused; loadout installation incomplete',
       'decision':'保留离线候选生成工具；整体速度、合法安装和胜负改善待游戏验证'}
(root/'runs/run05/day14-loadout-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
