# CLAUDE.md

Guidance for working in this repository. Public; CC0; nothing here is private.

## What this repository is

A **decision-aperture layer**: it locates implementation-bearing choices
in a request *before* the code is written, refuses to make them, and
treats the usefulness of its own questions as an experimental variable
rather than a design assumption.

Sibling to `vibe-code-audit`, `method-layer` and the `Simulators` tree.
`vibe-code-audit` measures the **link surface** of code that exists.
This measures the **decision surface** of a request that does not.

```text
request text (underspecified)
      |
      v
aperture_scan.py ------------------------------ LOCATE ONLY
   REGISTRY of decision-surface signatures      proposes nothing
   one hit per surface, first firing pattern    no answer field
   ordered TERMINAL > REVERSIBLE > COSMETIC     no default
   no match -> UNMAPPED, first line, exit 3     not padded
      |
      v
decision_ledger.py ---------------------------- STATE + PROVENANCE
   7 states, a closed TRANSITIONS table         anything absent raises
   ONE door into RESOLVED: answer + by-whom     no silent resolve
   no `default` key anywhere in the schema      no substitution
   fatigue budget (default 5), TERMINAL first   overflow REPORTED as
   unresolved printed FIRST in the report       suppressed_by_budget,
   RESOLVED -> {} : never rewritten, supersede  never dropped
      |
      +----> assessment_frame.py --------------- SCOPE
      |         human / ai / project / environment / constraints
      |         + instruments + knowns/unknowns/unverified
      |         route(surface) -> instruments IN THIS FRAME
      |                        or FRAME_UNMAPPED, never a nearest guess
      v
usefulness_lab.py ----------------------------- THE INSTRUMENT MEASURES ITSELF
   fix frame -> ask question -> build under profile A and profile B
      |
      v
discriminate.py
   AST (python) or token multiset -> structural divergence
   below THRESHOLD 0.20 -> DID NOT DISCRIMINATE
      |
      v
   usefulness = divergence - friction_penalty, clamped, explanation printed
   a non-discriminating question -> registry_suspect IN THAT FRAME'S LEDGER
                                    frame-local evidence, never a universal verdict
```

## Hard constraints

```text
python >= 3.9         parses under 3.9; phone-buildable
stdlib ONLY           no pip, no runtime deps
no network            nothing here fetches anything
CC0
ASCII in authored text
tests: python3 test_aperture.py    prints its own count; must stay green
```

## Operations it must not perform

Each is enforced in code, not promised in prose. Breaking one is the
only way to make this folder useless.

```text
MUST NOT silently resolve       one transition into RESOLVED, requiring
                                answer AND provenance from a closed set
                                {user, agent, operator, experiment}.
                                Four forbidden paths raise LedgerError;
                                the CLI exits 4 with REFUSED.
MUST NOT substitute a default   no `default` key in the ledger schema.
                                Unresolved surfaces print FIRST.
MUST NOT rank universally       a cross-frame comparison reports deltas
                                and frame differences, and states that a
                                delta is not evidence one question is
                                universally better.
MUST NOT propose                aperture_scan carries no identifier from
                                {suggest, recommend, pick, choose, best,
                                 preferred, default, should_use, instead}.
                                test_aperture.py walks its AST and plants
                                one to show the guard is not silent.
```

## States, and the ones that are not errors

```text
DETECTED        surface located; nothing more known
UNRESOLVED      exposed and decomposed; no answer on record
RESOLVED        answer on record WITH provenance      (terminal: {})
DEFERRED        explicitly postponed -- owned, on record, scored as owned
UNMAPPED        request text matched no registry surface  (terminal: {})
UNMEASURED      question generated; discriminating power untested
NOT_APPLICABLE  surface bears no implementation consequence here
```

`UNMAPPED` and `UNMEASURED` are **states, not failures**. A frame field
that was never provided is `UNMAPPED`; one declared but never probed is
`UNMEASURED`. Collapsing either into a zero, a default, or an error
loses the whole reading.

