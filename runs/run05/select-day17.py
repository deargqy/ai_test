import copy,importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'runs/run05'
sp=importlib.util.spec_from_file_location('loadout',root/'tools/loadout.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
d=json.loads((out/'day17-loadout-input.json').read_text(encoding='utf-8'))
def assess(name,orderids,points):
 order=[next(g for g in d['equipment'] if g['id']==i) for i in orderids];ps=[]
 for pid,pts in points.items():
  p=next(p for p in d['parts'] if p['id']==pid)
  ps.append(next(p for p in m.placements(order,p,4) if p['points']==pts))
 assert all(not m.conflicts(a,b,'solid') for i,a in enumerate(ps) for b in ps[i+1:])
 r=m.evaluate(order,d['parts'],ps,d['mainBonus']);r.update(name=name,note='显式候选，几何通过；动态触发与战斗结果未模拟',scores=m.scores(r),remainingGold=60-r['cost'],purchases=[g['id'] for g in order if g['price']],unusedParts=[p['id'] for p in d['parts'] if p['id'] not in points],replacedEquipment=[i for i in d['currentOrder'] if i not in orderids])
 allports={(i*4+x,y):g['id'] for i,g in enumerate(order) for x,y in g['ports']};end={tuple(p) for c in ps for p in c['points']}
 r['portAudit']=[dict(point=pt,owner=g,state='connected' if pt in end else 'blocked' if any(c['points'][0][1]==pt[1] and min(p[0] for p in c['points'])<pt[0]<max(p[0] for p in c['points']) for c in ps) else 'free') for pt,g in allports.items()]
 return r
base={'main-long':[(2,1),(6,1)],'damage-long':[(8,1),(12,1)],'hits-long':[(8,2),(12,2)],'charge-short':[(14,0),(16,0)],'damage-short':[(14,1),(16,1)],'cd-short':[(14,2),(16,2)],'cd-single':[(8,0)],'growth-single':[(0,1)],'calibration-single':[(18,0)]}
rs=[assess('现装基线',d['currentOrder'],base)]
# Core order shoulder-hand: fast hand and shoulder share acceleration directly.
core={'damage-long':[(10,1),(14,1)],'hits-long':[(8,2),(12,2)],'charge-short':[(10,0),(12,0)],'cd-single':[(8,1)],'calibration-single':[(18,0)]}
for back in ['back-b','back-force-s','back-firm-hp-s','back-firm-growth-s']:
 mp=dict(core)
 if back=='back-b':mp.update({'main-long':[(0,1),(4,1)],'growth-single':[(4,2)],'cd-short':[(16,0),(18,0)]});mp.pop('calibration-single')
 elif back=='back-firm-hp-s':mp.update({'main-long':[(2,1),(6,1)],'growth-single':[(0,0)],'cd-short':[(2,2),(4,2)]})
 else:mp.update({'main-long':[(0,1),(4,1)],'growth-single':[(0,2)],'cd-short':[(2,2),(4,2)]})
 r=assess('S加速甲 + '+back+'：核心直连加速', [back,'armor-firm-s','shoulder-ss','hand-s','drone-s-live'],mp)
 rs.append(r)
 # Alternative sacrifices single CD to use mature +120% fire control on shoulder.
 if back=='back-firm-growth-s':
  mp2=dict(mp);mp2['calibration-single']=[(8,1)];mp2['cd-single']=[(0,0)]
  rs.append(assess('S甲+曙光：火控给肩，单孔CD给背',r['order'],mp2))
selected=rs[-2]
selected['name']='选定：S曙光盾—S加速甲—SS肩—S手—S无人机'
selected['fundingPlan']='60现金，售出闲置S神速神经+16，购买甲/曙光各32，余12；旧B背甲暂留作机制对照，不预支未成交收入。'
selected['bluePlan']='B4力量附魔放S甲左上空位；是否赋予力量标签/条件600%增益为未知，先不计模型收益。'
selected['reason']='已有快手显示2.3秒可先产生坚固；S甲获得坚固触发随机加速，手肩直连加速服务核心，曙光强化坚固装备并减速全敌2秒。肩单孔CD优先于多120%伤害，针对上战肩未兑现。旧背物伤产盾/甲力量被动被放弃，未模拟净收益，保留旧件。'
selected['prediction']='按已读比例估算：手10段/5723伤害/CD约2.55（失去10%单孔）；肩9段/7214伤害/CD约6.9（单孔-10%），手肩使用互相加速2秒。曙光/甲分别约806/3813初始盾；共享-12.5%CD后背5.25/甲11.375。蓝附魔和动态成长不预支。先验收端点与数值，再决定是否出战。'
(out/'day17-manual-comparison.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'day17-selected.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
r={'policy':'solid','candidates':rs,'metrics':{'equipmentOrders':len(rs),'evaluatedFinals':len(rs),'retained':len(rs),'seconds':0,'beamPerObjective':0,'expandedStates':0},'limitations':['明确候选比较，非全局最优；无战斗模拟。','蓝附魔未计预期标签收益；已记录待验。','新S甲孔位本轮纠正，旧报告误写右上不可沿用。']}
m.render(d,[r,dict(r,policy='endpoints')],root/'docs/loadout-selected-day17.html')
for r in rs:print(json.dumps({'name':r['name'],'cost':r['cost'],'metrics':r['metrics'],'equipment':[(g['slot'],g['damage'],g['shield'],g['cooldown']) for g in r['equipment']]},ensure_ascii=False))
