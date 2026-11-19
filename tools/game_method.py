"""Join a game's reusable decision method to its versioned RSI rules and evidence."""


def describe(game, data, key):
    if data.get("game") != game.name:
        raise ValueError("经验记录与当前游戏不符")
    if key not in game.methods:
        raise ValueError(f"当前游戏未登记判断方法 {key}")
    method = game.methods[key]
    rules = {m["id"]: m for m in data["memories"]}
    missing = set(method["memories"]) - rules.keys()
    if missing:
        raise ValueError(f"{key} 引用了不存在的经验 {', '.join(sorted(missing))}")
    return {**method, "rules": [rules[mid] for mid in method["memories"]]}


def recorded_decisions(data, method):
    """Only historical decisions that applied a related rule in the specified phase."""
    relevant = set(method["memories"])
    for run in data["runs"]:
        matches = []
        for day in run["days"]:
            for decision in day.get("decisions", []):
                if decision["phase"] not in method["phases"]:
                    continue
                uses = [use for use in decision["before"].get("memories", [])
                        if use["id"] in relevant and use["use"] == "applied"]
                if uses:
                    matches.append((day["day"], decision, uses))
        if matches:
            yield run, matches
