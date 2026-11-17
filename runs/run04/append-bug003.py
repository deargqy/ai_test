import json,pathlib
p=pathlib.Path('docs/bugs/003-sale-overlay/index.html');s=p.read_text(encoding='utf-8')
addition='<h2>第四局第4天再次观察</h2><p>2026-11-16 15:30，旧C手出售尝试后余额仍26，已关闭仓库进入林恩对话，左侧仍显示释放以出售与价格2。此次出售是否成功尚未确认，因此只证明退出仓库后提示残留，不将拖放当作有效出售。</p><figure><a href="06-run04-event.jpg"><img src="06-run04-event.jpg" alt="第四局进入对战事件仍残留出售提示"></a><figcaption>第四局第4天，林恩对话。</figcaption></figure>'
if '第四局第4天再次观察' not in s:p.write_text(s.replace('</main>',addition+'</main>'),encoding='utf-8')
p=pathlib.Path('data/playtest.json');d=json.loads(p.read_text(encoding='utf-8'));i=next(x for x in d['issues'] if x['id']=='003');i['status']='第四局再次观察';o={'runId':'run04','day':4}
if o not in i['occurrences']:i['occurrences'].append(o)
if '第四局第4天再次观察' not in i['detailHtml']:i['detailHtml']=i['detailHtml'].replace('</main>',addition.replace('06-run04-event.jpg','bugs/003-sale-overlay/06-run04-event.jpg')+'</main>')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
