import pathlib,json
p=pathlib.Path('data/playtest.json');d=json.loads(p.read_text(encoding='utf-8'))
h=pathlib.Path('docs/bugs/009-boss-life-text/index.html').read_text(encoding='utf-8');body=h[h.index('<main>'):h.index('</main>')+7].replace('../../rsi-workflow.html','rsi-workflow.html').replace('01-boss-text.jpg','bugs/009-boss-life-text/01-boss-text.jpg')
if not any(x['id']=='009' for x in d['issues']):d['issues'].append({'id':'009','title':'首领扣命提示与玩家说明冲突','status':'候选：尚未实测失败结算','summary':'界面写首领失败扣命，用户明确说明不掉命；待下一次首领核对。','source':'bugs/009-boss-life-text/index.html','detailHtml':body,'occurrences':[{'runId':'run04','day':9}]})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
