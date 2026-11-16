"use strict";
const data = window.PLAYTEST_DATA;
const view = document.getElementById("view");
function esc(value) {
 return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}
function link(url, text, cls="") { return '<a class="'+cls+'" href="'+esc(url)+'">'+esc(text)+'</a>'; }
function para(text) { return '<p>'+esc(text)+'</p>'; }
function dayLink(id, day) {
 const run=data.runs.find(r=>r.id===id);
 return link("#runs/"+id+"/"+day,(run?.title||id)+" · 第 "+day+" 天");
}
function workflow() {
 return '<details id="workflow"><summary>AI 怎样做一次决定 · 下一局执行方案</summary>'+
 data.protocol.steps.map(s=>'<h3>'+esc(s.title)+'</h3>'+para(s.text)).join("")+
 '<p class="notice">'+esc(data.protocol.nextExperiment)+'</p>'+para("基线 · "+data.protocol.baseline)+
 '<ul>'+data.protocol.metrics.map(m=>'<li>'+esc(m)+'</li>').join("")+'</ul>'+
 link("RSI-RUNBOOK.md","下一局执行说明")+'</details><details><summary>历史打法、按钮实测与讨论稿</summary><p>'+
 link("rsi-history.html#playbook","v0.1—v0.5 完整打法")+' · '+link("rsi-history.html#verified","按钮实测")+' · '+
 link("rsi-history.html#review","保留的讨论稿")+'</p></details>';
}
function memoryPage(id) {
 const m=data.memories.find(m=>m.id===id)||data.memories[0], latest=data.runs.at(-1);
 const uses=data.runs.flatMap(r=>r.days.flatMap(d=>d.decisions.filter(x=>x.before.memories.some(u=>u.id===m.id)).map(x=>'<p>'+dayLink(r.id,d.day)+' · '+esc(x.before.chosenAction)+' · '+esc(x.after?.observed||"等待结果")+'</p>'))).join("");
 return '<div class="actions"><h2>下一局会用到的经验</h2>'+link("#runs/"+latest.id+"/"+(latest.days.at(-1)?.day||1),latest.title+" · "+latest.result,"button")+'</div><div class="layout"><aside>'+
 data.memories.map(x=>link("#memory/"+x.id,x.title+" · "+x.status,"item "+(x.id===m.id?"current":""))).join("")+
 '</aside><div><article class="panel"><h2>'+esc(m.title)+'</h2><span class="badge">'+esc(m.status)+'</span><p class="small">'+esc(m.id)+" · 修订 "+m.revision+" · 游戏版本 "+esc(m.gameVersion)+'</p>'+
 [["什么时候用",m.condition],["下次具体做什么",m.action],["用什么结果核对",m.expected],["适用边界",m.caveat]].map(([t,v])=>'<h3>'+t+'</h3>'+para(v)).join("")+
 '<h3>这条经验从哪里来</h3>'+m.evidence.map(e=>'<p>'+dayLink(e.runId,e.day)+' · '+esc(e.note)+(e.href?' · '+link(e.href,"原图"):"")+'</p>').join("")+
 '<h3>后来用上了吗</h3>'+(uses||'<p class="small">尚无按该经验编号登记的后续调用。下一局开始记录实际使用和结果。</p>')+
 '<details><summary>修订记录</summary>'+m.history.map(h=>para(h.date+" · 修订 "+h.revision+" · "+h.change)).join("")+'</details></article>'+workflow()+'</div></div>';
}
function decisionHtml(d) {
 return '<section class="panel"><h3>'+esc(d.id)+" · "+esc(d.before.chosenAction)+'</h3>'+para(d.before.state)+para("目标 · "+d.before.goal)+para("经验检索 · "+d.before.memorySearch)+
 d.before.memories.map(m=>'<p>'+link("#memory/"+m.id,m.id)+" · 修订 "+m.revision+" · "+(m.origin==="autonomous"?"自主调用":"玩家提醒")+" · "+esc(m.reason)+'</p>').join("")+
 '<details><summary>比较过的选择</summary>'+d.before.candidates.map(c=>'<h4>'+esc(c.action)+'</h4>'+para("收益 · "+c.benefit)+para("代价 · "+c.cost)+para("风险 · "+c.risk)+para("未知 · "+c.unknown)).join("")+'</details>'+
 para("原预测 · "+d.before.prediction)+para("实际结果 · "+(d.after?.observed||"等待回填"))+
 [...d.before.evidence,...(d.after?.evidence||[])].map(e=>link(e,"证据")).join(" · ")+'</section>';
}
function runPage(id, number) {
 const r=data.runs.find(r=>r.id===id)||data.runs.at(-1),d=r.days.find(d=>d.day===Number(number))||r.days.at(-1);
 const picker='<div class="actions">'+data.runs.map(r=>link("#runs/"+r.id+"/"+(r.days.at(-1)?.day||1),r.title+" · "+r.result,"button")).join("")+link("#bugs","全部 Bug 与异常","button")+'</div>';
 if(!d)return picker+para("新局已建立，等待现场决策记录。");
 const related=data.memories.filter(m=>m.evidence.some(e=>e.runId===r.id&&e.day===d.day));
 const issues=data.issues.filter(i=>i.occurrences.some(o=>o.runId===r.id&&o.day===d.day));
 return picker+'<p class="small">日期 '+esc(r.date)+'　·　终局时刻 '+esc(r.endedAt||"未完整记录")+'　·　实际总耗时 '+(r.durationMinutes==null?"未完整记录":r.durationMinutes+" 分钟")+'</p><div class="layout"><aside><h3>'+esc(r.title)+'完整时间线</h3><select class="mobile-day" id="day-select" aria-label="选择游戏日">'+
 r.days.map(x=>'<option value="#runs/'+r.id+'/'+x.day+'" '+(x.day===d.day?"selected":"")+'>第 '+x.day+' 天 · '+esc(x.title)+'</option>').join("")+'</select><div class="day-list">'+
 r.days.map(x=>link("#runs/"+r.id+"/"+x.day,"第 "+x.day+" 天 · "+x.title+"　"+x.wins+"胜"+x.losses+"负","item "+(x.day===d.day?"current":""))).join("")+
 '</div></aside><div><article class="panel"><h2>第 '+d.day+' 天 · '+esc(d.title)+'</h2><span class="badge">'+esc(d.phase)+" · "+d.wins+"胜"+d.losses+'负</span>'+
 (d.before?'<div class="columns"><div><h3>当时的行动与判断</h3>'+para(d.before)+'</div><div><h3>结果与疑问</h3>'+para(d.after)+'</div></div>':"")+
 '<div class="notice"><h3>当时用到了哪些经验</h3>'+para(d.legacyUsage||"逐条引用见下方决策记录。")+'</div>'+
 (related.length?'<h3>由这段记录整理的经验</h3>'+related.map(m=>'<p>'+link("#memory/"+m.id,m.title)+" · "+esc(m.status)+'</p>').join(""):"")+
 '<details><summary>完整当天记录与原始截图</summary>'+d.detailHtml+
 (d.decisions.length?"":'<p>'+d.images.map(i=>link(i.src,i.label)).join(" · ")+'</p>')+'</details><p class="small">'+d.sources.map(s=>link(s,"原始复盘")).join(" · ")+'</p></article>'+
 d.decisions.map(decisionHtml).join("")+'<section class="panel"><h3>当天关联的 Bug 与异常</h3>'+
 (issues.length?issues.map(i=>'<p>'+link("#bugs/"+i.id,i.id+" · "+i.title)+' <span class="badge">'+esc(i.status)+'</span></p>').join(""):para("当前归档没有关联到这一天的异常报告。"))+'</section></div></div>';
}
function bugPage(id) {
 const issue=data.issues.find(i=>i.id===id);
 return '<div class="actions"><h2>Bug 与异常</h2>'+link("#runs/run02/16","返回对局记录","button")+'</div><div class="layout"><aside>'+
 data.issues.map(i=>link("#bugs/"+i.id,i.id+" · "+i.title,"item "+(issue?.id===i.id?"current":""))).join("")+'</aside><div>'+
 (issue?'<article class="panel"><h2>'+esc(issue.title)+'</h2><span class="badge">'+esc(issue.status)+'</span>'+para(issue.summary)+
 '<h3>出现在哪些对局</h3><div class="actions">'+issue.occurrences.map(o=>dayLink(o.runId,o.day)).join("")+'</div><details open><summary>报告与原始证据</summary>'+issue.detailHtml+'</details>'+link(issue.source,"独立报告原页")+'</article>':
 data.issues.map(i=>'<article class="panel"><h3>'+link("#bugs/"+i.id,i.id+" · "+i.title)+'</h3>'+para(i.summary)+'<span class="badge">'+esc(i.status)+'</span></article>').join(""))+'</div></div>';
}
function render() {
 let hash;
 try{hash=decodeURIComponent(location.hash.slice(1));}catch{hash="memory/M01";}
 if(["verified","review","feedback"].includes(hash)){location.replace("rsi-history.html#"+hash);return;}
 const aliases={playbook:"memory/M01",workflow:"memory/M01",issues:"bugs","opponent-issue":"bugs/001",checkpoint:"runs/run02/16"};
 const [page,id,day]=(aliases[hash]||hash||"memory/M01").split("/");
 view.innerHTML=page==="runs"?runPage(id,day):page==="bugs"?bugPage(id):memoryPage(id);
 document.querySelectorAll("header nav a").forEach((a,index)=>{
  if(index===(page==="runs"||page==="bugs"?1:0))a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");
 });
 const select=document.getElementById("day-select");
 if(select)select.addEventListener("change",()=>{location.hash=select.value;});
 if(hash==="workflow")document.getElementById("workflow").open=true;
}
window.addEventListener("hashchange",render);
render();
