"""Archive a visible postbattle review; no retrospective prebattle prediction."""
import copy
import html
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/run05'
DOCS=ROOT/'docs'
E='playtest-2026-11-16-run05/'
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def evidence(name,label):return dict(src=E+name+'.jpg',label=label)

parts=[
 ('armor-back-top','甲—背上排','重型护盾校准器','护盾+640%，每天再+160%','shield_growth',6.4),
 ('armor-back-mid','甲—背中排','坚固','使用一端为另一端直接充能2秒','instant_charge',2),
 ('armor-back-bottom','甲—背下排','标准型护盾校准器','护盾+800%，每天再+80%','shield_growth',8),
 ('armor-single','甲单孔','齐射','主属性+100%','main_pct',1),
 ('back-hand-mid','背—手中排','坚固','使用一端为另一端直接充能0.25秒','instant_charge',.25),
 ('back-hand-bottom','背—手下排','标准型循环校准器','冷却-20%，每天再-2.5%','cd_pct',-.2),
 ('hand-shoulder-top','手—肩上排','军械库','进攻型装备伤害+800%','damage_pct',8),
 ('hand-single','手单孔','继电器','附魔16坚固','firm_enchantment',16),
 ('hand-shoulder-bottom','手—肩下排','生命偷取','攻击段数+3','hits',3),
 ('shoulder-single','肩单孔','生命偷取','攻击段数+3','hits',3),
 ('shoulder-drone-mid','肩—无人机中排','力场猛攻','伤害+400%；坚固装备改为+1200%','conditional_damage_pct',12),
 ('shoulder-drone-bottom','肩—无人机下排','标准型屏障增幅器','元素+72%；坚固改为+216%','conditional_element_pct',2.16),
 ('drone-top','无人机自身上排两孔','轮转','使用一端使另一件元素+64%；同件两孔是否触发未知','element_growth_unverified',.64),
 ('drone-single','无人机单孔','军械库','进攻型装备伤害+200%；此SS召唤受益未隔离验证','damage_pct_unverified',2)]
owntech=['全部装备主属性+10%','开场全部装备加速3秒','每秒8力量','开场375力量','每3秒随机一件装备直接充能3秒']
enemytech=['每3秒随机一件装备直接充能1秒','每当任意装备被使用，对同一槽位敌方装备禁用0.9秒','最大生命+20%','最大生命+12500','每3秒随机敌装禁用3秒']
gear=[
 dict(id='armor',name='S 塞玛·量产',cdObserved=13,rawShieldObserved=1332,firmPerApplication=130,
      passive='获得坚固→随机一件装备加速2.5秒',active='超载IV、盾、坚固',directStat='无主动盾行；不能推导被动未触发'),
 dict(id='back',name='SS 英勇盾',cdObserved=4,rawShieldObserved=342,firmPerApplication=70,
      passive='坚固每秒还提供+2最大生命',active='减速全部敌装3秒；盾与坚固',directStat='10808盾、140坚固'),
 dict(id='hand',name='SS 熵',cdObserved=2.2,rawDamageObserved=428,hitsShown=7,firmPerApplication=23,
      passive='命中自身坚固+15%',active='多段伤害及坚固',directStat='31504伤害、556坚固'),
 dict(id='shoulder',name='SS 链法手枪',cdObserved=8,rawDamageObserved=6660,hitsShown=9,firmPerApplication=97,
      passive='每层坚固使本装备伤害+6',active='多段伤害及坚固',directStat='281106伤害、291坚固'),
 dict(id='drone',name='SS 侍灵·量产',cdObserved=7,
      passive='召唤物命中：敌方防御型装备-20护盾，己方获得+20',active='召唤',directStat='伤害/增益无行；未将纸面能力计为已兑现胜因')]

