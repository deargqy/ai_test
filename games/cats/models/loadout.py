"""Adapt the existing equipment search to the shared JSON model interface."""
from equipment import render, search


def predict(state, beam=8, limit=48):
    if beam < 1 or limit < 1:
        raise ValueError("beam 和 limit 必须为正数")
    return {"policies": [search(state, beam, limit, policy) for policy in ("solid", "endpoints")]}


def render_prediction(state, result, path):
    render(state, result["policies"], path)
