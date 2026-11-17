const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL,fileURLToPath}=require('node:url');
// NODE_PATH may point to the bundled runtime; no package download required.
const {chromium}=require('playwright');
(async()=>{
  const root=path.resolve(__dirname,'..'),out=path.join(root,'runs/run05/model-view-qa');
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({executablePath:process.env.MODEL_BROWSER||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(pathToFileURL(path.join(root,'docs/models.html')).href);
    assert.equal(await page.locator('#part-controls input:checked').count(),10);
    assert.match(await page.locator('#counts').innerText(),/16\/21/);
    await page.locator('#part-hits-long').uncheck();
    assert.match(await page.locator('#unit-table').innerText(),/× 3/);
    assert.match(await page.locator('#unit-table').innerText(),/× 4/);
    assert.equal(await page.locator('#counts .metric').nth(3).locator('strong').innerText(),'6');
    await page.locator('#reset').click();
    await page.locator('#part-controls [data-select="damage-short"]').click();
    assert.match(await page.locator('#part-detail').innerText(),/2个端点 → 1件装备受益/);
    for(const id of ['calibration-single','damage-short'])await page.locator('#part-'+id).uncheck();
    assert.match(await page.locator('#unit-table').innerText(),/138伤/);
    await page.locator('#reset').click();
    await page.locator('#part-controls [data-select="damage-long"]').click();
    await page.screenshot({path:path.join(out,'layout.jpg'),type:'jpeg',quality:80,fullPage:true});
    await page.locator('#tab-layout').focus();await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#tab-combat').getAttribute('aria-selected'),'true');
    await page.locator('[data-facet="survival"]').click();
    assert.match(await page.locator('#combat-summary').innerText(),/初始盾低于旧配装/);
    assert.match(await page.locator('#combat').innerText(),/首次有效命中：未知/);
    await page.screenshot({path:path.join(out,'combat.jpg'),type:'jpeg',quality:80,fullPage:true});
    await page.locator('#tab-cases').click();
    for(const id of ['run05-d13','run05-d15','run05-d16']){
      await page.locator('#case-select').selectOption(id);
      assert.match(await page.locator('#case-detail a').getAttribute('href'),new RegExp(id));
    }
    assert.match(await page.locator('#case-detail').innerText(),/无统计行/);
    await page.screenshot({path:path.join(out,'cases.jpg'),type:'jpeg',quality:80,fullPage:true});
    const links=await page.locator('a[href],link[href],script[src]').evaluateAll(xs=>xs.map(x=>x.href||x.src));
    for(const href of links){const u=new URL(href);if(u.protocol==='file:')assert.ok(fs.existsSync(fileURLToPath(u)),href);}
    await page.setViewportSize({width:390,height:844});await page.locator('#tab-layout').click();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile document must not overflow');
    assert.ok(await page.locator('.diagram-wrap').first().evaluate(el=>el.scrollWidth>el.clientWidth),'diagram should scroll locally');
    await page.screenshot({path:path.join(out,'mobile.jpg'),type:'jpeg',quality:75,fullPage:true});
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'audit.json'),JSON.stringify({status:'passed',browser:'Edge headless',offline:true,viewport:[1440,1100],mobile:[390,844],linksChecked:links.length,errors,checks:['10 parts and 21 ports','remove and reset','single beneficiary','drone lookup','keyboard tabs','combat facet','3 cases','unknowns','local links','mobile overflow']},null,2));
    console.log('Browser checks passed: offline interactions, 3 cases, '+links.length+' local links, desktop/mobile; 4 QA screenshots.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
