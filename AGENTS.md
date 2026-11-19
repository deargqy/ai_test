# ai_test 项目协作约定

接手先确定游戏标识，并运行 `python3 tools/game.py --game <标识> info`。按 [游戏接入说明](docs/game-packs.md) 读取该游戏的基础知识、观察配置和独立记录。新游戏先 init；建模参考 [.agents/skills/game-model/SKILL.md](.agents/skills/game-model/SKILL.md)。以下旧项目约定适用于猫壳机动队。

- 试玩与恢复会话都直接用 Steam 截图。在保存 Steam 截图的电脑运行 `screenshot mark`，用键鼠工具将目标游戏置前并按一次 Steam 截图键（默认 F12），再用同一标记 `screenshot read`。无需先试原生抓窗。若抓窗接口报超时，照常走 Steam；若 Steam 没出新图，记录具体停在哪一步。[可复制的命令](docs/game-packs.md#steam-capture)
- 选猫后用 `rsi start-run --pilot` 记下选角页确认的机师。恢复已有局时用 `rsi memories --run 局号 --phase 阶段` 读取该猫的玩法；补充角色机制时附本猫的原图或对局记录。[机师玩法模型](docs/pilots.html)

- 首次在自己的电脑试玩，从[仓库首页](README.md)开始，核对本机 Steam 新图，选用独立局号。恢复自己已有的对局时，再核对自己的局号、存档和快照。原项目的[历史交接](HANDOFF.md)及[试玩记忆](GAME-NOTES.md)可作参考。
- 开发进度、排障过程和会话工作日志仅保存在本机的 `.local/work-logs/`，该目录已由 Git 忽略。README 面向使用者。供读者复核的对局结果、原图和问题单按游戏归档。
- 每次优化先写基线和假设，复测后追加前后数据与保留、撤回或待验证的决定。
- 进入实测后保存本局证据。游戏日结束或中断时更新当前局的快照和下一步，跨局结论附来源和适用条件。

- 下一局按 docs/RSI-RUNBOOK.md 执行，按阶段从 data/playtest.json 读取经验。重要决策点击前记录引用、候选和预测，操作后回填结果；用 tools/rsi.py 更新网页数据。
