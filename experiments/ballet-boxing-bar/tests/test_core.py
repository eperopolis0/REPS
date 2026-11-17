import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pydantic import TypeAdapter, ValidationError
from ballet_boxing_bar.models import Params, Payload
from ballet_boxing_bar.core import score, parse_choice, parse_forecast, prompt, orders
from ballet_boxing_bar.main import run

BASE = json.loads((Path(__file__).parent / "smoke.json").read_text())

def params(**updates):
    return Params.model_validate(BASE | updates)

class CoreTests(unittest.TestCase):
    def test_all_nine_coordination_cells(self):
        p = params()
        expected = [[10, 0, 0], [0, 10, 0], [5, 5, 5]]
        self.assertEqual([[score(p, a, b) for b in ("A", "B", "Bar")] for a in ("A", "B", "Bar")], expected)

    def test_all_nine_anti_cells(self):
        p = params(game="anti_coordination")
        self.assertEqual([[score(p, a, b) for b in ("A", "B", "Bar")] for a in ("A", "B", "Bar")], [[0,10,0],[10,0,0],[5,5,5]])

    def test_stag_and_no_bar(self):
        p = params(game="stag_hunt", reward_a=20, reward_b=10, include_bar=False)
        self.assertEqual([[score(p, a, b) for b in ("A", "B")] for a in ("A", "B")], [[20,0],[10,10]])
        with self.assertRaises(ValueError): score(p, "Bar", "A")

    def test_reject_false_partner_claim(self):
        for update in ({"model_b":"mock/other"}, {"order":"independent_random"}):
            with self.assertRaises(ValidationError): params(**update)

    def test_reject_bad_params(self):
        for update in ({"trials":0}, {"trials":True}, {"reward_a":-1}, {"wording":4}, {"max_tokens":0}, {"extra":1}):
            with self.assertRaises(ValidationError): params(**update)

    def test_invalid_choice_never_defaulted(self):
        for text in ('', 'Ballet', '{"choice":"C"}', '{"choice":null}', '{"choice":"Ballet", "extra":1}'):
            with self.assertRaises((ValueError,TypeError)): parse_choice(text, params())
        self.assertEqual(parse_choice('{"choice":"Boxing"}', params()), 'B')

    def test_forecast_requires_complete_finite_distribution(self):
        for text in ('{"Ballet":1}', '{"Ballet":0.5,"Boxing":0.5,"Bar":0.5}', '{"Ballet":NaN,"Boxing":0,"Bar":0}', '{"Ballet":true,"Boxing":0,"Bar":0}'):
            with self.assertRaises(ValueError): parse_forecast(text, params())
        self.assertEqual(parse_forecast('{"Ballet":0.2,"Boxing":0.3,"Bar":0.5}',params()), {"A":0.2,"B":0.3,"Bar":0.5})

    def test_seed_reproducibility_and_shared_prompt(self):
        p = params()
        self.assertEqual(orders(p,42),orders(p,42))
        self.assertEqual(prompt(p,orders(p,42)[0]),prompt(p,orders(p,42)[1]))
        self.assertNotEqual(prompt(params(wording=1),['A','B','Bar']), prompt(params(wording=2),['A','B','Bar']))

class OrchestrationTests(unittest.TestCase):
    def execute(self, p, invalid_player=None):
        records, calls = [], []
        def factory(model, agent, **kwargs):
            def create(**request):
                messages=copy.deepcopy(request['messages'])
                calls.append((agent,messages))
                instruction=messages[-1]['content']
                if instruction.startswith('Predict'):
                    answer='{"Ballet":0.5,"Boxing":0.5,"Bar":0}'
                elif instruction.startswith('Write'):
                    answer='private-message-'+agent
                else:
                    answer='invalid' if agent==invalid_player else '{"choice":"Ballet"}'
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=answer))])
            return SimpleNamespace(model_id=model,chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        # These are unit checks of orchestration and typed payloads, NOT a
        # substitute for the separate event_capture and built-launcher tests.
        with patch.dict(os.environ,{'REPS_SEED':'37'}), patch('ballet_boxing_bar.main.emit',side_effect=records.append):
            result=run(p,client_factory=factory)
        adapter=TypeAdapter(Payload)
        for event in records:
            adapter.validate_json(event.model_dump_json(),strict=True)
        return result,records,calls

    def test_all_clients_use_run_seed_and_report_actual_seeds(self):
        captured, records = [], []
        def factory(model, **kwargs):
            captured.append(kwargs)
            def create(**request):
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"choice":"Ballet"}'))])
            return SimpleNamespace(model_id=model, chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with patch.dict(os.environ, {'REPS_SEED':'37'}), patch('ballet_boxing_bar.main.emit', side_effect=records.append):
            run(params(trials=3, communication=False, forecasts=False), client_factory=factory)
        # REPS verify.py requires call.request.seed == run.start.seed, including
        # the second player and subsequent trials (the original smoke failure).
        self.assertEqual([c['seed'] for c in captured], [37] * 6)
        trials = [e.data for e in records if getattr(e, 'kind', None) and e.data['phase']=='trial']
        self.assertEqual([t['sampling_seeds'] for t in trials], [[37,37]] * 3)
        self.assertEqual([t['order_seed'] for t in trials], [37,38,39])

    def test_messages_barrier_and_no_choice_leak(self):
        result, records, calls = self.execute(params(trials=1))
        sends=[(a,m) for a,m in calls if m[-1]['content'].startswith('Write')]
        self.assertEqual(len(sends),2)
        for _,messages in sends:
            self.assertNotIn('private-message-',json.dumps(messages))
        final=[(a,m) for a,m in calls if m[-1]['content'].startswith('Choose')]
        for agent,messages in final:
            self.assertIn('private-message-player_'+('1' if agent=='player_0' else '0'),json.dumps(messages))
            self.assertNotIn('{"choice":', '\n'.join(m['content'] for m in messages[:-1]))
        self.assertEqual(result['valid_trials'],1)
        self.assertEqual(result['forecast_count'],4)
        self.assertEqual(result['brier_sum'],2)

    def test_fresh_conversations_per_pair(self):
        _,_,calls=self.execute(params(trials=2))
        starts=[m for _,m in calls if m[-1]['content'].startswith('Predict') and len(m)==2]
        self.assertEqual(len(starts),4)

    def test_invalid_pair_not_scored_as_zero(self):
        result,records,_=self.execute(params(trials=1),invalid_player='player_1')
        self.assertEqual(result['valid_trials'],0)
        self.assertEqual(result['invalid_choices'],1)
        outcomes=[e.data for e in records if getattr(e,'kind',None) and e.data['phase']=='outcome']
        self.assertIsNone(outcomes[0]['payoffs'])

    def test_no_communication_no_forecasts(self):
        result,_,calls=self.execute(params(trials=1,communication=False,forecasts=False))
        self.assertEqual(len(calls),2)
        self.assertEqual(result['forecast_count'],0)

if __name__=='__main__': unittest.main()
