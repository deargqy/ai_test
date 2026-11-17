import copy, datetime, importlib.util, json
from pathlib import Path
root=Path(__file__).resolve().parents[2]; out=root/'runs/run05'; prefix='playtest-2026-11-16-run05/'
spec=importlib.util.spec_from_file_location('loadout',root/'tools/loadout.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((out/'day14-live-loadout-input.json').read_text(encoding='utf-8'))
order=[next(g for g in d['equipment'] if g['id']==id) for id in ['back-b','armor-b','drone-s-live','shoulder-ss','hand-s']]
points={'main-long':[(2,1),(6,1)],'hits-long':[(10,0),(14,0)],'damage-long':[(14,1),(18,1)],
 'charge-short':[(14,2),(16,2)],'firm-short':[(6,2),(8,2)],'cd-single':[(16,0)],'growth-single':[(12,1)]}
chosen=[]
for id,pts in points.items():
 p=next(x for x in d['parts'] if x['id']==id)
 chosen.append(next(x for x in m.placements(order,p,4) if x['points']==pts))
assert all(not m.conflicts(a,b,'solid') for i,a in enumerate(chosen) for b in chosen[i+1:])
r=m.evaluate(order,d['parts'],chosen,d['mainBonus'])
r.update(verifiedLayout=True,remainingGold=62,scores=m.scores(r),purchases=[],replacedEquipment=[],
 unusedParts=[p['id'] for p in d['parts'] if p['id'] not in points],
 verificationEvidence=prefix+'day14-verified-layout.jpg',
 note='人工比较并按实机反馈修订；端点、段数、元素、冷却已核，真实战斗未检验。原计划下排伤害改中排右侧，加速改下排。')
assert r['metrics']['baseVolley']==70858 and r['metrics']['firmPerVolley']==286
assert r['equipment'][-1]['cooldown']==4.5 and r['equipment'][2]['hits']==7
(out/'day14-live-verified.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
results=json.loads((out/'day14-live-loadout-results.json').read_text(encoding='utf-8'))
for result in results:
 result['candidates']=[r]+[x for x in result['candidates'] if not x.get('verifiedLayout')]
 result['metrics']['retained']=len(result['candidates'])
 result['limitations'].append('首项由人工补充并实装核对，不是束搜索自动选出的最强。部署力量仍为条件预测。')
d['unknown'].append('实装候选70858基础伤害/286坚固仅静态对比；与旧40846/337有取舍。每秒成长、实际无人机攻击和力量供盾未实战核对。')
(out/'day14-live-loadout-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
m.render(d,results,root/'docs/loadout-live-day14.html')
html=(root/'docs/loadout-live-day14.html').read_text(encoding='utf-8').replace('主核CD与互充','主核CD与互相加速')
html=html.replace('<p id="scope"></p>', '<p><a href="'+prefix+'day14-verified-layout.jpg">查看实机最终布局</a> · 搜索约5.5秒，实机装配有失败重试，不能声称整日提速。实装方案置顶；战斗效果未验证。</p><p id="scope"></p>')
(root/'docs/loadout-live-day14.html').write_text(html,encoding='utf-8')
after=dict(observed='已装成背—甲—S无人机—SS肩—S手。+6长上排无人机右上至肩右上，x7/x9；600%伤害中排肩右至手右；互加速下排肩右至手左；元素短甲右下至无人机左下；CD手左上；精械肩左中。肩5.8Kx9/30、手4.6Kx4/4/CD4.5、无人机94x7/18/CD7.5，甲76力背38；盾5.3K/8.2K；62金。下排伤害桥两试未成后改用已知中排；清除悬浮说明后单孔冷却成功，遮挡是否根因尚未隔离。',
 evidence=[prefix+x+'.jpg' for x in ['day14-verified-layout','day14-verified-shoulder-details','day14-verified-hand-details','day14-verified-drone-details','day14-verify-growth-shoulder','day14-verify-charge-left']],
 operationResult='succeeded',predictionResult='supported',memoryDecision='narrow',
 reason='最终功能布局和数值支持修订预测，但端点路线与最初图有调整；仅装配验证，未战斗，不能推断胜率。原方案失败记录保留。',
 nextAction='保持当前完整配置；最终确定出战装备后使用库存攻击校准+6；A200%短桥留作改装/恢复对照候选。商店新刀与48金弹头未买、未刷新。选敌与实战须另prepare。')
(out/'run05-d14-05.after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2),encoding='utf-8')
oldafter=dict(observed='原d14-03被物理Esc中断，之后玩家自行改装及升级；本次恢复无法区分中断动作最终效果。新图为无人机x7/肩3，不能归因旧自动操作。',evidence=[prefix+'day14-resume-after-reset.jpg'],operationResult='unknown',predictionResult='unknown',memoryDecision='pending',reason='玩家后续操作造成混杂，旧预测保留且不补记为成功。',nextAction='由d14-04/05记录新状态上的独立决策与验证。')
(out/'run05-d14-03.after.json').write_text(json.dumps(oldafter,ensure_ascii=False,indent=2),encoding='utf-8')
data_path=root/'data/playtest.json'; data=json.loads(data_path.read_text(encoding='utf-8'))
mem=next(x for x in data['memories'] if x['id']=='M05')
if mem['revision']==8:
 old={k:copy.deepcopy(v) for k,v in mem.items() if k!='history'}
 mem['revision']=9
 mem['action']+=' run05第14天实装：+6段长桥可让S无人机数量x7与肩9段同时受益；召唤数量、部署属性和实际攻击频率分开建模。搜索须保留召唤/启动/副属性的不同触发链代表；静态束搜索可能漏掉人工均衡候选。'
 mem['caveat']+=' 本次双核基础释放40846→70858但坚固337→286，未战斗，未证明胜率改善；互加速词条是持续2秒加速，不是立即充能2秒。第一次几何候选未按图装成，改端点后才核实。'
 mem['evidence'].append(dict(runId='run05',day=14,note='玩家要求实机验证模型；不购买新刀/减益桥，已有+6长双端受益与库存成长实装，保留失败及剪枝遗漏。',href=prefix+'day14-verified-layout.jpg'))
 mem['history'].append(dict(date='2026-11-17',revision=9,change='实装验证召唤与肩炮共用六段；修正互加速语义与模型静态筛选边界。',previous=old))
run=next(x for x in data['runs'] if x['id']=='run05');day=next(x for x in run['days'] if x['day']==14)
day['title']='第14天 · 玩家更新后模型实装核验，62金，12胜1负'
day['detailHtml']=day.get('detailHtml','')+'<p>玩家升级S无人机、刷新刀后重新采集。自动控制重置JS后恢复。d14-04原布局反驳，d14-05替代布局装成。<a href="loadout-live-day14.html">当前组合模型与实机图</a>；肩9段、无人机x7，手4.5秒；购物与战斗尚未继续。</p>'
data['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();data_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
snapshot='2026-11-17 实机模型验证完成，尚未出战：run05第14天，12胜1负，Lv14 XP6/50，164000HP，62金。玩家先升级S无人机并刷新商店；自动操作重置node_repl后恢复。现背—甲—S无人机—SS肩—S手；主属性长桥背右中—甲右中；+6段长桥无人机右上—肩右上；600%伤害长桥肩右中—手右中；互相加速短桥肩右下—手左下；元素短桥甲右下—无人机左下；10%CD单孔手左上；每秒主属性+4%单孔肩左中。肩5.8K×9/30坚固/CD9，手4.6K×4/4坚固/CD4.5，无人机94×7/18力量/CD7.5，背5.3K盾/38力，甲8.2K盾/76力。库存A200%伤害短桥保留供后续改装或恢复对照，攻击校准+6尚未使用，最终出战装备确定后使用。商店32金朦胧斩者和48金敌减益增长长桥均未买、未刷新。新刀缺已证实优于旧手的净收益，减益桥缺匹配触发链。d14-04布局未完整成功，d14-05替代布局端点/数值已核；实战胜率未验证。模型漏掉均衡候选，由人工补充，不称自动最优。[当前模型](docs/loadout-live-day14.html)；[实机图](docs/'+prefix+'day14-verified-layout.jpg)。下一步核对现场后使用消耗品、选敌、登记战前预测并战斗；版本菜单仍未重新核实。'
for file,heading in [('README.md','## 当前进度'),('GAME-NOTES.md','## 本局快照')]:
 p=root/file;s=p.read_text(encoding='utf-8');s=s.replace(heading,heading+'\n\n'+snapshot,1)
 if file=='README.md':s=s.replace('## 工作日志','## 工作日志\n\n- '+snapshot,1)
 p.write_text(s,encoding='utf-8')
p=root/'docs/play-flow.html';s=p.read_text(encoding='utf-8');s=s.replace('</body>','<p><a href="loadout-live-day14.html">第14天实机验证：几何成功与失败、静态收益与代价</a>。重置自动控制会话恢复；布局搜索约5.5秒，不包含装配重试。下次先清除覆盖源/目标的悬浮说明，再拖动；根因尚未隔离。</p></body>');p.write_text(s,encoding='utf-8')
start=(root/'docs'/prefix/'day14-resume-after-reset.jpg').stat().st_mtime
end=(root/'docs'/prefix/'day14-verified-layout.jpg').stat().st_mtime
timing=dict(scope='本次首张成功截图至最终装配截图，不含此前工具恢复及此后归档；含模型修改、讨论、搜索和装配重试，不是完整游戏日',seconds=round(end-start,3),searchSeconds=sum(x['metrics']['seconds'] for x in results))
(out/'day14-model-validation-timing.json').write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(metrics=r['metrics'],timing=timing),ensure_ascii=False))
