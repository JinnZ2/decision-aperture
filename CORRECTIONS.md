# Correction records

Original readings are retained beside their corrections, not silently
replaced. These are instrument-behavior records, not measurements of human
value or universal question quality.

## Missing friction and missing usefulness: 2026-11-11

The intended contract was already present: usefulness must not silently fill
missing friction or divergence. At
[`5f8d316`](https://github.com/JinnZ2/decision-aperture/blob/5f8d316dc76f1a722b70c616fcecc76926ed8283/usefulness_lab.py),
the friction mapping nevertheless contained `None: 0.0`; a selected
divergence of 0.6 with omitted friction scored the same as explicit `low`.
The ledger separately used
`abs(pred_val - (entry["actual_usefulness"] or 0))`, converting a missing
actual usefulness into a measured-looking prediction error.

The [dated specimen](fixtures/missing_friction_2026-11-11.json) retains the
original contract, source pin, illustrative inputs, outputs and correction.
The shipped baseline passed its checks before the new regressions were
added; with those regressions and before either implementation was changed,
the suite reported 82 checks and 11 failures.

### Corrected scope

- **Missing friction:** `compute_usefulness` returns `None` and
  `UNMEASURED: friction not available`. Omission does not select `low`.
- **Retained measurement:** the experiment keeps structural divergence, its
  verdict, frame and profile paths. It records the absent friction separately,
  persists usefulness as JSON `null`, and retains the reason.
- **Explicit zero:** the declared `low` band still selects zero penalty.
  Numeric zero seconds, including the CLI string `"0"`, remains a supplied
  input rather than missing evidence.
- **Comparison:** an unmeasured usefulness does not get a numeric pairwise
  delta. Measured pairs remain comparable when another experiment is
  unmeasured, and the omitted pairs are named.
- **Ledger:** prediction error requires both prediction and actual
  usefulness. An incoming unmeasured result resets an older numeric delta;
  an explicit measured zero still has a numeric prediction error.
- **Provenance:** new experiment records identify usefulness instrument
  version `2`. The JSON schema remains `da-experiment/1`; historical
  experiments and pinned samples are not regenerated or relabeled.

### Reproduce

Run the standard suite; it prints its current count rather than relying
on a stored count. The direct probes below distinguish missing cost from
an explicitly supplied zero-penalty input.

```sh
python3 test_aperture.py
python3 -c 'import usefulness_lab as u; print(u.compute_usefulness(0.6, None))'
python3 -c 'import usefulness_lab as u; print(u.compute_usefulness(0.6, "low"))'
python3 -c 'import usefulness_lab as u; print(u.compute_usefulness(0.6, 0))'
```

### What this does not establish

This correction does not calibrate the friction bands or prove that the
usefulness formula measures human benefit. Structural divergence remains
a structural proxy, not a behavioral oracle, and a supplied band remains
a supplied input rather than an independently verified cost measurement.

It does not re-score historical experiments or retroactively infer their
missing costs. It does not fix unrelated input-validation, frame-identity,
or cross-frame causal-inference questions; the existing scope limitations
and unresolved findings remain in place.
