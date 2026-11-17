(function(root){
  'use strict';
  // Static counterfactuals for the verified day17 snapshot, not a combat simulator.
  function analyze(data,removed=[]){
    const off=new Set(removed),parts=data.actual.placements.filter(p=>!off.has(p.part));
    const ports=data.gear.flatMap((g,i)=>g.ports.map(([x,y])=>({point:[i*4+x,y],owner:g.id})));
    const key=p=>p.join(','),owners={},counts={connected:0,blocked:0,free:0};
    for(const p of parts)owners[p.part]=[...new Set(p.points.map(pt=>ports.find(x=>key(x.point)===key(pt)).owner))];
    const ends=new Set(parts.flatMap(p=>p.points.map(key)));
    const audit=ports.map(p=>{const [x,y]=p.point;const blockers=parts.filter(a=>a.points.length>1&&a.points[0][1]===y&&Math.min(...a.points.map(q=>q[0]))<x&&x<Math.max(...a.points.map(q=>q[0]))).map(a=>a.part);const state=ends.has(key(p.point))?'connected':blockers.length?'blocked':'free';counts[state]++;return {...p,state,blockers};});
    const has=id=>parts.some(p=>p.part===id),mult=1.1+(has('damage-long')?6:0),extra=has('hits-long')?6:0;
    const ceil=x=>Math.ceil(x-1e-8),round=x=>Math.round(x*10)/10;
    const units={
      back:{shield:ceil(260*(1.1+(has('main-long')?2:0))),cd:has('cd-short')?5.2:6}, // observed baseline UI
      armor:{shield:ceil(1230*(1.1+(has('main-long')?2:0))),cd:round(13*(has('cd-short')?.875:1))},
      shoulder:{damage:ceil(1016*mult),hits:3+extra,cd:has('cd-single')?6.9:7.7},
      hand:{damage:ceil(806*mult),hits:4+extra,cd:2.6},
      // Empirical lookup; do not pretend the unverified raw damage formula is known.
      drone:{damage:has('damage-short')?(has('calibration-single')?477:350):(has('calibration-single')?265:138),force:has('blue-force')?14:10,cd:7.1}
    };
    return {parts,owners,audit,counts,units,firstEffectiveHit:null,coreVolley:units.hand.damage*units.hand.hits+units.shoulder.damage*units.shoulder.hits,mutualAcceleration:has('charge-short'),dynamicGrowth:has('growth-single')};
  }
  const api={analyze};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ModelMath=api;
})(typeof window!=='undefined'?window:globalThis);