review=dict(runId='run05',day=16,opponent='Rogas',operator='player',outcome='loss',wins=14,losses=2,
 phase='postbattle statistics; not advanced',reward=dict(gold=78,income=70,interest=8,xp=2,lifeChange=-1),
 prebattlePrediction=None,firstHitSeconds=None,durationSeconds=None,
 displayedHp=dict(own=191000,enemy=275400,enemyShield=5404,meaning='result UI labels, not verified initial or remaining HP; enemy has max-HP growth'),
 armorActuallyEquipped='B 祸津神; offered S armor is not equipped in this battle',
 damage=dict(own=dict(hand=141488,shoulder=None,drone=None),enemy=dict(shoulder=281106,hand=31504,drone=None)),
 defense=dict(own=dict(backShield=1652,firmShield=44,armor=None),enemy=dict(backShield=10808,firmShield=584,buffPlus=1168,techPlus=234,armor=None)),
 buffs=dict(own=dict(openingForce=375,periodicForce=48,droneForce=48,handFirm=32,otherTechFirm=1,shoulderFirm=None),
            enemy=dict(handFirm=556,shoulderFirm=291,backFirm=140)),
 nullMeaning='No displayed row; never proof of no passive contribution or complete absence of action',
 counters=dict(ownHand=29,enemyHand=32,enemyShoulder=1,note='UI counters, not complete cast counts'),
 ownTech=owntech,enemyTech=enemytech,enemyEquipment=gear,
 enemyParts=[dict(id=a,connection=b,name=c,text=d,effectKind=e,value=f,evidence=E+'day16-part-'+a+'.jpg') for a,b,c,d,e,f in parts],
 evidence=[evidence('day16-loss-resume','失败结算'),evidence('day16-loss-damage','伤害'),evidence('day16-loss-defense','防御'),evidence('day16-loss-buffs','增益')],
 observedComparisons=dict(enemyDamage=312610,ownDamage=141488,enemyShoulderDamageShare=round(281106/312610,4),
                         shoulderHitsShown=dict(own=9,enemy=9),
                         damageMultipliers=dict(own=9.1,enemy=21,ratio=round(21/9.1,4),
                           basis='own1+.1+6+2; enemy1+8+12, additive modifiers only, not whole-battle damage ratio'),
                         ownShoulderPortCount=5,ownShoulderConnectedPortCount=5,
                         ownCooldownObserved=dict(back=6.6,armor=10.1,hand=4.1,shoulder=7.7,drone=7.1)),
 causalAssessment=[
  dict(confidence='observed',claim='我手输出已启动，但肩没有伤害或坚固行；不能把几何接满与9段潜力当已兑现输出。'),
  dict(confidence='observed',claim='敌肩占其伤害89.9%；两条已读伤害桥共同服务肩，另有两处+3段及元素强化。'),
  dict(confidence='mechanism-supported inference',claim='快手坚固成长、甲随机加速、直接充能、减速与两种禁用为敌肩争取爆发窗口，可能使我肩未能完成有效命中。'),
  dict(confidence='unknown',claim='未拍到过程，不能确认某次随机禁用命中我肩，也不能判定肩完全未施法；动画、弹道、死亡截断也未排除。'),
  dict(confidence='not tested',claim='S甲没有出战；本场不支持或反驳换S甲一定更好，不能断言换了能赢。')],
 modelChanges=[
  dict(id='readiness_gate',rule='每个核心分别过实际输出门槛，再计完整轮和多段收益；先记录是否有伤害行/状态贡献，未启动不能套满轮。'),
  dict(id='control_schedule',rule='同时列开场、使用触发、周期随机三类控制与前置条件；不把控制持续时间简单相加，也不把随机控制固定分配核心。'),
  dict(id='charge_semantics',rule='直接充能=当次推进冷却；加速=持续时间内改变冷却速度。分字段记录，不把2秒加速当2秒直接充能。'),
  dict(id='trigger_producer',rule='快速手部即使伤害较低，也可能是坚固/随机加速与槽位封锁的触发来源；支援边际价值按整条链评估。'),
  dict(id='core_resource_allocation',rule='比较核心实际吃到的倍率/段数/控制保护，而非孔数或品级。放大不出手的核心无法自动增加本场伤害。')],
 unknowns=['真实首击、肩是否起手、禁用目标、战斗时长与击杀时点','敌手2.2秒的完整来源：-20%共享桥只能解释一部分，历史消耗品/其他修正未知','槽位封锁按装备类别还是排列位置映射未隔离验证','加速刷新/叠加规则、随机选目标分布、瞬间充能在禁用中如何处理','最大生命增长与防御统计加号项不能直接视作有效治疗','机师能力未读到，不凭头像补机制','敌无人机轮转跨同件两孔的实际效果未验证'],
 nextPredictions=['战前分别写手与肩首次有效命中是否有可能被周期/使用触发控制拖后，并记录0输出分支。','若采用快手坚固→随机加速，核第一次坚固产生时间、加速目标和第二轮核心命中；不能仅凭装备名称称复刻。','对同类控制与高倍率肩，先考虑减少核心启动依赖、直接充能/控制应对或可用换敌，再比较额外伤害与多段。'],
 bugConclusion='No confirmed new game bug. Missing rows, counters and HP labels do not establish a numerical bug.')
