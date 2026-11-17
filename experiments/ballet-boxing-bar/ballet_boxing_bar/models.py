from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from reps_events import CapturedLine, CustomEvent, LLMCall, Log, ProducerPython, Result, RunEnd, RunStart, Status

class Params(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    game: Literal["coordination", "anti_coordination", "stag_hunt"]
    model_a: str
    model_b: str
    trials: Annotated[int, Field(ge=1, le=10000)]
    wording: Literal[1, 2, 3]
    labels: Literal["neutral", "ballet_boxing"]
    partner: Literal["same_model_same_prompt", "another_ai"]
    order: Literal["fixed", "shared_random", "independent_random"]
    include_bar: bool
    reward_a: Annotated[int, Field(ge=1)]
    reward_b: Annotated[int, Field(ge=1)]
    bar_reward: Annotated[int, Field(ge=0)]
    communication: bool
    forecasts: bool
    temperature: float | None
    max_tokens: Annotated[int, Field(ge=1)]

    @model_validator(mode="after")
    def coherent(self):
        if self.partner == "same_model_same_prompt":
            if self.model_a != self.model_b or self.order == "independent_random":
                raise ValueError("same-model/same-prompt requires equal model IDs and shared option order")
        if self.game == "anti_coordination" and self.reward_a != self.reward_b:
            raise ValueError("anti-coordination currently requires equal A/B rewards")
        if not self.model_a or not self.model_b:
            raise ValueError("model IDs must be nonempty")
        return self

class Observation(CustomEvent[dict[str, JsonValue]]):
    kind: Literal["ballet_boxing_bar.observation"] = "ballet_boxing_bar.observation"

type Payload = Annotated[
    RunStart | RunEnd | LLMCall | Observation | Result | Status | Log | CapturedLine | ProducerPython,
    Field(discriminator="type"),
]
