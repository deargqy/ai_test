import json, pathlib, datetime
root=pathlib.Path(__file__).resolve().parents[2]
p=root/'data/playtest.json'
d=json.loads(p.read_text(encoding='utf-8'))
r=next(x for x in d['runs'] if x['id']=='run03')
day=r['days'][0]
day.update(title='若茜冷系开局，首战低估燃烧',phase='挑战赛',outcome='loss',wins=0,losses=1,before='若茜开战全装备充能50%，3次失败上限。Lv4/7500生命，C力甲、C冷枪、B冷肩炮、C冷无人机，320盾短桥共享。',after='0胜1负。输出10837，敌方燃烧8320为主要压力。我方手武护盾1600、装甲1440；无人机未见护盾条目。',detailHtml='<p>选角前核对十只猫的能力，选择若茜的启动优势并承担少一条命的代价。初始事件胜利后，升级到Lv4，买B冷肩炮与冷无人机；出售闲置燃烧肩炮，4金币买修复短桥。</p><p>重排无人机与冷枪，通过中心对齐完成共享连接。免费换掉30000生命对手，改打12500生命全C五件装备。战前倾向胜被反驳；对手燃烧8320伤害，加上基础HP差与持续防御，耗尽我方生命。精确首击时间未完整捕获，不能称启动模型验证通过。</p><p>共享护盾只在手武有统计，召唤卡与召唤物使用语义待验证，单独保存问题008。</p>',images=[{'src':'playtest-2026-11-16-run03/day01-result.jpg','caption':'首日失败结算'},{'src':'playtest-2026-11-16-run03/day01-damage.jpg','caption':'双方伤害来源'},{'src':'playtest-2026-11-16-run03/day01-defense.jpg','caption':'防御统计：未见无人机盾'}])
r.update(wins=0,losses=1,result='进行中：0胜1负')
for mid,action,caveat,note,href in [
('M02','比较双方首次与重复触发、成长、护盾、回复，并估计被击倒时间；把基础生命差与燃烧等持续伤害纳入，不能仅比较卡面攻击。','累计护盾和回复不等于有效吸收；持续伤害对护盾的具体交互需实测。','run03首日倾向胜被反驳：7500对12500生命，敌方燃烧8320，我方输出10837仍失败。','day01-damage.jpg'),
('M04','确认配件位置、两端同高和词条适用；短桥可用中心对齐两槽中点，操作后核对连线。不要固定认为左端抓取一定可用。','run03的320盾短桥左端拖拽两次提示无效，中心对齐成功；其他形状继续现场核对。','同一短桥从左端拖到槽位失败，改中心拖到两槽中点成功。','day01-shared-shield-equipped.jpg'),
('M05','比较整排有效连接与丢失收益；除槽位接通外，还要确认使用、攻击、召唤等触发语义，战后核对两端实际来源。','run03冷枪和无人机共享320盾桥：统计仅手武1600，未见无人机盾。可能是召唤卡使用规则，尚不能确定为Bug。','共享320盾短桥接上两件，但首战防御只有手武与装甲；不能把视觉连接当双端收益已验证。','day01-defense.jpg')]:
 m=next(x for x in d['memories'] if x['id']==mid)
 old={k:v for k,v in m.items() if k!='history'}
 m['revision']+=1
 m.update(action=action,caveat=caveat)
 m['history'].append({'date':'2026-11-16','revision':m['revision'],'change':note,'previous':old})
 m['evidence'].append({'runId':'run03','day':1,'note':note,'href':'playtest-2026-11-16-run03/'+href})
d['memories'].append({'id':'M09','revision':1,'title':'开局先把猫的能力和生命数纳入计划','phases':['observe','shop','build','opponent'],'tags':['机师','角色','经济','充能','容错'],'condition':'新开一局，或者基于其他角色经验计算资源、成长与启动。','action':'先读猫能力和可失败次数，再建立经济、成长、首轮冷却基线。若茜开局50%充能不等于整场CD减半，也不继承莫瑟每日主属性增长。','expected':'角色能力截图与选择理由可查；后续按当前角色估计首次/重复触发。','caveat':'角色差异由玩家提醒，十位能力由本轮自主查看。尚未比较各角色胜率。','status':'机制文字已核对，强度待验证','gameVersion':'1.0.0.2218','evidence':[{'runId':'run03','day':1,'note':'查看十位机师后选择若茜；50%初始充能与3次失败上限。','href':'playtest-2026-11-16-run03/pilot-ruoqian.jpg'}],'history':[{'date':'2026-11-16','revision':1,'change':'根据玩家提醒与本局选角调查建立角色前提经验。'}]})
d['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
snap='第三局 run03：若茜（开战全装备充能50%，3次失败上限），版本1.0.0.2218。第1天结束0胜1负，Lv4、7500生命、2/10经验、25金币。C力甲480盾/32力量；C冷枪180×3/2寒冷；B冷肩410×3/20寒冷且按敌寒冷成长；C冷无人机6伤5寒冷；背部空。无人机—冷枪共享320盾短桥，首战仅手武1600盾，召唤端触发待核。下一步离开日末事件，优先补生命/防御，检查科技与商店。证据 docs/playtest-2026-11-16-run03/day01-result.jpg，决策 runs/run03/，原始数据 data/playtest.json。'
p=root/'GAME-NOTES.md';s=p.read_text(encoding='utf-8');a=s.index('## 本局快照')+len('## 本局快照');b=s.index('### Mac 串流阶段');s=s[:a]+'\n\n'+snap+'\n\n'+s[b:];p.write_text(s,encoding='utf-8')
p=root/'README.md';s=p.read_text(encoding='utf-8');a=s.index('## 当前进度')+len('## 当前进度');b=s.index('\n\n2026-11-16，本机');s=s[:a]+'\n\n'+snap+s[b:];s=s.replace('## 工作日志\n','## 工作日志\n\n- 2026-11-16 14:00—14:21：第三局首日0胜1负。保留战前预测及失败反例，按实际燃烧伤害修订M02；短桥中心对齐实测修订M04，共享召唤端收益未证实修订M05；新增角色前提M09。下一步补生存并继续，未知项不伪装成已校准模型。\n',1);p.write_text(s,encoding='utf-8')