save(OUT/'day16-player-loss.json',review)

study=dict(id='run05-d16',runId='run05',day=16,title='Rogas：坚固快手与控制保护高倍率肩炮',origin='player-requested-postbattle-review',
 status='装备/科技/14个配件已读；过程时序与复现待验证',
 observed='玩家败；我手141488，肩无伤害行；敌肩281106（89.9%）、手31504。双方肩均SS/9段。我方仍B祸津神，未装备建议的S甲。',
 transferable='候选最小功能组合：快速多段坚固手→坚固成长与S甲随机加速→有伤害倍率和段数的坚固肩；控制/减速/直接充能为兑现争取窗口。',
 unknown='实际随机目标与首击未观察；2.2秒手部冷却完整来源未知；未做移除对照，不能宣称这些组件均必要。',
 nextPrediction='复刻前先验证快速坚固来源及首个加速目标，预测肩能否在敌爆发前有效命中；无法验证时保留肩零输出分支。',
 evidence=review['evidence']+[evidence('day16-gear-enemy-2','快手与坚固成长'),evidence('day16-gear-enemy-0','S甲随机加速'),evidence('day16-tech-enemy-1','槽位封锁'),evidence('day16-tech-enemy-4','周期随机禁用'),evidence('day16-part-hand-shoulder-top','800%伤害桥'),evidence('day16-part-shoulder-drone-mid','坚固1200%伤害桥')],adoption=[],
 chain=['手2.2秒为战后可见值；7段、+16坚固附魔、命中坚固+15%','获得坚固→S甲随机一件加速2.5秒；甲背直接充能2秒、背手0.25秒支援循环','背主动减速所有敌装3秒；装备使用触发同槽位禁用0.9秒；每3秒随机禁用3秒','肩每坚固+6伤，800%与1200%伤害桥、共享+3与单孔+3形成9段，实际281106伤害'],
 dependencies=['关键实际输出为肩，手同时提供坚固；两条伤害桥对肩均为明确有效目标。','S甲是刚讨论的同类随机加速甲，但我未装备；敌方完整联动不等于买一件甲即可复刻。','敌有大量成长配件与已改变CD，购入同名新物品不能直接获得本场数值；购买价格未知，售价值不冒充购入成本。','背的坚固转最大生命提供纸面持续价值，不能把最大生命增长全部当有效回复；无人机未有伤害/增益行，不列已兑现胜因。'],
 response=['先解决肩能否有效命中的门槛，再考虑给肩继续堆倍率。','将直接充能和持续加速分开；随机脉冲不当确定核心启动。','短战可比较把资源集中已能出手的核心，但不得仅凭一场伤害榜永久弃肩。','换甲建议仍为待验证候选；本场不构成S甲实战试验。'])

p=ROOT/'data/playtest.json';data=json.loads(p.read_text(encoding='utf-8'))
data['opponentStudies']=[s for s in data['opponentStudies'] if s['id']!=study['id']]+[study]
changes={
 'M01':('第16天周期禁用/同槽封锁反例：核心孔接满也可能无伤害行。',
        ' 逐核心审计是否能有效命中：开场、每次使用触发、周期随机控制分别列；核心零输出是必须保留的分支，不能只算双核完整轮。',
        ' 第16天我手有输出、肩无伤害/坚固行；敌有0.9秒槽位封锁与每3秒随机禁用3秒。没有过程录像，不能把肩无输出确定归给某次禁用。',E+'day16-loss-damage.jpg'),
 'M02':('第16天Rogas快手坚固→随机加速与高倍率肩复盘。',
        ' 低直接伤害装备也可能是快速触发源；先核产生第一份关键状态的速度，再评估随机加速、直接充能及主炮倍率。复制对手时写明基础冷却/成长配件来源缺口。',
        ' Rogas手2.2秒来源未完全解释；其肩伤害281106占89.9%，我肩无记录。我仍B甲，不能把此战作为S甲试换的因果检验。', 'combat-review-day16.html'),
 'M07':('明确区分敌直接充能桥与我互相加速桥，保留战报CD时点。',
        ' 对每条时间收益注明instant_charge或acceleration：本场敌甲背直接充能2秒、背手0.25秒；我肩机为加速持续2秒。不能共用同一时间减法，也不能将战后CD当初始冷却。',
        ' 使用次数/命中次数/完整段数仍不同。敌无人机同件两孔轮转未验证；不能用图上连线就认定两件装备受益。',E+'day16-part-armor-back-mid.jpg')}
