"""Transcription of already viewed screenshots; never reads live game state."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
prefix='playtest-2026-11-16-run05/'

def gear(id,name,slot,grade,ports,kind,tags,damage,hits,shield,element,cd,price,passive,evidence,growth):
 return dict(id=id,name=name,slot=slot,grade=grade,ports=ports,kind=kind,tags=tags,
             damage=damage,hits=hits,shield=shield,element=element,cooldown=cd,price=price,
             passive=passive,evidence=prefix+evidence+'.jpg',growth=growth)
g=[
gear('back-b','深红尊','back','B',[[0,1],[2,1]],'defense',['force'],0,1,740,38,7,0,'物理伤害产生等于力量层数的盾；使用减速全部敌装1秒','day14-remove-firm-short','原实例跨日积累，740按每日快照推算；卡面5.3K作交叉核对'),
gear('armor-b','祸津神','armor','B',[[2,1],[2,2]],'defense',['force'],0,1,1160,44,10.5,0,'超载II；力量额外提供1层伤害，精确系数待核','day03-drone-equipped','保留旧成长与0.5秒CD消耗品；1160据跨日快照'),
gear('shoulder-ss','链法手枪','shoulder','SS',[[0,1],[0,2],[2,0],[2,1],[2,2]],'attack',['firm'],820,3,0,30,9,0,'每层坚固使本装备伤害+6；本工具未模拟战中转伤','day14-long-bottom','820由第14天原始说明确认；新实例不继承'),
gear('hand-s','虚空撕裂','hand','S',[[0,0],[0,1],[0,2],[2,1]],'attack',['firm'],650,4,0,4,5,0,'获得相当于失去护盾12%的伤害；未模拟','day14-remove-firm-short','旧实例每日+50；650按卡面4.6K与增幅反核'),
gear('drone-b','野衾','drone','B',[[0,1],[0,2]],'summon',['force'],73,1,0,6,8,0,'部署获得24力量；无人机攻击间隔须单列，不能把部署CD当DPS','day03-drone-equipped','旧实例每日+5；两左孔由原图确认，修正先前只记一个孔'),
gear('armor-a','塞玛·量产','armor','A',[[0,2],[2,1],[2,2]],'defense',['firm'],0,1,990,66,13,16,'获得坚固时，随机一件装备加速2秒；可能与两核命中联动，频率未模拟','day14-shop','商店新实例，无旧成长，CD消耗品不继承'),
gear('back-a','天火反应堆','back','A',[[2,0],[2,1],[2,2]],'defense',['burn'],0,1,190,38,5.5,16,'使用慢全敌装1.5秒；燃烧伤害等额转盾，当前缺燃烧链','day14-s0-g0','新实例，失去原物理伤害转盾；有3孔但不自动更好'),
gear('drone-s-force','式神稻荷','drone','S',[[0,0],[0,1],[2,1],[2,2]],'summon',['force'],50,1,0,10,8,32,'每台提供14%吸血；部署前无吸血，未模拟无人机频率','day14-shop','新增右侧孔位；原73伤害成长不继承'),
gear('drone-s-shock','潜伏者','drone','S',[[0,0],[0,1],[0,2],[2,0]],'summon',['shock'],21,1,0,7,6,32,'每台额外造成20%雷电伤害；当前无感电核心','day14-s0-g3','较快部署与更多孔；原成长不继承')]

def part(id,name,span,effect,description,evidence,price=0,sell=0):
 return dict(id=id,name=name,shape=[[0,0]] if span==0 else [[0,0],[span,0]],effect=effect,
             description=description,evidence=prefix+evidence+'.jpg',price=price,sell=sell)
p=[
part('main-long','S力量主属性长桥',4,dict(stat='main_pct',value=2,tag='force',tagValue=6),'主属性+200%，力量装备改为+600%','day14-remove-firm-short',sell=24),
part('damage-long','A坚固伤害长桥',4,dict(stat='damage_pct',value=2,tag='firm',tagValue=6),'伤害+200%，坚固装备改为+600%','day14-restore-damage-endpoint',sell=12),
part('damage-short','A200%伤害短桥',2,dict(stat='damage_pct',value=2),'进攻型装备伤害+200%','day14-remove-damage-short',sell=8),
part('firm-short','S216%坚固短桥',2,dict(stat='element_pct',value=.72,tag='firm',tagValue=2.16),'元素+72%，坚固装备改+216%','day14-remove-firm-short',sell=16),
part('charge-short','S互充2秒短桥',2,dict(stat='charge',value=2),'使用一端给另一端充能2秒；不是每段命中充能','day13-current',sell=16),
part('cd-single','S10%冷却单孔',0,dict(stat='cd_pct',value=-.1),'面板冷却-10%','day14-cd-to-back',sell=8),
part('hits-long','S+6段长桥',4,dict(stat='hits',value=6),'进攻型装备攻击段数+6；召唤是否适用未确认，本版不计','day14-s0-p1',sell=24),
part('hits-short-shop','商店S+3段短桥',2,dict(stat='hits',value=3),'进攻型装备攻击段数+3','day14-s0-p0-read',price=32,sell=16)]
d=dict(schemaVersion=1,snapshot='run05 day14 paused / 2026-11-17',gold=116,stride=4,mainBonus=.1,
       slots=['back','armor','shoulder','hand','drone'],equipment=g,parts=p,
       currentOrder=['back-b','armor-b','shoulder-ss','hand-s','drone-b'],
       baselineNote='试装前：肩约7.5K×3、95坚固，手约4.6K×4、13坚固、CD4.5秒；背约5.3K盾CD7秒，甲约8.2K盾CD10.5秒。暂停前：两下排短桥已拆，肩5.8K×3/30坚固，手4.6K×4/4坚固；单孔CD在背。最后中心试装被Esc中断，现场须重看。',
       unknown=['桥身可否交叠尚未确认，双假设结果不可混为已验证。',
                '长桥失败可能涉及拖拽锚点，未排除合法几何；不录为禁止布局。',
                '旋转/斜向配件未验证；当前仅录入可见水平形状。',
                '商店候选在暂停后是否还在原位，需要恢复时新截图。',
                '商店装备孔位为人工从截图转录，安装前核实；不按阶级自动补孔。',
                '额外段数对召唤装备曾显示数量变化，但实际部署/无人机机制未验证，数值模型暂不计。',
                '双端落在同一装备时只计算一次属性；互充在同件两孔的行为未验证。',
                '主属性加算、取整为卡面近似；按静态原始伤害比较，不把被动价值设为零强度结论。',
                '买下所有候选前先看预算与组合；当前拥有的+6长桥不重复算24金币采购。'])
(root/'runs/run05/day14-loadout-input.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
