"""Fresh visible screenshot transcription and offline comparison; no game access."""
import copy, importlib.util, json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/'runs/run05'
spec=importlib.util.spec_from_file_location('loadout',root/'tools/loadout.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((out/'day14-loadout-input.json').read_text(encoding='utf-8'))
d.update(snapshot='run05 day14 refreshed after player changes / 2026-11-17',gold=62)
d['equipment']=[g for g in d['equipment'] if g['id'] in ['back-b','armor-b','shoulder-ss','hand-s']]
prefix='playtest-2026-11-16-run05/'
d['equipment'].append(dict(id='drone-s-live',name='式神野衾',slot='drone',grade='S',
    ports=[[0,0],[0,1],[0,2],[2,0]],kind='summon',tags=['force'],damage=85,hits=1,
    shield=0,element=10,cooldown=7.5,price=0,acceptsHits=True,deploymentForce=48,
    passive='部署获得48力量；+6桥卡面召唤x7。336力量为7次部署条件预测，尚未战报验证。',
    evidence=prefix+'day14-new-drone.jpg',growth='玩家升级后的实例；85由94/1.1反推，非原始无人机弹体详情'))
d['equipment'].append(dict(id='sword-s-shop',name='朦胧斩者',slot='hand',grade='S',
    ports=[[0,0],[0,1],[0,2],[2,0]],kind='attack',tags=['force'],damage=405,hits=3,
    shield=0,element=4,cooldown=6,price=32,
    passive='命中剥夺敌最大生命，等于自身力量140%；不是命中增长力量。未模拟。',
    evidence=prefix+'day14-new-shop-sword.jpg',growth='新实例无原650伤害积累；商店405按原始值待装后核'))
d['parts']=[p for p in d['parts'] if p['id']!='hits-short-shop']
for p in d['parts']:
    if p['id']=='hits-long':p.update(description='进攻型装备+6段；现有S无人机可见x7，战斗部署计数待核',evidence=prefix+'day14-current-six-bridge.jpg')
    if p['id']=='charge-short':p.update(name='S互相加速2秒短桥',description='使用一端使另一端加速持续2秒；不是立即充能2秒',evidence=prefix+'day14-charge-bridge-current.jpg')
d['parts'] += [dict(id='growth-single',name='S精械单孔',shape=[[0,0]],effect=dict(stat='main_per_second',value=.04),
    description='每秒主属性+4%；动态增幅未纳入静态评分',price=0,sell=8,evidence=prefix+'day14-stock-cd.jpg'),
    dict(id='debuff-long-shop',name='S弹头长桥',shape=[[0,0],[4,0]],effect=dict(stat='debuff_growth',value=.2),
    description='使用镶嵌装备时敌人减益层数+20%；依赖已有敌方减益，不等于自己力量+20%',price=48,sell=24,evidence=prefix+'day14-new-shop-part.jpg')]
d['currentOrder']=['drone-s-live','back-b','armor-b','shoulder-ss','hand-s']
d['baselineNote']='玩家调整后的新基线：62金；S无人机x7/7.5秒；肩7462x3/95坚固；手4615x4/13坚固/4.5秒；库存精械+4%/秒及攻击校准+6消耗品。'
d['unknown']=['双方完整战斗未模拟；候选不能按静态排名当最强。','互加速持续2秒与立即充能不同，模型仅记连接，不换算首击。','桥身交叠仍未知。','无人机x7可见，7次部署的336力量与攻击频率未实测。','新刀最大生命剥夺与每秒主属性、敌人减益增长均列动态项，未赋虚构战力分。','库存校准消耗品未使用；刀与弹头合计80金超过当前62金，不预支卖物。']
(out/'day14-live-loadout-input.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
results=[m.search(d,beam=8,limit=48,policy=p) for p in ['solid','endpoints']]
(out/'day14-live-loadout-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
m.render(d,results,root/'docs/loadout-live-day14.html')
order=[next(g for g in d['equipment'] if g['id']==id) for id in d['currentOrder']]
expected={'hits-long':[(0,1),(4,1)],'main-long':[(6,1),(10,1)],'damage-short':[(10,2),(12,2)],
    'damage-long':[(12,1),(16,1)],'charge-short':[(14,0),(16,0)],'firm-short':[(14,2),(16,2)],'cd-single':[(18,1)]}
chosen=[]
for id,pts in expected.items():
    part=next(p for p in d['parts'] if p['id']==id)
    chosen.append(next(p for p in m.placements(order,part,4) if p['points']==pts))
baseline=m.evaluate(order,d['parts'],chosen,d['mainBonus'])
(out/'day14-live-baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
order2=[next(g for g in d['equipment'] if g['id']==id) for id in ['armor-b','back-b','drone-s-live','shoulder-ss','hand-s']]
expected2={'main-long':[(2,1),(6,1)],'hits-long':[(8,1),(12,1)],
    'damage-long':[(14,1),(18,1)],'charge-short':[(14,0),(16,0)],
    'firm-short':[(14,2),(16,2)],'cd-single':[(8,0)],'growth-single':[(12,2)]}
chosen2=[]
for id,pts in expected2.items():
    part=next(p for p in d['parts'] if p['id']==id)
    chosen2.append(next(p for p in m.placements(order2,part,4) if p['points']==pts))
assert all(not m.conflicts(a,b,'solid') for i,a in enumerate(chosen2) for b in chosen2[i+1:])
balanced=m.evaluate(order2,d['parts'],chosen2,d['mainBonus'])
balanced['note']='人工补充均衡候选：束搜索48强未保留本方案。证明当前代理剪枝会遗漏保留召唤与双核心加速的组合。非全局最优。'
(out/'day14-live-selected.json').write_text(json.dumps(balanced,ensure_ascii=False,indent=2),encoding='utf-8')
print('BASELINE',json.dumps(baseline['metrics']))
print('SELECTED',json.dumps(balanced['metrics']))
for r in results:
    print(r['policy'],r['metrics'])
    for sword in [False,True]:
        candidates=[x for x in r['candidates'] if ('sword-s-shop' in x['order'])==sword]
        for x in sorted(candidates,key=lambda x:x['metrics']['baseDps'],reverse=True)[:2]:
            print('SWORD',sword,x['order'],x['cost'],x['metrics'])
            print([(p['part'],p['points'],p['beneficiaries']) for p in x['placements']])
