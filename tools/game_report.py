"""Standalone HTML views over a game's saved records and screenshot batches."""
from html import escape
import json
import os
from urllib.parse import quote

from game_profile import GameProfile, ROOT, load_json
from game_pilots import for_run
from rsi import write_atomic
from steam_shots import capture_settings


def e(value):
    return escape(str(value), quote=True)


def link(href, label):
    return f'<a href="{e(href)}">{e(label)}</a>'


def relative(path, folder):
    return quote(os.path.relpath(path, folder).replace(os.sep, "/"), safe="/")


def layout(title, body, *, navigation="", extra_css=""):
    return f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<style>
*{{box-sizing:border-box}} body{{max-width:1060px;margin:auto;padding:clamp(16px,4vw,44px);font:16px/1.65 system-ui;color:#182e35;background:#f6f7f4}}
h1,h2,h3{{line-height:1.3}}section,article{{background:white;border:1px solid #ccdad7;border-radius:8px;padding:16px;margin:12px 0}}
summary{{cursor:pointer;font-weight:600;padding:6px 0}}a{{color:#075c65;overflow-wrap:anywhere}}nav a{{display:inline-block;margin:0 18px 6px 0}}
img{{display:block;max-width:100%;height:auto}}figure{{margin:12px 0}}.frame{{position:relative;width:fit-content;max-width:100%}}
.box{{position:absolute;border:3px solid #ffcb40;box-shadow:0 0 0 1px #222;pointer-events:none}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
dt{{font-weight:600}}dd{{margin:0 0 8px}}p{{margin:6px 0}}details{{margin:6px 0}}
.games{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:18px;margin-top:24px}}
.game-link{{display:grid;grid-template-columns:1fr auto;gap:12px;padding:24px;color:inherit;text-decoration:none;background:white;border:1px solid #a7bfba;border-top:4px solid #267060;border-radius:8px}}
.game-link:hover,.game-link:focus-visible{{background:#eaf4ef;border-color:#267060}}
.game-link strong{{font-size:1.35rem}}.game-link small{{grid-column:1/-1;font-size:.94rem;color:#435b58}}
.crumb{{margin-bottom:18px}}.jump-links{{display:flex;gap:10px 18px;flex-wrap:wrap;margin:20px 0}}.jump-links a{{margin:0}}{extra_css}
</style><main>{navigation}<h1>{e(title)}</h1>{body}</main></html>"""


def evidence(refs):
    return " · ".join(link(ref, f"证据 {i}") for i, ref in enumerate(refs, 1))


def catalog_html():
    cards = []
    for config in sorted((ROOT / "games").glob("*/game.json")):
        # A game under construction must not break the home page of another game.
        try:
            game = GameProfile(config.parent.name)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        if not game.page.is_file() or not game.data.is_file():
            continue
        data = load_json(game.data)
        runs = len(data["runs"])
        summary = (f"{runs} 局试玩 · {len(data['issues'])} 份问题记录"
                   if runs else "等待第一局实机记录")
        card = (f'<a class="game-link" href="{e(relative(game.page, ROOT))}"><strong>{e(game.name)}</strong>'
                f'<span aria-hidden="true">→</span><small>{e(summary)}</small></a>')
        cards.append((-runs, game.name, card))
    tiles = "".join(card for _, _, card in sorted(cards))
    return layout("游戏测试库", f'<nav class="games" aria-label="选择游戏">{tiles}</nav>')


def refresh_catalog():
    home = ROOT / "index.html"
    content = catalog_html()
    # Reports from different games can finish together. Recheck after publishing
    # so that an older snapshot cannot overwrite a newer catalog.
    while not home.is_file() or home.read_text(encoding="utf-8") != content:
        write_atomic(home, content)
        content = catalog_html()


def method_page(game, data, key):
    from game_method import describe, recorded_decisions
    method = describe(game, data, key)
    parts = [f'<p>{e(method["question"])}</p>']
    if game.pilots:
        parts.append(f'<p>先按{link("pilots.html", "本局机师的技能")}核对哪些判断需要调整。</p>')
    for title, field, tag in [("当前局需要读取什么", "inputs", "ul"), ("判断顺序", "steps", "ol"),
                              ("给下一步决策的输出", "output", "ul")]:
        items = "".join(f"<li>{e(v)}</li>" for v in method[field])
        parts.append(f"<h2>{title}</h2><{tag}>{items}</{tag}>")
    parts.append(f'<p>{e(method["limit"])}</p>')
    if method.get("calculation"):
        parts.append(f'<p>可调用计算模型　<code>{e(method["calculation"])}</code></p>')
    if method.get("example"):
        path, _, anchor = method["example"].partition("#")
        href = relative(game.path(path), game.docs)
        parts.append(link(href + ("#" + quote(anchor, safe="") if anchor else ""), "打开历史实例"))
    parts.append("<h2>当前规则与修订依据</h2>")
    for rule in method["rules"]:
        parts.append(f'<details><summary>{e(rule["id"])} · {e(rule["title"])} · r{e(rule["revision"])}</summary>')
        for label, field in [("适用条件", "condition"), ("判断", "action"), ("核对", "expected"), ("边界", "caveat")]:
            parts.append(f"<p><b>{label}</b>　{e(rule[field])}</p>")
        parts.append("<ul>")
        for source in rule["evidence"]:
            label = f'{source["runId"]} · 第 {source["day"]} 天'
            origin = link(source["href"], label) if source.get("href") else e(label)
            parts.append(f'<li>{origin}　{e(source.get("note", ""))}</li>')
        parts.append("</ul></details>")
    if not method["rules"]:
        parts.append("<p>尚无关联的实测经验。</p>")
    parts.append("<h2>历史决策中的应用</h2>")
    records = list(recorded_decisions(data, method))
    if records:
        parts.append("<p>这里按当时实际采用的经验修订号，重现操作前的预测及事后核对。每项核对针对当时整条决策。</p>")
    else:
        parts.append("<p>尚无采用相关规则的决策记录。</p>")
    for run, decisions in records:
        parts.append(f'<details><summary>{e(run["title"])} · {len(decisions)} 项决策</summary>')
        for day, decision, uses in decisions:
            before, after = decision["before"], decision.get("after")
            refs = "、".join(f'{u["id"]} r{u["revision"]}' for u in uses)
            parts.append(f'<article><h3>第 {day} 天 · {e(before["chosenAction"])}</h3><p>当时采用　{e(refs)}</p>'
                         f'<p>当时状态　{e(before["state"])}</p><p>操作前预测　{e(before["prediction"])}</p>'
                         + evidence(before["evidence"]))
            if after:
                parts.append(f'<p>实际观察　{e(after["observed"])}</p>' + evidence(after["evidence"]))
            else:
                parts.append("<p>等待实测</p>")
            parts.append("</article>")
        parts.append("</details>")
    back = link(relative(game.page, game.docs) + "#models", game.name + " · 专业模型")
    write_atomic(game.docs / f"method-{key}.html", layout(method["title"], "".join(parts),
                                                          navigation=f'<nav class="crumb">{back}</nav>'))


def capture_guide(game):
    modes = {"frame": "直接截全景", "region": "从当前画面裁图", "hover": "悬停", "click": "点击页签或详情"}
    back = link(relative(game.page, game.docs) + "#knowledge", game.name + " · 测试回放")
    parts = ['<nav class="jump-links" aria-label="观察阶段">' +
             "".join(link("#phase-" + phase, name) for phase, name in game.phases.items()) + "</nav>"]
    steam = capture_settings(game)
    if steam:
        how = relative(ROOT / "docs/game-packs.md", game.docs) + "#steam-capture"
        parts.append(f'<section><h2>用 Steam 取得本次原图</h2><p>在保存游戏截图的电脑运行 <code>screenshot mark</code>，'
                     f'将游戏置于前台，按一次 Steam 截图键（默认 F12），再用 <code>screenshot read</code> 读取游戏 '
                     f'{e(steam["appId"])} 的新原图。每次换目标重新标记，整批采齐后一起裁图、读取。</p>'
                     f'<pre>python tools/game.py --game {e(game.id)} screenshot mark\n'
                     f'按一次 Steam 截图键后运行\npython tools/game.py --game {e(game.id)} screenshot read --marker "&lt;标记路径&gt;"</pre>'
                     f'<p>{link(how, "截图命令与目录定位")}</p></section>')
    for phase, title in game.phases.items():
        group = game.observations[phase]
        targets = game.targets(phase)
        parts.append(f'<section id="phase-{e(phase)}"><h2>{e(title)}</h2>')
        if group.get("actions"):
            parts.append("<ol>" + "".join(f"<li>{e(step)}</li>" for step in group["actions"]) + "</ol>")
        ref = group.get("reference")
        if ref:
            left, top, right, bottom = ref["bounds"]
            image_url = relative(game.path(ref["image"]), game.docs)
            parts.append(f'<figure class="map"><img src="{e(image_url)}" alt="{e(ref["alt"])}">')
            for key, target in targets.items():
                point = target.get("clickAt") or target.get("hoverAt")
                if point and target.get("size") == ref["size"]:
                    x, y = point
                    if left <= x < right and top <= y < bottom:
                        style = f"left:{100*(x-left)/(right-left):.3f}%;top:{100*(y-top)/(bottom-top):.3f}%"
                        label = e(target.get("label", key))
                        parts.append(f'<a class="pin" style="{style}" href="#{e(phase)}-{e(key)}" aria-label="{label}" title="{label}"></a>')
            parts.append(f'</figure><p>{e(ref["note"])}</p>')
        for key, target in targets.items():
            mode = target["mode"]
            point = target.get("clickAt") or target.get("hoverAt")
            box = target.get("box")
            parts.append(f'<article id="{e(phase)}-{e(key)}"><h3>{e(target.get("label", key))} · {modes[mode]}</h3>')
            if target.get("locate"):
                parts.append(f'<p>{e(target["locate"])}</p>')
            if point:
                w, h = target["size"]
                parts.append(f'<p>参考操作点　({point[0]}, {point[1]}) · 窗口 {w} × {h}</p>')
            elif mode in ("click", "hover"):
                parts.append("<p>操作点　按本次画面定位</p>")
            if box:
                x0, y0, x1, y1 = box
                crop = f"({x0}, {y0}) → ({x1}, {y1})"
            else:
                crop = "整个窗口" if mode == "frame" else "在当前截图标出需要读取的区域"
            parts.append(f'<p>截取范围　{crop}</p><p>读取字段　{e("、".join(target["fields"]))}</p>')
            for sample in target.get("samples", []):
                src = relative(game.path(sample["path"]), game.docs)
                parts.append(f'<details><summary>{e(sample["label"])}</summary><img loading="lazy" src="{e(src)}" alt="{e(sample["label"])}"></details>')
            parts.append("</article>")
        if group.get("sheet"):
            sheet = group["sheet"]
            parts.append(link(relative(game.path(sheet["path"]), game.docs), sheet["label"]))
        parts.append("</section>")
    css = """.map{position:relative;width:fit-content;max-width:100%}.pin{position:absolute;transform:translate(-50%,-50%);width:22px;height:22px;border:3px solid white;border-radius:50%;background:#007c8599;box-shadow:0 0 0 2px #163039}.pin:hover,.pin:focus-visible{background:#01656e}article:target{outline:2px solid #267060}"""
    write_atomic(game.docs / "capture-guide.html", layout(game.name + " · 批量截图与操作位置", "".join(parts),
                                                         navigation=f'<nav class="crumb">{back}</nav>', extra_css=css))


def pilot_page(game):
    roster = game.pilots["pilots"]
    parts = ['<nav class="jump-links" aria-label="选择机师">' +
             "".join(link("#" + key, p["name"]) for key, p in roster.items()) + '</nav>']
    for key, pilot in roster.items():
        source = link(relative(game.path(pilot["source"]), game.docs), "选角原图")
        parts.append(f'<section id="{e(key)}"><h2>{e(pilot["name"])}</h2><p><b>{e(pilot["skill"])}</b> · '
                     f'可失败 {e(pilot["lives"])} 次</p><p>{e(pilot["ability"])}　{source}</p><h3>决策时看什么</h3><dl>')
        for phase, guidance in pilot["focus"].items():
            parts.append(f'<dt>{e(game.phases[phase])}</dt><dd>{e(guidance)}</dd>')
        parts.append('</dl><h3>实战观察</h3>')
        for item in pilot["observations"]:
            ref = link(relative(game.path(item["source"]), game.docs), "对局记录")
            parts.append(f'<p>{e(item["text"])}　{ref}</p>')
        if not pilot["observations"]:
            parts.append('<p>待首次实战记录。</p>')
        parts.append('<h3>下次验证</h3><ul>' + "".join(f'<li>{e(q)}</li>' for q in pilot["toVerify"]) + '</ul></section>')
    back = link(relative(game.page, game.docs) + '#models', game.name + " · 专业模型")
    write_atomic(game.docs / "pilots.html", layout(game.name + " · 机师玩法模型", "".join(parts),
                                                 navigation=f'<nav class="crumb">{back}</nav>'))


def report(game, data):
    from rsi import validate
    validate(data, game)
    sections = {"knowledge": "基础知识与观察", "models": "专业模型", "runs": "对局与决策",
                "memories": "跨局经验", "issues": "问题记录"}
    parts = ['<nav aria-label="游戏内导航" class="jump-links">' +
             "".join(link("#" + key, name) for key, name in sections.items()) + "</nav>"]
    parts.append('<h2 id="knowledge">基础知识与观察</h2>')
    capture_guide(game)
    parts.append('<nav aria-label="观察资料">' + link("capture-guide.html", "批量截图与操作位置") +
                 link(relative(game.knowledge, game.docs), "查看游戏知识") + "</nav>")
    for phase, label in game.phases.items():
        targets = game.targets(phase)
        rows = "".join(f"<dt>{e(k)}</dt><dd>{e('、'.join(t['fields']))}　{e(t.get('locate', ''))}</dd>" for k,t in targets.items())
        parts.append(f"<details><summary>{e(label)}</summary><dl>{rows}</dl></details>")
    parts.append('<h2 id="models">专业模型</h2>')
    if game.pilots:
        pilot_page(game)
        parts.append(f'<article><h3>{link("pilots.html", "机师玩法模型")}</h3><p>按本局机师查看技能、决策要点、实战观察和下一次要验证的问题。</p></article>')
    for key, method in game.methods.items():
        method_page(game, data, key)
        parts.append(f'<article><h3>{link(f"method-{key}.html", method["title"])}</h3><p>{e(method["question"])}</p></article>')
    for name, view in game.model_views.items():
        path, _, anchor = view["href"].partition("#")
        href = relative(game.path(path), game.docs)
        if anchor:
            href += "#" + quote(anchor, safe="")
        parts.append(f'<article><h3>{link(href, name)}</h3><p>{e(view["description"])}</p></article>')
    if game.models:
        parts.append("<p>可调用模型　" + e("、".join(game.models)) + "</p>")
    elif not game.model_views and not game.methods:
        parts.append("<p>尚未登记专业模型。</p>")
    if game.views:
        parts.append('<nav aria-label="相关专题">' + "".join(link(relative(game.path(path), game.docs), name)
                     for name, path in game.views.items()) + "</nav>")
    parts.append(f'<h2 id="runs">对局与决策 · {len(data["runs"])}</h2>')
    if not data["runs"]:
        parts.append("<p>等待第一局实机记录。</p>")
    for run in reversed(data["runs"]):
        parts.append(f"<section><details><summary>{e(run['title'])} · {e(run['id'])}</summary>")
        pilot = for_run(game, run, None)
        if pilot:
            parts.append('<p>本局机师　' + link("pilots.html#" + pilot["id"], pilot["name"]) + '</p>')
        for day in run["days"]:
            parts.append(f"<details><summary>{e(day['day'])} · {e(day['title'])}</summary>")
            for dec in day.get("decisions", []):
                before, after = dec["before"], dec.get("after")
                parts.append(f"<article><h3>{e(before['chosenAction'])}</h3><p>{e(before['state'])}</p>"
                             f"<p>原预测　{e(before['prediction'])}</p>{evidence(before['evidence'])}")
                if after:
                    parts.append(f"<p>实测　{e(after['observed'])} · {e(after['predictionResult'])}</p>{evidence(after['evidence'])}")
                else:
                    parts.append("<p>等待实测</p>")
                parts.append("</article>")
            parts += [f"<p>{e(day.get('after') or day.get('before', ''))}</p>", evidence(day.get("sources", [])), "</details>"]
        parts.append("</details></section>")
    parts.append(f'<h2 id="memories">跨局经验 · {len(data["memories"])}</h2>')
    for m in data["memories"]:
        parts.append(f"<details><summary>{e(m['title'])} · r{e(m['revision'])}</summary><p>{e(m.get('condition',''))}</p>"
                     f"<p>{e(m.get('action',''))}</p><p>{e(m.get('caveat',''))}</p>"
                     + evidence([s["href"] for s in m["evidence"] if s.get("href")]) + "</details>")
    parts.append(f'<h2 id="issues">问题记录 · {len(data["issues"])}</h2>')
    parts.extend(f"<p>{link(i['source'], i['title'])} · {e(i['status'])}</p>" for i in data["issues"])
    home = link(relative(ROOT / "index.html", game.docs), "全部游戏")
    write_atomic(game.page, layout(game.name + " · 测试回放", "".join(parts),
                                   navigation=f'<nav class="crumb" aria-label="上一级">{home}</nav>'))
    refresh_catalog()


def observation_page(game, bundle, path, final_folder):
    from pathlib import Path
    from PIL import Image
    parts = [f"<p>{e(game.phases[bundle['phase']])} · {e(bundle['batchId'])}</p>"]
    for entry in bundle["entries"]:
        source = (final_folder / Path(entry["source"])).resolve()
        with Image.open(source) as img:
            w, h = img.size
        x0, y0, x1, y1 = entry["box"]
        style = f"left:{100*x0/w:.4f}%;top:{100*y0/h:.4f}%;width:{100*(x1-x0)/w:.4f}%;height:{100*(y1-y0)/h:.4f}%"
        href = relative(source, final_folder)
        parts.append(f'<section><details><summary>{e(entry["id"])} · {e("、".join(entry["fields"]))}</summary>'
                     f'<figure class="frame"><img src="{e(href)}" alt="原始画面"><span class="box" style="{style}"></span></figure>'
                     f'<p>{link(href, "查看原图")}</p><img src="{e(entry["crop"])}" alt="识别区域">')
        reading = entry["reading"]
        parts.append("<pre>" + e(json.dumps(reading, indent=2, ensure_ascii=False)) + "</pre>" if reading else "<p>等待读取</p>")
        parts.append("</details></section>")
    write_atomic(path, layout(game.name + " · 截图观察", "".join(parts)))
