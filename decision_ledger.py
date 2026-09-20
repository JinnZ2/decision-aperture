#!/usr/bin/env python3
# decision_ledger.py -- CC0, stdlib only, no network, phone-buildable.
#
# The decision ledger: the state machine over decision surfaces, with
# provenance. This module exists for two prohibitions from the work
# order, and they are enforced in its transitions, not promised in
# prose:
#
#   MUST NOT silently resolve a decision.
#       There is exactly one transition into RESOLVED, and it requires
#       an answer string AND a provenance field naming who answered
#       (user / agent / operator). No code path sets RESOLVED without
#       both. The suite attempts the forbidden paths and shows them
#       raising.
#
#   MUST NOT substitute a default for something unknown.
#       A surface with no answer stays UNRESOLVED. The report prints
#       unresolved surfaces FIRST, before resolved ones, because the
#       absence of a decision is the headline, not the footnote. There
#       is no default field anywhere in the ledger schema.
#
# THE FATIGUE BUDGET
#     A gate that gets routinely overridden has become bulk. The ask
#     step is budgeted: surfaces are emitted in consequence order
#     (TERMINAL first) up to --budget N (default 5). Surfaces past the
#     budget are not dropped; they are reported as suppressed_by_budget
#     so the user can see what the budget hid.
#
# STATES: DETECTED, UNRESOLVED, RESOLVED, DEFERRED, UNMAPPED,
#         UNMEASURED, NOT_APPLICABLE
#     DEFERRED is a first-class owned decision: deliberately postponed,
#     with the deferral and its author on record. UNMEASURED marks a
#     question whose discriminating power was never tested; a
#     discrimination result moves it to registry_suspect or clears it.
#
# usage:  python3 decision_ledger.py --new "request text" [--budget 5]
#         python3 decision_ledger.py LEDGER --expose
#         python3 decision_ledger.py LEDGER --resolve D2 --by user \
#                                          --answer "..."
#         python3 decision_ledger.py LEDGER --defer D3 --by user \
#                                          --reason "..."
#         python3 decision_ledger.py LEDGER --mark D1 --state UNMEASURED
#         python3 decision_ledger.py LEDGER --report

import json
import os
import sys
import time

SCHEMA = "da-ledger/2"

STATES = frozenset([
    "DETECTED", "UNRESOLVED", "RESOLVED", "DEFERRED",
    "UNMAPPED", "UNMEASURED", "NOT_APPLICABLE",
])

PROVENANCE = frozenset(["user", "agent", "operator", "experiment"])

# legal transitions. Anything absent from this table raises.
TRANSITIONS = {
    "DETECTED": {"UNRESOLVED", "NOT_APPLICABLE"},
    "UNRESOLVED": {"RESOLVED", "DEFERRED", "NOT_APPLICABLE", "UNMEASURED"},
    "UNMEASURED": {"RESOLVED", "DEFERRED", "NOT_APPLICABLE",
                   "UNRESOLVED"},
    "DEFERRED": {"RESOLVED", "UNRESOLVED"},
    "RESOLVED": set(),          # a recorded decision is never rewritten;
                                # supersede by new decision id instead
    "NOT_APPLICABLE": {"UNRESOLVED"},
    "UNMAPPED": set(),
}


class LedgerError(Exception):
    pass


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_ledger(request, scan_result, budget=5, frame=None):
    """Open a ledger from a scan, optionally scoped to an assessment
    frame. Surfaces past the budget are marked suppressed_by_budget --
    visible, not dropped. If frame is provided, every entry inherits
    the frame id so usefulness measurements can be compared across
    frames later."""
    frame_id = None
    if frame:
        frame_id = "%s+%s+%s" % (
            frame.get("human", {}).get("value", "?"),
            frame.get("ai", {}).get("value", "?"),
            frame.get("project", {}).get("value", "?"))
    entries = {}
    for i, h in enumerate(scan_result.get("surfaces", [])):
        did = "D%d" % (i + 1)
        entries[did] = {
            "surface": h["surface"],
            "matched": h["matched"],
            "consequence_class_prior": h["consequence_prior"],
            "decomposes_into": h["decomposes_into"],
            "question_hypothesis": h["question_hypothesis"],
            "state": "UNRESOLVED" if i < budget else "DETECTED",
            "suppressed_by_budget": i >= budget,
            "answer": None,
            "provenance": None,
            "history": [{
                "at": _now(),
                "event": ("exposed" if i < budget
                          else "detected, suppressed by budget"),
            }],
            "frame_id": frame_id,
            "predicted_usefulness": None,
            "actual_usefulness": None,
            "discrimination": {"tested": False, "result": None,
                               "divergence": None, "experiments": []},
            "dependencies": [],
        }
    return {
        "schema": SCHEMA,
        "request": request,
        "created": _now(),
        "budget": budget,
        "status": scan_result.get("status", "UNMAPPED"),
        "frame": frame,
        "entries": entries,
    }


