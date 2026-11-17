"""Preserve sourced loss lessons in the existing canonical data and offline page."""
import datetime,html,json,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
p=root/'data/playtest.json';d=json.loads(p.read_text(encoding='utf-8'))
# Mechanism / transferable idea / unknown prerequisite / prospective test.
notes={
('run01',2):('Kazeron：护盾与恢复拖过我方输出','敌同一增益统计盾与回复各8767；我的输出未完成击杀。','学习同时提供续航的来源，而非只补血量；先识别触发条件再采购。','额外生命及该增益的完整来源未知；回复可能含最大生命增长，不能全部算有效治疗。','下次相似敌先查增益来源，预测前两轮是否能净削血。'),
('run01',4):('高频叠盾压制','敌累计盾274220，结束仍有223969；我方主武输出增长仍未穿盾。','学习“持续属性供应→产盾”的循环，查是否还能把盾转进攻。','该场完整科技/被动链未收齐；不能仅靠累计盾量反推触发频率。','相似敌分别预测首盾与第二轮净盾变化，不将初始HP当全部耐久。'),
('run01',5):('燃烧持续伤害超过我方压力','敌燃烧65139；我手23915、肩12014。','学习状态伤害的供应与持续结算，避免只比较物理面板。','叠层来源、额外结算和控制的精确链缺证据。','遇到相似燃烧敌先读叠层/结算/充能来源，预测哪个来源先启动。'),
('run01',10):('huerowakame：失盾转伤多段手','S虚空撕裂失盾12%转伤，末场29.2K七段，手统计230984。','最小功能组合：持续产盾＋可消耗的盾＋失盾转伤手＋多段；这也可用于我方构筑。','敌产盾完整来源、动画时序和有效伤害未隔离；42k初始HP不是易打证据。','采用时在首盾前后读手伤害变化；若没失盾就不预期转伤。'),
('run02',4):('寄生阈值把减速转禁用','S寄生背在寄生超过250时消耗一半把减速转禁用；A手有寄生削减最大生命。','学习“阈值供应→控制升级→削生命”的链，配件应服务叠层频率。','实际达到阈值的时间与禁用对象未完整捕获；旧治疗数字不能全当有效恢复。','下次预测到250层的区间与首次禁用；未达阈值时不得按硬控估计。'),
('run02',6):('全力量供应与转盾','敌A力量背每次使用让全部力量装+10力量，B科技伤害6%转盾；敌肩末场23800。','学习同属性装备共享增长、把伤害反馈为防御；开场力量只是起点。','防御统计口径待核；每次背使用的实际频率未知。','比较双方第二次背/主核使用后的面板增长，检验持续供应是否超过开场优势。'),
('run02',12):('青一色：燃烧成长与高额护盾','我刀180904、肩111640仍败；敌背统计220899盾，另有22634与3283盾。','学习输出与产盾共同成长；先确认敌背的触发条件，而非再单纯堆物理总伤。','燃烧到护盾的具体映射该条记录不足，不能用累计量当瞬时盾或全部有效吸收。','预测首盾之后净伤害是否为正，核对实际消耗盾与终场剩盾。'),
('run02',16):('C4C：成长力量武器与周期禁用','敌SS成长力量刀，SS每3秒随机禁用3秒；我伤害/治疗栏空，敌肩137214刀125749。','学习先手控制保护成长启动；对我方先补可用的首次出手条件。','缺每次控制对象和完整命中时间线，不能认定禁用为唯一败因；大面板不是已发生输出。','明确预测主核能否出手及区间；遇同类优先保留控制目标/首击证据。'),
('run03',1):('低阶燃烧与生命优势','敌燃烧8320；我输出10837仍败，起始7500对12500生命。','学习低阶也能靠状态供应与生存形成压力，不按装备阶级直接选敌。','精确首击与完整燃烧链未知；若茜50%初始充能不代表全程CD减半。','分开预测先手与击杀所需轮数，检查较快首击能否转为实际优势。'),
('run03',2):('燃烧伤害加恢复维持战线','敌肩9948、燃烧5341，回复4896、盾2722；我总伤6915。','学习输出与续航兼备的组合；我方配件应覆盖实际核心与新甲有效孔。','回复与盾都是累计，不能直接相加当全部有效抵消；等级/HP/装配同时混杂。','先优化现装配件端点，再预测核心两轮输出；不据两败认定寒冷弱。'),
('run04',1):('我方生存改善但击杀能力不足','我双端盾甲2700背2800，寄生栏5771，伤害仅5406；正式结算失败。','该战优先学的是构筑平衡：有效供盾也要有足够杀伤或成长来源。','敌完整致胜链与终场未捕获，不能编造敌套路或把寄生栏当有效治疗。','下次同时记录终场条件和两方主伤害；缺敌资料时保持“未知”，只改善已证实缺口。'),
('run04',8):('初始力量→命中百分比增长→力量转伤肩','开场225力量；SS剑命中力量+15%；肩每力量伤害+5；力量伤害桥+300%、刀背互充0.5秒。敌肩131100、刀52280，我甲未产盾。','可借鉴的核心角色：启动力量供应、百分比增长武器、按力量转伤输出、段数/充能。不是只换一个力量图标。','单配件净收益及精确首击时序未隔离；是否可凑齐与成本需现场比较。','采用或对阵时预测前两轮力量与主伤害来源，先检验活过首轮。'),
('run04',9):('神秘：燃烧叠层—充能—召唤—额外结算','SS斧命中燃烧+15%；燃伤给肩充1.4秒、全燃装+3燃烧；每累计施加140燃烧召无人机；甲每1.8秒按层数额外结算。敌燃烧94126，手50171，肩26208。','学习闭环的功能顺序：种子叠层→按命中增长→燃伤反馈充能/增长→额外结算；可逐步成型。','每环独立贡献、召唤频率和我方削增益净效果未分离；不等于所有部件都必需。','先收齐至少种子与反馈两环，再预测重复触发；对手完整成型时不只算首轮面板。'),
('run05',13):('林弦：先手六连力量成长与物伤产盾','敌1–2秒首次有效伤害，约3秒我HP归零；手169102伤害、雷电64、背146599盾，敌满227000HP；我伤害和盾栏空。','优先学习实际短链：450初始力量→快速六连击每命中力量+10%→物伤产力量等额盾；快速背叠力并减速保护连击。','背/手显示1秒CD的形成来源未明，不能当同名装备基础CD；精确每次施法次数不可从战报x12/x19直接读出。','拿到相似组件时先核可达到的CD，再写首击与第二轮预测；如果仍5–7秒启动，不宣称已复刻该快攻。')}
studies=[]
for run in d['runs']:
 for day in run['days']:
  if day.get('outcome')!='loss':continue
  key=(run['id'],day['day']);title,observed,learn,unknown,test=notes[key]
  images=day.get('images',[])[:]
  if key==('run05',13):
   images=[{'src':'playtest-2026-11-16-run05/'+x+'.jpg','label':label} for x,label in [
    ('day13-enemy3-settled','敌方全套与卡序'),('day13-ec-g4','六连与命中力量+10%'),
    ('day13-ec-g0','背部物伤产盾与减速'),('day13-ec-t4','开场450力量'),
    ('day13-ec-p15','共享+3段'),('day13-ec-p16','力量伤害+600%'),
    ('day13-fight-14','约3秒我方归零'),('day13-stats','伤害统计'),('day13-defense','防御统计'),('day13-buffs','增益来源')]]
  s=dict(id=f"{run['id']}-d{day['day']:02d}",runId=run['id'],day=day['day'],title=title,
         origin='player-requested-retrospective',status='本战触发链已分析，复现待验证' if key==('run05',13) else '既有复盘二次提炼，缺项明确保留',
         observed=observed,transferable=learn,unknown=unknown,nextPrediction=test,evidence=images,
         adoption=[])
  if key==('run05',13):
   s['chain']=['SS突进V开场450力量','手部六段；每命中力量+10%，力量伤害/每日成长伤害桥放大物理输出',
               '背部：物伤触发力量等额盾；主动给力量并减速全敌装2秒；配件增加防御施法与盾',
               '我方核心未产生有效伤害与护盾，约3秒被结束']
   s['dependencies']=['核心：快速多段成长手、开局力量、伤害放大、快速背的减速与物伤产盾。仅为本战解释，尚无移除对照证明必要性。',
                      '配件已见：手肩共享+3段、力量伤害+600%、成长伤害桥+480%；背甲共享+600%及+1200%盾、背额外防御施法。',
                      '背/手1秒CD是复现瓶颈：当前可见配件没有直接解释其全部降幅，可能还有历史强化，但来源未知。',
                      '甲减伤、肩十段、无人机吸血有纸面后续价值，本场没有对应统计贡献，不归为已兑现胜因。']
   s['response']=['购物阶段先改善首次有效行动与控制条件；多升一级和追加伤害都不能保证跨过3秒死亡门槛。',
                  '避开已确认极快成长/控制链是候选，但免费换敌可能更差：本次最后换到林弦，不证明换敌必然改善。',
                  '不要照抄整套21配件；先在离线模型里找核心所需有效端点，随后核实真实CD与启动。']
  studies.append(s)
