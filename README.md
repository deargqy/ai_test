# 用 AI 测试《猫壳机动队》

让 Agent 通过 Steam 截图读界面，用普通键鼠打一局挑战赛。它可以在买装备前留下预测，在战报里核对结果，把疑似 Bug 连同操作步骤和原图交给玩家复查。本仓库包含可复用的测试管线、猫壳的游戏配置，以及已归档的对局和问题单。

## 人先看哪里

**想看 AI 实际测出了什么，先看[猫壳测试回放](docs/game-report.html)。** 下载整个仓库后，用浏览器打开 `docs/game-report.html`。从“问题记录”点进一份报告，可以看到现象和原图。从“对局与决策”展开某一天，可以看到当时怎么选、预期是什么、后来实际发生了什么。直接在 GitHub 上阅读文字，可以先看[猫壳试玩说明与 Bug 索引](docs/README.md)。

| 想了解什么 | 打开哪份文档 |
| --- | --- |
| Agent 在商店或战报里点哪里、截哪一块 | [批量截图与操作位置](docs/capture-guide.html) |
| 选不同机师会改变哪些判断 | [机师玩法模型](docs/pilots.html) |
| 想自己给另一款游戏配置这套管线 | [按游戏接入测试管线](docs/game-packs.md) |

## 让自己的 Agent 测一局

在装有 Steam 和《猫壳机动队》Demo 的 Windows 电脑上，用能操作本机键鼠、读写本地文件和查看图片的 Agent 打开本仓库。测试工具使用 Python 3.10 或更新版本，截图读取和裁切需要 Pillow。玩家想自己选猫时，可以在下面这段话末尾加上机师名。

**把这段话发给 Agent**

> 请用这个仓库，在我的电脑上实际试玩并测试 Steam《猫壳机动队》Demo，打到本局挑战赛结算。先读 AGENTS.md 和 docs/RSI-RUNBOOK.md，用 tools/game.py 的 cats 配置开始。通过 Steam 截图确认我当前的游戏画面，默认按 F12。如果新开会覆盖我已有的进度，先问我是续玩还是另开。为我的试玩使用独立局号，记下实际机师和版本。仓库里的旧对局可用来查经验。
>
> 购物、换装或选敌时，用当前机师的特点和对应模型比较选项。关键操作前记下预期，操作后用新截图或战报核对。遇到疑似 Bug 时，留下复现步骤、预期、实际和原图，有机会再复测。最后告诉我打到了哪里、哪些问题已复现、哪些还待确认，并给我这次回放和问题单的位置。

### 获取和运行

从 GitHub 下载整个仓库并解压，或运行以下命令获取代码。

```sh
git clone https://github.com/edwardwu94/ai_test.git
cd ai_test
```

在同一个 Python 环境中安装截图依赖并检查配置。Windows 上可以使用 `py`，其他系统可将其换成对应的 Python 命令。

```sh
py -m pip install Pillow
py tools/game.py --game cats info
py tools/game.py --game cats check
```

键鼠由 Agent 操作。它在 Steam 保存截图的电脑上运行 `screenshot mark`，将游戏置前并按一次截图键，再用 `screenshot read` 取得这次的新图。观察阶段决定要点哪些位置、截哪些区域，同一阶段可以采齐后一起读取。[Steam 截图步骤](docs/game-packs.md#steam-capture)

确认开局后，通过 `rsi start-run --pilot` 在自己的仓库副本登记对局。随后用 `rsi memories --run 局号 --phase 阶段` 读取经验，按实际游戏版本核对适用条件。完成记录后运行 `py tools/game.py --game cats report`，用浏览器打开 `docs/game-report.html` 查看更新。只看已有回放时，下载完整目录后即可离线浏览。

## 游戏与实例

[游戏测试库](index.html)按游戏组织资料。猫壳已有战力、配件、未来规划和机师玩法模型。小丑牌提供了另一份游戏配置，等待首次实机校准。

- [第二局挑战赛](docs/playtest-2026-11-15-run02/run.html) 和[随后三天的爬塔](docs/playtest-2026-11-15-run02/tower.html)
- [配件与战力交互页](docs/models.html) 和[对手配装案例库](docs/opponent-library.html)
