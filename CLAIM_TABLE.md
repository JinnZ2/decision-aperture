# CLAIM TABLE -- decision-aperture

Ids are permanent. `DA_` = decision-aperture. Status is one of
SUPPORTED / REFUTED / UNVERIFIED. Every SUPPORTED claim is a property
of the three modules or of their measured output, and is recomputable
by anyone with the folder: `python3 test_aperture.py` (38 checks).

---

## aperture_scan.py

**DA_001 -- LOCATE ONLY is enforced, not promised. SUPPORTED.**
The module carries no identifier from the resolution vocabulary
(`suggest / recommend / pick / choose / best / preferred / default /
should_use / instead`). The AST guard is planted-against: a module
containing `def recommend_default` fires it (`ast.guard_not_silent`).
*Falsifier:* an identifier from that vocabulary appearing in the
module, or a returned field carrying a proposed answer.

**DA_002 -- consequence routing orders surfaces TERMINAL before
REVERSIBLE before COSMETIC. SUPPORTED.** A five-surface request
returns persistence / error_handling / security ahead of caching /
scale (`scan.consequence_routed`). *Falsifier:* an output violating
the class ordering.

**DA_003 -- one hit per surface, first firing pattern. SUPPORTED.**
A request matching several patterns of one surface yields one entry
(`scan.one_hit_per_surface`). *Falsifier:* a duplicate surface id in
one scan.

**DA_004 -- UNMAPPED is a first-class return, first line, exit
nonzero. SUPPORTED.** "how do i bake bread" yields status UNMAPPED,
empty surfaces, the rendered output leading with the UNMAPPED line,
and process exit 3 (`scan.unmapped_status`,
`scan.unmapped_first_line`, `scan.unmapped_exit_nonzero`). The absence
is printed before anything else.

**DA_005 -- THE LIMIT: a word list, and a paraphrase steps around it.
SUPPORTED, and measured rather than asserted.** "store it in a
database" fires persistence; "keep it around across runs" carries the
same surface and returns UNMAPPED (`scan.paraphrase_limit_measured`).
A zero from this module is a property of THE REGISTRY, never evidence
a request was fully specified. During the build, the registry's first
`keep it` pattern was found to be too broad precisely because this
test caught it firing on the paraphrase case -- the measurement
working as designed, recorded here rather than smoothed.

## decision_ledger.py

**DA_006 -- there is exactly one door into RESOLVED and it requires
answer + provenance. SUPPORTED.** Four forbidden paths -- no answer,
no provenance, blank answer, unknown provenance party -- all raise
`LedgerError` (`ledger.no_silent_resolve_answer`,
`ledger.no_silent_resolve_provenance`, `ledger.no_blank_answer`,
`ledger.provenance_closed_set`). The CLI refuses the same and exits 4
with REFUSED (`e2e.cli_refuses_silent_resolve`). *Falsifier:* any
code path reaching RESOLVED without both fields.

**DA_007 -- the ledger schema carries no default field. SUPPORTED.**
No `default` key exists anywhere in the ledger construction
(`ast.ledger_no_default_field`). Substituting a default for something
unknown is not a discouraged practice here; it is a structural
impossibility.

**DA_008 -- RESOLVED is terminal; a recorded decision is never
rewritten. SUPPORTED.** RESOLVED has an empty transition set; the
attempt to move back to UNRESOLVED raises
(`ledger.resolved_never_rewritten`). Supersession happens by new
decision id, so history is never falsified in place.

**DA_009 -- DEFERRED is an owned decision and requires an author.
SUPPORTED.** A deferral without `--by` raises; a deferral with one is
recorded with provenance and reason (`ledger.defer_needs_author`,
`ledger.defer_is_owned`). A decision deliberately postponed with the
postponement on record is not a silent default.

**DA_010 -- the report prints unresolved decisions FIRST. SUPPORTED.**
The first line of every non-UNMAPPED report is the unresolved count,
and unresolved entries precede owned ones
(`ledger.report_unresolved_headline`). The absence of a decision is
the headline, not the footnote.

**DA_011 -- the fatigue budget suppresses visibly, never drops.
SUPPORTED.** An eight-surface request at budget 3 exposes exactly
three as UNRESOLVED and marks the remaining five
`suppressed_by_budget`, and the report names them
(`ledger.budget_caps_exposed`, `ledger.budget_suppression_visible`,
`ledger.suppressed_shown_in_report`). The user can always see what
the budget hid.

## discriminate.py

