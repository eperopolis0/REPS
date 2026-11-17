{ experiment, reps }: {
  pytest = reps.testers.pytest { inherit experiment; tests = ./.; flags = [ "-n" "0" ]; };
  smoke = reps.testers.smoke {
    inherit experiment;
    params = builtins.fromJSON (builtins.readFile ./smoke.json);
  };
  smoke-provider-random = reps.testers.smoke {
    inherit experiment;
    params = (builtins.fromJSON (builtins.readFile ./smoke.json)) // {
      sampling = "provider_random";
    };
  };
}
