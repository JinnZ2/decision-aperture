#!/usr/bin/env python3
# aperture_scan.py -- CC0, stdlib only, no network, phone-buildable.
#
# Locate decision surfaces in an underspecified coding request.
#
# A DECISION SURFACE is a span of request text that names a place where
# an implementation-bearing choice exists but is not made: "store",
# "cache", "secure", "handle errors", "scale". A coding agent receiving
# the request will not stop at these words -- it will resolve each one
# silently, with a default. This module finds them. It does not resolve
# them, rank them into a plan, or propose answers.
#
# LOCATE ONLY. This module proposes nothing. There is no answer field,
# no suggestion, no recommended default, no verdict on the request.
# That is enforced structurally rather than promised: test_aperture.py
# walks this module's AST and fails if an identifier from the
# resolution vocabulary (default / suggest / recommend / should_use /
# pick / choose / best) appears anywhere in it, and plants one to show
# the scan is not silent.
#
# THE LIMIT, STATED HERE RATHER THAN AT THE BOTTOM
#     This is a WORD LIST over decision-surface signatures. A request
#     phrased outside every signature maps to zero surfaces, and that
#     zero is a property of THE REGISTRY, never evidence that the
#     request was fully specified. "persist it" fires; "keep it around
#     across runs" carries the same surface and does not. Paraphrase
#     steps around the list; the suite shows one doing so. The
#     registry's coverage is the measurement; the request is the sample.
#
# A SECOND LIMIT
#     Consequence classes are assigned by signature, not by analysis of
#     the codebase the request will land in. "add logging" is reversible
#     in a script and near-terminal in a library others import. This
#     module cannot see which. The class is a PRIOR and is emitted as
#     such; the ledger carries it as a prior so it is never mistaken
#     for a measured one.
#
# usage:  python3 aperture_scan.py "add caching to the app"
#         python3 aperture_scan.py --file REQUEST.md
#         python3 aperture_scan.py --selftest

import json
import re
import sys

SCHEMA = "da-scan/1"

# consequence classes, ranked for routing
TERMINAL = "TERMINAL"        # hard or impossible to reverse later
REVERSIBLE = "REVERSIBLE"    # changeable with bounded effort
COSMETIC = "COSMETIC"        # no downstream constraint

CLASS_RANK = {TERMINAL: 0, REVERSIBLE: 1, COSMETIC: 2}

# ---------------------------------------------------------------------
# The registry. Each surface: word-boundary patterns that fire it, the
# sub-distinctions it decomposes into, a consequence prior, and the
# question the surface supports. The question is a hypothesis about
# what discriminates -- discriminate.py exists because some of these
# will turn out not to.
# ---------------------------------------------------------------------

REGISTRY = {
    "persistence": {
        "patterns": [
            r"\b(store|persist|saved?|database|db|warehouse)\b",
        ],
        "decomposes_into": [
            "storage engine / format",
            "durability requirement (what may be lost)",
            "schema ownership (who may change the shape)",
            "retention (what gets deleted, when)",
        ],
        "consequence_prior": TERMINAL,
        "question": "What must still be true about this data after the "
                    "process that wrote it is gone -- read by whom, "
                    "changed by whom, kept for how long?",
    },
    "caching": {
        "patterns": [
            r"\bcach(e|ing|ed)\b",
            r"\bmemoiz",
        ],
        "decomposes_into": [
            "invalidation rule (when is a hit wrong)",
            "scope (per-process, shared, distributed)",
            "failure mode on miss/stale (recompute or serve)",
        ],
        "consequence_prior": REVERSIBLE,
        "question": "When the cached value is wrong, what breaks -- and "
                    "is serving a stale value ever worse than "
                    "recomputing?",
    },
    "error_handling": {
        "patterns": [
            r"\bhandle (errors?|failures?|exceptions?)\b",
            r"\berror handling\b",
            r"\brobust\b",
            r"\bfail[- ]?safe\b",
        ],
        "decomposes_into": [
            "which failures are expected vs exceptional",
            "who sees the failure (caller, operator, user)",
            "recovery vs abort per failure class",
        ],
        "consequence_prior": TERMINAL,
        "question": "Name one specific failure this must survive and one "
                    "it must not hide -- what does each look like from "
                    "the caller's side?",
    },
    "security": {
        "patterns": [
            r"\bsecur(e|ity)\b",
            r"\bauth(entication|orization|enticate)?\b",
            r"\bencrypt",
            r"\bpermissions?\b",
        ],
        "decomposes_into": [
            "threat model (who is the adversary)",
            "identity boundary (who may do what)",
            "secret handling (where keys live)",
        ],
        "consequence_prior": TERMINAL,
        "question": "Whose action must this prevent -- an outside "
                    "attacker, another user, or the operator -- and what "
                    "is the worst single thing that party could do?",
    },
    "scale": {
        "patterns": [
            r"\bscal(e|able|ing)\b",
            r"\bperformance\b",
            r"\bfast\b",
            r"\boptimi[sz]e\b",
        ],
        "decomposes_into": [
            "which quantity grows (users, data, requests)",
            "the current binding constraint",
            "acceptable cost of the growth path",
        ],
        "consequence_prior": REVERSIBLE,
        "question": "Which number is expected to grow by 100x -- and "
                    "what is the measured (not assumed) constraint "
                    "today?",
    },
    "api_shape": {
        "patterns": [
            r"\bapi\b",
            r"\binterface\b",
            r"\bendpoint",
            r"\bexpose\b",
        ],
        "decomposes_into": [
            "who the callers are (internal, public, machine)",
            "versioning / change policy",
            "what is promised vs incidental",
        ],
        "consequence_prior": TERMINAL,
        "question": "Once a caller depends on this, what are you "
                    "promising never to change without notice -- names, "
                    "shapes, or behaviors?",
    },
    "dependency": {
        "patterns": [
            r"\buse (a |an |the )?(library|package|framework|tool)\b",
            r"\bintegrat(e|ion)\b",
            r"\bplugin\b",
        ],
        "decomposes_into": [
            "what the dependency must do vs what it happens to do",
            "upgrade / abandonment policy",
            "what breaks if it is removed",
        ],
        "consequence_prior": REVERSIBLE,
        "question": "If this dependency disappeared tomorrow, which of "
                    "your requirements would no longer be met -- and "
                    "which were only conveniences?",
    },
    "concurrency": {
        "patterns": [
            r"\bconcurren",
            r"\bparallel",
            r"\basync\b",
            r"\bmulti[- ]?thread",
        ],
        "decomposes_into": [
            "what is shared between workers",
            "ordering guarantees required",
            "failure isolation between workers",
        ],
        "consequence_prior": TERMINAL,
        "question": "What is the one invariant that must hold no matter "
                    "how the work is interleaved?",
    },
    "config_vs_code": {
        "patterns": [
            r"\bconfigur",
            r"\bsettings?\b",
            r"\bcustomiz",
        ],
        "decomposes_into": [
            "who changes it (developer, operator, end user)",
            "what must be possible without a redeploy",
            "validation of bad configuration",
        ],
        "consequence_prior": REVERSIBLE,
        "question": "Who changes this value in production, and what "
                    "happens when they set it wrong?",
    },
}

