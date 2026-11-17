import pathlib,json
p=pathlib.Path('docs/bugs/004-weapon-tooltip/index.html')
s=p.read_text(encoding='utf-8')
a='<h2>第四局第8天动态伤害补充</h2><p>2026-11-16，同版本战后同屏：敌肩卡面53.9k，而说明为4次3477；敌SS刀卡面130.0k，而说明为3次7502。对手存在初始225力量、命中力量+15%、力量转伤肩、伤害+300%和充能等机制。差异可见，但尚未区分基础值、实时加成和额外转伤，不能据此认定伤害结算错误。</p><figure><img src="04-run04-shoulder.jpg" alt="第四局力量肩卡面与说明不同"><figcaption>力量肩：53.9k与3477。</figcaption></figure><figure><img src="05-run04-sword.jpg" alt="第四局SS刀卡面与说明不同"><figcaption>SS刀：130.0k与7502。</figcaption></figure>'
if '第四局第8天动态伤害补充' not in s:p.write_text(s.replace('</main>',a+'</main>'),encoding='utf-8')
p=pathlib.Path('data/playtest.json');d=json.loads(p.read_text(encoding='utf-8'));i=next(x for x in d['issues'] if x['id']=='004');o={'runId':'run04','day':8}
if o not in i['occurrences']:i['occurrences'].append(o)
if '第四局第8天动态伤害补充' not in i['detailHtml']:i['detailHtml']=i['detailHtml'].replace('</main>',a.replace('04-run04-shoulder.jpg','bugs/004-weapon-tooltip/04-run04-shoulder.jpg').replace('05-run04-sword.jpg','bugs/004-weapon-tooltip/05-run04-sword.jpg')+'</main>')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
