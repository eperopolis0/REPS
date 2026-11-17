"""Pure payoff, prompt and parsing functions; no network or event transport."""
import json
import math
import random
from .models import Params

def actions(p: Params) -> list[str]:
    return ["A", "B"] + (["Bar"] if p.include_bar else [])

def labels(p: Params) -> dict[str, str]:
    return {"A": "Ballet" if p.labels == "ballet_boxing" else "A",
            "B": "Boxing" if p.labels == "ballet_boxing" else "B", "Bar": "Bar"}

def score(p: Params, own: str, other: str) -> int:
    if own not in actions(p) or other not in actions(p):
        raise ValueError("cannot score an invalid action")
    if own == "Bar":
        return p.bar_reward
    if p.game == "stag_hunt":
        return p.reward_b if own == "B" else (p.reward_a if other == "A" else 0)
    success = (own == other) if p.game == "coordination" else (other in ("A", "B") and own != other)
    return (p.reward_a if own == "A" else p.reward_b) if success else 0

def orders(p: Params, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    first = actions(p)
    if p.order != "fixed":
        rng.shuffle(first)
    second = first.copy()
    if p.order == "independent_random":
        rng.shuffle(second)
    return [first, second]

def prompt(p: Params, order: list[str]) -> str:
    names = labels(p)
    intro = {
        1: "You and another AI each choose one option in a one-round game.",
        2: "Two AI players each make one choice. This game lasts one round.",
        3: "Play a one-round game with another AI by selecting one option.",
    }[p.wording]
    if p.partner == "same_model_same_prompt":
        intro += " Your partner is a separate instance of the exact same model, receiving the same initial prompt as you."
    intro += " Your final choices are hidden from each other until both have been submitted."
    intro += (" You will each write one short message, then see the other's message before choosing. Neither sees the other's message before writing their own."
              if p.communication else " You cannot communicate with your partner.")
    intro += (" You and your partner see the same option order." if p.order != "independent_random"
              else " Option order is randomized independently for you and your partner.")
    intro += "\nOptions: " + ", ".join(names[x] for x in order) + ".\n"
    # List every cell to make the Bar/mismatch scope unambiguous. Integer point
    # values are an explicit framing choice, not assumed equivalent behaviorally.
    intro += "Your points for each pair of choices (your choice / partner's choice):\n"
    for own in order:
        for other in order:
            intro += f"{names[own]} / {names[other]}: {score(p, own, other)}\n"
    intro += "Your partner uses the same scoring rule from their own perspective."
    return intro

def parse_choice(text: str, p: Params) -> str:
    obj = json.loads(text)
    if not isinstance(obj, dict) or set(obj) != {"choice"}:
        raise ValueError('expected only a JSON "choice" field')
    reverse = {labels(p)[a]: a for a in actions(p)}
    if not isinstance(obj["choice"], str) or obj["choice"] not in reverse:
        raise ValueError("invalid choice label")
    return reverse[obj["choice"]]

def parse_forecast(text: str, p: Params) -> dict[str, float]:
    obj = json.loads(text)
    expected = {labels(p)[a] for a in actions(p)}
    if not isinstance(obj, dict) or set(obj) != expected:
        raise ValueError("forecast must contain exactly one probability per available option")
    if any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1 for x in obj.values()):
        raise ValueError("probabilities must be finite numbers in [0,1]")
    if not math.isclose(sum(obj.values()), 1, abs_tol=1e-6):
        raise ValueError("probabilities must sum to 1")
    return {a: float(obj[labels(p)[a]]) for a in actions(p)}

def brier(probabilities: dict[str, float], actual: str) -> float:
    return sum((v - int(k == actual)) ** 2 for k, v in probabilities.items())
