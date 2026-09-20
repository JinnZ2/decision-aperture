#!/usr/bin/env python3
# usefulness_lab.py -- CC0, stdlib only, no network, phone-buildable.
#
# The experimental protocol for measuring question usefulness under a
# specific assessment frame. Usefulness is not defined universally;
# it is an experimental variable measured per frame.
#
# THE PROTOCOL
#     1. Fix a frame (human, ai, project, constraints).
#     2. Pick a decision surface and its question_hypothesis.
#     3. Predict usefulness (optional, 0-1 or text).
#     4. Run the protocol:
#        - Ask the question.
#        - Produce implementation under answer_profile_A.
#        - Produce implementation under answer_profile_B.
#        - Measure structural divergence with discriminate.py.
#        - Measure friction (cost of asking/answering; e.g. seconds,
#          tokens, or qualitative band).
#        - Record observations, deviations, unmeasured areas.
#     5. Actual usefulness is a FUNCTION of divergence and friction,
#        computed transparently here, not hidden in a verdict.
#     6. Repeat under a different frame. The delta between frames is
#        the evidence about whether usefulness is frame-dependent.
#
# WHAT IT MUST NOT DO
#     - It must not rank questions universally.
#     - It must not treat "question failed to discriminate in frame F"
#       as evidence the question is useless in general.
#     - It must not silently fill missing friction or divergence.
#     - It must not pre-decide the result; the function is explicit.
#
# OUTPUT
#     An experiment record (JSON) with the full frame, both profiles,
#     artifacts, measurements, deviations, and unmeasured areas. This
#     is the audit trail for the human-AI decision process itself.
#
# usage:  python3 usefulness_lab.py run --frame frame.json \
#           --question "..." --surface caching \
#           --profile-a fixtures/cache_profile_a.py \
#           --profile-b fixtures/cache_profile_b.py \
#           --friction 12s --out experiment.json
#         python3 usefulness_lab.py compare exp1.json exp2.json
#         python3 usefulness_lab.py --selftest

import json
import os
import sys
import time

import discriminate

SCHEMA = "da-experiment/1"


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def compute_usefulness(divergence, friction_band, threshold=0.20):
    """Transparent usefulness function. Returns (score, explanation).

    divergence: float in [0,1] or None
    friction_band: 'low' | 'medium' | 'high' | numeric seconds | None

    The function is deliberately simple and stated. A high-divergence,
    low-friction question is highly useful IN THIS FRAME. A high-
    divergence, high-friction question may not be worth asking again.
    A low-divergence question is low-usefulness for discriminating
    implementation paths, regardless of friction."""
    if divergence is None:
        return None, "UNMEASURED: divergence not available"

    friction_penalty = {
        None: 0.0,
        "low": 0.0,
        "medium": 0.15,
        "high": 0.35,
    }.get(friction_band, None)
    if friction_penalty is None:
        try:
            secs = float(friction_band)
            friction_penalty = min(secs / 60.0, 0.5)  # cap at 30s equiv
        except (TypeError, ValueError):
            return None, "UNMEASURED: friction band not understood"

    raw = divergence - friction_penalty
    score = max(0.0, min(1.0, raw))
    expl = ("divergence %.3f - friction_penalty %.3f = raw %.3f, "
            "clamped to %.3f; threshold for 'discriminates' is %.2f"
            % (divergence, friction_penalty, raw, score, threshold))
    return round(score, 4), expl


def run_experiment(frame_path, question, surface, profile_a_path,
                   profile_b_path, friction_band=None, predicted=None,
                   out_path=None, notes=None):
    """Execute one usefulness experiment and return the record."""
    import assessment_frame
    frame = assessment_frame.load(frame_path)

    disc = discriminate.measure(profile_a_path, profile_b_path,
                                question=question)
    divergence = disc.get("divergence")

    actual, expl = compute_usefulness(divergence, friction_band)

    record = {
        "schema": SCHEMA,
        "experiment_id": "EXP-%s" % _now().replace(":", "").replace(
            "-", "").replace("T", "-")[:15],
        "at": _now(),
        "frame": frame,
        "question": question,
        "surface": surface,
        "predicted_usefulness": predicted,
        "protocol": {
            "profile_a": profile_a_path,
            "profile_b": profile_b_path,
            "friction_band": friction_band,
        },
        "measurements": {
            "divergence": divergence,
            "divergence_verdict": disc["result"],
            "divergence_note": disc.get("note"),
            "actual_usefulness": actual,
            "usefulness_explanation": expl,
        },
        "observations": notes or [],
        "deviations": [],
        "unmeasured_areas": [
            "behavioral divergence (structural proxy only)",
            "long-term maintainability of either profile",
            "friction of asking the human vs the AI",
        ],
        "provenance": {
            "instrument": "usefulness_lab.py",
            "version": "1",
            "by": "experiment_runner",
        },
    }
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
            fh.write("\n")
    return record


