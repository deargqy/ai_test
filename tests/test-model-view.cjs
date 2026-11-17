const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),M=require('../docs/model-math.js');
const actual=JSON.parse(fs.readFileSync(path.join(root,'runs/run05/day17-actual-loadout.json'),'utf8'));
const catalog=JSON.parse(fs.readFileSync(path.join(root,'runs/run05/day17-loadout-input.json'),'utf8'));
const data={actual,gear:actual.order.map(id=>catalog.equipment.find(x=>x.id===id))};
let x=M.analyze(data,[]);
assert.deepEqual(x.counts,{connected:16,blocked:2,free:3});
assert.deepEqual(x.owners['damage-short'],['drone-s-live']);
assert.equal(x.units.hand.hits,10);assert.equal(x.units.shoulder.hits,9);assert.equal(x.units.drone.damage,477);
assert.equal(x.units.back.cd,5.2); // Preserve observed UI value, not JS rounding of 5.25.
x=M.analyze(data,['hits-long']);
assert.equal(x.units.hand.hits,4);assert.equal(x.units.shoulder.hits,3);assert.equal(x.counts.blocked,1);assert.equal(x.counts.free,6);
x=M.analyze(data,['damage-long']);assert.equal(x.units.hand.damage,887);assert.equal(x.units.shoulder.damage,1118);
x=M.analyze(data,['calibration-single']);assert.equal(x.units.drone.damage,350);
x=M.analyze(data,['damage-short']);assert.equal(x.units.drone.damage,265);
x=M.analyze(data,['damage-short','calibration-single']);assert.equal(x.units.drone.damage,138);
assert.equal(M.analyze(data,[]).firstEffectiveHit,null);
console.log('7 model behavior groups passed.');
