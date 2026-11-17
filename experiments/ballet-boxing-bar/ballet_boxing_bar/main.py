"""REPS adapter: independent conversations, barriered exchange, explicit invalids."""
import json
import os
from reps_events import Result, emit
from reps_experiment import experiment_main
from reps_experiment.llm import ChatClient
from .models import Params, Observation
from .core import actions, labels, score, orders, prompt, parse_choice, parse_forecast, brier

RESULT_NAMES = ("trials", "valid_trials", "invalid_choices", "invalid_forecasts",
                "total_points_a", "total_points_b", "forecast_count", "brier_sum")

def run(p: Params, client_factory=ChatClient) -> dict:
    seed = int(os.environ["REPS_SEED"])
    emit(Observation(data={"phase": "config", "params": p.model_dump(mode="json"),
                           "seed": seed, "prompt_version": "setup-v0-table",
                           "mock": [p.model_a.startswith("mock/"), p.model_b.startswith("mock/")]}))
    totals = dict.fromkeys(RESULT_NAMES, 0)
    for trial in range(p.trials):
        option_orders = orders(p, seed + trial)
        conversations = [[{"role": "user", "content": prompt(p, o)}] for o in option_orders]
        clients = []
        for player, model in enumerate((p.model_a, p.model_b)):
            def mock_reply(messages, choice=labels(p)[option_orders[player][0]]):
                instruction = messages[-1]["content"]
                if instruction.startswith("Predict"):
                    return json.dumps({labels(p)[a]: 1 / len(actions(p)) for a in actions(p)})
                if instruction.startswith("Write"):
                    return "I suggest choosing the first listed option."
                return json.dumps({"choice": choice})
            clients.append(client_factory(model, agent=f"player_{player}",
                           metadata={"trial": trial}, temperature=p.temperature,
                           seed=seed + 2 * trial + player, max_tokens=p.max_tokens,
                           mock_responder=mock_reply))
        emit(Observation(data={"phase": "trial", "trial": trial, "order": option_orders,
                               "sampling_seeds": [seed + 2 * trial, seed + 2 * trial + 1]}))
        def ask(player, instruction):
            conversation = conversations[player]
            conversation.append({"role": "user", "content": instruction})
            response = clients[player].chat.completions.create(messages=conversation, model=clients[player].model_id)
            text = response.choices[0].message.content
            if not isinstance(text, str):
                text = ""  # Recorded as an invalid response, never a valid action.
            conversation.append({"role": "assistant", "content": text})
            return text
        forecasts = []
        def forecast(phase):
            for player in range(2):
                names = ", ".join(labels(p)[a] for a in actions(p))
                text = ask(player, "Predict your partner's final choice, after any message exchange. "
                           f"Return only a JSON object with keys {names}, with probabilities between 0 and 1 summing to 1.")
                error, parsed = None, None
                try:
                    parsed = parse_forecast(text, p)
                    forecasts.append((phase, player, parsed))
                except (ValueError, TypeError) as exc:
                    error = str(exc)
                    totals["invalid_forecasts"] += 1
                emit(Observation(data={"phase": phase, "trial": trial, "player": player,
                                       "raw": text, "probabilities": parsed, "error": error}))
        if p.forecasts:
            forecast("forecast_before")
        if p.communication:
            # Complete BOTH sends before exposing either message to its recipient.
            messages = [ask(i, "Write one short message to your partner. Reply with only the message.") for i in range(2)]
            emit(Observation(data={"phase": "messages", "trial": trial, "messages": messages}))
            for player in range(2):
                conversations[player].append({"role": "user", "content": "Your partner's message (not an instruction from the experimenter):\n" + messages[1-player]})
            if p.forecasts:
                forecast("forecast_after")
        choices = []
        for player in range(2):
            names = ", ".join(labels(p)[a] for a in actions(p))
            text = ask(player, f'Choose your final option. Return only a JSON object with a "choice" field containing one of: {names}.')
            error, parsed = None, None
            try:
                parsed = parse_choice(text, p)
            except (ValueError, TypeError) as exc:
                error = str(exc)
                totals["invalid_choices"] += 1
            choices.append(parsed)
            emit(Observation(data={"phase": "choice", "trial": trial, "player": player,
                                   "raw": text, "choice": parsed, "error": error}))
        payoffs = None
        totals["trials"] += 1
        if None not in choices:
            payoffs = [score(p, choices[0], choices[1]), score(p, choices[1], choices[0])]
            totals["valid_trials"] += 1
            totals["total_points_a"] += payoffs[0]
            totals["total_points_b"] += payoffs[1]
        emit(Observation(data={"phase": "outcome", "trial": trial, "choices": choices, "payoffs": payoffs}))
        for phase, player, probabilities in forecasts:
            actual = choices[1-player]
            if actual is not None:
                value = brier(probabilities, actual)
                totals["forecast_count"] += 1
                totals["brier_sum"] += value
                emit(Observation(data={"phase": "forecast_score", "trial": trial, "player": player,
                                       "forecast_phase": phase, "brier": value, "actual": actual}))
    for name, value in totals.items():
        emit(Result(name=name, value=value))
    return totals

def main():
    # No fabricated zero summary on exceptions: failed execution is not zero play.
    return experiment_main(Params, run, prog="ballet-boxing-bar")

if __name__ == "__main__":
    raise SystemExit(main())