**DA_012 -- the two-profile test distinguishes a discriminating
question from a non-discriminating one. SUPPORTED, with shipped
measurements.** The caching-scope question, run under two answer
profiles (in-memory dict vs sqlite), measures divergence **0.7419**
and returns DISCRIMINATES. A wording-level question (log line text),
run the same way, measures **0.0** and returns DOES_NOT_DISCRIMINATE
(fixtures/cache_profile_*.py vs fixtures/color_profile_*.py;
`disc.profiles_diverge`, `disc.cosmetic_twins_do_not`).

**DA_013 -- cosmetic differences do not count as divergence.
SUPPORTED.** Comments, docstrings and whitespace are removed by AST
normalization; cosmetic twins measure below threshold
(`disc.cosmetic_twins_do_not`, threshold 0.20, stated in the module
header, tunable, never hidden).

**DA_014 -- a changed constant IS divergence. SUPPORTED.** Constants
are folded into the structural multiset with their values, so
`CACHE.get(k)` vs `CACHE.get(k, 42)` diverges
(`disc.constant_is_divergence`) -- behavioral difference that AST
shape alone would miss is partially recovered, and the recovery is
stated as partial.

**DA_015 -- UNMEASURABLE is a return type, not an error. SUPPORTED.**
An unparseable artifact yields result UNMEASURABLE with divergence
None and a stated reason, not an exception
(`disc.unparseable_is_return_not_crash`). *Falsifier:* a traceback
from the measure path on any input pair.

**DA_016 -- THE PROXY LIMIT, stated: structural divergence is not
behavioral divergence. SUPPORTED (the limit exists and is carried),
UNVERIFIED (how often it bites).** Two implementations can diverge in
structure and not behavior, or agree in structure and diverge in
behavior beyond what constants capture. Every verdict carries the
note naming this false-negative class. No measurement of the proxy's
error rate against a behavioral oracle has been made; it is claimed
nowhere.

## cross-cutting

**DA_017 -- a question is a hypothesis until measured, and the ledger
marks failed questions registry_suspect. SUPPORTED.** Every scan
emits `question_hypothesis`; every new ledger entry starts with
`discrimination.tested = False`; recording a DOES_NOT_DISCRIMINATE
result appends a registry_suspect history event and the report
surfaces it (`ledger.registry_suspect_recorded`,
`ledger.report_shows_suspect`). The instrument's reward -- generating
intelligent-sounding questions -- is attacked by the instrument
itself, in the open.

**DA_018 -- every decision and observation is scoped to an assessment
frame. SUPPORTED.** `new_ledger` accepts a frame and stamps every
entry with a `frame_id` derived from human+AI+project
(`ledger.frame_scoped`); the report prints the frame
(`ledger.report_shows_frame`). *Falsifier:* a ledger entry without a
frame_id when a frame was provided.

**DA_019 -- usefulness is computed transparently, not hidden.
SUPPORTED.** `compute_usefulness` returns the explicit formula
(divergence - friction_penalty, clamped) and the explanation string
contains both terms (`lab.explanation_transparent`). Changing the
friction band changes the score predictably
(`lab.friction_reduces_usefulness`).

**DA_020 -- cross-frame comparison reports deltas, not universal
rankings. SUPPORTED.** `usefulness_lab.compare` on two experiments
with different frames reports the numeric delta and explicitly states
it is "NOT evidence one question is universally better"
(`lab.compare_reports_delta`, `lab.compare_no_universal_rank`).

**DA_021 -- the frame routes instruments or returns FRAME_UNMAPPED;
it never guesses. SUPPORTED.** A frame with one instrument for
`api_shape` routes it; the same frame returns FRAME_UNMAPPED for
`persistence` with no nearest-guess offered (`frame.route_mapped`,
`frame.route_unmapped_no_guess`).

**DA_022 -- instrument availability is UNMEASURED until exercised.
SUPPORTED.** Every added instrument starts with state UNMEASURED;
`probe_instruments` marks MEASURED_OK or MEASURED_FAIL only when a
runner is provided (`frame.blank_all_unmapped` family and the
instrument state in the routing output).

**DA_023 -- predicted usefulness can be recorded and compared to
actual. SUPPORTED.** `set_predicted_usefulness` stores the prediction;
`record_discrimination` computes `usefulness_prediction_delta` when an
experiment result arrives (`ledger.predicted_vs_actual`). Absence of
prediction is UNMEASURED, not zero.

**DA_024 -- the registry_suspect marking is frame-local evidence,
not a universal verdict. SUPPORTED.** The report language states
explicitly that a question failing to discriminate "IN THEIR FRAME"
is frame-local (`ledger.suspect_is_frame_local`). *Falsifier:* a
report presenting one frame's failure as a global property of the
question.
