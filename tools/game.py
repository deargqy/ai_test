"""Agent entry point for observing, modelling and reviewing a configured game."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from game_profile import GameProfile, StateCache, fingerprint, load_json
from game_report import report
import rsi
import steam_shots


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def initialize(game):
    game.data.parent.mkdir(parents=True, exist_ok=True)
    with rsi.data_lock(game.data):
        if not game.data.exists():
            data = {"schemaVersion": 1, "game": game.name, "protocol": {"version": "1"},
                    "memories": [], "runs": [], "issues": []}
            rsi.write_atomic(game.data, dump(data) + "\n")
        data = load_json(game.data)
        rsi.validate(data, game)
        report(game, data)
    return {"data": str(game.data), "report": str(game.page)}


def model(game, name, input_file, html=None):
    if name not in game.models:
        raise ValueError(f"尚未登记模型 {name}；请在当前游戏配置的 models 中登记")
    descriptor = game.models[name]
    path = game.path(descriptor["entry"])
    state = load_json(input_file)
    cache = StateCache(game)
    memoize = descriptor.get("cache", False) and bool(game.version)
    dependencies = [path, *(game.path(p) for p in descriptor.get("dependencies", []))]
    key = fingerprint(["model", game.id, game.version, name, descriptor["revision"], descriptor.get("settings", {}),
                       [hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies], state])
    result = cache.access(key) if memoize else None
    hit = result is not None
    if not hit or html:
        spec = importlib.util.spec_from_file_location("_game_model_" + name, path)
        if not spec or not spec.loader:
            raise ValueError(f"无法读取模型文件 {path}")
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(path.parent))
        try:
            spec.loader.exec_module(module)
            if not hit:
                result = module.predict(state, **descriptor.get("settings", {}))
                if not isinstance(result, dict):
                    raise ValueError("predict 需要返回 JSON 对象")
                dump(result)
                if memoize:
                    cache.access(key, result)
            if html:
                from game_report import layout, e
                html.parent.mkdir(parents=True, exist_ok=True)
                if hasattr(module, "render_prediction"):
                    module.render_prediction(state, result, html)
                else:
                    blocks = "".join(f"<details open><summary>{e(label)}</summary><pre>{e(dump(value))}</pre></details>"
                                     for label, value in result.items())
                    rsi.write_atomic(html, layout(f"{game.name} · {name} · 离线试算", blocks))
        finally:
            sys.path.pop(0)
    return {"gameId": game.id, "gameVersion": game.version, "model": name, "revision": descriptor["revision"],
            "inputDigest": key, "cacheHit": hit, "result": result}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", default="cats", help="games/ 下的目录名，默认 cats")
    cli.add_argument("--version", help="本次实测的游戏版本，覆盖配置默认值")
    commands = cli.add_subparsers(dest="command", required=True)
    steam_shots.register(commands)
    commands.add_parser("init", help="准备本游戏的记录与 HTML，可重复运行")
    commands.add_parser("info", help="查看阶段、基础知识、模型和界面")
    commands.add_parser("check", help="检查配置和现有记录")
    commands.add_parser("report", help="从本游戏数据重新生成 HTML")
    method = commands.add_parser("method", help="读取判断步骤、适用条件、经验修订和证据")
    method.add_argument("name")
    plan = commands.add_parser("plan", help="列出本阶段的观察目标、坐标与读取字段")
    plan.add_argument("phase")
    plan.add_argument("--size", nargs=2, type=int, metavar=("WIDTH", "HEIGHT"), help="当前游戏窗口截图尺寸")
    observe = commands.add_parser("observe", help="按游戏配置裁切并打包一批原始截图")
    observe.add_argument("phase")
    observe.add_argument("--input", required=True, type=Path)
    observe.add_argument("--output", required=True, type=Path)
    annotate = commands.add_parser("annotate", help="保存识别结果并更新可复用的精确匹配")
    annotate.add_argument("--bundle", required=True, type=Path)
    annotate.add_argument("--input", required=True, type=Path)
    run_model = commands.add_parser("model", help="执行本游戏登记的离线模型")
    run_model.add_argument("name")
    run_model.add_argument("--input", required=True, type=Path)
    run_model.add_argument("--output", type=Path)
    run_model.add_argument("--html", type=Path, help="保存模型专属交互页或通用结果页")
    commands.add_parser("rsi", add_help=False, help="跨局记忆和决策记录，传入 --help 查看")
    args, extra = cli.parse_known_args(argv)
    if args.command != "rsi" and extra:
        cli.error(f"未知参数 {' '.join(extra)}")
    game = GameProfile(args.game)
    if args.version:
        game.version = args.version
    game.check()
    if args.command == "rsi":
        return rsi.main(extra, game)
    if args.command == "screenshot":
        result = steam_shots.run(game, args)
    elif args.command == "init":
        result = initialize(game)
    elif args.command == "info":
        result = {"game": game.name, "version": game.version, "phases": game.phases,
                  "capture": steam_shots.capture_settings(game),
                  "knowledge": game.knowledge.read_text(encoding="utf-8"), "models": game.models, "views": game.views,
                  "methods": {k: v["title"] for k, v in game.methods.items()}}
        if game.pilots:
            result["pilots"] = {k: v["name"] for k, v in game.pilots["pilots"].items()}
    elif args.command == "method":
        from game_method import describe
        result = describe(game, load_json(game.data), args.name)
    elif args.command == "check":
        if game.data.exists():
            rsi.validate(load_json(game.data), game)
        result = {"game": game.id, "configuration": "ok", "records": "checked" if game.data.exists() else "not-initialized"}
    elif args.command == "report":
        with rsi.data_lock(game.data):
            report(game, load_json(game.data))
        result = {"report": str(game.page)}
    elif args.command == "plan":
        result = game.observation_plan(args.phase, args.size)
        settings = steam_shots.capture_settings(game)
        if settings:
            result["capture"] = settings
    elif args.command in ("observe", "annotate"):
        import game_observation
        if args.command == "observe":
            batch = game_observation.capture(game, args.phase, args.input, args.output)
        else:
            batch = game_observation.annotate(game, args.bundle, args.input)
        result = {"batch": batch["batchId"], "recognition": batch["recognition"], **batch["metrics"]}
    else:
        result = model(game, args.name, args.input, args.html)
        if args.output:
            rsi.write_atomic(args.output, dump(result) + "\n")
            result = {"output": str(args.output), "model": args.name, "cacheHit": result["cacheHit"]}
    print(dump(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, ImportError) as error:
        raise SystemExit(f"未完成：{error}") from error