def _transition(ledger, did, target, **fields):
    if did not in ledger["entries"]:
        raise LedgerError("no decision id %s" % did)
    entry = ledger["entries"][did]
    current = entry["state"]
    if target not in TRANSITIONS.get(current, set()):
        raise LedgerError(
            "illegal transition %s -> %s for %s" % (current, target, did))

    if target == "RESOLVED":
        # the two prohibitions, enforced at the only door into RESOLVED
        answer = fields.get("answer")
        by = fields.get("by")
        if not answer or not str(answer).strip():
            raise LedgerError(
                "RESOLVED requires an answer; substituting nothing for "
                "unknown is the failure this ledger exists to prevent")
        if by not in PROVENANCE:
            raise LedgerError(
                "RESOLVED requires provenance in %s; a decision without "
                "a named author is a silent decision" % sorted(PROVENANCE))
        entry["answer"] = answer
        entry["provenance"] = {"by": by, "at": _now()}
    if target == "DEFERRED":
        if fields.get("by") not in PROVENANCE:
            raise LedgerError("DEFERRED requires --by: a deferral is an "
                              "owned decision and carries an author")
        entry["provenance"] = {"by": fields["by"], "at": _now(),
                               "reason": fields.get("reason", "")}
    entry["history"].append({
        "at": _now(),
        "event": "%s -> %s" % (current, target),
        **({"by": fields["by"]} if fields.get("by") else {}),
    })
    entry["state"] = target
    entry["suppressed_by_budget"] = False
    return entry


def record_discrimination(ledger, did, result):
    """A question's measured discriminating power, recorded against the
    entry. DOES_NOT_DISCRIMINATE marks the registry entry suspect --
    the instrument auditing its own registry. If the result carries
    an experiment record, the full frame and usefulness are preserved
    so cross-frame comparison remains possible."""
    entry = ledger["entries"][did]
    if "experiments" not in entry["discrimination"]:
        entry["discrimination"]["experiments"] = []
    disc = {
        "tested": True,
        "result": result.get("result"),
        "divergence": result.get("divergence"),
        "at": _now(),
        "experiments": entry["discrimination"]["experiments"],
    }
    if result.get("experiment"):
        exp = result["experiment"]
        disc["experiments"].append(exp.get("experiment_id"))
        entry["actual_usefulness"] = exp["measurements"].get(
            "actual_usefulness")
        pred = entry.get("predicted_usefulness")
        if pred is not None and isinstance(pred, dict):
            pred_val = pred.get("value")
        else:
            pred_val = pred
        if pred_val is not None:
            delta = abs(pred_val - (entry["actual_usefulness"] or 0))
            entry["usefulness_prediction_delta"] = round(delta, 4)
    entry["discrimination"] = disc
    if result.get("result") == "DOES_NOT_DISCRIMINATE":
        entry["history"].append({
            "at": _now(),
            "event": "registry_suspect: question failed to discriminate "
                     "under two answer profiles in frame %s"
                     % (result.get("experiment", {}).get("frame", {})
                        .get("human", {}).get("value", "?")),
        })


def set_predicted_usefulness(ledger, did, value, rationale=None):
    """Record a predicted usefulness (0-1 or band) with provenance.
    Prediction is optional; absence is UNMEASURED."""
    entry = ledger["entries"][did]
    entry["predicted_usefulness"] = {
        "value": value,
        "rationale": rationale,
        "at": _now(),
    }


