import copy, html, json
from pathlib import Path
from datetime import datetime, timezone

root=Path(__file__).resolve().parents[2]
out=root/'runs/run05'; docs=root/'docs'; E='playtest-2026-11-16-run05/'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
source=json.loads((out/'day17-loadout-input.json').read_text(encoding='utf-8'))
chosen=json.loads((out/'day17-selected.json').read_text(encoding='utf-8'))
points={'main-long':[(0,1),(4,1)],'growth-single':[(0,2)],'cd-short':[(2,2),(4,2)],'damage-long':[(10,1),(14,1)],'hits-long':[(8,2),(12,2)],'charge-short':[(10,0),(12,0)],'cd-single':[(8,1)],'damage-short':[(16,0),(18,0)],'calibration-single':[(16,1)],'blue-force':[(16,2)]}
labels={'main-long':'主属性+200%','growth-single':'每秒主属性+4%','cd-short':'冷却−12.5%','damage-long':'坚固伤害+600%','hits-long':'攻击段数+6','charge-short':'使用→另一端加速2秒','cd-single':'冷却−10%','damage-short':'伤害+200%','calibration-single':'伤害+120%','blue-force':'附魔力量+4'}
order=[next(g for g in source['equipment'] if g['id']==gid) for gid in chosen['order']]
ports={(i*4+x,y):g['id'] for i,g in enumerate(order) for x,y in g['ports']}
ends={p for pts in points.values() for p in pts}
audit=[dict(point=p,owner=g,state='connected' if p in ends else 'blocked' if any(len(pts)>1 and pts[0][1]==p[1] and min(q[0] for q in pts)<p[0]<max(q[0] for q in pts) for pts in points.values()) else 'free') for p,g in ports.items()]
counts={s:sum(p['state']==s for p in audit) for s in ['connected','blocked','free']}
assert counts=={'connected':16,'blocked':2,'free':3}
actual=dict(day=17,wins=14,losses=2,gold=12,level=15,hp=191000,battleStarted=False,order=chosen['order'],placements=[dict(part=k,label=labels[k],points=v) for k,v in points.items()],portAudit=audit,portCounts=counts,
 observedEquipment=[dict(slot='back',name='S曙光盾',shieldShown='806',cooldownShown=5.2,firm=52),dict(slot='armor',name='S塞玛·量产',shieldShown='3.8K',cooldownShown=11.4,firm=82),dict(slot='shoulder',name='SS链法手枪',damageShown='7.2K',hits=9,cooldownShown=6.9,firm=30),dict(slot='hand',name='S虚空撕裂',damageShown='5.7K',hits=10,cooldownShown=2.6,firm=4),dict(slot='drone',name='S式神野衾',damageShown='477',force=14,cooldownShown=7.1)],
 inventory=['旧B深红尊','旧B祸津神'],economy='60 + 出售闲置S神速16 − 曙光32 − 塞玛32 = 12',
 evidence=E+'day17-verified-layout.jpg',unknowns=['未战斗；不能宣称最强或保证比旧配置赢率高','蓝附魔在坚固背甲未成功安装，是否赋予力量条件标签未知；无人机+4成功','首击、随机加速目标与刷新/叠加规则未观察','无人机显示值138/265/350/477不能由原输入111与统一10%加成准确解释，保留实测查表，完整来源未核'],
 modelCorrections=['原手工候选漏掉无人机同件双孔200%桥与左中120%单孔可共存；最终全部10配件使用','S甲孔位以本轮左上/左中/左下/右中为准，旧报告右上误读','不从单张已加成卡面反推统一基础伤害；机实测无伤害件138，仅120%265，仅200%350，两件477'],
 timing=dict(startedAt='2026-11-17T03:50:57.705Z',verifiedAt='2026-11-17T04:08:13.461Z',seconds=1035.756,scope='本次整排优化：批采、离线比较、交易、拖放重试及最终验收；不含后续归档，不是完整游戏日',fullGameDaySeconds=None))
save(out/'day17-actual-loadout.json',actual)

svg=['<svg viewBox="0 0 1080 320" role="img" aria-label="最终插槽图">']
names=['S曙光背','S加速甲','SS链法肩','S虚空手','S力量机']
for i,n in enumerate(names):svg.append(f'<rect x="{15+i*212}" y="25" width="195" height="265" rx="12" fill="#1c3046"/><text x="{30+i*212}" y="55" fill="white">{n}</text>')
colors=['#f6c969','#f6c969','#66caf1','#cb88ed','#f6c969','#72dfb6','#66caf1','#cb88ed','#f6c969','#72dfb6']
def xy(p):return (55+p[0]*53,105+p[1]*70)
for c,(pid,pts) in zip(colors,points.items()):
 if len(pts)>1:
  (x,y),(xx,yy)=map(xy,pts);svg.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="{c}" stroke-width="9"><title>{labels[pid]}</title></line>')
