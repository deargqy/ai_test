"""Evidence-based opponent case index; no game access or strength prediction."""
import argparse
import html
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
# Explicit historical observations only; never derive enemy tags from our build.
TRAITS={
 'run04-d08':['力量','百分比成长','属性转伤','充能'],
 'run04-d09':['燃烧','百分比成长','充能','额外结算','召唤'],
 'run05-d13':['力量','快速启动','百分比成长','物伤产盾','减速'],
 'run05-d15':['感电','开场禁用'],
 'run05-d16':['坚固','百分比成长','随机加速','直接充能','减速','周期禁用','使用触发禁用','属性转伤'],
}
NAMES={'run05-d13':'林弦','run05-d14':'Dempsey','run05-d15':'Ranka0423','run05-d16':'Rogas'}
def make_cases(data,snapshots):
    studies={s['id']:s for s in data.get('opponentStudies',[])}
    rows=[]
    for run in data['runs']:
        for day in run['days']:
            if day.get('outcome') not in ('win','loss'):continue
            cid=f"{run['id']}-d{day['day']:02d}"
            study=studies.get(cid);snap=snapshots.get(cid)
            evidence=list(day.get('images',[]))
            if study:evidence+=study.get('evidence',[])
            if snap:evidence+=snap.get('evidence',[])
            unique={}
            for e in evidence:
                if isinstance(e,dict) and e.get('src'):unique.setdefault(e['src'],e)
            equipment=(snap or {}).get('enemyEquipment',[])
            tech=(snap or {}).get('enemyTech',[])
            parts=(snap or {}).get('enemyParts',[])
            rows.append(dict(id=cid,runId=run['id'],day=day['day'],gameVersion=run.get('gameVersion'),
                ownOutcome=day['outcome'],enemyName=(snap or {}).get('opponent') or NAMES.get(cid),
                title=day.get('title',''),ownContext=day.get('before') or '当时我方条件未完整结构化；见原始对局记录',
                encounterSummary=day.get('after') or day.get('title',''),
                enemyMechanisms=TRAITS.get(cid,[]),mechanismEvidence='已核对历史复盘，非全文关键词自动推断' if cid in TRAITS else None,
                enemyEquipment=equipment,enemyTech=tech,enemyParts=parts,
                snapshotTiming='postbattle' if snap else 'mixed_historical_notes',
                stats={k:snap[k] for k in ('damage','defense','buffs','ownDefense','displayedHp','ownHp','enemyHp') if k in snap} if snap else None,
                firstEffectiveHit=(snap or {}).get('firstEffectiveHit',(snap or {}).get('firstHitSeconds')),
                durationSeconds=(snap or {}).get('durationSeconds'),
                coverage='装备/科技/配件有结构数据；时序仍待核' if equipment and tech and parts else '部分统计/科技' if snap else '历史摘要与证据索引',
                study=study,unknowns=(snap or {}).get('unknowns',(snap or {}).get('unknown',[])) or ['完整装备、科技、配件端点和首次命中未全部结构化'],
                evidence=list(unique.values()),sourceDay=f"data/playtest.json:runs[{run['id']}].days[{day['day']}]",
                predictionRefs=[d['id'] for d in day.get('decisions',[]) if d.get('phase')=='opponent'],
                validationUse='历史建模样本；不能同时计为未来独立验证样本'))
    return rows

def search(rows,query='',mechanism='',outcome=''):
    terms=query.casefold().split()
    return [r for r in rows if (not outcome or r['ownOutcome']==outcome)
            and (not mechanism or mechanism in r['enemyMechanisms'])
            and all(t in json.dumps(r,ensure_ascii=False).casefold() for t in terms)]

