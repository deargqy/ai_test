# 下一局执行说明

先读 GAME-NOTES.md 的当前停点，用现场新图核对游戏版本和局号。经验的唯一数据来源为 data/playtest.json，网页由它生成。当前经验来自版本 1.0.0.2218，其他版本先核对机制。

## 开局与决策

确认新局已开始后建立记录。以下以第三局为例，日期和版本使用现场值。

    python tools/rsi.py start-run --id run03 --title 第三局 --date 2026-11-16 --game-version 1.0.0.2218

进入选敌、购物、装配等需要取舍的页面，按阶段读取经验。关键词只改变排序，阶段内经验完整返回。阶段可选 observe、shop、build、opponent、result。

    python tools/rsi.py memories --phase opponent --tags 禁用 启动

根据当前画面核对经验的条件，补看会改变选择的未知信息。比较实际可行的选择，每个选择写收益、代价、失败条件及未知信息。构筑、战力和经济共同参与同一次判断。没有匹配经验时照常推理，记录检索结果。

先保存截图，再生成并填写点击前的模板。文件路径由本次执行者决定，下面的 before.json 为示例。

    python tools/rsi.py decision-template --run run03 --day 1 --phase opponent > before.json
    python tools/rsi.py prepare --input before.json

before.memories 中每条引用填写 id、revision、origin、use、reason。origin 为 autonomous 或 player，use 为 applied 或 notApplied。未采用的相关经验也记录理由。evidence 使用相对于 docs 的真实证据路径。prediction 写战后能核对的现象。保留原预测，之后用新的决策编号记录修正。

## 操作后的核对

    python tools/rsi.py outcome-template > after.json
    python tools/rsi.py finish --id run03-d01-01 --input after.json

先核实操作是否成功，再比较预测和结果。operationResult 使用 succeeded、failed 或 unknown；predictionResult 使用 supported、refuted 或 unknown；memoryDecision 使用 retain、narrow、revise 或 pending。观察不足就写 unknown。记录实际结果、证据、解释、下一步。

每个游戏日结束时，在 data/playtest.json 对应局和游戏日填写真实阶段、标题、胜负和累计战绩。终局再填 status 为 complete、endedAt、finalImage、result、wins、losses，有完整计时才填 durationMinutes。随后执行 build 更新网页。

    python tools/rsi.py build

prepare 和 finish 自动更新网页数据。Python 不可用时，按同一结构读写 JSON，并在有 Python 的环境生成页面。任何中断都更新 GAME-NOTES.md 的最新画面和下一步。

## 复测和经验更新

优先核对 M01 的主力首次有效攻击预测。记录控制对象、首次出手和生命变化。没有遇到适用条件时保留待测。

核对实际符合条件的决定有多少次，其中自主调用与玩家提醒各多少次。另数预测支持、反驳和未知的次数，保留操作失败、人工帮助、耗时及可得用量。旧两局缺少逐条引用，历史回顾不能补记为当时自主调用。

经验条目修改时增加 revision，并追加 history，保存旧判断及变更依据。下一次调用记录当时的修订号。来源和反例追加到 evidence，回到对应游戏日查看。只用可比较结果决定保留、缩小条件或回退；一次胜负保留为线索。

现有三场爬塔预测均为胜、实际两胜一负，尚无校准胜率。下一局同时核查过程预测与代价，整局胜场单独报告。若需检验经验本身，另用未参与制订规则的战前局面，在独立会话中做有无经验对照。
