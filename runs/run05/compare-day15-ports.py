"""Compare evidence-transcribed layouts offline; no game interaction."""
import importlib.util, json
from pathlib import Path

root=Path(__file__).resolve().parents[2]
out=root/'runs/run05'
spec=importlib.util.spec_from_file_location('loadout', root/'tools/loadout.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((out/'day15-loadout-input.json').read_text(encoding='utf-8'))
d['gold']=16
next(g for g in d['equipment'] if g['id']=='shoulder-ss')['cooldown']=8.1
d['snapshot']='Day15 after player shop/consumable and port-occlusion discussion; 13W1L,16gold'
d['unknown'] += ['肩部超驰后冷却8.1秒已核；现无人机CD显示6.8（模型6.75），手无减CD按原5秒。', '蓝色+4力量附魔未纳入数值模型，候选在甲右下预留；真实取整待装后核。']

def assess(name, ids, mapping, verified=False):
    order=[next(g for g in d['equipment'] if g['id']==i) for i in ids]
    chosen=[]
    for part_id, points in mapping.items():
        part=next(p for p in d['parts'] if p['id']==part_id)
        chosen.append(next(p for p in m.placements(order,part,4) if p['points']==points))
    assert all(not m.conflicts(a,b,'solid') for i,a in enumerate(chosen) for b in chosen[i+1:])
    r=m.evaluate(order,d['parts'],chosen,d['mainBonus'])
    endpoints={tuple(p) for c in chosen for p in c['points']}
    blocked=[]; free=[]
    for i,g in enumerate(order):
        for x,y in g['ports']:
            p=(i*4+x,y)
            if p in endpoints: continue
            cover=[c['part'] for c in chosen if len(c['points'])>1 and c['points'][0][1]==y and min(q[0] for q in c['points'])<p[0]<max(q[0] for q in c['points'])]
            (blocked if cover else free).append(dict(equipment=g['id'],port=[x,y],point=p,coveredBy=cover))
    r.update(name=name,verifiedLayout=verified,portAudit=dict(blocked=blocked,free=free),scores=m.scores(r),remainingGold=16,purchases=[],unusedParts=[p['id'] for p in d['parts'] if p['id'] not in mapping],replacedEquipment=[],note='实装基线' if verified else '仅离线候选，未操作游戏')
    return r

base=assess('当前玩家调整后基线', ['back-b','armor-b','shoulder-ss','hand-s','drone-s-live'],{
 'main-long':[(2,1),(6,1)],'damage-long':[(8,1),(12,1)],'hits-long':[(8,2),(12,2)],
 'damage-short':[(10,0),(12,0)],'charge-short':[(14,1),(16,1)],'firm-short':[(16,0),(18,0)],
 'cd-single':[(16,2)],'growth-single':[(0,1)],'calibration-single':[(6,2)]},True)
mapping={'main-long':[(2,1),(6,1)],'damage-long':[(10,1),(14,1)],'hits-long':[(8,2),(12,2)],
 'charge-short':[(14,0),(16,0)],'firm-short':[(14,2),(16,2)],'cd-single':[(8,0)],
 'growth-single':[(0,1)],'calibration-single':[(8,1)]}
alt=assess('手在肩左：少遮一孔，CD回手，元素增强肩', ['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'],mapping)
mapping2=dict(mapping);mapping2.pop('firm-short');mapping2['damage-short']=[(14,2),(16,2)]
alt2=assess('手在肩左：肩保留200%短桥，减少坚固收益', ['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'],mapping2)
knife=assess('新力量刀：增长链未知，不能只比静态', ['back-b','armor-b','sword-force-s','shoulder-ss','drone-s-live'],{
 'main-long':[(2,1),(6,1)],'damage-long':[(10,1),(14,1)],'hits-long':[(10,0),(14,0)],
 'charge-short':[(6,2),(8,2)],'firm-short':[(14,2),(16,2)],'cd-single':[(8,0)],
 'growth-single':[(0,1)],'calibration-single':[(12,2)]})
mapping3=dict(mapping)
mapping3['damage-long']=[(8,1),(12,1)]
mapping3['calibration-single']=[(14,1)]
alt3=assess('手在肩左：两长桥走左侧，SS肩五孔全用', ['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'],mapping3)
mapping4=dict(mapping3)
mapping4.pop('calibration-single')
mapping4['damage-short']=[(14,1),(16,1)]
observed=assess('最新可见：肩右三短桥共享无人机；单孔待核', ['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'],mapping4)
# UI evidence: this summon accepts the attack-only +200% damage bridge.
# Record the manual correction explicitly; do not silently fix the generic solver.
next(g for g in observed['equipment'] if g['id']=='drone-s-live')['damage']=298
next(p for p in observed['placements'] if p['part']=='damage-short')['beneficiaries'].append('drone-s-live')
observed['metrics']['effectiveEndpoints']+=1
observed['note']='最新可见图 day15-blue-drone-mid：肩8K/95、手5K、无人机298/18；手4.5与肩8.1此前已核。无人机伤害298与短桥端点由截图人工校正，通用求解器仍漏算此机制。火控在库、蓝色归属待核；本布局含玩家交叉操作。'
rs=[base,alt,alt2,knife,alt3,observed]
result={'policy':'solid','candidates':rs,'metrics':{'equipmentOrders':len(rs),'evaluatedFinals':len(rs),'retained':len(rs),'seconds':0,'beamPerObjective':0},'limitations':['六个显式候选按同一基线比较，不称全局最优。','实际首击、力量复利、失盾、坚固转伤和敌人尚未模拟。','遮孔记录具体装备和位置；不为每个孔虚构统一战力扣分。','当前火控单孔在防御甲上无可见伤害收益；更高等级不等于更多有效端点。','通用工具对伤害桥作用于该S无人机存在遗漏；第六项用截图人工修正，未假装自动求解正确。']}
(out/'day15-port-comparison.json').write_text(json.dumps({'input':d,'result':result},ensure_ascii=False,indent=2),encoding='utf-8')
result['metrics']['expandedStates']=0
m.render(d,[result,dict(result,policy='endpoints')],root/'docs/loadout-ports-day15.html')
page=root/'docs/loadout-ports-day15.html'
s=page.read_text(encoding='utf-8')
s=s.replace('run05 · 第14天记录','run05 · 第15天记录')
s=s.replace('主核CD与互充','主核CD与互相加速')
start=s.index(" $('search').textContent=")
end=s.index('\n',start)
s=s[:start]+" $('search').textContent='六个显式布局的离线比较；两种碰撞假设使用同一批兼容候选，未作全空间重新搜索。';"+s[end:]
s=s.replace("$('title').textContent=(r.verifiedLayout?", "$('title').textContent=(r.name||'')+' · '+(r.verifiedLayout?")
s=s.replace('runs/run05/day14-loadout-input.json','runs/run05/day15-port-comparison.json').replace('runs/run05/day14-loadout-results.json','runs/run05/day15-port-comparison.json')
rows=''.join('<tr><td>'+r['name']+'</td><td>'+str(r['metrics']['baseVolley'])+'</td><td>'+str(r['metrics']['firmPerVolley'])+'</td><td>'+', '.join(p['equipment']+str(p['port']) for p in r['portAudit']['blocked'])+'</td></tr>' for r in rs)
report='<section><h2>离线比较与现场验证必须分开</h2><p>采集并冻结快照 → 枚举装备/顺序/配件 → 几何合法性 → 有效端点与遮孔机会成本 → 启动/触发链/敌人情景 → 预算与候选取舍 → 写预测 → 一次实装验收 → 战报反馈。</p><p>当前工具完成几何与部分静态指标；没有完整战斗模拟，也不是全局最优求解器。下面是六个显式候选，不能称为完整空间搜索。</p><table><tr><th>候选</th><th>双核基础伤害/轮</th><th>全段条件坚固/轮</th><th>桥身遮住的孔</th></tr>'+rows+'</table><p>“每轮”是假设两核心各完整使用一次，不代表相同时间内实际输出。附魔、失盾、力量、坚固逐段转伤、互加速及对手控制未包含在伤害数字里。孔位代价由被排挤的最佳可行配件决定，不对每个空孔扣同一个虚构分数。</p><p><a href="playtest-2026-11-16-run05/day15-current-final-check.jpg">比较基线</a> · <a href="playtest-2026-11-16-run05/day15-blue-drone-mid.jpg">最新可见混合操作布局</a>。后者肩右三孔分别共享加速、伤害、元素，左两孔接长桥；火控与蓝色单孔未完成最终验收。</p><p>购买纪律：先列入库存/商店的假想候选，离线选中且买后布局与净收益明确，再购买。没有购买前比较的刀不补写为“预先规划的投资”。</p></section>'
s=s.replace('<p id="scope"></p>',report+'<p id="scope"></p>')
page.write_text(s,encoding='utf-8')
for r in rs:
 print(json.dumps({'name':r['name'],'metrics':r['metrics'],'blocked':r['portAudit']['blocked'],'free':r['portAudit']['free'],'ineffective':[p['part'] for p in r['placements'] if not p['beneficiaries']]},ensure_ascii=False))