for mid,(change,action,caveat,href) in changes.items():
 mm=next(m for m in data['memories'] if m['id']==mid)
 if any(h.get('change')==change for h in mm['history']):continue
 old=copy.deepcopy({k:v for k,v in mm.items() if k!='history'})
 mm['revision']+=1;mm['action']+=action;mm['caveat']+=caveat
 mm['evidence'].append(dict(runId='run05',day=16,note=change,href=href))
 mm['history'].append(dict(date='2026-11-17',revision=mm['revision'],change=change,previous=old))
r=next(r for r in data['runs'] if r['id']=='run05');r.update(wins=14,losses=2,result='进行中：14胜2负，第16天战后；玩家操作，优先模型复盘')
day=next(x for x in r['days'] if x['day']==16)
day.update(title='第16天 · 玩家负Rogas，肩炮未兑现与控制链复盘',phase='已结算，停留双方统计',outcome='loss',wins=14,losses=2,
 after='玩家手动负Rogas；仍穿B祸津神，S甲未出战。我手141488、肩无伤害行；敌肩281106、手31504。敌快手坚固成长/S甲随机加速、直接充能桥、全体减速和两种禁用形成候选解释；真实命中和禁用目标未观察。结算-1命、78金=70+8利息、XP2；14胜2负。无本场自主战前预测。')
if 'combat-review-day16.html' not in day['detailHtml']:day['detailHtml']+='<p><a href="combat-review-day16.html">第16天完整败局复盘</a>；<a href="opponent-studies.html#run05-d16">Rogas可学习的触发链</a>。S甲未出战，不把胜负归因换甲。新M01r6/M02r7/M07r7分开静态输出容量与实际兑现。双方科技、装备、敌14个配件均有截图。</p>'
data['updatedAt']=datetime.now(timezone.utc).isoformat(timespec='seconds');save(p,data)

