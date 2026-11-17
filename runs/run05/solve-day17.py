"""Search only the frozen visible shop/stock; projected sale cash is explicit."""
import copy, importlib.util, json
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'runs/run05'
spec=importlib.util.spec_from_file_location('loadout',root/'tools/loadout.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=json.loads((out/'day15-reviewed-loadout-input.json').read_text(encoding='utf-8'))
d.update(snapshot='Day17: player60gold, stock S神速神经; fresh full shop/current gear, no autonomous purchase',gold=76,currentOrder=['back-b','armor-b','hand-s','shoulder-ss','drone-s-live'])
d['funding']='Search upper envelope only: 60 actual + up to16 from selling unused stock S back. Filter every result by unused owned back assets; actual sales must precede spending.'
d['equipment']=[g for g in d['equipment'] if g['id']!='sword-force-s']
by={g['id']:g for g in d['equipment']}
by['back-b'].update(shield=890,element=38,cooldown=6.6,sell=4)
by['armor-b'].update(shield=1310,element=44,cooldown=10.1,sell=4)
by['armor-b'].pop('fixedModifier',None)
by['hand-s'].update(damage=806,element=4,cooldown=2.3/.9)
by['shoulder-ss'].update(damage=1016,element=30,cooldown=6.7/.875)
by['drone-s-live'].update(damage=111,element=10,cooldown=6.2/.875,acceptsDamagePct=True)
for g in d['equipment']:
 g['evidence']='playtest-2026-11-16-run05/day17-equipped-'+g['slot']+'.jpg'
 g.pop('postbattleCooldownObserved',None)
for id,name,slot,tags,kind,ports,shield,element,cd,price,passive in [
 ('back-force-s','神速神经','back',['force'],'defense',[[0,1],[2,1],[0,2],[2,2]],260,52,6,0,'使用全力量装备+15力量；减速全敌2秒'),
 ('back-firm-hp-s','英勇盾','back',['firm'],'defense',[[0,0],[0,2],[2,1],[2,2]],235,47,5.5,32,'坚固每秒+1最大生命；减速全敌2秒'),
 ('back-firm-growth-s','曙光盾','back',['firm'],'defense',[[0,0],[0,1],[0,2],[2,2]],260,52,6,32,'使用全坚固装备+15坚固；减速全敌2秒'),
 ('armor-firm-s','塞玛·量产','armor',['firm'],'defense',[[0,0],[0,1],[0,2],[2,1]],1230,82,13,32,'获得坚固随机一件加速2.5秒；超载IV'),
 ('drone-firm-s','侍灵·量产','drone',['firm'],'summon',[[0,0],[0,1],[0,2],[2,1]],0,10,7.5,32,'命中敌防御装备-10盾，己方+10；实际攻击频率未知')]:
 d['equipment'].append(dict(id=id,name=name,slot=slot,grade='S',tags=tags,kind=kind,ports=ports,shield=shield,element=element,cooldown=cd,damage=36 if slot=='drone' else 0,hits=1,price=price,sell=16,passive=passive))
d['parts']=[p for p in d['parts'] if p['id']!='firm-short']
next(p for p in d['parts'] if p['id']=='calibration-single')['effect']['value']=1.2
d['parts'] += [dict(id='cd-short',name='S反击冷却短桥',shape=[[0,0],[2,0]],effect=dict(stat='cd_pct',value=-.125),price=0,sell=16),
               dict(id='shield-long-shop',name='S重型护盾校准器',shape=[[0,0],[4,0]],effect=dict(stat='shield_pct',value=1.6),price=24,sell=24,description='本日+160%，每天+160%，本日不预支成长'),
               dict(id='shield-short-shop',name='S伏特守卫',shape=[[0,0],[2,0]],effect=dict(stat='shield_pct',value=2,tag='shock',tagValue=6),price=32,sell=16)]
d['unknown']=['手/肩/无人机裸CD由已装比例与四舍五入显示反推，误差约0.1秒；不当首击时间。',
 '蓝色4力量单孔完整计入库存，但未证实附魔会否赋予力量标签；不预支600%条件增益。留待最终空孔分配和实机验证。',
 '旧甲力量被动、S甲随机加速、背部成长与最大生命、失盾手增伤、控制、动画未被静态分模拟。',
 '新S护甲孔位本次原图确认为左上/左中/左下/右中；纠正此前误写右上，旧购买建议的几何部分不再沿用。',
 '仓库全图只有S神速神经，旧新刀/元素短桥未见，不能当可用库存。',
 '玩家调整当前手到显示2.3秒，不能沿用旧4.5秒。']
d['manualParts']=[dict(id='blue-force',name='B神盾',shape=[[0,0]],forceEnchantment=4,price=0,sell=2)]
(out/'day17-loadout-input.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
r=m.search(d,beam=10,limit=120,policy='solid')
valid=[]
for c in r['candidates']:
 credit=16 if 'back-force-s' not in c['order'] else 0
 credit+=4 if 'back-b' not in c['order'] else 0
 if c['cost']<=60+credit:
  c['actualCashBeforeSales']=60;c['availableSaleCredit']=credit
  c['salesNeeded']=max(0,c['cost']-60)
  valid.append(c)
r['candidates']=valid;r['metrics']['retainedAfterSaleCheck']=len(valid)
(out/'day17-loadout-results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
m.render(d,[r,dict(r,policy='endpoints')],root/'docs/loadout-live-day17.html')
print('SEARCH',r['metrics'])
for armor in ['armor-b','armor-firm-s']:
 for back in ['back-b','back-force-s','back-firm-hp-s','back-firm-growth-s']:
  cs=[c for c in valid if armor in c['order'] and back in c['order'] and 'drone-s-live' in c['order']]
  for key in ['baseDps','coreChargeTargets']:
   if not cs:continue
   c=max(cs,key=lambda c:(c['metrics'][key],-c['metrics']['coreCdSum']))
   print(json.dumps(dict(armor=armor,back=back,axis=key,order=c['order'],cost=c['cost'],metrics=c['metrics'],placements=[(p['part'],p['points']) for p in c['placements']]),ensure_ascii=False))
