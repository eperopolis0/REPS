"""Run in the packaged dev environment: uses REPS's own receiver fixture."""
import json
from pathlib import Path
from pydantic import TypeAdapter
from ballet_boxing_bar.models import Params, Payload
from ballet_boxing_bar.main import run

def test_mock_emission(event_capture, monkeypatch):
    monkeypatch.setenv("REPS_SEED", "0")
    p=Params.model_validate(json.loads((Path(__file__).parent/"smoke.json").read_text()))
    result=run(p)
    events=event_capture.read()
    for event in events:
        TypeAdapter(Payload).validate_json(json.dumps(event),strict=True)
    assert result['valid_trials']==2
    assert sum(e['type']=='llm.call' for e in events)==16
    assert {e['name'] for e in events if e['type']=='result'}==set(result)
