import json,pathlib,datetime
p=pathlib.Path('data/playtest.json');d=json.loads(p.read_text(encoding='utf-8'));r=next(x for x in d['runs'] if x['id']=='run04');r.update(startedAt='2026-11-16T14:42:51+08:00',result='进行中：第1天0胜0负',pilot='胡班·本·帕尔文');day=r['days'][0];day.update(title='30金币开局，重新检查整排布局',phase='开局选择',outcome='unknown',before='玩家要求第三局停止重开，并讨论寒冷强度与装备换序。选择胡班，开局额外30金币。',after='新局已确认：Lv1/1500生命/30金币/0胜0负/3次失败上限；尚未领取初始装甲。',detailHtml='<p>本轮不预先锁定流派。比较初始装备的输出方式和被动后，再按实际供给补强。每次换装读取左右槽位，至少比较当前顺序与主力移到中间的排列，核对两端触发及频率后才购买配件。</p><p>取舍：胡班把资源集中在开局，可同时补生命与装备；代价为只有3次失败。本次没有声称该角色最强。</p>',images=[{'src':'playtest-2026-11-16-run04/day01-start.jpg','label':'第四局开局确认'}])
for r0 in d['runs']:
 for day0 in r0['days']:
  for img in day0.get('images',[]):
   if 'caption' in img and 'label' not in img: img['label']=img.pop('caption')
d['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
snap='第四局run04已于2026-11-16 14:42:51（香港时间）确认开始。胡班·本·帕尔文：开局额外30金币，3次失败上限；第1天0胜0负、Lv1、1500生命、30金币，停在初始装甲自选/随机选项，尚无装备。第三局按用户要求停止于0胜2负，非自然终局。当前讨论结论：不能由两败断言寒冷流派弱；B冷甲双下槽漏用说明M05引用未落实。下一步先选装甲与主武，比较整排槽位和有效触发后购物；不预锁流派。证据 docs/playtest-2026-11-16-run04/day01-start.jpg；M05修订3来自玩家再次提醒。'
p=pathlib.Path('GAME-NOTES.md');s=p.read_text(encoding='utf-8');a=s.index('## 本局快照')+len('## 本局快照');b=s.index('### Mac 串流阶段');s=s[:a]+'\n\n'+snap+'\n\n'+s[b:];p.write_text(s,encoding='utf-8')
p=pathlib.Path('README.md');s=p.read_text(encoding='utf-8');a=s.index('## 当前进度')+len('## 当前进度');b=s.index('\n\n2026-11-16，本机');s=s[:a]+'\n\n'+snap+s[b:];s=s.replace('## 工作日志\n','## 工作日志\n\n- 2026-11-16 14:42：第四局已重开，胡班30金币开局状态已确认。原选角决定先写入文件，确认新局后导入RSI；第三局原始判断、两败统计和Bug截图全部保留。当前停在初始装甲领取，下一步按用户讨论后的全排布局规则进行初始选择。\n',1);p.write_text(s,encoding='utf-8')
