// Offline DOM smoke check: exercises generated page JS, not a browser render.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../..');
const source=fs.readFileSync(path.join(root,'docs/loadout-lab.html'),'utf8');
const ids=[...source.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
if(new Set(ids).size!==ids.length)throw Error('duplicate IDs');
const elements=Object.fromEntries(ids.map(id=>[id,{value:'0',innerHTML:'',textContent:''}]));
elements.sort.value='2';
const ctx=vm.createContext({document:{getElementById:id=>{if(!elements[id])throw Error('missing element '+id);return elements[id]}},console});
vm.runInContext(source.match(/<script>([\s\S]*)<\/script>/)[1],ctx);
let checked=0;
for(let policy=0;policy<2;policy++)for(const sort of ['0','1','2','cost']){
 elements.policy.value=String(policy);elements.sort.value=sort;
 vm.runInContext('refresh()',ctx);
 const n=vm.runInContext('shown.length',ctx);
 for(let i=0;i<n;i++){
  elements.candidates.value=String(i);vm.runInContext('show()',ctx);checked++;
  if(!elements.diagram.innerHTML.includes('<svg')||/NaN|undefined/.test(elements.diagram.innerHTML+elements.metrics.innerHTML))throw Error('bad rendered markup');
 }
}
console.log(JSON.stringify({checkedCandidateViews:checked,kind:'DOM smoke only; not browser visual QA'}));
