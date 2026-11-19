"""Use the selected phase to turn Agent captures into a batch of calibrated crops."""
import os
from pathlib import Path
import tempfile

from PIL import Image

import observe
from game_profile import StateCache, fingerprint, load_json


def cache_key(game, bundle, entry, target):
    return fingerprint(["reading", game.id, bundle["gameVersion"], bundle["phase"],
                        entry["target"], target, entry["cropSha256"]])


def capture(game, phase, source_list, output):
    targets = game.targets(phase)
    source_list = source_list.resolve()
    frames = load_json(source_list)
    entries, definitions = [], {}
    size = None
    for item in frames["entries"]:
        key = item["target"]
        if key not in targets:
            raise ValueError(f"{phase} 没有观察对象 {key}")
        target = targets[key]
        source = (source_list.parent / item["source"]).resolve()
        with Image.open(source) as image:
            width, height = image.size
        if size and size != [width, height]:
            raise ValueError("同一批次的截图分辨率不一致")
        size = [width, height]
        if "box" in item:
            box = item["box"]
        elif "box" in target:
            if size != target["size"]:
                raise ValueError(f"{key} 的标定尺寸与现场不同，请在当前截图重新标定")
            box = target["box"]
        elif target["mode"] == "frame":
            box = [0, 0, width, height]
        else:
            raise ValueError(f"{key} 需要在当前截图定位，并在 entries 中填 box")
        identifier = item.get("id", key)
        entries.append({"source": str(source), "id": identifier, "label": key, "box": box})
        definitions[identifier] = key
    if not entries:
        raise ValueError("本批次缺少截图")
    manifest = {"batchId": frames["batchId"], "entries": entries, "expectedSize": size,
                "context": frames.get("context", {})}
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish the entire directory at once, including its reading template and preview.
    if output.exists():
        raise ValueError(f"批次目录已存在 {output}")
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        working = Path(tmp) / "batch"
        path = Path(tmp) / "manifest.json"
        observe.save(path, manifest)
        bundle = observe.pack(path, working)
        bundle.update(gameId=game.id, gameVersion=game.version, phase=phase)
        pending, hits = [], 0
        cache = StateCache(game)
        for entry in bundle["entries"]:
            entry["source"] = os.path.relpath(entry["source"], output).replace(os.sep, "/")
            key = definitions[entry["id"]]
            target = targets[key]
            entry["target"] = key
            entry["fields"] = target["fields"]
            if game.version and target.get("cacheReading"):
                entry["cacheKey"] = cache_key(game, bundle, entry, target)
                reading = cache.access(entry["cacheKey"])
                if reading is not None:
                    entry["reading"] = {**reading, "id": entry["id"], "method": "exact-crop-cache",
                                        "evidenceSha256": entry["sourceSha256"]}
                    hits += 1
            if entry["reading"] is None:
                pending.append({"id": entry["id"], **dict.fromkeys(target["fields"]), "uncertain": ["not read"]})
        bundle["metrics"]["cacheHits"] = hits
        bundle["recognition"] = recognition(bundle)
        observe.save(working / "bundle.json", bundle)
        observe.save(working / "readings-template.json", {"entries": pending})
        from game_report import observation_page
        observation_page(game, bundle, working / "index.html", output)
        working.rename(output)
    return bundle


def recognition(bundle):
    count = sum(e["reading"] is not None for e in bundle["entries"])
    if count == len(bundle["entries"]):
        return "assistant-visual-complete"
    return "assistant-visual-partial" if count else "pending-assistant-visual"


def annotate(game, path, answers):
    from game_report import observation_page
    import json
    from rsi import data_lock, write_atomic
    with data_lock(path):
        bundle = load_json(path)
        if bundle.get("gameId") != game.id:
            raise ValueError("截图批次与所选游戏不符")
        by_id = {e["id"]: e for e in bundle["entries"]}
        for answer in load_json(answers)["entries"]:
            entry = by_id[answer["id"]]
            if not all(f in answer for f in entry["fields"]):
                raise ValueError(f"{entry['id']} 缺少配置要求的识别字段")
        def save_bundle(destination, data):
            write_atomic(destination, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

        bundle = observe.annotate(path, answers, save_bundle=save_bundle)
        pending = [{"id": e["id"], **dict.fromkeys(e["fields"]), "uncertain": ["not read"]}
                   for e in bundle["entries"] if e["reading"] is None]
        save_bundle(path.with_name("readings-template.json"), {"entries": pending})
        cache = StateCache(game)
        for entry in bundle["entries"]:
            reading = entry["reading"]
            if entry.get("cacheKey") and reading and reading.get("method") == "assistant-visual" and not reading["uncertain"]:
                cache.access(entry["cacheKey"], {k: reading[k] for k in [*entry["fields"], "uncertain", "readAt"]})
        observation_page(game, bundle, path.with_name("index.html"), path.parent)
        return bundle