def esc(s):return html.escape(str(s))
def links(es):return ' · '.join(f'<a href="{x["src"]}">{esc(x["label"])}</a>' for x in es)
partrows=''.join(f'<tr><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td><td><a href="{E}day16-part-{a}.jpg">原图</a></td></tr>' for a,b,c,d,e,f in parts)
techrows=''.join('<tr><td>'+esc(a)+'</td><td>'+esc(b)+'</td></tr>' for a,b in zip(owntech,enemytech))
pagerows=''.join('<tr><td>'+esc(g['name'])+'</td><td>'+str(g['cdObserved'])+'</td><td>'+esc(g['passive'])+'</td><td>'+esc(g['directStat'])+'</td></tr>' for g in gear)
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第16天败局：输出兑现与控制链</title>
<style>body{{max-width:1160px;margin:auto;padding:24px;background:#0d1727;color:#e1ebf5;font:16px/1.7 system-ui}}a{{color:#82caff}}section{{background:#14243a;padding:24px;border-radius:14px;margin:20px 0}}h1,h2{{line-height:1.3}}table{{width:100%;border-collapse:collapse}}td,th{{padding:9px;text-align:left;border-bottom:1px solid #3a4d63}}.chain{{padding:18px;border-left:4px solid #e9bd61;background:#24364b}}.fact{{color:#72dfb6}}.unknown{{color:#ffc779}}@media(max-width:700px){{body{{padding:12px}}section{{overflow:auto;padding:14px}}}}</style>
<h1>第16天败局：肩炮接满孔，仍未兑现输出</h1><p>玩家手动负 Rogas，14胜2负。仍穿B祸津神，刚讨论的S甲没有出战。本战没有自主战前胜负预测；换甲建议不能由这次胜负验证或反驳。</p><p><a href="rsi-workflow.html">RSI</a> · <a href="opponent-studies.html#run05-d16">对手学习库</a> · <a href="combat-review-day15.html">上一战模型</a> · <a href="../runs/run05/day16-player-loss.json">结构化证据与模型规则</a></p>
<section><h2>最确定的失败差异</h2><table><tr><th>项目</th><th>我方</th><th>敌方</th></tr><tr><td>直接伤害</td><td>手141,488；肩、机无行</td><td>肩281,106（89.9%）；手31,504；共312,610</td></tr><tr><td>肩</td><td>SS / 9段 / 五孔全连接</td><td>SS / 9段 / 伤害倍率集中</td></tr><tr><td>确认的肩伤害倍率</td><td>1+6+2+0.1=9.1倍</td><td>1+8+12=21倍；仅此项为我方约2.31倍</td></tr><tr><td>防御统计</td><td>背1,652；坚固44；甲无行</td><td>背10,808；坚固584；加号1,168、科技234口径待核</td></tr><tr><td>状态来源</td><td>开场375力、周期48力、无人机48力；手32坚固</td><td>手556坚固、肩291、背140</td></tr></table><p>{links(review['evidence'])}</p><p>不把无统计行当作没有被动价值；但肩无伤害和坚固行，已足以反驳“按双核完整一轮计算实际输出”。统计次数x29/x32/x1不等于完整施法次数。</p></section>
<section><h2>对方如何组织输出窗口</h2><div class="chain">快速多段手：产生坚固＋命中坚固增长<br>↓<br>S甲：获得坚固 → 随机一件加速2.5秒<br>＋ 甲背直接充能2秒／背手直接充能0.25秒<br>↓<br>背减速全体3秒；装备使用触发同槽禁用0.9秒；每3秒随机禁用3秒<br>↓<br>坚固转伤肩：800%＋1200%伤害桥、两处+3段 → 9段爆发<br>↓<br>实际肩伤害281,106，我方肩没有伤害行</div><p class="fact">词条与累计贡献可确认；敌肩是实际主输出。</p><p class="unknown">整条时序是机制支持的解释，不是观测到的逐秒录像。未确认随机禁用命中我肩，也没确认我肩完全未起手；动画/弹道和死亡截断仍可能影响输出。敌甲没有主动盾行不排除随机加速被动。</p></section>
<section><h2>完整读取的装备与科技</h2><table><tr><th>敌装</th><th>战后CD</th><th>被动</th><th>本场贡献</th></tr>{pagerows}</table><p>敌手2.2秒不是已解释的可复制基础值。-20%桥只解释部分；历史消耗品等来源仍未知。敌无人机没有伤害/增益行，不把其减敌盾被动列为已兑现胜因。</p><table><tr><th>我方科技</th><th>敌方科技</th></tr>{techrows}</table><p><a href="{E}day16-gear-own-contact.jpg">我装备拼图</a> · <a href="{E}day16-gear-enemy-contact.jpg">敌装备拼图</a> · <a href="{E}day16-tech-own-contact.jpg">我科技拼图</a> · <a href="{E}day16-tech-enemy-contact.jpg">敌科技拼图</a></p></section>
<section><h2>敌方14个配件：端点与作用分开</h2><table><tr><th>连接</th><th>配件</th><th>实际词条</th><th>证据</th></tr>{partrows}</table><p>敌两条伤害长桥分别共享手肩、肩无人机，肩是共同核心；不是机械追求全部两端同等收益。无人机同件两孔轮转是否有效仍未知，不能据图认定双装备联动。所有售价值均未当购入成本。</p></section>
<section><h2>本次真正修改的战斗模型</h2><table><tr><th>原模型不足</th><th>修订</th><th>下一战验证</th></tr><tr><td>几何接满＋完整轮伤害容易被当战力</td><td>逐核心先过“能否有效命中”的门槛，保留肩零输出分支</td><td>手/肩首击、起手到命中的延迟、是否被截断</td></tr><tr><td>时间收益容易混算</td><td>直接充能、持续加速、禁用、减速分别记录</td><td>每次触发推进多少冷却、目标是谁；不把持续2秒直接减CD2秒</td></tr><tr><td>按伤害榜判断支援价值</td><td>快手可以是坚固、加速、槽位封锁的触发来源</td><td>第一份坚固何时到达、随后哪个核心加速</td></tr><tr><td>只查开场控制</td><td>同时检查使用触发和周期控制，区分确定与随机目标</td><td>我肩是否被对应槽位封锁或随机禁用，能否赶上爆发窗口</td></tr></table><p>这些是带证据的规则和数据结构修订。通用配装求解器仍是几何＋静态指标，不宣称已成为完整战斗模拟器，也不输出校准胜率。</p></section>
<section><h2>玩法调整顺序</h2><p>先解决核心兑现：比较直接充能、控制应对、快触发来源或可用换敌；再比较伤害倍率和多段。对敌同类构筑，单纯继续给尚未能命中的肩加伤害不够。将资源暂时集中已能出手的手部可列候选，但不能仅凭这一战永久弃肩。</p><p>S甲仍是候选，不能说换了就能赢：它依赖先获得坚固且随机分配加速，无法保证解决肩的首次命中。对方更完整的快手、充能、控制和高倍率肩共同构成条件，买同一件甲不等于复制整条链。</p><p>没有新确认游戏Bug。战报血量275,400含何种时点未知，敌背又能增长最大生命；不把它当初始或终局剩余生命。护盾/加号/计数口径异常继续待核，不据此指控数值结算错误。</p></section></html>'''
(DOCS/'combat-review-day16.html').write_text(page,encoding='utf-8')

# Keep the existing opponents page, add this new study without rewriting historical analysis.
p=DOCS/'opponent-studies.html';s=p.read_text(encoding='utf-8')
if 'id="run05-d16"' not in s:
 block='<section id="run05-d16"><h2>'+esc(study['title'])+'</h2><p>'+esc(study['observed'])+'</p><p><b>可学习：</b>'+esc(study['transferable'])+'</p><p><b>未知：</b>'+esc(study['unknown'])+'</p><p><b>下一次检验：</b>'+esc(study['nextPrediction'])+'</p><p><a href="combat-review-day16.html">完整装备、科技、14配件与触发链</a> · '+links(study['evidence'])+'</p></section>'
 s=s.replace('<section id="run05-d13">',block+'<section id="run05-d13">',1).replace('14场已记录败局均有条目。','15场已记录败局均有条目。').replace('最新林弦战按战前词条、过程和三页战报拆解。','最新Rogas战按战后装备、科技、配件与三页统计拆解，缺实际过程时序。')
 p.write_text(s,encoding='utf-8')
snapshot='2026-11-17 最新停点：run05第16天玩家负Rogas，14胜2负，仍在双方战报，未继续下一天。实际穿B祸津神，刚讨论S甲未出战，不能归因换甲。我手141488，肩无伤害/坚固行；敌肩281106、手31504。双方10装备/10科技及敌14配件已批采。敌S甲随机加速、快手坚固成长、甲背2秒/背手0.25秒直接充能、背全体减速及两类禁用，保护21倍伤害/9段肩；具体控制目标与首击未知。结算78金=70+8利息、XP2/-1命；到账后总金币未读。M01r6/M02r7/M07r7已修订。玩家优先模型复盘，不自主开新战。[败局与模型修订](docs/combat-review-day16.html)。'
for fn,marker in [('README.md','## 当前进度'),('GAME-NOTES.md','## 本局快照')]:
 p=ROOT/fn;s=p.read_text(encoding='utf-8')
 if snapshot not in s:s=s.replace(marker+'\n',marker+'\n\n'+snapshot+'\n',1)
 if fn=='README.md':
  log='- 2026-11-17 第16天败局复盘：确认实际未换S甲；我肩无伤害行，敌肩281106。批采双方装备/科技及敌14配件，新增Rogas对手学习条目与战斗模型门槛/控制分类修订；未伪造首击、禁用目标和胜负预测，无新确认游戏Bug。游戏停战报，后续优先检验核心实际兑现与直接充能/加速区别。'
  if log not in s:s=s.replace('## 工作日志\n','## 工作日志\n\n'+log+'\n',1)
 p.write_text(s,encoding='utf-8')
armor=OUT/'day16-s-armor-comparison.json';a=json.loads(armor.read_text(encoding='utf-8'));a['battleFollowup']={'actualArmor':'B祸津神','offeredSArmorTested':False,'outcome':'loss vs Rogas','causalConclusion':'未构成换甲试验；不能从本场裁决试换建议','evidence':E+'day16-gear-own-1.jpg'};save(armor,a)
start=datetime.fromisoformat('2026-11-17T03:39:30.034+00:00');last=DOCS/E/'day16-part-drone-single.jpg'
save(OUT/'day16-review-timing.json',dict(startedAt=start.isoformat(),savedAt=datetime.now(timezone.utc).isoformat(),
 coreCaptureWindowSeconds=round(last.stat().st_mtime-start.timestamp(),3),scope='Postbattle collection of result, stats,10gear,10tech,14enemy parts; includes reading/tool overhead',fullGameDaySeconds=None))
print(json.dumps({'ownDamage':141488,'enemyDamage':312610,'enemyShoulderShare':281106/312610,'enemyParts':len(parts),'studies':len(data['opponentStudies']),'record':'14W2L'},ensure_ascii=False))
