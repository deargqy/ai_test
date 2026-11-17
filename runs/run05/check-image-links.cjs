// Check generated links in actual offline pages after screenshot cleanup.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL,fileURLToPath}=require('node:url');
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(__dirname,'../..'),docs=path.join(root,'docs');
  const browser=await chromium.launch({executablePath:process.env.MODEL_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const checked=new Set(),missing=[],errors=[];let views=0;
  try{
    const page=await browser.newPage();page.on('pageerror',e=>errors.push({page:page.url(),message:e.message,stack:e.stack}));
    async function inspect(){
      await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
      const urls=await page.locator('a[href],img[src],script[src],link[href],source[src]').evaluateAll(xs=>xs.map(x=>x.href||x.src));
      for(const href of urls){const u=new URL(href);if(u.protocol!=='file:')continue;u.hash='';u.search='';if(checked.has(u.href))continue;checked.add(u.href);if(!fs.existsSync(fileURLToPath(u)))missing.push({page:page.url(),target:u.href});}
      views++;
    }
    const pages=fs.readdirSync(docs).filter(n=>n.endsWith('.html'));
    for(const name of pages){await page.goto(pathToFileURL(path.join(docs,name)).href);await inspect();}
    const data=JSON.parse(fs.readFileSync(path.join(root,'data/playtest.json'),'utf8'));
    const rsi=pathToFileURL(path.join(docs,'rsi-workflow.html')).href;
    for(const hash of [...data.memories.map(m=>'memory/'+m.id),...data.runs.flatMap(r=>r.days.map(d=>'runs/'+r.id+'/'+d.day)),'bugs']){
      await page.goto(rsi+'#'+hash);await inspect();
      if(hash.startsWith('runs/'))assert.ok((await page.locator('article.panel > h2').first().innerText()).startsWith('第 '+hash.split('/')[2]+' 天'));
    }
    await page.goto(pathToFileURL(path.join(docs,'models.html')).href);
    await page.locator('#tab-cases').click();
    for(const id of ['run05-d13','run05-d15','run05-d16']){await page.locator('#case-select').selectOption(id);await inspect();}
    const result={status:missing.length||errors.length?'failed':'passed',browser:'Edge headless',staticPages:pages.length,renderedViews:views,uniqueLocalTargets:checked.size,missing,errors};
    fs.writeFileSync(path.join(__dirname,'image-link-browser-audit.json'),JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));assert.deepEqual(missing,[]);assert.deepEqual(errors,[]);
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
