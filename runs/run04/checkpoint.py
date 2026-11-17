import json,pathlib,sys,datetime
root=pathlib.Path(__file__).resolve().parents[2]
c=json.loads((root/sys.argv[1]).read_text(encoding='utf-8'))
p=root/'data/playtest.json';d=json.loads(p.read_text(encoding='utf-8'))
r=next(x for x in d['runs'] if x['id']=='run04')
r.update(c.get('run_fields',{}))
for change in c.get('memory_revisions',[]):
 m=next(x for x in d['memories'] if x['id']==change['id'])
 old={k:v for k,v in m.items() if k!='history'}
 m['revision']+=1
 m.update(change.get('fields',{}))
 m['evidence'].extend(change.get('evidence',[]))
 m['history'].append({'date':'2026-11-16','revision':m['revision'],'change':change['change'],'previous':old})
day=next((x for x in r['days'] if x['day']==c['day']),None)
if day is not None: day.update(c.get('day_fields',{}))
d['updatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=root/'GAME-NOTES.md';s=p.read_text(encoding='utf-8');a=s.index('## 本局快照')+len('## 本局快照');b=s.index('### Mac 串流阶段');s=s[:a]+'\n\n'+c['snapshot']+'\n\n'+s[b:];p.write_text(s,encoding='utf-8')
p=root/'README.md';s=p.read_text(encoding='utf-8');a=s.index('## 当前进度')+len('## 当前进度');b=s.index('\n\n2026-11-16，本机');s=s[:a]+'\n\n'+c['snapshot']+s[b:]
entry='- '+c['log']
if entry not in s:s=s.replace('## 工作日志\n','## 工作日志\n\n'+entry+'\n',1)
p.write_text(s,encoding='utf-8')
