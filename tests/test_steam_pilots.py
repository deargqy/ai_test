import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def command(*args):
    return subprocess.run([sys.executable, str(ROOT / "tools/game.py"), "--game", "cats", *map(str, args)],
                          capture_output=True, text=True)


class SessionCaptureTests(unittest.TestCase):
    def test_only_new_full_size_image_from_selected_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "Steam"
            (root / "userdata").mkdir(parents=True)
            marker = base / "session.json"
            def shot(app, filename):
                folder = root / "userdata" / "123" / "760" / "remote" / app / "screenshots"
                path = folder / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (64, 36), "green").save(path)
                return path
            shot("4822560", "old.jpg")
            cmd = command("screenshot", "mark", "--steam-root", root, "--marker", marker)
            self.assertEqual(cmd.returncode, 0, cmd.stderr)
            shot("2379780", "other.jpg")
            shot("4822560", "thumbnails/thumbnail.jpg")
            def read():
                return command("screenshot", "read", "--marker", marker, "--timeout", "0")
            stale = read()
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("尚未发现", stale.stderr)
            new = shot("4822560", "new.jpg")
            p = read()
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(Path(json.loads(p.stdout)["source"]).resolve(), new.resolve())
            shot("4822560", "another.jpg")
            self.assertNotEqual(read().returncode, 0)

    def test_first_screenshot_folder_and_incomplete_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "userdata").mkdir()
            marker = root / "marker.json"
            cmd = command("screenshot", "mark", "--steam-root", root, "--marker", marker)
            self.assertEqual(cmd.returncode, 0, cmd.stderr)
            img = root / "userdata/567/760/remote/4822560/screenshots/first.jpg"
            img.parent.mkdir(parents=True)
            img.write_bytes(b"partial")
            p = command("screenshot", "read", "--marker", marker, "--timeout", 0)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("完整", p.stderr)
            Image.new("RGB", (24, 13)).save(img)
            p = command("screenshot", "read", "--marker", marker, "--timeout", 0)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)["size"], [24, 13])

    def test_archives_selected_account_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            folders = [base / "userdata" / user / "760/remote/4822560/screenshots" for user in ("100", "101")]
            for folder in folders:
                folder.mkdir(parents=True)
            marker = base / "session.json"
            captured = command("screenshot", "mark", "--steam-root", base, "--account", "101", "--marker", marker)
            self.assertEqual(captured.returncode, 0, captured.stderr)
            for folder in folders:
                Image.new("RGB", (24, 13)).save(folder / "first.jpg")
            output = base / "evidence/first.jpg"
            args = ("screenshot", "read", "--marker", marker, "--timeout", 0, "--output", output)
            p = command(*args)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(Path(json.loads(p.stdout)["source"]), (folders[1] / "first.jpg").resolve())
            self.assertEqual(output.read_bytes(), (folders[1] / "first.jpg").read_bytes())
            output.write_bytes(b"previous")
            self.assertNotEqual(command(*args).returncode, 0)
            self.assertEqual(output.read_bytes(), b"previous")


class PilotTests(unittest.TestCase):
    def test_each_cat_has_independent_sources_and_focused_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            def predict(pilot):
                path.write_text(json.dumps({"pilot":pilot, "phase":"shop"}))
                p = command("model", "pilot", "--input", path)
                self.assertEqual(p.returncode, 0, p.stderr)
                return json.loads(p.stdout)["result"]
            a,b = predict("莫瑟"),predict("德米特里")
            self.assertNotEqual(a["focus"], b["focus"])
            self.assertIn("50", a["ability"])
            self.assertNotIn("莫瑟", json.dumps(b, ensure_ascii=False))
            self.assertEqual(b["observations"], [])
            path.write_text('{"pilot":"unknown"}')
            self.assertNotEqual(command("model","pilot","--input",path).returncode, 0)

    def test_resume_resolves_only_documented_pilot(self):
        for run,pilot in [("run03","若茜"),("run04","胡班·本·帕尔文"),("run05","莫瑟")]:
            p = command("rsi", "memories", "--phase", "shop", "--run", run)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)["pilot"]["name"], pilot)

    def test_new_run_takes_only_its_pilot_specific_memories(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads((ROOT / "data/playtest.json").read_text())
            file = Path(tmp) / "playtest.json"
            file.write_text(json.dumps(data))
            def rsi(*args):
                return command("rsi", "--data", file, "--output", file.with_suffix(".js"), *args)
            p = rsi("start-run", "--id", "sample", "--title", "测试", "--date", "2026-11-19",
                    "--game-version", "fixture", "--pilot", "德米特里")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(file.read_text())["runs"][-1]["pilotId"], "dimitri")
            original = next(m for m in data["memories"] if "shop" in m["phases"])
            for pilot in ("mose", "dimitri"):
                card = {**original, "id": pilot + "-test", "revision": 1, "history": original["history"][:1],
                        "pilotId": pilot}
                path = Path(tmp) / (pilot + ".json")
                path.write_text(json.dumps(card))
                saved = rsi("memory", "--input", path)
                self.assertEqual(saved.returncode, 0, saved.stderr)
            def memories(run):
                found = rsi("memories", "--run", run, "--phase", "shop")
                self.assertEqual(found.returncode, 0, found.stderr)
                return json.loads(found.stdout)
            current = memories("sample")
            self.assertEqual(current["pilot"]["id"], "dimitri")
            ids = [m["id"] for m in current["memories"]]
            self.assertIn("dimitri-test", ids)
            self.assertIn(original["id"], ids)
            self.assertNotIn("mose-test", ids)
            unknown = memories("run01")
            self.assertIsNone(unknown["pilot"])
            self.assertFalse(any("pilotId" in m for m in unknown["memories"]))
