// Exercises the actual generated filter script with a minimal DOM. Not visual QA.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'docs/opponent-library.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'data/opponents.json'),'utf8')).cases;
const decode=s=>s.replace(/&quot;/g,'"').replace(/&#x27;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
const cards=[...src.matchAll(/<article id="([^"]+)" data-outcome="([^"]*)" data-mechanisms="([^"]*)" data-search="([^"]*)">/g)].map(m=>({id:m[1],dataset:{outcome:m[2],mechanisms:decode(m[3]),search:decode(m[4])},hidden:false}));
if(cards.length!==data.length)throw Error('missing rendered cases');
const el=Object.fromEntries(['q','outcome','mechanism','count','empty'].map(k=>[k,{value:'',addEventListener(){}}]));
const ctx=vm.createContext({document:{querySelectorAll:()=>cards,querySelector:s=>el[s.slice(1)]}});
vm.runInContext(src.match(/<script>([\s\S]*?)<\/script>/)[1],ctx);
function check(q,o,m,expected){el.q.value=q;el.outcome.value=o;el.mechanism.value=m;vm.runInContext('filter()',ctx);const actual=cards.filter(c=>!c.hidden).map(c=>c.id).sort();if(JSON.stringify(actual)!==JSON.stringify(expected.sort()))throw Error(JSON.stringify({q,o,m,actual,expected}));}
check('','','',data.map(x=>x.id));
check('','win','',data.filter(x=>x.ownOutcome==='win').map(x=>x.id));
check('','loss','',data.filter(x=>x.ownOutcome==='loss').map(x=>x.id));
check('roGAs','','',['run05-d16']);
check('','','快速启动',['run05-d13']);
check('','win','开场禁用',['run05-d15']);
check('no_such_opponent','','',[]);if(el.empty.hidden)throw Error('empty state missing');
console.log('7 generated-page filter scenarios passed; DOM only, not browser rendering.');
