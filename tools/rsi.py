"""Read RSI memories and record decisions for the offline playtest page.

Uses Python's standard library. Run with --help for the available commands.
The JSON file is the source of truth; the browser data is regenerated from it.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PHASES = ("observe", "shop", "build", "opponent", "result")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def data_lock(path):
    lock = path.with_suffix(path.suffix + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError(f"另一个记录操作正在进行，请稍后重试。锁文件 {lock}") from error
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)


def read_data(path):
    return json.loads(path.read_text(encoding="utf-8"))


def local_reference(reference):
    require(isinstance(reference, str) and reference.strip(), "证据路径不能为空")
    parts = urlsplit(reference)
    require(parts.scheme in ("", "https", "http"), f"不支持的链接 {reference}")
    if parts.scheme or not parts.path:
        return
    target = (DOCS / unquote(parts.path)).resolve()
    require(target.is_relative_to(ROOT), f"引用超出项目目录 {reference}")
    require(target.is_file(), f"文件不存在 {reference}")


class References(HTMLParser):
    def handle_starttag(self, tag, attrs):
        require(tag not in ("script", "iframe", "object"), f"记录正文含不支持的元素 {tag}")
        for key, value in attrs:
            require(not key.startswith("on"), "记录正文不能包含事件处理器")
            if key in ("href", "src") and value:
                local_reference(value)


def validate(data):
    require(data.get("schemaVersion") == 1, "不支持的数据版本")
    memories = {memory["id"]: memory for memory in data["memories"]}
    require(len(memories) == len(data["memories"]), "经验编号重复")
    runs = {run["id"]: run for run in data["runs"]}
    require(len(runs) == len(data["runs"]), "局号重复")
    issues = {issue["id"]: issue for issue in data["issues"]}
    require(len(issues) == len(data["issues"]), "问题编号重复")
    decisions = set()
    day_keys = set()
    for run in data["runs"]:
        numbers = [day["day"] for day in run["days"]]
        require(len(numbers) == len(set(numbers)), f"{run['id']} 游戏日重复")
        if run["status"] == "complete":
            require(sorted(numbers) == list(range(1, max(numbers) + 1)), f"{run['id']} 缺游戏日")
        for day in run["days"]:
            require(isinstance(day["day"], int) and day["day"] > 0, "游戏日需为正整数")
            day_keys.add((run["id"], day["day"]))
            for ref in day.get("sources", []):
                local_reference(ref)
            for image in day.get("images", []):
                local_reference(image["src"])
            References().feed(day.get("detailHtml", ""))
            for decision in day.get("decisions", []):
                require(decision["id"] not in decisions, "决策编号重复")
                decisions.add(decision["id"])
                validate_before(decision, memories)
                if decision.get("after"):
                    validate_after(decision["after"])
    for memory in data["memories"]:
        require(memory["revision"] > 0 and memory["phases"], "经验需有修订号和适用阶段")
        require(all(phase in PHASES for phase in memory["phases"]), "未知经验阶段")
        for evidence in memory["evidence"]:
            require((evidence["runId"], evidence["day"]) in day_keys, "经验来源日不存在")
            if evidence.get("href"):
                local_reference(evidence["href"])
    for issue in data["issues"]:
        local_reference(issue["source"])
        References().feed(issue["detailHtml"])
        for occurrence in issue["occurrences"]:
            require((occurrence["runId"], occurrence["day"]) in day_keys, "问题关联日不存在")


def validate_before(decision, memories):
    require(decision.get("id") and decision.get("phase") in PHASES, "决策需有编号及有效阶段")
    before = decision["before"]
    for key in ("state", "goal", "memorySearch", "chosenAction", "prediction"):
        require(isinstance(before.get(key), str) and before[key].strip(), f"决策前字段未填写 {key}")
    require(before.get("evidence"), "决策前需有现场截图路径")
    for ref in before["evidence"]:
        local_reference(ref)
    require(before.get("candidates"), "至少记录一个实际可行的动作")
    for option in before["candidates"]:
        for key in ("action", "benefit", "cost", "risk", "unknown"):
            require(isinstance(option.get(key), str) and option[key].strip(), f"候选字段未填写 {key}")
    cited = set()
    for use in before.get("memories", []):
        require(use["id"] in memories, f"未知经验 {use['id']}")
        require(use["id"] not in cited, "同一决策不能重复引用同一经验")
        cited.add(use["id"])
        versions = [item["revision"] for item in memories[use["id"]]["history"]]
        require(use["revision"] in versions, "经验修订号不存在")
        require(use["origin"] in ("autonomous", "player"), "经验来源需标记自主调用或玩家提醒")
        require(use["use"] in ("applied", "notApplied"), "需记录经验采用情况")
        require(use.get("reason"), "需说明采用或未采用经验的原因")


def validate_after(after):
    require(after.get("observed") and after.get("nextAction"), "结果与下一步不能为空")
    require(after.get("evidence"), "结果需附截图或原始记录")
    for ref in after["evidence"]:
        local_reference(ref)
    require(after["operationResult"] in ("succeeded", "failed", "unknown"), "操作结果无效")
    require(after["predictionResult"] in ("supported", "refuted", "unknown"), "预测核对结果无效")
    require(after["memoryDecision"] in ("retain", "narrow", "revise", "pending"), "经验处理结果无效")
    require(after.get("reason"), "需记录结果解释及限制")


def build(data, path):
    validate(data)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    write_atomic(path, "// Generated from data/playtest.json by tools/rsi.py build.\nwindow.PLAYTEST_DATA = " + text + ";\n")


def persist(data, args):
    validate(data)
    write_atomic(args.data, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    build(data, args.output)


def find_run(data, run_id):
    run = next((run for run in data["runs"] if run["id"] == run_id), None)
    require(run is not None, f"局号不存在 {run_id}")
    return run


def run_template(run_id, day, phase):
    return {
        "runId": run_id, "day": day, "id": f"{run_id}-d{day:02d}-01", "phase": phase,
        "before": {
            "state": "", "goal": "", "evidence": [], "memorySearch": "",
            "memories": [],
            "candidates": [{"action": "", "benefit": "", "cost": "", "risk": "", "unknown": ""}],
            "chosenAction": "", "prediction": "",
        },
    }


def mutate(args):
    with data_lock(args.data):
        data = read_data(args.data)
        if args.command == "start-run":
            require(not any(run["id"] == args.id for run in data["runs"]), "局号已经存在")
            data["runs"].append({
                "id": args.id, "title": args.title, "status": "active",
                "date": args.date, "endedAt": None, "durationMinutes": None,
                "gameVersion": args.game_version, "build": args.build,
                "result": "进行中", "wins": 0, "losses": 0,
                "finalImage": None, "sources": [], "days": [],
                "protocolVersion": data["protocol"]["version"],
            })
        elif args.command == "prepare":
            incoming = read_data(args.input)
            run = find_run(data, incoming["runId"])
            require(run["status"] == "active", "只向进行中的对局追加新决策")
            require(not incoming.get("after"), "prepare 记录点击前的判断，请用 finish 回填结果")
            validate_before(incoming, {m["id"]: m for m in data["memories"]})
            existing = next((item for r in data["runs"] for d in r["days"] for item in d.get("decisions", []) if item["id"] == incoming["id"]), None)
            if existing:
                require(existing["runId"] == incoming["runId"] and existing["day"] == incoming["day"] and existing["phase"] == incoming["phase"] and existing["before"] == incoming["before"], "该编号已有不同的战前记录，请保留原判断并使用新的编号")
                build(data, args.output)
                print("该决策已记录，原判断已保留。")
                return
            day = next((day for day in run["days"] if day["day"] == incoming["day"]), None)
            if day is None:
                day = {
                    "day": incoming["day"], "title": "正在记录决策", "phase": "待现场确认",
                    "outcome": "unknown", "wins": run["wins"], "losses": run["losses"],
                    "before": "", "after": "", "detailHtml": "", "sources": [],
                    "images": [], "decisions": [], "legacyUsage": "",
                }
                run["days"].append(day)
                run["days"].sort(key=lambda item: item["day"])
            incoming["recordedAt"] = timestamp()
            incoming["after"] = None
            incoming["protocolVersion"] = data["protocol"]["version"]
            day["decisions"].append(incoming)
        elif args.command == "finish":
            after = read_data(args.input)
            validate_after(after)
            record = next((item for r in data["runs"] for d in r["days"] for item in d.get("decisions", []) if item["id"] == args.id), None)
            require(record is not None, "请先用 prepare 保存决策前的判断")
            if record["after"]:
                require(record["after"] == after, "已有不同结果，请保留原结果并在原始日志追加纠正依据")
            else:
                record["after"] = after
                record["finishedAt"] = timestamp()
        persist(data, args)
    print("已保存，并更新离线网页数据。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data/playtest.json")
    parser.add_argument("--output", type=Path, default=DOCS / "playtest-data.js")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="校验数据并更新离线页面")
    sub.add_parser("check", help="核对来源、编号、决策和结果")
    memories = sub.add_parser("memories", help="读取当前阶段的经验；关键词只改变排序")
    memories.add_argument("--phase", choices=PHASES, required=True)
    memories.add_argument("--tags", nargs="*", default=[])
    memories.add_argument("--game-version", default="1.0.0.2218")
    template = sub.add_parser("decision-template", help="输出点击前的记录模板")
    template.add_argument("--run", required=True)
    template.add_argument("--day", type=int, required=True)
    template.add_argument("--phase", choices=PHASES, required=True)
    sub.add_parser("outcome-template", help="输出动作后的核对模板")
    start = sub.add_parser("start-run", help="确认现场已开始新局后建立记录")
    start.add_argument("--id", required=True)
    start.add_argument("--title", required=True)
    start.add_argument("--date", required=True)
    start.add_argument("--game-version", required=True)
    start.add_argument("--build", default="待现场确认")
    prepare = sub.add_parser("prepare", help="点击前保存决定，原判断按编号保留")
    prepare.add_argument("--input", type=Path, required=True)
    finish = sub.add_parser("finish", help="回填操作结果和预测核对")
    finish.add_argument("--id", required=True)
    finish.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    if args.command in ("start-run", "prepare", "finish"):
        mutate(args)
    elif args.command == "decision-template":
        print(json.dumps(run_template(args.run, args.day, args.phase), ensure_ascii=False, indent=2))
    elif args.command == "outcome-template":
        print(json.dumps({
            "observed": "", "evidence": [], "operationResult": "unknown",
            "predictionResult": "unknown", "memoryDecision": "pending",
            "reason": "", "nextAction": "",
        }, ensure_ascii=False, indent=2))
    else:
        data = read_data(args.data)
        if args.command == "memories":
            matches = [memory for memory in data["memories"] if args.phase in memory["phases"]]
            matches.sort(key=lambda item: -sum(tag in " ".join(item["tags"]) for tag in args.tags))
            print(json.dumps({
                "protocol": data["protocol"],
                "gameVersion": args.game_version,
                "versionCheck": "条件仍需与现场核对",
                "memories": [{**item, "versionMatches": item["gameVersion"] == args.game_version} for item in matches],
            }, ensure_ascii=False, indent=2))
        elif args.command == "build":
            with data_lock(args.data):
                build(read_data(args.data), args.output)
            print("数据校验通过，离线页面已更新。")
        else:
            validate(data)
            print(f"校验通过，{len(data['memories'])} 条经验、{sum(len(run['days']) for run in data['runs'])} 个游戏日、{len(data['issues'])} 份问题报告。")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(f"记录未完成：{error}") from error
