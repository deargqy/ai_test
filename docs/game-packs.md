# 按游戏接入测试管线

从项目根目录运行命令。记录、模型和 HTML 使用 Python 3.10 或更新版本；截图打包和标注另需 Pillow。使用同一个 Python 环境运行，缺少图像依赖时可用 `python3 -m pip install Pillow` 安装到自己的虚拟环境。

## 游戏入口

从[游戏测试库](../index.html)选择游戏。每个游戏页都有基础知识与观察、专业模型、对局与决策、跨局经验和问题记录。初始化新游戏或更新回放时，首页会自动刷新。

| 游戏 | 配置与知识 | 本游戏的记录 | 测试回放 |
|---|---|---|---|
| 猫壳机动队 | [games/cats](../games/cats/) | [原始对局数据](../data/playtest.json) | [通用回放](game-report.html) · [交互配件与战力页](models.html) |
| 小丑牌 | [games/balatro](../games/balatro/) | [独立记录](../games/balatro/data/playtest.json) | [测试回放](../games/balatro/report/index.html) |

```sh
python3 tools/game.py --game balatro info
python3 tools/game.py --game balatro plan hand
python3 tools/game.py --game balatro init
python3 tools/game.py --game balatro check
```

`init` 可重复执行，保留已有记录。小丑牌的初始记录为空。进入游戏后先核实版本、窗口标题、分辨率和布局，再填入配置。版本可以用全局 `--version` 临时覆盖；未知版本时跳过跨批读取缓存。点击与读屏由操作游戏的 Agent 执行。Mac 窗口工具可用 `./Steam-Window.command balatro` 指定配置，默认选择 cats。两款游戏共用桌面控制会话，一次操作一个游戏。Windows 本机键鼠工具可向前台游戏发送 Steam 截图键。

## 新游戏需要提供的文件

在 `games/<游戏标识>/` 创建以下三个文件。可以从小丑牌复制这三个文件作为起点。对局数据、缓存和历史页面由各游戏分别保存。

| 文件 | 内容 |
|---|---|
| `game.json` | 游戏名、已核实的版本、阶段标识及显示名、可选的 Steam 窗口信息、专业模型和 HTML 视图。路径相对本文件。新游戏默认使用本目录的 `data/playtest.json` 和 `report/index.html`。猫壳配置显式引用原档案。 |
| `knowledge.md` | 胜负目标、术语、操作、玩家先验或公开规则。附来源和适用版本，实机确认与待验证的推断分别注明。 |
| `observations.json` | 每个阶段的可选操作、观察对象和读取字段。列出需要拍全景、裁区域或展开提示框的对象。 |
| `models/*.py`（按需） | 将已观察到的现场状态送入专业模型，离线输出预测。模型文件和登记项随游戏保存。 |
| `pilots.json`（按需） | 在 game.json 的 pilots 指向此文件。每个角色分别登记技能原文依据、各阶段决策关注点、带来源的实战观察和待验证问题。 |

<a id="steam-capture"></a>

### 新会话怎样取得 Steam 原图

在 **Steam 保存截图的电脑** 执行。下面以猫壳为例。先定位游戏窗口，标记当前已有的文件。

```sh
python3 tools/game.py --game cats screenshot mark
```

把游戏置前，用桌面键鼠工具按一次 Steam 的截图键（默认 F12，改过键就用实际绑定）。把上一步返回的 marker 路径填入下一条命令。Python 负责找图，按键由操作游戏的 Agent 发送。

```sh
python3 tools/game.py --game cats screenshot read --marker "<上一步返回的 marker 路径>"
```

成功时返回新图路径和尺寸，可直接作为批量裁图清单中的 source。若要保存证据，在 read 后加 `--output runs/本局/文件名.jpg`，扩展名与 Steam 原图一致。每张图重新 mark 一次，返回的标记各自独立。两张新图、图片仍在写入、目标游戏未生成新文件都会分别报告原因；文件仍在写入时可拿同一个标记重读。

Windows 默认从 Steam 注册的安装位置找到 `userdata/<账号>/760/remote/<AppID>/screenshots`。第五局的 Steam 安装在 F 盘；若自动定位失败，给 mark 加 `--steam-root "F:/steam"`（替换为本机实际目录）。共享电脑可用 `--account` 指定当前账号对应的数字目录。远程串流时以实际保存 F12 原图的一端为准。Windows 的 python 若指向商店占位程序，请用已安装 Pillow 的项目 Python 执行。换小丑牌时把两条命令的游戏标识改为 `balatro`。

### 截图、坐标与状态库

每个游戏的测试回放在“基础知识与观察”中链接“批量截图与操作位置”。[猫壳示例](capture-guide.html)可点选商店货位和战报页签，分别查看操作点、裁剪框和实际裁图。

`plan 阶段` 列出配置的 actions 和 targets。Agent 从当前窗口定位对象，按需要悬停，确认弹窗和阶段仍然正确，再保存截图。一张画面可以读多个字段，移动到下一张牌时也可以新增截图。购买、弃牌、结算等改变现场的操作之后，另起一个批次。

每个 target 设 `fields` 和 `mode`。frame 使用全景；region、hover 和 click 使用已校准的 `size: [宽,高]` 和 `box: [左,上,右,下]`（右、下不包含），或在本次截图条目中填写 box。box 表示**截图裁切范围**。固定位置可另填 `hoverAt: [x,y]`（悬停）或 `clickAt: [x,y]`（点击只读页签或详情），并注明标定 size；动态对象由 locate 和实机位置确定。用 `plan hand --size 1920 1080` 按实际窗口尺寸取计划，尺寸不同时会移除旧坐标并标记需要重新定位。不同窗口尺寸拒绝沿用固定框；动态牌列每次根据现场定位。先用全景校准，再写入固定布局。

