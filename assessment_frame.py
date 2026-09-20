# assessment_frame.py -- CC0, stdlib only, no network, phone-buildable.
#
# Constructs the ASSESSMENT FRAME for one experiment: the specific
# configuration of human, AI/model, project, development environment,
# constraints, available instruments, and epistemic state under which
# decision surfaces will be detected, questions asked, and usefulness
# measured.
#
# THE POINT OF THIS MODULE
#     decision-aperture does not assume one set of questions is
#     universally helpful. A question that discriminates for a solo
#     developer with Claude on a greenfield script may be noise for a
#     team with GPT on a legacy codebase. This module makes that
#     configuration explicit so the rest of the system can scope every
#     claim, measurement, and refusal to it.
#
# STATES IT PRODUCES
#     A frame is not "valid" or "invalid". It is a record with:
#       - human / ai / project / environment / constraints (who/what)
#       - instruments (what can measure: files, test runners, auditors)
#       - knowns / unknowns / unverified (what the frame asserts vs
#         suspects vs has not checked)
#     Any field may be UNMAPPED (not provided) or UNMEASURED (provided
#     but not yet probed). Those are states, not errors.
#
# ROUTING, NOT PRESCRIPTION
#     Given a decision surface, route() returns the instruments *in
#     this frame* that could investigate it, or FRAME_UNMAPPED. It
#     never ranks universally, never says "use X", and never resolves
#     the surface. It answers: under THIS configuration, what is
#     available?
#
# THE LIMIT, STATED HERE
#     A frame is a snapshot of declared and detected facts. If the
#     human says "I have pytest" and pytest is broken, the frame is
#     wrong; the system downstream must treat instrument availability
#     as UNVERIFIED until used. This module cannot verify claims; it
#     can only record them with provenance.
#
# usage:  python3 assessment_frame.py --new frame.json
#         python3 assessment_frame.py frame.json --add-known "tests exist"
#         python3 assessment_frame.py frame.json --route persistence
#         python3 assessment_frame.py --selftest

import json
import os
import re
import sys
import time

SCHEMA = "da-frame/1"

FRAME_UNMAPPED = "FRAME_UNMAPPED"
UNMEASURED = "UNMEASURED"

# ---------------------------------------------------------------------
# The frame schema. Every field is optional; absence is UNMAPPED.
# ---------------------------------------------------------------------

FIELDS = ("human", "ai", "project", "environment", "constraints")


def new_frame(path=None):
    """Blank frame. All fields UNMAPPED. Instruments empty.
    Knowns/unknowns/unverified empty."""
    return {
        "schema": SCHEMA,
        "created": _now(),
        "human": {"state": "UNMAPPED", "value": None, "provenance": None},
        "ai": {"state": "UNMAPPED", "value": None, "provenance": None},
        "project": {"state": "UNMAPPED", "value": None, "provenance": None},
        "environment": {"state": "UNMAPPED", "value": None, "provenance": None},
        "constraints": {"state": "UNMAPPED", "value": [], "provenance": None},
        "instruments": [],
        "knowns": [],
        "unknowns": [],
        "unverified": [],
        "notes": [],
    }


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _set_field(frame, field, value, provenance=None):
    if field not in FIELDS:
        raise ValueError("unknown frame field %s" % field)
    if frame[field]["state"] == "UNMAPPED":
        frame[field]["value"] = value
        frame[field]["state"] = "DECLARED"
    else:
        # revision: keep history
        frame["notes"].append({
            "at": _now(),
            "event": "field %s revised: %r -> %r" % (
                field, frame[field]["value"], value),
        })
        frame[field]["value"] = value
        frame[field]["state"] = "DECLARED"
    if provenance:
        frame[field]["provenance"] = provenance


def add_instrument(frame, name, kind, path_or_cmd, surface_map=None,
                   provenance=None):
    """Register an instrument available in this frame.

    kind: scanner | test_runner | auditor | simulator | custom
    surface_map: list of decision surfaces this instrument can
                 investigate (e.g. ["persistence", "error_handling"]).
                 None = frame cannot route it to any surface."""
    inst = {
        "name": name,
        "kind": kind,
        "locator": path_or_cmd,
        "surface_map": surface_map or [],
        "state": "UNMEASURED",  # availability not yet exercised
        "provenance": provenance or {"by": "frame_declared"},
        "added": _now(),
    }
    frame["instruments"].append(inst)
    return inst


def route(frame, surface):
    """Return instruments in THIS frame that could investigate surface.
    FRAME_UNMAPPED if none registered for it. Never a nearest guess.
    Returns (status, hits_list); caller renders."""
    hits = [i for i in frame["instruments"]
            if surface in i.get("surface_map", [])]
    if not hits:
        return FRAME_UNMAPPED, []
    return "FRAME_MAPPED", hits


