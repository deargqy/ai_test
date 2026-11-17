# 下一局执行说明

配件/换装先用[离线组合实验室](loadout-lab.html)核对整排候选。输入来自已读可见截图，包含拥有和当前商店候选；价格、孔位、形状、被动和来源必须记录。枚举装备替换与卡序，搜索配件端点分配，比较预算与分项收益后再prepare购买/装配。模型候选不等于实机合法；交叠、旋转或拖动失败仍未知时不可伪造确定约束。当前工具不模拟完整战斗，不能把代理分当胜率或首击时间。恢复游戏先新图核暂停状态，再按选定方案执行。

每日流程优化草案见[流程图与验证计划](play-flow.html)：按阶段集中观察与比较，保留重要决策点击前预测；已试行用户授权的固定点只读详情批采与tools/observe.py截图打包；采集逐项刷新，整组读取。重要动作仍先prepare，批次遇输入变化立即重新观察。

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

每次正式战败必须建立或更新[击败我们的对手](opponent-studies.html)条目，数据写入 `data/playtest.json` 的 `opponentStudies`。先核双方伤害/防御/增益和启动时间，再拆解对方的启动条件、实际致胜链、核心装备/科技/配件及有效端点。没有战报贡献的备用环节不得直接归为胜因；累计伤害不等于有效扣血，统计次数不直接当完整施法次数。

每条写清可借鉴的最小组合、可替代功能、成型成本/成长与冷却来源、我方缺口、可尝试的应对，以及下次点击前能登记的预测。未核对的来源（例如敌1秒CD如何形成）保留未知，不能复制显示数值当作可购买的基础属性。旧局只从既有复盘提炼时标为历史二次整理，不伪装当时已自主学习。学到的套路在 shop/build/opponent 阶段检索；实际采用后回链新决策与结果，反例不删。

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


## 对手案例检索与差异比较

先用[对手配装案例库](opponent-library.html)检索胜局和败局，数据来源仍为原始逐日记录与`opponentStudies`，`data/opponents.json`是生成索引。更新对局后运行 `python tools/opponents.py build`。

    python tools/opponents.py search --mechanism 坚固
    python tools/opponents.py search --query Rogas

全文可能命中我方条件；敌方机制标签仅用明确核对的敌方观察。当前索引以一个游戏日的主要结果为单位，不代表所有重随或额外首领。历史摘要不等于完整配装，缺值不填零；战后CD、成长后的数值不回填开场。

战前引用匹配案例ID和证据，逐项比较：机师/版本、核心装备真实数值、配件形状与端点、科技、初始状态、确定/随机充能、控制、双方生命与盾。再说明新对手相对案例的变化，登记可核验的首击/前两轮/生存风险预测。无匹配或关键项缺失时明确未知，不把检索结果数量当相似度、战力或胜率。

新战后回填命中时序与三页统计。用于制定模型的旧案例不能同时计为独立验证成功；须以之后的新场次检验。胜过和输过的构筑都保留，避免只记失败造成样本偏差。