for a in audit:
 x,y=xy(a['point']);color={'connected':'#72dfb6','blocked':'#e78a81','free':'#6e8196'}[a['state']]
 svg.append(f'<circle cx="{x}" cy="{y}" r="12" fill="#102030" stroke="{color}" stroke-width="3"><title>{a["owner"]} {a["point"]} {a["state"]}</title></circle>')
svg.append('</svg>')
rows=''.join('<tr><td>'+html.escape(labels[k])+'</td><td>'+html.escape(str(v))+'</td></tr>' for k,v in points.items())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第17天最终配装验收</title><style>body{max-width:1100px;margin:auto;padding:24px;background:#101c2b;color:#e5edf4;font:16px/1.65 system-ui}a{color:#8bcbff}section{padding:20px;background:#17273c;margin:18px 0;border-radius:12px}img,svg{width:100%}td,th{padding:8px;border-bottom:1px solid #435368;text-align:left}table{width:100%;border-collapse:collapse}svg text{font-size:19px}</style><h1>第17天：双核互加速，配件全部落位</h1><p>14胜2负 · Lv15 · 191000生命 · 剩12金 · 本配置尚未出战。</p><p><a href="rsi-workflow.html">RSI记录</a> · <a href="loadout-selected-day17.html">原候选比较（含被反驳预测）</a> · <a href="../runs/run05/day17-actual-loadout.json">最终结构化数据</a></p><section><h2>实际装备与孔位</h2>'''+''.join(svg)+'''<p>绿圈16个已连接；红圈2个被桥身遮挡；灰圈3个空孔。肩右下被多段桥遮挡，手左中被伤害桥遮挡。空孔在背左上、甲左上/右中。10件配件全部已装，没有闲置配件。</p><p>肩与手同时共享：+6段长桥、坚固+600%伤害长桥、使用时互相加速2秒短桥。肩独享−10%冷却。背甲共享主属性+200%和−12.5%冷却；成长单孔给背。无人机顶部自桥+200%只算一件受益，左中火控+120%，左下力量+4。</p></section><section><h2>实际显示值</h2><table><tr><th>装备</th><th>主属性</th><th>段数</th><th>冷却</th></tr><tr><td>S曙光背</td><td>806盾 / 52坚固</td><td>—</td><td>5.2秒</td></tr><tr><td>S塞玛甲</td><td>3.8K盾 / 82坚固</td><td>—</td><td>11.4秒</td></tr><tr><td>SS链法肩</td><td>7.2K伤害 / 30坚固</td><td>9</td><td>6.9秒</td></tr><tr><td>S虚空手</td><td>5.7K伤害 / 4坚固</td><td>10</td><td>2.6秒</td></tr><tr><td>S式神机</td><td>477伤害 / 14力量</td><td>召唤1</td><td>7.1秒</td></tr></table><p>冷却是静态UI显示值，不是实际首次有效命中时间。</p></section><section><h2>选择依据与代价</h2><p>让已有快手直接带动肩炮，减少加速先经过无人机的依赖；曙光的坚固成长与全体减速，配合塞玛获得坚固时的随机加速，为肩输出创造候选窗口。随机加速不能保证落到肩，也不是直接充能2秒。尚未观测整条战斗链。</p><p>出售未上阵的S神速+16，购买曙光与塞玛各32：60+16−64=12。旧B背甲留库。新甲/背初始盾和原构筑静态总轮伤害较低，放弃旧物伤产盾与力量被动，换取控制、坚固成长、加速与槽位；这项取舍尚未经实战验证。</p></section><section><h2>模型与操作修订</h2><p>1680种装备顺序、44512个最终布局的搜索仍不是全局最优。手工选定后也遗漏了无人机自桥与左中单孔可共存，实装时修正，原预测保留。此后固定核心桥后必须审计每个剩余孔与库存单孔，不以一份候选表结束优化。</p><p>无人机无伤害件138，仅120%火控265，仅200%短桥350，两件合用477；原统一基础值反推不准确，保留实测查表，不伪造已解释公式。蓝附魔最终在力量机成功，不能据此前坚固背甲的拖入失败断言属性限制。</p><p>多次拖放失败；部分在清除说明、等待界面稳定、调整拾取点/槽心后成功。尚未隔离根因，不新增确定游戏Bug。副作用和失败截图均保留。</p><p>本次批采→比较→购买→实装验收17分16秒，含分析和重试；不是完整一天，后续归档未计入。速度仍受装配失败和候选补漏影响。</p></section><section><h2>最终现场</h2><a href="'''+E+'''day17-verified-layout.jpg"><img src="'''+E+'''day17-verified-layout.jpg" alt="第17天最终装配与库存"></a></section></html>'''
(docs/'loadout-verified-day17.html').write_text(page,encoding='utf-8')
for filename in ['loadout-selected-day17.html','loadout-live-day17.html']:
 p=docs/filename;s=p.read_text(encoding='utf-8');s=s.replace('<body>','<body><p><a href="loadout-verified-day17.html">最终实装：全部10配件已用，余12金；原候选未覆盖全部改进</a></p>',1);p.write_text(s,encoding='utf-8')
data=json.loads((root/'data/playtest.json').read_text(encoding='utf-8'))
r=next(r for r in data['runs'] if r['id']=='run05');r.update(wins=14,losses=2,result='进行中：第17天配装完成，14胜2负，12金，未出战')
day=next(d for d in r['days'] if d['day']==17)
day.update(title='第17天 · 双S背甲与双核互加速配装完成',phase='配装验收完成，未出战',wins=14,losses=2,after='60金出售库存S神速+16，购买S曙光与S塞玛各32后12金。背—甲—肩—手—机；手5.7K×10/CD2.6，肩7.2K×9/CD6.9；全部10配件已用，16孔连接2孔遮挡3孔空闲。旧B背甲保留，未战斗。')
day['detailHtml']=day.get('detailHtml','')+'<p><a href="loadout-verified-day17.html">最终实装插槽图、数值、预算与模型反例</a>：10件配件全部已装备，余12金。实装优化17分16秒，非整日。</p>'
study=next(s for s in data['opponentStudies'] if s['id']=='run05-d16');study.setdefault('adoption',[]).append(dict(runId='run05',day=17,decisionId='run05-d17-02',result='采用坚固与随机加速候选链、核心互加速；仅装配已验，战斗效果待核',href='loadout-verified-day17.html'))
m=next(m for m in data['memories'] if m['id']=='M05');old=copy.deepcopy({k:v for k,v in m.items() if k!='history'});m['revision']+=1
change='第17天原候选漏无人机同件双孔伤害桥与空闲单孔共存，实装补全10配件。'
m['action']+=' 核心桥确定后再做剩余孔审计：枚举同装备双孔桥与其余单孔共存，逐个确认闲置配件是否仍有净收益，避免手工候选遗漏。'
m['caveat']+=' 第17天原手工候选漏无人机200%自桥+120%单孔，不能把大规模搜索或手工精选宣称全局最优。'
m['evidence'].append(dict(runId='run05',day=17,note=change,href='loadout-verified-day17.html'));m['history'].append(dict(date='2026-11-17',revision=m['revision'],change=change,previous=old))
data['updatedAt']=datetime.now(timezone.utc).isoformat();save(root/'data/playtest.json',data)
snap='2026-11-17 最新停点：run05第17天配装完成，14胜2负，Lv15/191000HP/12金，未出战。售库存S神速16，买S曙光与S塞玛各32。顺序背—甲—SS肩—S手—S无人机；手5.7K×10/CD2.6，肩7.2K×9/CD6.9，机477/14力量/CD7.1；背806盾/CD5.2，甲3.8K盾/CD11.4。全部10配件已用，16孔连接2孔遮挡3孔空闲；库存旧B背甲保留。最终图及端点见[配装验收](docs/loadout-verified-day17.html)。蓝附魔在机左下成功，甲/背失败不能推断机制限制。原候选遗漏机自桥+火控并存，M05r12修订。批采至验收17分16秒，非整日。下一步先新图、查敌与记录预测，尚无此配置战绩。'
for fn,marker in [('README.md','## 当前进度'),('GAME-NOTES.md','## 本局快照')]:
 p=root/fn;s=p.read_text(encoding='utf-8').replace(marker+'\n',marker+'\n\n'+snap+'\n',1)
 if fn=='README.md':s=s.replace('## 工作日志\n','## 工作日志\n\n- 2026-11-17 第17天整排优化：4条决策先prepare后操作，完成交易和10配件实装；16连2挡3空。保留机数值预测反例和拖放失败，M05r12记录候选补漏；无新增确认游戏Bug。实际17分16秒，不是一天用时。下一步战前查敌、记录核心首次有效出手预测。\n',1)
 p.write_text(s,encoding='utf-8')
print(json.dumps({'counts':counts,'gold':12,'parts':len(points),'battleStarted':False},ensure_ascii=False))