例如在小丑牌建立 `hand-01.json`，截图路径相对这个文件。下面的提示框数字只是格式示例，应以本机实测替换。

```json
{"batchId":"hand-01","entries":[
  {"target":"scene","source":"hand.png"},
  {"target":"joker","id":"joker-2","source":"hover-second.png","box":[100,80,420,340]}
]}
```

```sh
python3 tools/game.py --game balatro observe hand --input hand-01.json --output games/balatro/report/hand-01
```

打开批次目录的 `index.html` 查看原图、裁切框和实际裁图。Agent 一次阅读整批联系表，在 `readings-template.json` 副本填入识别结果和 uncertain 列表。用 `annotate --bundle 批次/bundle.json --input 填好的记录.json` 保存。报告中的图片路径相对批次目录，保留原图即可随项目迁移。

仅对明确声明 `cacheReading: true` 的目标复用无疑点的可见字段。游戏、版本、阶段、目标定义和裁图像素都必须一致。相似画面继续读取。只有全部来自裁图本身的信息才宜开启，例如牌面说明。当前余额、牌序和战后结算要用最新现场。修正规则时修改目标定义或版本以隔离旧读数。缓存存放在本游戏的 `.cache/states.sqlite3`。

以下是可直接执行的真实历史样本，三张来源图已经在工程中：

```sh
python3 tools/game.py --game cats observe shop --input games/cats/examples/shop.json --output games/cats/report/shop-replay
```

### 建立和调用专业模型

玩家先给已知条件，Agent 记录状态、预测和实测偏差。完整做法见[模型建立指引](../.agents/skills/game-model/SKILL.md)。模型文件实现 `predict(state)`，返回可 JSON 编码的对象。登记示例为 `"score": {"entry":"models/score.py","revision":"1","cache":true}`。需要参数可添加 settings，需要额外计算文件可添加 dependencies。缓存按游戏版本、模型、修订、参数、实现和依赖的内容以及完整输入匹配。存在隐藏状态或随机性时关闭缓存，或把种子和全部必要条件显式包含在输入中。

```sh
python3 tools/game.py --game cats model loadout --input runs/run05/day14-loadout-input.json --output /tmp/cats-layout.json --html /tmp/cats-layout.html
```

每个模型可实现 `render_prediction(state, result, path)` 提供专属交互，例如配件端点与收益变化。只实现 predict 时，`--html` 会生成可折叠的通用结果页。模型专题在 game.json 的 `modelViews` 以显示名登记 `href` 和 `description`。href 可以指向模型 HTML 的具体页签或锚点。可运行模型仍登记在 `models`，其他专题链接放在 `views`。

判断方法由游戏配置的可选 `methods` 文件提供。每个方法描述当前局需要的输入、判断顺序、输出、边界、关联经验和适用阶段；可选 `calculation` 指向已登记的计算模型，`example` 指向历史实例。使用 `python3 tools/game.py --game cats method combat` 获取和网页相同的方法、当前规则修订及来源。游戏回放会按当前数据生成方法页，并展示当时实际采用对应经验的决策和事后观察。

### 实机决策和测试回放

猫壳选角确认后，给正常的开局命令加 `--pilot 莫瑟`（或对应角色的标识）。续局可运行 `python3 tools/game.py --game cats rsi memories --run run05 --phase shop`，结果含该机师在商店的判断要点及其证据。单独查看角色时，使用 `model pilot --input 状态.json`，输入如 `{"pilot":"莫瑟","phase":"shop"}`。历史局只关联有选角依据的角色。

试玩后，将截图支持的观察和还要复测的问题补入该角色条目，运行 `python3 tools/game.py --game cats report` 刷新[机师玩法模型](pilots.html)。写入跨局经验时可附 `pilotId` 标明角色专属；按局取经验会带出该猫专属和未限定机师的记录。历史通用经验仍须核对原有适用条件。

```sh
python3 tools/game.py --game balatro rsi start-run --id run01 --title 第一局 --date YYYY-MM-DD --game-version 实测版本
python3 tools/game.py --game balatro rsi memories --phase hand --game-version 实测版本
python3 tools/game.py --game balatro rsi decision-template --run run01 --day 1 --phase hand > before.json
python3 tools/game.py --game balatro rsi prepare --input before.json
python3 tools/game.py --game balatro rsi outcome-template > after.json
python3 tools/game.py --game balatro rsi finish --id run01-d01-01 --input after.json
python3 tools/game.py --game balatro report
```

在 prepare 和 finish 之前分别填完模板；证据链接相对于本游戏的回放页目录。可引用批次 index.html、模型输出和实机截图。一次重要决策分配一个新编号；同一阶段可有多次决策。day 是既有数据格式中的进度序号，小丑牌可按轮次记录。战绩和实际耗时有独立证据才填写。游戏配置中的阶段名仅约束结构化决策，不改变旧记录的标题。

`rsi memory --input 文件` 保存带来源的新经验或递增修订，保留旧 history 和 evidence。`rsi issue --input 文件` 保存含 id、title、status、source、occurrences 的问题单；occurrences 中的 runId 和 day 对应已有记录。预测不符先定位读屏、模型或游戏行为的差异，形成可复现的证据后再提交。两条命令都会更新该游戏的回放。需要回填复杂的既有档案字段时，可参照猫壳的 JSON 结构并运行 check 和 report。