def render_route(surface, hits):
    lines = ["FRAME_MAPPED -- %d instrument(s) for surface %r:"
             % (len(hits), surface)]
    for i in hits:
        lines.append("  %s (%s) at %s [%s]" % (
            i["name"], i["kind"], i["locator"], i["state"]))
    lines.append("")
    lines.append("Availability is UNMEASURED until exercised; this is")
    lines.append("a routing table, not a recommendation.")
    return "\n".join(lines)


def add_epistemic(frame, category, claim, provenance=None):
    """Record a known, unknown, or unverified area."""
    if category not in ("knowns", "unknowns", "unverified"):
        raise ValueError("category must be knowns|unknowns|unverified")
    frame[category].append({
        "claim": claim,
        "provenance": provenance or {"by": "frame_declared"},
        "at": _now(),
    })


def probe_instruments(frame, runner=None):
    """Exercise each instrument's locator and mark state:
    MEASURED_OK, MEASURED_FAIL, or leave UNMEASURED if runner is None.
    runner(inst) -> (ok: bool, detail: str)"""
    if runner is None:
        return
    for inst in frame["instruments"]:
        ok, detail = runner(inst)
        inst["state"] = "MEASURED_OK" if ok else "MEASURED_FAIL"
        inst["probe_detail"] = detail
        inst["probed_at"] = _now()


def render(frame):
    out = ["ASSESSMENT FRAME (%s)" % frame["schema"]]
    for f in FIELDS:
        v = frame[f]
        if v["state"] == "UNMAPPED":
            out.append("  %-12s UNMAPPED" % f)
        else:
            out.append("  %-12s %s" % (f, v["value"]))
    if frame["instruments"]:
        out.append("  instruments:")
        for i in frame["instruments"]:
            out.append("    - %s (%s) maps: %s [%s]" % (
                i["name"], i["kind"], ",".join(i["surface_map"]),
                i["state"]))
    else:
        out.append("  instruments: none registered")
    for cat in ("knowns", "unknowns", "unverified"):
        if frame[cat]:
            out.append("  %s:" % cat)
            for item in frame[cat]:
                out.append("    - %s" % item["claim"])
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as fh:
        f = json.load(fh)
    if f.get("schema") != SCHEMA:
        raise ValueError("not a %s frame" % SCHEMA)
    return f


def save(path, frame):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(frame, fh, indent=2)
        fh.write("\n")


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        f = new_frame()
        assert f["schema"] == SCHEMA
        assert f["human"]["state"] == "UNMAPPED"
        _set_field(f, "human", "solo_dev", provenance={"by": "cli"})
        _set_field(f, "ai", "claude-3.7", provenance={"by": "cli"})
        add_instrument(f, "crosslink_scan", "scanner",
                       "vibe-code-audit/crosslink_scan.py",
                       surface_map=["api_shape", "dependency"])
        st, hits = route(f, "api_shape")
        assert st == "FRAME_MAPPED" and len(hits) == 1
        st2, _ = route(f, "persistence")
        assert st2 == FRAME_UNMAPPED
        print("selftest ok: frame routes api_shape, unmapped for "
              "persistence")
        return 0
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--new":
        f = new_frame()
        save(args[1], f)
        print("wrote blank frame to %s" % args[1])
        return 0
    path = args[0]
    frame = load(path)
    if "--set" in args:
        idx = args.index("--set")
        _set_field(frame, args[idx + 1], args[idx + 2],
                   provenance={"by": "cli", "at": _now()})
        save(path, frame)
        print("set %s" % args[idx + 1])
    elif "--add-instrument" in args:
        idx = args.index("--add-instrument")
        name, kind, locator = args[idx + 1:idx + 4]
        smap = args[idx + 4].split(",") if len(args) > idx + 4 else []
        add_instrument(frame, name, kind, locator, smap,
                       provenance={"by": "cli", "at": _now()})
        save(path, frame)
        print("added instrument %s" % name)
    elif "--add-known" in args or "--add-unknown" in args \
            or "--add-unverified" in args:
        for flag, cat in (("--add-known", "knowns"),
                          ("--add-unknown", "unknowns"),
                          ("--add-unverified", "unverified")):
            if flag in args:
                add_epistemic(frame, cat, args[args.index(flag) + 1],
                              provenance={"by": "cli", "at": _now()})
        save(path, frame)
        print("recorded")
    elif "--route" in args:
        st, hits = route(frame, args[args.index("--route") + 1])
        if st == "FRAME_MAPPED":
            print(render_route(args[args.index("--route") + 1], hits))
        else:
            print(FRAME_UNMAPPED
                  + " -- no instrument in this frame maps that surface")
        return 0 if st == "FRAME_MAPPED" else 3
    else:
        print(render(frame))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