# Retain any later adoption records when rebuilding this historical collection.
old={s['id']:s for s in d.get('opponentStudies',[])}
for s in studies:
 if s['id'] in old:s['adoption']=old[s['id']].get('adoption',[])
d['opponentStudies']=studies
m=next(m for m in d['memories'] if m['id']=='M02')
if m['revision']==4:
 old_m={k:v for k,v in m.items() if k!='history'}
 m['revision']=5
 m['action']+=' 每次战败拆解获胜对手实际兑现的最小触发链，记录核心/可替代部件、配件端点、启动来源与成本，形成可检索的候选套路；购物和构筑时调用，实际采用后回填验证。'
 m['caveat']+=' run05第13天偏败方向命中，但约3秒零输出反驳我方首击区间。敌1秒CD来源未解释，不能照搬同名装备当可复现快攻；对手存在却无战报贡献的组件不直接算胜因。'
 m['status']='已有偏败方向命中与启动反例；胜率仍未校准，敌方套路复现待验证'
 m['history'].append(dict(date='2026-11-17',revision=5,change='玩家要求每个获胜对手均复盘，新增14败局套路索引，run05林弦拆分实际短链与未验证配置。',previous=old_m))
 m['evidence'].append(dict(runId='run05',day=13,note='林弦约3秒获胜；我无伤害无盾，手169102/背146599；1秒CD来源待验证',href='opponent-studies.html#run05-d13'))
