"""Locate a fresh screenshot saved by Steam after the Agent invokes its hotkey."""
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from uuid import uuid4

from game_profile import load_json
from rsi import data_lock, write_atomic


def capture_settings(game):
    steam = game.config.get("steam", {})
    app = str(steam.get("appId", ""))
    if not app.isascii() or not app.isdigit():
        return None
    return {"provider": "steam", "appId": app, "defaultHotkey": "F12",
            "workflow": "先 screenshot mark，再在目标游戏按 Steam 截图键，最后 screenshot read 读取本次新图。"}


def default_roots():
    if sys.platform == "win32":
        import winreg
        for key, value, hive in [(r"Software\Valve\Steam", "SteamPath", winreg.HKEY_CURRENT_USER),
                                 (r"Software\WOW6432Node\Valve\Steam", "InstallPath", winreg.HKEY_LOCAL_MACHINE)]:
            try:
                with winreg.OpenKey(hive, key) as registry:
                    yield Path(winreg.QueryValueEx(registry, value)[0])
            except OSError:
                continue
        for env in ("ProgramFiles(x86)", "ProgramFiles"):
            if os.getenv(env):
                yield Path(os.environ[env]) / "Steam"
    elif sys.platform == "darwin":
        yield Path.home() / "Library/Application Support/Steam"
    else:
        for folder in (".local/share/Steam", ".steam/steam", ".var/app/com.valvesoftware.Steam/.local/share/Steam"):
            yield Path.home() / folder


def user_data_directory(root):
    override = root or os.getenv("AI_TEST_STEAM_ROOT")
    candidates = [Path(override).expanduser()] if override else default_roots()
    for candidate in candidates:
        data = candidate / "userdata"
        if data.is_dir():
            return data.resolve()
    raise ValueError("未找到 Steam 客户端的 userdata。请在保存截图的电脑执行，用 --steam-root 指定含 userdata 的 Steam 安装目录。")


def snapshot(userdata, app, account):
    files = {}
    for user in userdata.iterdir():
        if not user.name.isascii() or not user.name.isdigit() or (account and user.name != account):
            continue
        folder = user / "760" / "remote" / app / "screenshots"
        try:
            for p in folder.iterdir():
                if p.suffix.lower() not in (".jpg", ".jpeg", ".png") or not p.is_file():
                    continue
                try:
                    stat = p.stat()
                except FileNotFoundError:
                    continue
                files[p.relative_to(userdata).as_posix()] = [stat.st_size, stat.st_mtime_ns]
        except FileNotFoundError:
            continue
    return files


def mark(game, app, args):
    userdata = user_data_directory(args.steam_root)
    account = args.account
    if account is not None and not (account.isascii() and account.isdigit()):
        raise ValueError("--account 需要填写 userdata 下的数字目录名")
    marker = args.marker or game.folder / ".cache" / "steam-shots" / f"{uuid4().hex}.json"
    state = {"game": game.id, "app": app, "userdata": str(userdata), "account": account,
             "baseline": snapshot(userdata, app, account)}
    write_atomic(marker, json.dumps(state, ensure_ascii=False))
    return {"marker": str(marker.resolve()), "appId": app, "existingFiles": len(state["baseline"]),
            "next": "保持目标游戏在前台，按一次 Steam 的截图快捷键（默认 F12），然后用此 marker 执行 screenshot read。"}


def archive(destination, payload, suffix):
    if destination.suffix.lower().replace(".jpeg", ".jpg") != suffix.lower().replace(".jpeg", ".jpg"):
        raise ValueError(f"归档文件请使用原图扩展名 {suffix}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with data_lock(destination):
        if destination.exists():
            if destination.read_bytes() != payload:
                raise ValueError(f"已有不同的截图，请使用新的归档文件名 {destination}")
            return
        descriptor, name = tempfile.mkstemp(dir=destination.parent)
        temp = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as f:
                f.write(payload)
            os.replace(temp, destination)
        finally:
            temp.unlink(missing_ok=True)


def read(game, app, args):
    from PIL import Image
    state = load_json(args.marker)
    if (state["game"], state["app"]) != (game.id, app):
        raise ValueError("截图基线属于其他游戏，请为本游戏重新 mark")
    if not 0 <= args.timeout <= 60:
        raise ValueError("等待时间范围为 0 到 60 秒")
    userdata = Path(state["userdata"])
    if not userdata.is_dir():
        raise ValueError("基线中的 Steam 目录在本机不可用，请在保存截图的电脑重新 mark")
    deadline = time.monotonic() + args.timeout
    while True:
        current = snapshot(userdata, app, state["account"])
        changed = [name for name, sig in current.items() if sig != state["baseline"].get(name)]
        if len(changed) > 1:
            raise ValueError("这次基线之后出现多张新截图。请重新 mark 后只按一次截图键，多账号时可用 --account 限定。")
        reason = "尚未发现该游戏的新 Steam 原图。核对目标游戏、Steam 截图快捷键和截图保存电脑或目录。"
        if changed:
            name = changed[0]
            source = userdata / name
            try:
                payload = source.read_bytes()
                with Image.open(BytesIO(payload)) as im:
                    im.verify()
                with Image.open(BytesIO(payload)) as im:
                    im.load()
                    size = list(im.size)
                stat = source.stat()
                if [stat.st_size, stat.st_mtime_ns] != current[name]:
                    raise OSError("文件仍在写入")
            except (OSError, SyntaxError, ValueError):
                reason = "发现 Steam 新文件，但还未得到完整可解码的截图。请用同一 marker 重试 read。"
            else:
                if args.output:
                    archive(args.output, payload, source.suffix)
                return {"source": str(source), "size": size, "appId": app,
                        "file": str((args.output or source).resolve())}
        left = deadline - time.monotonic()
        if left <= 0:
            raise ValueError(reason)
        time.sleep(min(0.2, left))


def register(commands):
    parser = commands.add_parser("screenshot", help="取得本次 Steam 新图，供单张或批量观察")
    sub = parser.add_subparsers(dest="shot_command", required=True)
    before = sub.add_parser("mark", help="在按截图键前记录目标游戏原图目录")
    before.add_argument("--steam-root", type=Path)
    before.add_argument("--account")
    before.add_argument("--marker", type=Path)
    after = sub.add_parser("read", help="等待并读取此基线之后的单张可解码原图")
    after.add_argument("--marker", type=Path, required=True)
    after.add_argument("--timeout", type=float, default=8)
    after.add_argument("--output", type=Path, help="可选，按原格式归档到项目")


def run(game, args):
    settings = capture_settings(game)
    if not settings:
        raise ValueError("该游戏未配置 Steam appId")
    if args.shot_command == "mark":
        return mark(game, settings["appId"], args)
    try:
        return read(game, settings["appId"], args)
    except ModuleNotFoundError as error:
        if error.name != "PIL":
            raise
        raise ValueError("验证 Steam 图片需要 Pillow；请使用截图管线的 Python 环境并用同一 marker 重试。") from error