## Exit codes

```text
0  result produced              2  usage / bad invocation
3  the absence IS the result    4  a refusal (silent resolve attempted)
   (UNMAPPED / FRAME_UNMAPPED /
    UNMEASURABLE / not COMPARED)
```

3 is not an error. It is the instrument saying the thing it exists to
say. Do not smooth it to 0.

## The limits, stated here rather than at the bottom

```text
aperture_scan.py   a WORD LIST. A paraphrase steps around it, and this is
                   MEASURED, not asserted: "store it in a database" fires
                   persistence; "keep it around across runs" carries the
                   same surface and returns UNMAPPED. A zero from this
                   module is a property of THE REGISTRY, never evidence a
                   request was fully specified.
discriminate.py    STRUCTURAL divergence (AST / token multiset), not
                   behavioural. Two implementations that differ only in
                   behaviour read as identical. That false negative is
                   named in every verdict; keep it named.
assessment_frame   records DECLARED facts. Instrument availability is
                   UNMEASURED until exercised.
the registry       is not a completeness claim.
```

## Known defects (verified 2026-09-22, not repaired)

```text
decision_ledger.py has no --selftest.
    The other four modules accept it and print a one-line result. This
    one takes a LEDGER path as its first positional argument, so
    `python3 decision_ledger.py --selftest` opens a file named
    "--selftest" and dies with a traceback, exit 1. Four modules
    refuse-or-run; one crashes. A caller sweeping the folder for
    selftests reads that crash as a failing module.

CLAIM_TABLE.md states "(38 checks)"; the suite prints 54.
    A stored count against a command that produces one. The README gets
    this right ("prints their count"). Fix by deleting the number and
    naming the command, not by typing 54 -- a stored count drifts again.
```

## Conventions when editing

- A new decision surface is a `REGISTRY` entry in `aperture_scan.py`
  with a consequence class. It is a hypothesis, not a feature: it is
  `UNMEASURED` until `usefulness_lab` shows it discriminating in some
  frame, and a frame is named in that result.
- A question that fails to discriminate is recorded `registry_suspect`
  **in that frame's ledger** and stays in the registry. Deleting it
  would throw away the measurement.
- Every claim in `CLAIM_TABLE.md` carries a falsifier and its id is
  permanent (`DA_001..DA_024`). A refuted claim keeps its id and gains a
  status; it is never renumbered and never removed.
- `samples/` holds pinned outputs. If a change moves one, regenerate it
  in the same commit and say what moved.
- Guards are AST walks with planted faults, not substring scans. A
  substring scan fires on the sentence saying what the module refuses.

## Commands

```sh
python3 test_aperture.py                        # the checks; prints their count

python3 assessment_frame.py --new frame.json
python3 assessment_frame.py frame.json --set human solo_dev
python3 assessment_frame.py frame.json --add-instrument X scanner ./x.py api_shape
python3 assessment_frame.py frame.json --route persistence

python3 aperture_scan.py "add caching to the app"

python3 decision_ledger.py --new "request text" --frame frame.json [--budget 5]
python3 decision_ledger.py LEDGER --expose
python3 decision_ledger.py LEDGER --resolve D2 --by user --answer "redis"
python3 decision_ledger.py LEDGER --defer D3 --by user --reason "..."
python3 decision_ledger.py LEDGER --report

python3 discriminate.py --artifacts a.py b.py [--question "..."] [--json]
python3 usefulness_lab.py run --frame frame.json --question "..." \
        --surface caching --profile-a fixtures/cache_profile_a.py \
        --profile-b fixtures/cache_profile_b.py --friction low --out exp.json
python3 usefulness_lab.py compare exp1.json exp2.json

# --selftest: aperture_scan, assessment_frame, discriminate, usefulness_lab
# decision_ledger does NOT accept it (see Known defects)
```
