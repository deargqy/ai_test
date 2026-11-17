"""Append the postbattle review without altering prebattle predictions."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[2]
p=root/'data/playtest.json'
d=json.loads(p.read_text(encoding='utf-8'))
e='playtest-2026-11-16-run05/'
changes={
 'M01':('run05第15天双方科技确认开场禁用与加速重叠，首次命中仍未知。',
        ' 显式列出双方开场控制与加速的重叠区间；随机充能按目标分支，不能保证给核心，也不能直接从CD减掉持续时间。',
        ' 第15天敌开场禁用2.5秒、我全装加速3秒同时存在；该战是玩家操作，只得战后统计，不能由胜利倒推首击时间。',e+'day15-tech-enemy-3.jpg'),
 'M02':('run05第15天补入无直接输出但有支援贡献的反例。',
        ' 伤害榜与支援账本分开：追踪属性提供者、被动产盾/转伤、加速受益装备及触发条件。没有主动统计行不能排除被动价值；配件收益比较替换前后的整条链，而非按历史伤害占比分配。',
        ' 第15天无人机伤害无行但提供48力量；甲无盾行仍带力量被动。不能把“无战报直接贡献”误用为“被动无贡献”；敌甲随机加速触发目标未读到。',e+'day15-result-buffs.jpg'),
 'M05':('第15天战报末态完成逐孔审计：17孔16连1挡，肩5孔全用；离线比较四方案。',
        ' 每个候选同时列孔总数、已连接、桥身遮挡、真正空闲和固定附魔；安装成功与触发有效分别评价。被挡孔的代价由替代布局和可用配件决定，不设统一罚分。',
        ' 本场17孔中16连接、1被挡、0空闲；不能沿用旧布局肩右两孔未用的判断。火控换手使静态完整轮+2.3%却失去手10%CD，尚未实战，不判更强。', 'combat-review-day15.html'),
 'M07':('修复已验证S力量无人机伤害桥漏算；战报计数/完整段数分离。',
        ' 已验证召唤实例用acceptsDamagePct能力纳入伤害配件，未验证实例不推广。多段完整轮是能力上限；统计x次数不当施法数，战后成长后的数值不回填开场。',
        ' 第15天肩95×9=855完整轮假设与统计285不一致，实际段数/截断/统计口径未核，不能直接判Bug。护盾统计也不直接拿雷伤×2对账。',e+'day15-result-own-shoulder.jpg')}
for mid,(change,action,caveat,href) in changes.items():
 m=next(m for m in d['memories'] if m['id']==mid)
 if any(h.get('change')==change for h in m['history']):continue
 previous=copy.deepcopy({k:v for k,v in m.items() if k!='history'})
 m['revision']+=1
 if mid=='M07':
  m['caveat']=m['caveat'].replace(' 通用tools/loadout.py当前damage_pct仍排除kind=summon；第15天比较报告用截图人工修正298与受益端点，并未假装工具已修好。',' 通用工具现已按明确实例能力修复漏算，旧第15天比较页保留为历史版本；新战后页使用修复后的求解器。')
 m['action']+=action;m['caveat']+=caveat
 m['evidence'].append(dict(runId='run05',day=15,note=change,href=href))
 m['history'].append(dict(date='2026-11-17',revision=m['revision'],change=change,previous=previous))

r=next(r for r in d['runs'] if r['id']=='run05')
r.update(wins=14,losses=1,result='进行中：14胜1负，第16天；玩家已完成第15天，当前优先离线优化插槽与战斗模型')
day=next(x for x in r['days'] if x['day']==15)
day.update(title='第15天 · 玩家胜Ranka0423，双核与支援链复盘',phase='已结算（玩家操作战斗）',outcome='win',wins=14,losses=1,
 after='玩家手动胜Ranka0423；手102003、肩92513，共194516；敌共25305，其中感电16697。己方背盾3280，甲无盾行；无人机提供48力量。实际末态肩5孔全连接，全排17孔16连接1遮挡0空闲。战报已确认火控在无人机右上、蓝色在甲右下。未观察首击、全程时长与结算剩余生命；不补写自主预测。后续切页与操作由玩家确认手动。')
day['detailHtml']+='<p><a href="combat-review-day15.html">本场战后复盘与修复后的四方案比较</a>：先批采双方装备/科技和三类战报。原“未出战/单孔待核”是此前停点，现由玩家战斗结果补充，旧决策预测与操作未知保留。新增M01r5/M02r6/M05r11/M07r6；本场没有自主战前预测，不计方向命中率。</p>' if 'combat-review-day15.html' not in day['detailHtml'] else ''
if not any(x['day']==16 for x in r['days']):
 r['days'].append(dict(day=16,title='第16天 · 玩家操作中，离线模型优化优先',phase='事件/商店（玩家操作）',outcome='unknown',wins=14,losses=1,before='',after='最近可见14胜1负/Lv15/191000HP/70金币。玩家确认中途切页与操作为手动；当前不自主购物或开战，优先插槽和战斗模型。现场可能已继续变化，恢复控制前需新截图。',detailHtml='<p><a href="playtest-2026-11-16-run05/day16-live-after-result-capture.jpg">最后可见现场</a>；当前复盘见<a href="combat-review-day15.html">第15天模型修订</a>。</p>',sources=[],images=[],decisions=[],legacyUsage=''))
d['updatedAt']=datetime.now(timezone.utc).isoformat(timespec='seconds')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

snapshot='2026-11-17 最新停点：run05已14胜1负；玩家手动完成第15天胜Ranka0423，当前第16天，最近图Lv15/191000HP/70金币。用户明确优先优化配件插槽与战斗模型，游戏由玩家先自行操作；恢复控制前须新截图。战报与双方10件装备/10项科技已批采，敌配件详情未采全；中途切页与操作已由玩家确认手动。手102003、肩92513，敌总25305；无人机48力量不能因无伤害行忽略。末态17孔16连接1遮挡0空闲，肩5孔全连接；火控机右上、蓝色甲右下已核。修复S无人机damage_pct漏算，11项测试通过；四个离线候选不称最强。M01r5/M02r6/M05r11/M07r6已更新。首击、战斗时长、段数兑现及统计口径仍未知，不补写本场战前预测。[战后模型与插槽图](docs/combat-review-day15.html)。'
for fn,marker in [('README.md','## 当前进度'),('GAME-NOTES.md','## 本局快照')]:
 path=root/fn;s=path.read_text(encoding='utf-8')
 if snapshot not in s:s=s.replace(marker+'\n',marker+'\n\n'+snapshot+'\n',1)
 if fn=='README.md':
  entry='- 2026-11-17 第15天战后：批采三类统计、双方装备与科技；确认玩家14胜1负。修复离线S无人机伤害桥漏算（失败106→预期298，再修复通过），11项测试通过；新建战斗链与17孔审计页，重算四个布局。玩家确认切页/操作手动。无新增已确认游戏Bug；下一步优先验证控制重叠、随机充能、有效段数与支援边际收益。'
  if entry not in s:s=s.replace('## 工作日志\n','## 工作日志\n\n'+entry+'\n',1)
 path.write_text(s,encoding='utf-8')

log=root/'runs/run05/day15-model-revision.md'
s=log.read_text(encoding='utf-8')
s+='\n\n## 用户澄清与验证结果\n\n用户随后明确“中间的操作没有问题我先自己操作了”，因此页面切换和手动操作已归因玩家；不作为游戏Bug。仍保留采集边界，错误页面截图不得作为敌配件证据。优先离线优化插槽与战斗模型，不继续自主购物/开战。\n\n修复后11项单元测试通过。当前快照明确启用acceptsDamagePct，原伤害短桥从106正确算为298；加本日火控后336，与第15天切页画面相符。未知召唤保持排除；召唤频率不明，未伪造DPS。四个整排候选通过孔位/桥身冲突检查，实际布局17孔16连1挡0闲。战斗模型增加控制重叠、随机充能分支、支援链与有效段数约束，没有宣称完整模拟或校准胜率。\n'
log.write_text(s,encoding='utf-8')
print('archived run05 day15 result, day16 snapshot and four memory revisions')
