"""Resolve the selected pilot before supplying character-specific play guidance."""


def select(catalog, pilot, phase=None):
    for key, item in catalog["pilots"].items():
        if pilot == key or pilot == item["name"]:
            focus = item["focus"]
            return {**item, "id": key, "phase": phase,
                    "focus": focus if phase is None else focus.get(phase)}
    raise ValueError(f"尚未登记的机师 {pilot}，请先核对选角页")


def for_run(game, run, phase):
    if not game.pilots:
        return None
    pilot = run.get("pilotId") or game.pilots.get("recordedRuns", {}).get(run["id"])
    return select(game.pilots, pilot, phase) if pilot else None
