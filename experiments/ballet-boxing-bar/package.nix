{ reps, pkgs }:
let
  env = (reps.mkPythonEnv {
    name = "ballet-boxing-bar-env";
    workspaceRoot = ./.;
    python = pkgs.python313;
  }).overrideAttrs { meta.mainProgram = "ballet-boxing-bar"; };
in {
  ballet-boxing-bar = reps.mkExperiment {
    name = "ballet-boxing-bar";
    summary = "One-shot coordination and anti-coordination with optional outside option and message exchange.";
    program = env;
    schema = { version = 0; models = "ballet_boxing_bar.models:Payload"; };
    schemaPython = "${env}/bin/python";
    src = [ ./package.nix ./pyproject.toml ./uv.lock ./ballet_boxing_bar ];
    params = with reps.types; {
      game = param (enum [ "coordination" "anti_coordination" "stag_hunt" ]) { description = "Payoff rule; all players use the same rule from their own perspective."; initial = "coordination"; };
      model_a = param llm { description = "Player 0 model; mock/model is offline."; initial = "mock/model"; };
      model_b = param llm { description = "Player 1 model; must match player 0 for same-model framing."; initial = "mock/model"; };
      trials = param int { description = "Independent one-shot pairs, each with fresh conversations."; initial = 2; };
      wording = param int { description = "Introduction wording variant: 1, 2 or 3. Setup-v0 table wording is provisional."; initial = 1; };
      labels = param (enum [ "neutral" "ballet_boxing" ]) { description = "A/B versus Ballet/Boxing labels."; initial = "ballet_boxing"; };
      partner = param (enum [ "same_model_same_prompt" "another_ai" ]) { description = "Truthful initial partner description; separate calls, not a cloned internal model state."; initial = "same_model_same_prompt"; };
      order = param (enum [ "fixed" "shared_random" "independent_random" ]) { description = "Option ordering; independent order cannot claim identical initial prompts."; initial = "shared_random"; };
      include_bar = param bool { description = "Include the outside option."; initial = true; };
      reward_a = param int { description = "A coordination payoff, or risky stag payoff; positive integer."; initial = 10; };
      reward_b = param int { description = "B coordination payoff, or safe hare payoff; anti-coordination requires equal A/B rewards."; initial = 10; };
      bar_reward = param int { description = "Outside-option points regardless of partner action; integer framing is explicit."; initial = 5; };
      communication = param bool { description = "One barriered exchange of short messages before final choices."; initial = false; };
      forecasts = param bool { description = "Full partner-choice distribution before, and if messages enabled after, exchange."; initial = false; };
      temperature = param float { description = "Sampling temperature; null leaves backend default."; nullable = true; initial = 0.0; };
      max_tokens = param int { description = "Completion token cap per call."; initial = 256; };
    };
    results = with reps.types; [
      { name = "trials"; type = int; label = "Completed pairs"; description = "One-shot pairs reaching outcome recording, including invalid choices."; }
      { name = "valid_trials"; type = int; label = "Valid pairs"; description = "Pairs with two valid choices and computed payoffs."; }
      { name = "invalid_choices"; type = int; label = "Invalid choices"; description = "Unparseable or invalid final choices; never replaced by a default action."; }
      { name = "invalid_forecasts"; type = int; label = "Invalid forecasts"; description = "Missing, malformed or non-normalized probability distributions."; }
      { name = "total_points_a"; type = int; label = "Player 0 points"; description = "Sum over valid pairs only; invalid pairs have missing payoffs."; }
      { name = "total_points_b"; type = int; label = "Player 1 points"; description = "Sum over valid pairs only; invalid pairs have missing payoffs."; }
      { name = "forecast_count"; type = int; label = "Scored forecasts"; description = "Valid forecasts with a valid observed partner choice, pooling before and after phases."; }
      { name = "brier_sum"; type = float; label = "Brier score sum"; description = "Sum of unnormalized multiclass Brier scores; divide by forecast_count only when nonzero."; details = "Range per forecast is 0–2. Phase-specific scores are retained in events; this aggregate is not an optimism metric."; }
    ];
  };
}
