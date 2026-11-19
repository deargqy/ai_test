(()=>{
  'use strict';
  const D=window.MODEL_DATA,M=window.ModelMath,$=id=>document.getElementById(id);
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=n=>n.toLocaleString('zh-CN'),off=new Set(),base=M.analyze(D);
  const names=['S 曙光盾','S 塞玛·量产','SS 链法手枪','S 虚空撕裂','S 式神野衾'],short=['背部','护甲','肩炮','手部','无人机'];
  const owner=id=>names[D.actual.order.indexOf(id)];
  const colors=['#efc775','#79dfbf','#84cafa','#efc775','#bd9bfa','#79dfbf','#84cafa','#efc775','#efc775','#84cafa'];
  const notes={
    'main-long':'背、甲共享主属性+200%，这里提高护盾。力量达到600后的额外条件未计入；不能把力量375当作已满足。',
    'growth-single':'只服务背部，每秒主属性+4%为加算成长。首轮能否等到、实际吸收多少盾，需要过程证据。开关不改变初始面板。',
    'cd-short':'背、甲共享−12.5%冷却；收益是更早使用与更多循环，不能直接乘进伤害。',
    'damage-long':'手、肩都具有坚固，分别获得+600%伤害。长桥遮挡手左中孔，替换需要把这项机会成本一起比较。',
    'hits-long':'手4→10段，肩3→9段，两端均有收益。遮挡肩右下孔；完整段数必须有命中和存活时间才兑现。',
    'charge-short':'手、肩使用时互相加速2秒。持续加速不是立即充能；本页只标出链是否存在，不伪造提前多少秒。',
    'cd-single':'肩炮单孔−10%冷却，当前读数6.9秒。替换后7.7秒是静态参考，首击还受开场科技与控制影响。',
    'damage-short':'+200%伤害短桥的两端都在无人机上，实际受益对象只有一件。与火控单孔可同时存在。',
    'calibration-single':'火控单孔当前+120%伤害、每天+40%。无人机静态数值按已有观测查表，不推造底数与舍入规则。',
    'blue-force':'无人机力量10→14，不能仅因它没有伤害统计行就视作无用；召唤数量与施放频率未在此模拟。'
  };
  let selected='damage-long',facet='startup';
  function selectPart(id){selected=id;renderLayout();}
  function renderLayout(){
    const a=M.analyze(D,[...off]);
    $('counts').innerHTML=[[a.parts.length+'/10','在用配件'],[a.counts.connected+'/21','连接孔'],[a.counts.blocked,'遮挡孔'],[a.counts.free,'空孔'],[fmt(a.coreVolley),'双核心静态完整轮']].map(([v,l])=>`<div class="metric"><strong>${v}</strong><span>${l}</span></div>`).join('');
    $('part-controls').innerHTML=D.actual.placements.map((p,i)=>`<div class="part-row"><input type="checkbox" id="part-${p.part}" data-toggle="${p.part}" ${off.has(p.part)?'':'checked'} aria-label="启用${esc(p.label)}"><button data-select="${p.part}" aria-pressed="${selected===p.part}">${i+1}. ${esc(p.label)}</button><label for="part-${p.part}">${off.has(p.part)?'已移除':'在用'}</label></div>`).join('');
    const x=v=>58+54*v,y=v=>128+70*v;
    let svg=D.gear.map((g,i)=>`<rect x="${x(i*4)-27}" y="25" width="182" height="285" rx="13" fill="#14283c" stroke="#2a4059"/><text x="${x(i*4)+64}" y="58" fill="#e4eef9" text-anchor="middle" font-size="16">${esc(names[i])}</text><text x="${x(i*4)+64}" y="85" fill="#a5b7cc" text-anchor="middle" font-size="12">${short[i]} · ${g.ports.length}孔</text>`).join('');
    svg+=a.parts.map(p=>{const i=D.actual.placements.findIndex(t=>t.part===p.part),[u,v]=p.points[0],last=p.points[p.points.length-1];return `<g data-select="${p.part}" role="button" tabindex="0" aria-label="查看${esc(p.label)}" style="cursor:pointer" opacity="${selected===p.part?1:.55}"><line x1="${x(u)}" y1="${y(v)}" x2="${x(last[0])}" y2="${y(last[1])}" stroke="${colors[i]}" stroke-width="${selected===p.part?12:8}" stroke-linecap="round"/><rect x="${(x(u)+x(last[0]))/2-13}" y="${y(v)-26}" width="26" height="20" rx="5" fill="${colors[i]}"/><text x="${(x(u)+x(last[0]))/2}" y="${y(v)-11}" fill="#102030" text-anchor="middle" font-size="13" font-weight="700">${i+1}</text></g>`;}).join('');
    svg+=a.audit.map(p=>`<g><circle cx="${x(p.point[0])}" cy="${y(p.point[1])}" r="7" stroke="${p.state==='connected'?'#79dfbf':p.state==='blocked'?'#ef9d97':'#a5b7cc'}" stroke-width="2" fill="${p.state==='connected'?'#79dfbf':'#101d2d'}"/>${p.state==='blocked'?`<text x="${x(p.point[0])}" y="${y(p.point[1])+5}" text-anchor="middle" fill="#ef9d97" font-size="17">×</text>`:''}<title>${esc(owner(p.owner))} (${p.point})：${{connected:'已连接',blocked:'桥身遮挡',free:'空闲'}[p.state]}</title></g>`).join('');
    $('slots').innerHTML=svg;
    const p=D.actual.placements.find(p=>p.part===selected),owners=base.owners[selected],blocked=base.audit.filter(p=>p.blockers.includes(selected));
    const without=M.analyze(D,[selected]);
    $('part-title').textContent=p.label+(off.has(selected)?' · 已移除':'');
    $('part-detail').innerHTML=`<div class="effect"><b>${owners.map(owner).map(esc).join(' ＋ ')}</b><br>${p.points.length}个端点 → ${owners.length}件装备受益</div><p>${esc(notes[selected])}</p><p>遮挡：${blocked.length?blocked.map(p=>esc(owner(p.owner))+' '+p.point).join('、'):'无'}</p><p class="fine">从验收配置单独移除此件：双核心静态完整轮变化 ${fmt(without.coreVolley-base.coreVolley)}。0变化不代表无战斗价值。</p>`;
    const u=a.units;
    $('unit-table').innerHTML=`<table><thead><tr><th>装备</th><th>静态属性估算</th><th>CD约值</th></tr></thead><tbody>${[['背部',fmt(u.back.shield)+'盾',u.back.cd],['护甲',fmt(u.armor.shield)+'盾',u.armor.cd],['肩炮',fmt(u.shoulder.damage)+' × '+u.shoulder.hits,u.shoulder.cd],['手部',fmt(u.hand.damage)+' × '+u.hand.hits,u.hand.cd],['无人机',u.drone.damage+'伤 / '+u.drone.force+'力量',u.drone.cd]].map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table><p class="fine">相对验收配置：双核心完整轮 ${fmt(a.coreVolley-base.coreVolley)}；互加速链${a.mutualAcceleration?'保留':'移除'}；背部每秒成长${a.dynamicGrowth?'保留':'移除'}。</p>`;
  }
  document.addEventListener('click',e=>{const b=e.target.closest('[data-select]');if(b)selectPart(b.dataset.select);});
  $('slots').addEventListener('keydown',e=>{const b=e.target.closest('[data-select]');if(b&&(e.key==='Enter'||e.key===' ')){e.preventDefault();selectPart(b.dataset.select);}});
  $('part-controls').addEventListener('change',e=>{const id=e.target.dataset.toggle;if(!id)return;e.target.checked?off.delete(id):off.add(id);selected=id;renderLayout();$('part-'+id).focus();});
  $('reset').addEventListener('click',()=>{off.clear();renderLayout();});
  const nodes=[
    ['tech',35,30,'开场科技','加速3秒 · 375力量','startup output'],
    ['hand',405,30,'快手 · 10段','面板CD 2.6秒','startup output'],
    ['shoulder',790,30,'肩炮 · 9段','坚固转伤 · 每层+6','startup output'],
    ['firm',405,205,'获得坚固','来源、次数和时机分开','startup output survival'],
    ['armor',790,205,'S甲随机加速','获得坚固 → 随机一件2.5秒','startup survival'],
    ['back',35,205,'S背产盾与减速','使用 → 坚固装备+15坚固','startup survival'],
    ['survive',35,375,'生命与护盾缓冲','191000HP · 产盾≠吸收','survival'],
    ['risk',405,375,'对手控制与爆发','禁用、减速可能截断循环','startup output survival'],
    ['growth',790,375,'持续支援','每秒力量 / 随机直接充能','startup output']
  ];
  const edges=[['tech','hand','开场加速','startup'],['hand','shoulder','使用 → 互加速2秒','startup'],['hand','firm','手产生坚固','output'],['back','firm','使用时增加','survival'],['firm','armor','获得时触发','startup'],['firm','shoulder','层数增伤','output'],['armor','shoulder','随机目标候选','startup'],['back','survive','产盾缓冲','survival'],['survive','risk','能否撑到出手？','survival']];
  function renderCombat(){
    document.querySelectorAll('[data-facet]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.facet===facet));
    const summaries={startup:'<strong>启动保障是候选链，尚非实测时间表。</strong> 开场加速帮助第一轮，快手与肩互加速；坚固触发S甲随机加速。随机目标与敌方控制会改变结果，首次有效命中仍未知。',output:'<strong>手肩共享高倍率与多段，目标是让两件核心都兑现。</strong> 伤害桥、+6段、力量及肩的坚固转伤组成输出；手有失盾增伤。无人机还提供力量支援。面板完整轮不包含命中损失与动态成长。',survival:'<strong>生命提供缓冲，背甲产盾与减速争取循环时间。</strong> 新背甲的初始盾低于旧配装，需要更快行动与成长补偿；没观察到吸收、首轮与循环次数前，不能宣称生存已升级。'};
    $('combat-summary').innerHTML=summaries[facet]+'<p class="fine">本图固定对应验收配置；配件页的移除试算不改变此历史触发图。</p>';
    const byId=Object.fromEntries(nodes.map(n=>[n[0],n]));
    let svg='<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#79dfbf"/></marker></defs>';
    for(const [from,to,label,type] of edges){
      const a=byId[from],b=byId[to],horizontal=a[2]===b[2],down=b[2]>a[2];
      let x1=a[1]+(horizontal?270:135),y1=a[2]+(horizontal?36:down?72:0),x2=b[1]+(horizontal?0:135),y2=b[2]+(horizontal?36:down?0:72);
      if(from==='firm'&&to==='shoulder'){x1=a[1]+210;x2=b[1]+55;}
      const ly=(y1+y2)/2-8,lx=(x1+x2)/2;
      svg+=`<g opacity="${type===facet?1:.38}"><path d="M${x1} ${y1} L${x2} ${y2}" stroke="#79dfbf" stroke-width="2" fill="none" marker-end="url(#arrow)"/><rect x="${lx-label.length*5.8}" y="${ly-13}" width="${label.length*11.6}" height="18" rx="4" fill="#101d2d"/><text x="${lx}" y="${ly}" fill="#d0f3e7" text-anchor="middle" font-size="11">${label}</text></g>`;
    }
    svg+=nodes.map(([id,x,y,t,sub,types])=>`<g opacity="${types.includes(facet)?1:.28}"><rect x="${x}" y="${y}" width="270" height="72" rx="12" fill="${id==='risk'?'#432d32':'#1c3547'}" stroke="${id==='risk'?'#ef9d97':'#79dfbf'}"/><text x="${x+16}" y="${y+28}" fill="#e4eef9" font-size="17" font-weight="600">${t}</text><text x="${x+16}" y="${y+53}" fill="#b9cbdd" font-size="13">${sub}</text></g>`).join('');
    $('chain').innerHTML=svg;
  }
  document.querySelectorAll('[data-facet]').forEach(b=>b.addEventListener('click',()=>{facet=b.dataset.facet;renderCombat();}));
  $('cooldowns').innerHTML=[['手部',2.6],['背部',5.2],['肩炮',6.9],['无人机',7.1],['护甲',11.4]].map(([l,v])=>`<div class="cd-row"><span>${l}</span><div class="track"><div class="bar" style="width:${v/13*100}%"></div></div><span>${v}秒</span></div>`).join('');
  $('tech').innerHTML=D.tech.map(t=>`<li>${esc(t)}</li>`).join('');
  const comparisons={
    'run05-d13':{result:'我方败',facts:[['敌首次有效伤害','约1–2秒（观察）'],['我方归零','约3秒'],['敌手部累计伤害','169,102'],['我伤害与护盾统计','栏位空，非精确0']],chain:'450初始力量 → 快速六连每命中力量+10% → 物伤产力量等额盾；背部增力与全体减速支援。',difference:'现在有开场加速与手肩/S甲联动，但没有证据证明能跨过约3秒死亡门槛。敌背/手1秒CD来源未知，不能照抄装备名就当已复刻。'},
    'run05-d16':{result:'我方败',facts:[['敌肩 / 手伤害','281,106 / 31,504'],['我手伤害','141,488'],['我肩伤害','无统计行'],['双方肩段数','均9段']],chain:'快手坚固成长 → S甲随机加速 + 直接充能 → 控制保护高倍率坚固肩；敌肩承担约89.9%已列伤害。',difference:'最后配置借鉴坚固与随机加速，但伤害倍率、充能方式、控制强度和历史成长不同。这场我方用旧B甲；不能说新S甲已经被实战验证。'},
    'run05-d15':{result:'我方胜',facts:[['我手 / 肩伤害','102,003 / 92,513'],['敌已列总伤害','25,305'],['其中感电','16,697'],['无人机力量贡献','48（增益统计）']],chain:'这场手肩都贡献伤害；无人机提供力量。敌有感电与开场禁用，未能阻止我方核心输出。',difference:'战时装备和最后背甲不同，不能把胜局全部归因于新构筑；首击、战斗时长、禁用实际目标仍未知。'}
  };
  function renderCase(){const id=$('case-select').value,c=D.cases.find(c=>c.id===id),v=comparisons[id];$('case-detail').innerHTML=`<span class="badge">${v.result} · 第${c.day}天</span><h3>${esc(c.enemyName)}</h3><div class="case-grid"><div>${v.facts.map(([k,t])=>`<div class="datum"><span>${k}</span><strong>${t}</strong></div>`).join('')}</div><div><h4>实际触发链与贡献</h4><p>${v.chain}</p><h4>与最后配置的差异</h4><p>${v.difference}</p></div></div><p><a href="opponent-library.html#${id}">完整案例、未知项与截图 →</a></p>`;}
  $('case-select').addEventListener('change',renderCase);
  $('upgrades').innerHTML=D.upgrades.priority.map((u,i)=>`<article class="upgrade"><div class="eyebrow">候选 ${i+1} · 待验证</div><h4>${esc(u.target)}</h4><p><b>落点：</b>${esc(u.placement)}</p><p><b>代价：</b>${esc(u.cost)}</p><p class="fine"><b>战后检查：</b>${esc(u.test)}</p></article>`).join('');
  const tabs=[...document.querySelectorAll('[data-tab]')];
  function showTab(id,focus=false){tabs.forEach(b=>{const yes=b.dataset.tab===id;b.setAttribute('aria-selected',yes);b.tabIndex=yes?0:-1;$(b.dataset.tab).hidden=!yes;if(yes&&focus)b.focus();});}
  function openLinkedTab(){
    const target = document.getElementById(location.hash.slice(1));
    const panel = target?.closest('[role="tabpanel"]');
    if (!panel) return;
    showTab(panel.id);
    target.scrollIntoView({block:'start'});
  }
  window.addEventListener('hashchange', openLinkedTab);
  tabs.forEach((b,i)=>{b.addEventListener('click',()=>showTab(b.dataset.tab));b.addEventListener('keydown',e=>{let n;if(e.key==='ArrowRight')n=(i+1)%tabs.length;if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;if(e.key==='Home')n=0;if(e.key==='End')n=tabs.length-1;if(n!==undefined){e.preventDefault();showTab(tabs[n].dataset.tab,true);}});});
  renderLayout();renderCombat();renderCase();
  openLinkedTab();
})();