d['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
e=html.escape
page=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>击败我们的对手 · 套路与复现条件</title><link rel="stylesheet" href="playtest.css"><body><header><h1>击败我们的对手</h1><nav><a href="play-flow.html">每日流程</a><a href="loadout-lab.html">组合实验室</a><a href="rsi-workflow.html">RSI记忆</a></nav></header><main><section><h2>从败局学可复现的机制</h2><p>14场已记录败局均有条目。历史条目依据既有复盘二次提炼，未重新逐张审计旧图；缺失的敌方链保持未知。最新林弦战按战前词条、过程和三页战报拆解。没有移除对照，不把关联写成必需性证明。</p><p>每次记录：实际胜因 → 启动/循环/核心配件 → 我方缺口 → 可复制的最小功能组合 → 成型成本与未知 → 下次战前预测 → 实际采用结果。尚无条目完成整套复现，不能称已掌握或保证下次获胜。</p></section>']
for s in reversed(studies):
 page.append(f'<section id="{e(s["id"])}"><h2>{e(s["id"])} · {e(s["title"])}</h2><p><small>{e(s["status"])}</small></p>')
 for label,field in [('实际证据','observed'),('能学什么','transferable'),('复现瓶颈 / 未知','unknown'),('下一次要检验的预测','nextPrediction')]:page.append(f'<p><b>{label}：</b>{e(s[field])}</p>')
 if 'chain' in s:page.append('<p style="padding:16px;background:#e8eedf;line-height:2">'+'<br>↓<br>'.join(e(x) for x in s['chain'])+'</p>')
 for field,label in [('dependencies','核心与备用环节'),('response','采购与应对')]:
  if field in s:page.append(f'<h3>{label}</h3><ul>'+''.join('<li>'+e(x)+'</li>' for x in s[field])+'</ul>')
 page.append('<p><a href="rsi-workflow.html#runs/'+e(s['runId'])+'/'+str(s['day'])+'">原对局与当时预测</a> · '+' · '.join(f'<a href="{e(x["src"])}">{e(x["label"])}</a>' for x in s['evidence'])+'</p></section>')
page.append('</main></body></html>')
(root/'docs/opponent-studies.html').write_text(''.join(page),encoding='utf-8')
assert len(studies)==sum(day.get('outcome')=='loss' for r in d['runs'] for day in r['days'])
for s in studies:
 for image in s['evidence']:assert (root/'docs'/image['src']).is_file(),image['src']
print(json.dumps({'lossesCovered':len(studies),'latestDetailed':'run05-d13','historicalBasis':'existing written reviews','gameInput':'none'},ensure_ascii=False))
