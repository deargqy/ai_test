"""Load a game's offline testing configuration and resolve its project files."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


class GameProfile:
    def __init__(self, game_id):
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", game_id):
            raise ValueError("游戏标识只支持小写字母、数字、下划线和连字符")
        self.id = game_id
        self.folder = ROOT / "games" / game_id
        self.config = load_json(self.folder / "game.json")
        self.name = self.config["name"]
        self.version = self.config.get("version")
        self.phases = self.config["phases"]
        if not isinstance(self.phases, dict) or not self.phases or not all(self.phases.values()):
            raise ValueError("phases 需要填写阶段标识和名称")
        self.observations = load_json(self.folder / "observations.json")
        if set(self.observations) != set(self.phases):
            raise ValueError("观察配置和阶段必须对应")
        self.knowledge = self.path(self.config.get("knowledge", "knowledge.md"))
        self.data = self.path(self.config.get("data", "data/playtest.json"))
        self.page = self.path(self.config.get("report", "report/index.html"))
        self.docs = self.page.parent
        self.models = self.config.get("models", {})
        self.views = self.config.get("views", {})
        self.model_views = self.config.get("modelViews", {})
        self.pilots = load_json(self.path(self.config["pilots"])) if "pilots" in self.config else {}
        self.methods = load_json(self.path(self.config["methods"])) if "methods" in self.config else {}

    def path(self, reference):
        target = (self.folder / reference).resolve()
        if not target.is_relative_to(ROOT):
            raise ValueError(f"配置路径超出项目目录 {reference}")
        return target

    def targets(self, phase):
        if phase not in self.phases:
            raise ValueError(f"未知阶段 {phase}；可选 {', '.join(self.phases)}")
        return self.observations[phase]["targets"]

    def observation_plan(self, phase, size):
        targets = self.targets(phase)
        if size is None:
            return self.observations[phase]
        if min(size) <= 0:
            raise ValueError("窗口尺寸需要是正整数")
        calibrated = {}
        for key, original in targets.items():
            target = original.copy()
            if target.get("size") and target["size"] != size:
                target.pop("box", None)
                target.pop("hoverAt", None)
                target.pop("clickAt", None)
                target["calibrate"] = "先从本机全景重新定位操作点和截取区域"
            calibrated[key] = target
        return {**self.observations[phase], "size": size, "targets": calibrated}

    def check(self):
        if not self.knowledge.is_file():
            raise ValueError(f"找不到基础知识文件 {self.knowledge}")
        for phase in self.phases:
            targets = self.targets(phase)
            if not targets:
                raise ValueError(f"{phase} 缺少观察对象")
            for key, item in targets.items():
                fields = item["fields"]
                reserved = {"id", "uncertain", "method", "readAt", "evidenceSha256"}
                if (item["mode"] not in ("frame", "region", "hover", "click") or not isinstance(fields, list) or not fields
                        or not all(isinstance(f, str) and f for f in fields) or reserved.intersection(fields)):
                    raise ValueError(f"{phase}/{key} 的观察方式或字段无效")
                for mode, field in (("hover", "hoverAt"), ("click", "clickAt")):
                    if field in item:
                        w, h = item["size"]
                        x, y = item[field]
                        if not (item["mode"] == mode and type(x) is int and type(y) is int and 0 <= x < w and 0 <= y < h):
                            raise ValueError(f"{phase}/{key} 的操作点 {field} 无效")
                if item.get("box") is not None:
                    w, h = item["size"]
                    x0, y0, x1, y1 = item["box"]
                    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
                        raise ValueError(f"{phase}/{key} 的截取范围无效")
        if self.pilots:
            roster = self.pilots["pilots"]
            if not set(self.pilots.get("recordedRuns", {}).values()).issubset(roster):
                raise ValueError("历史对局引用了未知机师")
            names = [pilot["name"] for pilot in roster.values()]
            if len(set(names)) != len(names) or any(p["name"] in roster and p["name"] != k for k, p in roster.items()):
                raise ValueError("机师名称和标识须能唯一定位角色")
            for key, pilot in roster.items():
                if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key):
                    raise ValueError(f"无效的机师标识 {key}")
                if not isinstance(pilot["lives"], int) or pilot["lives"] < 1:
                    raise ValueError(f"{key} 的可失败次数须为正整数")
                for field in ("name", "skill", "ability"):
                    if not isinstance(pilot[field], str) or not pilot[field].strip():
                        raise ValueError(f"{key} 缺少 {field}")
                if not set(pilot["focus"]).issubset(self.phases):
                    raise ValueError("机师判断使用了未知决策阶段")
                for ref in [pilot["source"], *(o["source"] for o in pilot["observations"])]:
                    if not self.path(ref).is_file():
                        raise ValueError(f"找不到机师证据 {ref}")
        model_pages = [v["href"].partition("#")[0] for v in self.model_views.values()]
        for key, method in self.methods.items():
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", key):
                raise ValueError(f"无效的方法标识 {key}")
            for field in ("question", "title", "limit"):
                if not isinstance(method.get(field), str) or not method[field].strip():
                    raise ValueError(f"{key} 缺少 {field}")
            for field in ("inputs", "steps", "output", "memories", "phases"):
                items = method.get(field)
                if not isinstance(items, list) or not all(isinstance(v, str) and v for v in items):
                    raise ValueError(f"{key} 的 {field} 需为字符串列表")
            if not set(method["phases"]).issubset(self.phases):
                raise ValueError(f"{key} 引用了未配置的决策阶段")
            if method.get("calculation") and method["calculation"] not in self.models:
                raise ValueError(f"{key} 引用了未登记的计算模型")
            if method.get("example"):
                model_pages.append(method["example"].partition("#")[0])
        for asset in [*(m["entry"] for m in self.models.values()), *model_pages, *self.views.values()]:
            if not self.path(asset).is_file():
                raise ValueError(f"找不到游戏资源 {asset}")


def fingerprint(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


class StateCache:
    """Store exact, versioned matches. Runtime files belong to one game pack."""
    def __init__(self, game):
        self.path = game.folder / ".cache" / "states.sqlite3"

    def access(self, key, value=None):
        if value is None and not self.path.exists():
            return None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS states (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            if value is not None:
                db.execute("INSERT OR REPLACE INTO states VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))
                return value
            row = db.execute("SELECT value FROM states WHERE key = ?", (key,)).fetchone()
            return json.loads(row[0]) if row else None