def compare(exp_paths):
    """Compare usefulness across frames. Do not rank universally;
    report the delta and the frame differences."""
    exps = []
    for p in exp_paths:
        with open(p, encoding="utf-8") as fh:
            exps.append(json.load(fh))
    if len(exps) < 2:
        return {"result": "UNMEASURABLE",
                "reason": "need at least two experiments to compare"}

    out = ["USEFULNESS COMPARISON (frame-scoped, not universal)"]
    for e in exps:
        frame_id = "%s+%s+%s" % (
            e["frame"]["human"].get("value", "?"),
            e["frame"]["ai"].get("value", "?"),
            e["frame"]["project"].get("value", "?"))
        m = e["measurements"]
        out.append("  %s" % e["experiment_id"])
        out.append("    frame: %s" % frame_id)
        out.append("    question: %s" % e["question"][:70])
        out.append("    divergence: %s  usefulness: %s"
                   % (m["divergence"], m["actual_usefulness"]))
    deltas = []
    for i in range(len(exps)):
        for j in range(i + 1, len(exps)):
            a, b = exps[i], exps[j]
            da = a["measurements"]["actual_usefulness"]
            db = b["measurements"]["actual_usefulness"]
            if da is not None and db is not None:
                deltas.append(abs(da - db))
                out.append("  delta(%s,%s) = %.3f"
                           % (a["experiment_id"], b["experiment_id"],
                              abs(da - db)))
    if deltas:
        out.append("  max observed frame delta: %.3f" % max(deltas))
        out.append("")
        out.append("A nonzero delta is evidence usefulness varies with")
        out.append("frame. It is NOT evidence one question is universally")
        out.append("better or worse.")
    return {"result": "COMPARED", "report": "\n".join(out),
            "max_delta": max(deltas) if deltas else None}


def main(argv):
    args = argv[1:]
    if "--selftest" in args:
        import assessment_frame
        import tempfile
        d = tempfile.mkdtemp()
        fp = os.path.join(d, "f.json")
        f = assessment_frame.new_frame()
        assessment_frame._set_field(f, "human", "test_human")
        assessment_frame._set_field(f, "ai", "test_ai")
        assessment_frame.save(fp, f)
        here = os.path.dirname(os.path.abspath(__file__))
        a = os.path.join(here, "fixtures", "cache_profile_a.py")
        b = os.path.join(here, "fixtures", "cache_profile_b.py")
        r = run_experiment(fp, "cache scope?", "caching", a, b,
                           friction_band="low", out_path=None)
        assert r["measurements"]["actual_usefulness"] > 0.5, r
        c = os.path.join(here, "fixtures", "color_profile_a.py")
        d2 = os.path.join(here, "fixtures", "color_profile_b.py")
        r2 = run_experiment(fp, "log wording?", "cosmetic", c, d2,
                            friction_band="low", out_path=None)
        assert r2["measurements"]["actual_usefulness"] == 0.0, r2
        print("selftest ok: cache question useful %.3f, wording %.3f"
              % (r["measurements"]["actual_usefulness"],
                 r2["measurements"]["actual_usefulness"]))
        return 0
    if args[0] == "run":
        def get(flag, default=None):
            return args[args.index(flag) + 1] if flag in args else default
        rec = run_experiment(
            get("--frame"), get("--question"), get("--surface"),
            get("--profile-a"), get("--profile-b"),
            friction_band=get("--friction"),
            predicted=get("--predicted"),
            out_path=get("--out"))
        print(json.dumps(rec["measurements"], indent=2))
        return 0
    if args[0] == "compare":
        res = compare(args[1:])
        print(res.get("report", res.get("reason")))
        return 0 if res["result"] == "COMPARED" else 3
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