UNMAPPED = "UNMAPPED"


def scan(text):
    """Locate decision surfaces. Returns the scan dict.

    A surface hit carries: surface id, matched span, char offsets,
    consequence prior, decomposition, and the question hypothesis.
    Zero hits is UNMAPPED -- a property of the registry, stated as
    such in the output, never padded."""
    hits = []
    lowered = text.lower()
    for surface_id, entry in REGISTRY.items():
        for pat in entry["patterns"]:
            m = re.search(pat, lowered)
            if m:
                hits.append({
                    "surface": surface_id,
                    "matched": text[m.start():m.end()],
                    "span": [m.start(), m.end()],
                    "consequence_prior": entry["consequence_prior"],
                    "decomposes_into": list(entry["decomposes_into"]),
                    "question_hypothesis": entry["question"],
                })
                break  # one hit per surface, first pattern that fires
    hits.sort(key=lambda h: CLASS_RANK[h["consequence_prior"]])
    return {
        "schema": SCHEMA,
        "request": text,
        "surfaces": hits,
        "status": "MAPPED" if hits else UNMAPPED,
        "registry_note": (
            "zero surfaces is a property of THE REGISTRY, never "
            "evidence the request was fully specified"
        ) if not hits else None,
    }


def render(scan_result):
    out = []
    if scan_result["status"] == UNMAPPED:
        # the absence, first line -- before anything else
        out.append(UNMAPPED + " -- no decision surfaces detected. "
                   "This is a property of the registry's coverage, "
                   "not evidence the request is fully specified.")
        return "\n".join(out)
    out.append("MAPPED -- %d decision surface(s), consequence-routed:"
               % len(scan_result["surfaces"]))
    for h in scan_result["surfaces"]:
        out.append("  [%s] %s  (matched: %r)"
                   % (h["consequence_prior"], h["surface"], h["matched"]))
        for d in h["decomposes_into"]:
            out.append("      - %s" % d)
        out.append("      ? %s" % h["question_hypothesis"])
    return "\n".join(out)


def main(argv):
    if "--selftest" in argv:
        s = scan("please add caching and handle errors")
        assert s["status"] == "MAPPED"
        kinds = {h["surface"] for h in s["surfaces"]}
        assert kinds == {"caching", "error_handling"}, kinds
        # terminal routes before reversible
        prios = [h["consequence_prior"] for h in s["surfaces"]]
        assert prios == sorted(prios, key=lambda p: CLASS_RANK[p])
        s2 = scan("how do i bake bread")
        assert s2["status"] == UNMAPPED
        print("selftest ok: mapped %s; unmapped request returns UNMAPPED"
              % sorted(kinds))
        return 0
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--file":
        with open(args[1], encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    else:
        text = " ".join(args)
    result = scan(text)
    if "--json" in argv:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0 if result["status"] == "MAPPED" else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