def report(ledger):
    out = []
    entries = ledger["entries"]
    if ledger.get("status") == "UNMAPPED":
        out.append("UNMAPPED -- no decision surfaces were detected for "
                   "this request (a property of the registry, not of "
                   "the request's completeness).")
        return "\n".join(out)

    unresolved = [d for d, e in entries.items()
                  if e["state"] in ("UNRESOLVED", "DETECTED")]
    owned = [d for d, e in entries.items()
             if e["state"] in ("RESOLVED", "DEFERRED", "NOT_APPLICABLE")]
    unmeasured = [d for d, e in entries.items()
                  if e["state"] == "UNMEASURED"
                  or not e["discrimination"]["tested"]]

    # the absence of a decision is the headline, not the footnote
    out.append("UNRESOLVED DECISIONS: %d (printed first, on purpose)"
               % len(unresolved))
    for d in unresolved:
        e = entries[d]
        tag = " [suppressed_by_budget]" if e["suppressed_by_budget"] else ""
        out.append("  %s  %-14s [%s]%s" % (d, e["surface"],
                                           e["consequence_class_prior"],
                                           tag))
        out.append("      ? %s" % e["question_hypothesis"])
    if not unresolved:
        out.append("  none -- every detected surface carries an owned "
                   "state")

    out.append("")
    out.append("OWNED DECISIONS: %d" % len(owned))
    for d in owned:
        e = entries[d]
        prov = e.get("provenance") or {}
        by = prov.get("by", "--")
        if e["state"] == "RESOLVED":
            out.append("  %s  %-14s RESOLVED by %s: %s"
                       % (d, e["surface"], by, (e["answer"] or "")[:60]))
        elif e["state"] == "DEFERRED":
            out.append("  %s  %-14s DEFERRED by %s: %s"
                       % (d, e["surface"], by, prov.get("reason", "")[:60]))
        else:
            out.append("  %s  %-14s NOT_APPLICABLE" % (d, e["surface"]))

    out.append("")
    out.append("DISCRIMINATION: %d of %d questions untested"
               % (len(unmeasured), len(entries)))
    for d, e in entries.items():
        disc = e["discrimination"]
        if disc["tested"]:
            line = "  %s  %s (divergence %s" % (
                d, disc["result"], disc.get("divergence"))
            if e.get("actual_usefulness") is not None:
                line += ", usefulness %s" % e["actual_usefulness"]
            if e.get("usefulness_prediction_delta") is not None:
                line += ", pred_delta %.3f" % e[
                    "usefulness_prediction_delta"]
            line += ")"
            out.append(line)
    suspect = [d for d, e in entries.items()
               if e["discrimination"].get("result")
               == "DOES_NOT_DISCRIMINATE"]
    if suspect:
        out.append("  registry_suspect: %s -- these questions did not "
                   "discriminate under two profiles IN THEIR FRAME; "
                   "this is frame-local evidence, not a universal "
                   "verdict" % suspect)
    if ledger.get("frame"):
        out.append("")
        out.append("FRAME: %s" % (ledger["entries"] and
                   next(iter(ledger["entries"].values())).get(
                       "frame_id", "unscoped")))
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as fh:
        led = json.load(fh)
    if led.get("schema") != SCHEMA:
        raise LedgerError("not a %s ledger" % SCHEMA)
    return led


def save(path, ledger):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
        fh.write("\n")


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--new":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import aperture_scan
        request = args[1]
        budget = 5
        if "--budget" in args:
            budget = int(args[args.index("--budget") + 1])
        led = new_ledger(request, aperture_scan.scan(request), budget)
        print(json.dumps(led, indent=2))
        return 0 if led["status"] != "UNMAPPED" else 3

    path = args[0]
    led = load(path)
    try:
        if "--expose" in args or "--report" in args:
            print(report(led))
        elif "--resolve" in args:
            did = args[args.index("--resolve") + 1]
            by = args[args.index("--by") + 1] if "--by" in args else None
            ans = (args[args.index("--answer") + 1]
                   if "--answer" in args else None)
            _transition(led, did, "RESOLVED", answer=ans, by=by)
            save(path, led)
            print("%s RESOLVED by %s" % (did, by))
        elif "--defer" in args:
            did = args[args.index("--defer") + 1]
            by = args[args.index("--by") + 1] if "--by" in args else None
            reason = (args[args.index("--reason") + 1]
                      if "--reason" in args else "")
            _transition(led, did, "DEFERRED", by=by, reason=reason)
            save(path, led)
            print("%s DEFERRED by %s" % (did, by))
        elif "--mark" in args:
            did = args[args.index("--mark") + 1]
            state = args[args.index("--state") + 1]
            if state not in STATES:
                raise LedgerError("unknown state %s" % state)
            _transition(led, did, state)
            save(path, led)
            print("%s -> %s" % (did, state))
        else:
            print(__doc__)
            return 2
    except LedgerError as e:
        print("REFUSED: %s" % e)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
