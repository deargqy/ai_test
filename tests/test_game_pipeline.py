"""Exercise the real Agent entry point in an isolated checkout with a third game."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class GamePipelineTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        shutil.copytree(ROOT / "tools", self.root / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        self.pack = self.root / "games" / "fixture"
        self.pack.mkdir(parents=True)
        self.config = {"name": "验证游戏", "version": "test1", "phases": {"round": "回合"},
                       "models": {}, "views": {}}
        self.write("game.json", self.config)
        self.write("observations.json", {"round": {"targets": {
            "hand": {"fields": ["value"], "mode": "region", "size": [80, 60], "box": [5, 4, 40, 20]},
            "detail": {"fields": ["text"], "mode": "hover", "locate": "按现场定位", "cacheReading": True}
        }}})
        (self.pack / "knowledge.md").write_text("基础知识", encoding="utf-8")

    def write(self, name, data):
        (self.pack / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def cli(self, *args, ok=True):
        p = subprocess.run([sys.executable, "tools/game.py", "--game", "fixture", *args],
                           cwd=self.root, capture_output=True, text=True)
        self.assertEqual(p.returncode == 0, ok, p.stderr + p.stdout)
        return p.stdout

    def test_catalog_discovers_games_and_resolves_nested_report_links(self):
        second = self.root / "games" / "second"
        shutil.copytree(self.pack, second)
        second_config = {**self.config, "name": "第二款", "report": "../../docs/second game.html"}
        (second / "game.json").write_text(json.dumps(second_config))
        self.cli("init")
        index = self.root / "index.html"
        self.assertTrue(index.is_file())
        self.assertNotIn("第二款", index.read_text())
        subprocess.run([sys.executable, "tools/game.py", "--game", "second", "init"],
                       cwd=self.root, capture_output=True, check=True)
        contents = index.read_text()
        self.assertIn('href="docs/second%20game.html"', contents)
        self.assertIn('href="games/fixture/report/index.html"', contents)
        self.assertIn("第二款", contents)
        self.assertIn('href="../index.html"', (self.root / "docs/second game.html").read_text())
        self.assertIn('href="../../../index.html"', (self.pack / "report/index.html").read_text())
        self.cli("rsi", "start-run", "--id", "one", "--title", "入门", "--date", "2026-11-19",
                 "--game-version", "test1")
        self.assertIn("1 局试玩", index.read_text())

    def test_method_separates_reusable_rules_from_a_worked_example(self):
        self.config["methods"] = "methods.json"
        self.write("game.json", self.config)
        (self.pack / "example.html").write_text("<h1>当局实例</h1>")
        self.write("methods.json", {"timing": {
            "title": "启动判断", "question": "谁先启动？", "inputs": ["当前控制窗口"],
            "steps": ["比较两个区间"], "output": ["受支持的结论"], "limit": "缺少时序时保留未知",
            "memories": [], "phases": ["round"], "example": "example.html"
        }})
        self.cli("init")
        result = json.loads(self.cli("method", "timing"))
        self.assertEqual(result["inputs"], ["当前控制窗口"])
        page = self.pack / "report/method-timing.html"
        html = page.read_text()
        self.assertIn("比较两个区间", html)
        self.assertIn('href="../example.html"', html)
        self.assertIn('href="method-timing.html"', (page.parent / "index.html").read_text())
        self.assertIn("尚无", html)

    def test_profile_scopes_rsi_and_replay(self):
        self.cli("init")
        self.cli("init")
        self.cli("rsi", "start-run", "--id", "one", "--title", "验证", "--date", "2026-11-19", "--game-version", "test1")
        d = json.loads(self.cli("rsi", "decision-template", "--run", "one", "--day", "1", "--phase", "round"))
        self.cli("rsi", "decision-template", "--run", "one", "--day", "1", "--phase", "opponent", ok=False)
        web = self.pack / "report"
        (web / "frame.txt").write_text("test evidence")
        d["before"].update(state="现场", goal="核分", evidence=["frame.txt"], memorySearch="初次",
                           chosenAction="出牌", prediction="4")
        d["before"]["candidates"] = [dict.fromkeys(("action", "benefit", "cost", "risk", "unknown"), "test")]
        self.write("before.json", d)
        self.cli("rsi", "prepare", "--input", str(self.pack / "before.json"))
        after = json.loads(self.cli("rsi", "outcome-template"))
        after.update(observed="实得4", evidence=["frame.txt"], reason="一致", nextAction="继续")
        self.write("after.json", after)
        self.cli("rsi", "finish", "--id", d["id"], "--input", str(self.pack / "after.json"))
        memory = dict(id="M1", revision=1, title="算分", condition="简单牌", action="先计算", expected="4",
                      caveat="无随机效果", status="待再验", phases=["round"], tags=[], gameVersion="test1",
                      evidence=[{"runId":"one","day":1,"href":"frame.txt"}],
                      history=[{"revision":1,"change":"第一次观察"}])
        self.write("memory.json", memory)
        self.cli("rsi", "memory", "--input", str(self.pack / "memory.json"))
        self.cli("rsi", "memory", "--input", str(self.pack / "memory.json"))
        memory.update(revision=2, action="修订", history=[{"revision":2,"change":"遗失旧判断"}])
        self.write("damaged.json", memory)
        self.cli("rsi", "memory", "--input", str(self.pack / "damaged.json"), ok=False)
        self.write("issue.json", {"id":"B1","title":"待复测","status":"待核","source":"frame.txt",
                                  "detailHtml":"","occurrences":[{"runId":"one","day":1}]})
        self.cli("rsi", "issue", "--input", str(self.pack / "issue.json"))
        self.cli("rsi", "check")
        self.cli("report")
        report = (web / "index.html").read_text()
        for s in ["验证游戏", "出牌", "实得4", "frame.txt"]:
            self.assertIn(s, report)
        self.assertFalse((self.root / "data").exists())

    def test_capture_and_cache(self):
        frame = self.pack / "frame.png"
        Image.new("RGB", (80, 60), "navy").save(frame)
        self.write("frames.json", {"batchId": "sample", "entries": [
            {"target": "hand", "source": "frame.png"},
            {"target": "detail", "id": "joker-1", "source": "frame.png", "box": [6, 5, 40, 30]}]})
        def capture(name):
            out = self.pack / name
            self.cli("observe", "round", "--input", str(self.pack / "frames.json"), "--output", str(out))
            return json.loads((out / "bundle.json").read_text())
        bundle = capture("first")
        self.assertEqual(bundle["entries"][0]["box"], [5, 4, 40, 20])
        template = json.loads((self.pack / "first/readings-template.json").read_text())["entries"]
        self.assertIn("text", template[1])
        self.assertNotIn("grade", template[1])
        self.write("answers.json", {"entries": [{"id": "joker-1", "text": "x", "uncertain": []}]})
        self.cli("annotate", "--bundle", str(self.pack / "first/bundle.json"), "--input", str(self.pack / "answers.json"))
        second = capture("second")
        self.assertEqual(second["entries"][1]["reading"]["text"], "x")
        self.assertIsNone(second["entries"][0]["reading"])
        self.assertTrue((self.pack / "second/index.html").is_file())
        Image.new("RGB", (100, 60)).save(frame)
        self.cli("observe", "round", "--input", str(self.pack / "frames.json"), "--output", str(self.pack / "bad"), ok=False)
        self.assertFalse((self.pack / "bad/bundle.json").exists())

    def test_calibrated_hover_requires_matching_window_size(self):
        obs = json.loads((self.pack / "observations.json").read_text())
        obs["round"]["targets"]["detail"].update(size=[80, 60], hoverAt=[25, 12], box=[5, 4, 40, 20])
        self.write("observations.json", obs)
        plan = json.loads(self.cli("plan", "round", "--size", "80", "60"))
        self.assertEqual(plan["targets"]["detail"]["hoverAt"], [25, 12])
        wider = json.loads(self.cli("plan", "round", "--size", "100", "60"))
        self.assertNotIn("hoverAt", wider["targets"]["detail"])
        self.assertNotIn("box", wider["targets"]["detail"])
        self.assertIn("calibrate", wider["targets"]["detail"])

    def test_click_target_and_crop_are_distinct_in_guide_and_plan(self):
        obs = json.loads((self.pack / "observations.json").read_text())
        obs["round"]["targets"]["tab"] = {
            "label": "伤害页签", "mode": "click", "fields": ["damage"], "locate": "切到统计页",
            "size": [80, 60], "clickAt": [4, 5], "box": [10, 20, 70, 50]}
        self.write("observations.json", obs)
        self.cli("init")
        guide = (self.pack / "report/capture-guide.html").read_text()
        for value in ("伤害页签", "切到统计页", "(4, 5)", "(10, 20) → (70, 50)"):
            self.assertIn(value, guide)
        self.assertIn("capture-guide.html", (self.pack / "report/index.html").read_text())
        plan = json.loads(self.cli("plan", "round", "--size", "100", "60"))
        self.assertNotIn("clickAt", plan["targets"]["tab"])
        self.assertNotIn("box", plan["targets"]["tab"])
        self.assertIn("calibrate", plan["targets"]["tab"])

    def test_new_model_without_core_changes(self):
        (self.pack / "score.py").write_text('def predict(state):\n    return {"score": sum(state["cards"])}\n')
        self.config["models"]["score"] = {"entry": "score.py", "revision": "1", "cache": True}
        self.write("game.json", self.config)
        self.write("hand.json", {"cards": [2, 3]})
        def score():
            return json.loads(self.cli("model", "score", "--input", str(self.pack / "hand.json")))
        self.assertFalse(score()["cacheHit"])
        hit = score()
        self.assertTrue(hit["cacheHit"])
        self.assertEqual(hit["result"]["score"], 5)
        self.write("hand.json", {"cards": [3]})
        self.assertFalse(score()["cacheHit"])
        self.config["version"] = "test2"
        self.write("game.json", self.config)
        self.assertFalse(score()["cacheHit"])
