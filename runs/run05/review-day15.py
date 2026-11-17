"""Reproducible analysis of saved visible evidence; no game interaction."""
import copy
import html
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/run05'
DOCS = ROOT / 'docs'
E = 'playtest-2026-11-16-run05/'
spec = importlib.util.spec_from_file_location('loadout', ROOT / 'tools/loadout.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

d = json.loads((OUT/'day15-loadout-input.json').read_text(encoding='utf-8'))
d.update(snapshot='Day15 battle loadout, reconstructed from saved result; not Day16 live inventory', gold=16,
         currentOrder=['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'])
for g in d['equipment']:
    if g['id']=='drone-s-live':
        g['acceptsDamagePct']=True
        g['damageModifierEvidence']=E+'day15-blue-drone-mid.jpg'
    if g['id']=='armor-b':
        g.update(element=48)
        g['postbattleCooldownObserved']=10.6
        g['fixedModifier']='Blue +4 force at [2,2]; included in element, not double-counted'
    if g['id']=='shoulder-ss':
        g['cooldown']=8.1
        g['postbattleCooldownObserved']=8.2
d['unknown']=['This is the Day15 precombat baseline plus confirmed result layout; dynamic final damage is excluded.',
              'Cooldown proxy uses prior snapshot armor10.5 / shoulder8.1; result tooltips10.6 /8.2 are separate observations, not proof of initial cooldown. Changes require state/consumable attribution.',
              'Animation, random charge, acceleration/disable overlap, force coefficient and effective damage timing are uncalibrated.',
              'Blue +4 force is fixed on armor; not a freely optimized part in these comparisons.']
order=[next(g for g in d['equipment'] if g['id']==i) for i in d['currentOrder']]
base={'main-long':[(2,1),(6,1)],'damage-long':[(8,1),(12,1)],'hits-long':[(8,2),(12,2)],
      'charge-short':[(14,0),(16,0)],'damage-short':[(14,1),(16,1)],'firm-short':[(14,2),(16,2)],
      'cd-single':[(8,0)],'growth-single':[(0,1)],'calibration-single':[(18,0)]}

def assess(name, mapping, note):
    chosen=[]
    for pid, pts in mapping.items():
        p=next(p for p in d['parts'] if p['id']==pid)
        chosen.append(next(p for p in m.placements(order,p,4) if p['points']==pts))
    assert all(not m.conflicts(a,b,'solid') for i,a in enumerate(chosen) for b in chosen[i+1:])
    blue=dict(part='fixed-blue-force',points=[(6,2)],owners=['armor-b'])
    assert all(not m.conflicts(blue,p,'solid') for p in chosen)
    r=m.evaluate(order,d['parts'],chosen,d['mainBonus'])
    points={tuple(p) for c in chosen+[blue] for p in c['points']}
    audit=[]
    for i,g in enumerate(order):
        for x,y in g['ports']:
            pt=(i*4+x,y)
            covers=[c['part'] for c in chosen if len(c['points'])>1 and c['points'][0][1]==y
                    and min(p[0] for p in c['points'])<pt[0]<max(p[0] for p in c['points'])]
            audit.append(dict(equipment=g['id'],point=pt,localPort=[x,y],
                              state='connected' if pt in points else 'blocked' if covers else 'free',coveredBy=covers))
    r.update(name=name,note=note,portAudit=audit,fixedPlacements=[blue],battlePrediction=None)
    return r

cases=[assess('本场实际布局',base,'肩五孔均连接；手右中被长桥遮挡。该战胜利不证明全局最优。')]
alt=copy.deepcopy(base);alt['cd-single']=[(18,0)];alt['calibration-single']=[(8,0)]
cases.append(assess('火控给手，冷却给无人机',alt,'手基础伤害增加，但手CD4.5→5；无人机7.5→6.75。需比较第一次有效命中与部署，不能只按伤害份额决策。'))
alt=copy.deepcopy(base);alt['growth-single']=[(8,0)];alt['cd-single']=[(0,1)]
cases.append(assess('成长给手，冷却给背',alt,'手失去10%CD；成长4%每秒为加算，未实测该布局。短战可能来不及兑现，不能把未模拟收益写成零。'))
alt=copy.deepcopy(base);alt.pop('damage-short');alt['calibration-single']=[(14,1)]
cases.append(assess('移除200%桥，火控给肩',alt,'肩伤害降低、无人机也失去200%桥；只换来无人机可用孔，没有更好配件填入前不因空孔变多而判更强。'))
(OUT/'day15-reviewed-loadout-input.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'day15-reviewed-layouts.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')

review=dict(runId='run05',day=15,operator='player',opponent='Ranka0423',outcome='win',wins=14,losses=1,
            ownHp=191000,enemyHp=168000,prebattlePrediction=None,firstEffectiveHit=None,durationSeconds=None,
            damage=dict(own=dict(hand=102003,shoulder=92513,drone=None),enemy=dict(shock=16697,hand=3780,shoulder=3358,drone=1470)),
            defense=dict(own=dict(back=3280,firm=301,armor=None),enemy=dict(back=20380,firm=92,armor=None)),
            buffs=dict(own=dict(openingForce=375,periodicForce=80,droneForce=48,shoulderFirm=285,handFirm=20),
                       enemy=dict(openingShock=450,shoulderShock=727,backShock=466,handFirm=95,drone=dict(burn=22,cold=6,shock=11))),
            nullMeaning='not displayed / not observed, not proved zero contribution',
            ownTech=['主属性+10%','开场全装备加速3秒','每秒8力量','开场375力量','每3秒随机一件充能3秒'],
            enemyTech=['施加感电50%获得2坚固','施加寒冷50%获得3坚固','施加燃烧50%获得4坚固','开场禁用全部敌装2.5秒','开场施加450感电'],
            evidence=[E+'day15-result-'+n+'.jpg' for n in ['damage','defense','buffs']]+
                     [E+f'day15-tech-{side}-{i}.jpg' for side in ['own','enemy'] for i in range(5)],
            geometry=dict(ports=17,connected=16,blocked=1,free=0,blockedPort='hand right middle',shoulderConnected=5),
            changes=[
                dict(rule='startup',before='Nominal CD / opening acceleration used without explicit control overlap',
                     after='Include enemy opening disable2.5s and own acceleration3s as overlapping states. Random charge3s every3s remains a branch, not guaranteed core acceleration.',status='rule text verified; actual timing unknown'),
                dict(rule='support',before='Damage share could dominate allocation',
                     after='Separate direct damage, applied force/firm, triggered shields, lost-shield growth and acceleration recipients. Drone has48force despite no damage row; armor passive is independent of its active shield row.',status='support observed; marginal causal contribution unknown'),
                dict(rule='counters',before='Assumed full volley metrics might be mistaken for realized output',
                     after='Hand x10 and shoulder x9 are capacity; result counters x21/x1 do not mean complete casts. Shoulder285firm is not9*95=855, so realized fraction is unknown.',status='mismatch observed; no game bug conclusion'),
                dict(rule='layout',before='Missing summon damage eligibility and qualitative blocked-hole concern',
                     after='Explicit verified eligibility; enumerate exact occupied/blocked/free ports and compare alternatives with displaced parts.',status='offline regression verified; alternatives not played')],
            unknowns=['Enemy accessory details were not captured before leaving results; shapes alone do not establish effects.',
                      'No exact first-hit, battle duration, remaining HP or per-event damage timeline.',
                      'Displayed shields may not equal total generated or absorbed; cannot multiply16697 by2 and declare a discrepancy bug.',
                      'Enemy armor passive acceleration may operate even without armor defense row.',
                      'Victory and changed damage shares across different opponents are not a controlled +6 bridge experiment.'],
            nextValidation=['Record first effective hand/shoulder hit and first drone deployment before enemy burst.',
                            'Separate predicted attack segments from observed effective hit events and buff applications.',
                            'Compare control-free, disabled-start and delayed-core scenarios; leave unsupported rates unknown.'],
            inputAttribution='User confirmed intermediate operations were manual; no subsequent UI operations by agent.')
review['ownTotalDamage']=sum(v for v in review['damage']['own'].values() if v is not None)
review['enemyTotalDamage']=sum(review['damage']['enemy'].values())
(OUT/'day15-player-result.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')

def esc(x): return html.escape(str(x))
def link(n,label): return f'<a href="{E+n}.jpg">{esc(label)}</a>'
def diagram(r):
    names=['背','甲','手','肩','机']; s=['<svg viewBox="0 0 760 220" role="img" aria-label="整排插槽和连接图">']
    for i,n in enumerate(names):
        s.append(f'<rect x="{i*150+10}" y="20" width="140" height="190" rx="12" fill="#182a42" stroke="#57708d"/><text x="{i*150+70}" y="45" fill="white">{n}</text>')
    def xy(p):return (30+p[0]*37.5,75+p[1]*48)
    for p in r['placements']:
        pts=p['points'];x,y=xy(pts[0]);x2,y2=xy(pts[-1]);col='#eac869' if p['part'] in ['hits-long','main-long','firm-short'] else '#bd8dfa'
        s.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="8"><title>{esc(p["part"])}</title></line>')
    for p in r['portAudit']:
        x,y=xy(p['point']);col={'connected':'#56d6ad','blocked':'#fb7373','free':'#a7b5c5'}[p['state']]
        s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{col}"><title>{esc(p["equipment"]+str(p["localPort"])+p["state"])}</title></circle>')
    return ''.join(s)+'</svg>'

rows=''.join(f'<tr><td>{esc(r["name"])}</td><td>{r["metrics"]["baseVolley"]:,}</td><td>{r["metrics"]["coreCdSum"]}</td><td>{sum(p["state"]=="free" for p in r["portAudit"])}</td><td>{esc(r["note"])}</td></tr>' for r in cases)
gearrows=[('我背','7.0','物理伤害→按力量产盾；主动减速全部敌装1秒','3280盾'),('我甲','10.6','力量额外提供1层伤害；超载II','主动盾无记录，被动不能判无效'),('我手','4.5','10段；失去护盾的12%转为伤害','102003伤害 / 20坚固'),('我肩','8.2','9段；每层坚固→本装备伤害+6','92513伤害 / 285坚固'),('我机','7.5','部署+48力量；伤害桥与火控作用已确认','48力量，伤害无记录'),('敌甲','11.5','获得坚固→随机一件装备加速3.5秒；超载V','主动盾无记录，随机目标未知'),('敌背','4.5','每1雷电伤害→2盾；主动减速全敌装3秒','20380盾 / 466感电'),('敌手','5.0','10段；命中自身坚固+15%','3780伤害 / 95坚固'),('敌肩','9.0','8段；命中敌方感电+30%','3358伤害 / 727感电'),('敌机','6.5','部署造成敌感电层数对应雷电伤害，共2次','1470伤害 / 多种状态')]
gt=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in gearrows)
tech=''.join('<tr><td>'+esc(a)+'</td><td>'+esc(b)+'</td></tr>' for a,b in zip(review['ownTech'],review['enemyTech']))
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第15天：插槽与战斗模型修订</title>
<style>body{{background:#0d1727;color:#e1ebf5;font:16px/1.7 system-ui;margin:auto;max-width:1180px;padding:28px}}a{{color:#80c8ff}}section{{background:#122037;padding:22px;border-radius:14px;margin:20px 0}}h1,h2{{line-height:1.3}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;border-bottom:1px solid #34475c;padding:10px}}.flow{{padding:18px;background:#21364c;border-left:4px solid #57d6ad}}svg{{width:100%;max-height:300px}}small{{color:#a9bbce}}@media(max-width:700px){{body{{padding:12px}}section{{padding:12px;overflow:auto}}}}</style>
<h1>第15天：配件端点与实际触发分开建模</h1><p>玩家手动战胜 Ranka0423；14胜1负。已进入第16天，当前回合只做离线复盘。没有本场自主战前预测，不补写胜率或首击预测。</p>
<p><a href="rsi-workflow.html">RSI总览</a> · <a href="loadout-ports-day15.html">原六方案与旧模型边界</a> · <a href="../runs/run05/day15-player-result.json">结构化战报</a> · <a href="../runs/run05/day15-reviewed-layouts.json">重算候选</a></p>
<section><h2>先看证据</h2><table><tr><th>统计</th><th>我方</th><th>敌方</th></tr><tr><td>伤害</td><td>手102,003（52.44%）；肩92,513（47.56%）；共194,516</td><td>感电16,697；手3,780；肩3,358；机1,470；共25,305</td></tr><tr><td>防御栏</td><td>背3,280；坚固301；甲无记录</td><td>背20,380；坚固92；甲无记录</td></tr><tr><td>已读支援</td><td>开场375力量；周期80力量；无人机48力量；肩285坚固</td><td>开场450感电；肩727感电；背466感电；手95坚固</td></tr></table>
<p>{link('day15-result-damage','伤害原图')} · {link('day15-result-defense','防御原图')} · {link('day15-result-buffs','增益原图')} · {link('day16-live-after-result-capture','14胜1负现场')}</p><p>伤害总量不是有效扣血；“无记录”不是零被动贡献；统计次数不是完整施法次数。</p></section>
<section><h2>17个孔：16连接、1被挡、0空闲</h2>{diagram(cases[0])}<p>绿色为已连接，红色为手右中被长桥挡住。肩5个孔全部连接。蓝色+4力量固定甲右下；火控位于无人机右上。当前问题是配件分配和替代收益，不能再用“肩右两孔浪费”描述这一版。</p><table><tr><th>候选</th><th>双核基础完整轮</th><th>双核CD和</th><th>空孔</th><th>取舍</th></tr>{rows}</table><p>四个显式候选按同一基线重算，均通过端点/桥身冲突检查；不是全空间最优。完整轮假设双方核心各打完一次，不等于实战DPS。蓝色附魔固定，库存/第16天新物品不在此快照。<strong>空孔的代价取决于能填入的替代配件；没有可行替代时不能虚构收益。</strong></p></section>
<section><h2>双方装备和科技</h2><table><tr><th>装备</th><th>读到的CD</th><th>触发条件</th><th>本场证据</th></tr>{gt}</table><table><tr><th>我方科技</th><th>敌方科技</th></tr>{tech}</table><p>{link('day15-tech-own-contact','我方科技拼图')} · {link('day15-tech-enemy-contact','敌方科技拼图')}。敌方配件详情补采前页面已经离开战报；只见形状不推定效果。</p></section>
<section><h2>战斗模型改成两层证据链</h2><div class="flow">我方：开场力量 → 多段物伤 → 背部被动产盾 → 失盾强化手部 → 更多物伤<br>肩部获得坚固 → 肩部转伤；无人机部署 → 力量 → 支援物伤/护盾链<br>敌方：开场450感电 → 雷电伤害 → 背部产盾；肩命中 → 感电百分比增长<br>感电/寒冷/燃烧概率产坚固 → 甲被动随机加速 → 更多状态触发</div><p>以上箭头有词条依据；时序、次数、乘区和每条边的实际边际收益尚未完整验证。敌方不是没有联动，而是这场统计中未形成足以压住我方双核的实际输出。不能由一场胜利推出力量强于感电。</p>
<p><strong>启动层：</strong>敌开场禁用2.5秒与我开场加速3秒重叠；每3秒随机充能3秒不能保证落到手/肩。禁止直接拿CD减3秒算首击，缺动画/命中时间就留未知。</p><p><strong>兑现层：</strong>手10段、肩9段是能力上限；肩本场285坚固≠9×95=855。可能受打断、死亡截断或统计口径影响，不能假定每次全段兑现。双方统计计数x1/x21/x36不换算成完整施法次数。</p><p><strong>支援层：</strong>无人机没有直接伤害行但贡献48力量；甲没有主动护盾行，力量增伤被动仍可能生效。配件分配要比较替换前后整条链，不把伤害占比当边际收益。</p><p><strong>状态层：</strong>战后手21.8K、肩26.0K是已增长画面，不能写回开场基础伤害。战后肩8.2、甲10.6秒单独记录；不能直接覆盖此前8.1/10.5的战前快照。表中CD只是静态比较代理，真实首击必须重新观察。</p></section>
<section><h2>保留、修改与待验证</h2><p>保留：整排几何先算，实机验证；不能仅凭品级或伤害榜选配件。修改：召唤是否接受伤害配件用已验证实例能力，已修复本S无人机106→298漏算；未知召唤不推广。补强：记录控制重叠、随机目标、被动支援和未完成多段。</p><p>下一场需在点击前记录：双方首次有效命中、首盾、首次无人机部署、肩实际完成段数；对随机充能和禁用重叠给出分支，而非一个假精确时间。当前没有完整战斗模拟器，没有经校准的胜率。</p><p>本场没观察到可直接确认的新游戏Bug。敌雷电16,697×2与背盾20,380不能直接对账判Bug，必须先核防御统计计的是生成、吸收还是其他口径。第14→15天对手和血量不同，总伤害下降不能反驳多段给手。</p></section></html>'''
(DOCS/'combat-review-day15.html').write_text(page,encoding='utf-8')
print(json.dumps({'damage':review['ownTotalDamage'],'enemyDamage':review['enemyTotalDamage'],
                  'candidates':[{'name':r['name'],'baseVolley':r['metrics']['baseVolley'],
                                 'droneDamage':next(g['damage'] for g in r['equipment'] if g['slot']=='drone'),
                                 'portCounts':{s:sum(p['state']==s for p in r['portAudit']) for s in ['connected','blocked','free']}} for r in cases]},ensure_ascii=False))