def render(rows):
    e=lambda x:html.escape(str(x),quote=True)
    cards=[]
    for r in reversed(rows):
        study=r['study'] or {}
        refs=' · '.join(f'<a href="{e(x["src"])}">{e(x.get("label","证据"))}</a>' for x in r['evidence'])
        full=json.dumps({k:r[k] for k in ('enemyEquipment','enemyTech','enemyParts','stats','unknowns','predictionRefs')},ensure_ascii=False,indent=2)
        tags=' / '.join(r['enemyMechanisms']) or '敌方机制尚未单独标注'
        cards.append(f'''<article id="{r['id']}" data-outcome="{r['ownOutcome']}" data-mechanisms="{e(json.dumps(r['enemyMechanisms'],ensure_ascii=False))}" data-search="{e(json.dumps(r,ensure_ascii=False).casefold())}">
<h2>{e(r['enemyName'] or '对手姓名未录')} <small>{r['id']} · 我方{'胜' if r['ownOutcome']=='win' else '负'}</small></h2>
<p class="tags">{e(tags)}</p><p>{e(r['coverage'])} · 版本{e(r['gameVersion'] or '未知')} · {'战后快照' if r['snapshotTiming']=='postbattle' else '历史混合记录'}</p>
<p><b>对战观察：</b>{e(study.get('observed') or r['encounterSummary'])}</p>
<p><b>可借鉴：</b>{e(study.get('transferable') or '尚未提炼；不能仅凭胜负认定该配装强弱')}</p>
<p><b>下次核对：</b>{e(study.get('nextPrediction') or '先补齐核心、科技和端点，再比较双方启动、生存、控制与成长差异')}</p>
<details><summary>双方条件、缺失字段和原始证据</summary><p><b>当时我方：</b>{e(r['ownContext'])}</p><p>{e(study.get('unknown',''))}</p><pre>{e(full)}</pre><p>{refs or '没有关联截图；回原对局记录核对'}</p></details></article>''')
    mechanisms=sorted({t for r in rows for t in r['enemyMechanisms']})
    opts=''.join(f'<option>{e(t)}</option>' for t in mechanisms)
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>对手配装案例库</title><style>body{max-width:1120px;margin:auto;padding:24px;background:#101c2c;color:#e3edf8;font:16px/1.65 system-ui}a{color:#8dceff}article,section{background:#1a2c42;border-radius:12px;padding:22px;margin:16px 0}h1,h2{line-height:1.3}small{font-size:14px;color:#b6c9dc}input,select{font:inherit;padding:8px;margin:4px;max-width:95%}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.tags{color:#ffdb91}[hidden]{display:none!important}.flow{border-left:4px solid #79d6b6;padding-left:18px}summary{cursor:pointer}</style>
<h1>对手配装案例库</h1><p>胜过和输过的对手一起保留。当前是逐游戏日的历史索引；同日重随、额外首领没有单独穷举。未知终局不算新战果。</p>
<p><a href="models.html">战力与配件交互模型</a> · <a href="rsi-workflow.html">对局与RSI</a> · <a href="opponent-studies.html">15场败局详解</a> · <a href="../data/opponents.json">可检索数据</a></p>
<section><div class="flow">识别核心／科技／配件端点 → 找历史案例 → 比较双方差异 → 写首击与风险预测 → 战后校验</div><p>姓名只用于定位。真正需要比较的是装备实际数值与成长、机师、开场状态、确定/随机充能、控制、核心倍率、有效段数、生命和盾。战后冷却不冒充开局冷却，累计伤害不等于DPS或战力。</p><p>全文搜索可能匹配我方叙述；“敌方机制”筛选仅用已明确核对的敌方标签。未标注不代表没有。命中案例不自动产生胜率，历史建模样本不能同时充当独立验证。</p></section>
<label>全文 <input id="q" placeholder="例如 Rogas、充能、林弦"></label><label>我方结果 <select id="outcome"><option value="">全部</option><option value="win">胜</option><option value="loss">负</option></select></label><label>敌方机制 <select id="mechanism"><option value="">全部</option>'''+opts+'''</select></label><p id="count" aria-live="polite"></p><main>'''+''.join(cards)+'''</main><p id="empty" hidden>没有匹配案例；这不是“此构筑不存在”的证据。</p><script>
const cards=[...document.querySelectorAll('article')],q=document.querySelector('#q'),o=document.querySelector('#outcome'),m=document.querySelector('#mechanism');
function filter(){const terms=q.value.toLowerCase().trim().split(/\\s+/).filter(Boolean);let n=0;for(const c of cards){const ok=(!o.value||c.dataset.outcome===o.value)&&(!m.value||JSON.parse(c.dataset.mechanisms).includes(m.value))&&terms.every(t=>c.dataset.search.includes(t));c.hidden=!ok;if(ok)n++;}document.querySelector('#count').textContent=`显示 ${n} / ${cards.length} 个对战案例`;document.querySelector('#empty').hidden=n!==0;}
[q,o,m].forEach(x=>x.addEventListener('input',filter));filter();</script></html>'''
    return page

def build(root=ROOT):
    p=root/'data/playtest.json';data=json.loads(p.read_text(encoding='utf-8'))
    snapshots={}
    for cid,fn in [('run05-d14','day14-player-result.json'),('run05-d15','day15-player-result.json'),('run05-d16','day16-player-loss.json')]:
        snapshots[cid]=json.loads((root/'runs/run05'/fn).read_text(encoding='utf-8'))
    rows=make_cases(data,snapshots)
    payload=dict(schemaVersion=1,updatedAt=datetime.now(timezone.utc).isoformat(),cases=rows,
        note='从逐日历史资料生成，缺失不等于零；非完整敌方配装全集，不输出战力或胜率')
    (root/'data/opponents.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'docs/opponent-library.html').write_text(render(rows),encoding='utf-8')
    return rows

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['build','search']);ap.add_argument('--query',default='');ap.add_argument('--mechanism',default='');ap.add_argument('--outcome',default='',choices=['','win','loss']);args=ap.parse_args()
    if args.command=='build':
        rows=build();print(json.dumps(dict(cases=len(rows),wins=sum(r['ownOutcome']=='win' for r in rows),losses=sum(r['ownOutcome']=='loss' for r in rows)),ensure_ascii=False))
    else:
        rows=json.loads((ROOT/'data/opponents.json').read_text(encoding='utf-8'))['cases']
        print(json.dumps(search(rows,args.query,args.mechanism,args.outcome),ensure_ascii=False,indent=2))
