#!/usr/bin/env python3
# test_aperture.py -- CC0, stdlib only, no network, phone-buildable.
#
# The checks for decision-aperture. Prints their count.
#
# Families:
#   1. AST guards     -- aperture_scan carries no resolution vocabulary
#                        (enforced, planted-against); decision_ledger has
#                        no default field in its schema.
#   2. scanner        -- surfaces located, consequence-routed, one hit
#                        per surface; zero hits is UNMAPPED first line;
#                        paraphrase steps around the registry, measured.
#   3. ledger         -- the two prohibitions: every forbidden path into
#                        RESOLVED raises; DEFERRED requires an author;
#                        illegal transitions raise; report prints
#                        unresolved first; budget suppresses visibly.
#   4. discriminate   -- profiles diverge, cosmetic twins do not,
#                        changed constant IS divergence, unparseable is
#                        UNMEASURABLE return not a crash.
#   5. end to end     -- the shipped demo ledger reproduces.

import ast
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = [0]
FAILS = []


def check(name, cond, detail=""):
    CHECKS[0] += 1
    if not cond:
        FAILS.append("%s %s" % (name, detail))
        print("FAIL %s %s" % (name, detail))


def run_py(script, *args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(HERE, script)]
                          + list(args), capture_output=True, text=True,
                          cwd=cwd or HERE)


sys.path.insert(0, HERE)
import aperture_scan as ap  # noqa: E402
import decision_ledger as dl  # noqa: E402
import discriminate as dc  # noqa: E402
import assessment_frame as af  # noqa: E402
import usefulness_lab as ul  # noqa: E402

# ----------------------------------------------------------------------
# 1. AST guards
# ----------------------------------------------------------------------

RESOLUTION_VOCAB = {"suggest", "suggestion", "recommend", "recommendation",
                    "pick", "choose", "best", "preferred", "default",
                    "defaults", "should_use", "instead"}


def _identifiers(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    names = set()
    for node in ast.walk(tree):
        for attr in ("id", "name", "arg", "attr"):
            v = getattr(node, attr, None)
            if isinstance(v, str):
                names.update(v.lower().split("_"))
    return {n for n in names if n}


scan_ids = _identifiers(os.path.join(HERE, "aperture_scan.py"))
check("ast.scanner_locate_only", not (scan_ids & RESOLUTION_VOCAB),
      str(scan_ids & RESOLUTION_VOCAB))

# planted: a module carrying resolution vocabulary is caught
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
    fh.write("def recommend_default(x):\n    return x\n")
    plant = fh.name
check("ast.guard_not_silent",
      _identifiers(plant) & RESOLUTION_VOCAB != set())
os.unlink(plant)

# ledger schema has no default field anywhere
src = open(os.path.join(HERE, "decision_ledger.py"), encoding="utf-8").read()
check("ast.ledger_no_default_field",
      '"default"' not in src and "'default'" not in src)

# ----------------------------------------------------------------------
# 2. scanner
# ----------------------------------------------------------------------

s = ap.scan("add caching, store it in a database, handle errors, "
            "make it secure and fast")
check("scan.multi_surface", s["status"] == "MAPPED"
      and len(s["surfaces"]) == 5, str(len(s["surfaces"])))
surfaces = [h["surface"] for h in s["surfaces"]]
check("scan.consequence_routed",
      surfaces[0] in ("persistence", "error_handling", "security")
      and surfaces[-1] in ("caching", "scale"))
check("scan.one_hit_per_surface",
      len(surfaces) == len(set(surfaces)))
check("scan.decomposition_present",
      all(len(h["decomposes_into"]) >= 2 for h in s["surfaces"]))
check("scan.question_is_hypothesis",
      all("question_hypothesis" in h for h in s["surfaces"]))

s0 = ap.scan("how do i bake bread")
check("scan.unmapped_status", s0["status"] == ap.UNMAPPED
      and s0["surfaces"] == [])
rendered = ap.render(s0)
check("scan.unmapped_first_line",
      rendered.splitlines()[0].startswith("UNMAPPED"))

# the word-list limit, measured: same surface, no registry words
s_par = ap.scan("keep it around across runs")
check("scan.paraphrase_limit_measured",
      s_par["status"] == ap.UNMAPPED)

proc = run_py("aperture_scan.py", "how do i bake bread")
check("scan.unmapped_exit_nonzero", proc.returncode == 3)

# ----------------------------------------------------------------------
# 3. ledger: the two prohibitions
# ----------------------------------------------------------------------

led = dl.new_ledger("add caching and store results", ap.scan(
    "add caching and store results"), budget=5)
ids = sorted(led["entries"])
check("ledger.new_all_unresolved",
      all(e["state"] == "UNRESOLVED" for e in led["entries"].values()))

# forbidden path 1: resolve without answer
try:
    dl._transition(led, ids[0], "RESOLVED", by="user", answer=None)
    check("ledger.no_silent_resolve_answer", False)
except dl.LedgerError:
    check("ledger.no_silent_resolve_answer", True)

# forbidden path 2: resolve without provenance
try:
    dl._transition(led, ids[0], "RESOLVED", answer="redis", by=None)
    check("ledger.no_silent_resolve_provenance", False)
except dl.LedgerError:
    check("ledger.no_silent_resolve_provenance", True)

# forbidden path 3: resolve with blank answer
try:
    dl._transition(led, ids[0], "RESOLVED", answer="   ", by="user")
    check("ledger.no_blank_answer", False)
except dl.LedgerError:
    check("ledger.no_blank_answer", True)

# forbidden path 4: unknown provenance party
try:
    dl._transition(led, ids[0], "RESOLVED", answer="redis", by="nobody")
    check("ledger.provenance_closed_set", False)
except dl.LedgerError:
    check("ledger.provenance_closed_set", True)

# legal: answer + provenance
dl._transition(led, ids[0], "RESOLVED", answer="redis", by="user")
check("ledger.resolve_legal", led["entries"][ids[0]]["state"] == "RESOLVED"
      and led["entries"][ids[0]]["provenance"]["by"] == "user")

# RESOLVED is terminal: no rewrite
try:
    dl._transition(led, ids[0], "UNRESOLVED")
    check("ledger.resolved_never_rewritten", False)
except dl.LedgerError:
    check("ledger.resolved_never_rewritten", True)

# DEFERRED requires an author
try:
    dl._transition(led, ids[1], "DEFERRED", by=None)
    check("ledger.defer_needs_author", False)
except dl.LedgerError:
    check("ledger.defer_needs_author", True)
dl._transition(led, ids[1], "DEFERRED", by="user", reason="later")
check("ledger.defer_is_owned",
      led["entries"][ids[1]]["state"] == "DEFERRED")

# illegal transition raises
led2 = dl.new_ledger("add caching", ap.scan("add caching"))
try:
    dl._transition(led2, "D1", "UNMAPPED")
    check("ledger.illegal_transition_raises", False)
except dl.LedgerError:
    check("ledger.illegal_transition_raises", True)

# report prints unresolved first
led3 = dl.new_ledger("add caching and store results",
                     ap.scan("add caching and store results"))
first_id = sorted(led3["entries"])[0]
dl._transition(led3, first_id, "RESOLVED", answer="x", by="agent")
rep = dl.report(led3)
check("ledger.report_unresolved_headline",
      rep.splitlines()[0].startswith("UNRESOLVED DECISIONS"))
check("ledger.report_provenance_shown",
      "by agent" in rep)

# budget suppresses visibly, never drops
big = "store it, secure it, handle errors, add caching, make it fast, " \
      "expose an api, add a plugin system, make it configurable"
led4 = dl.new_ledger(big, ap.scan(big), budget=3)
states = [e["state"] for e in led4["entries"].values()]
supp = [e["suppressed_by_budget"] for e in led4["entries"].values()]
check("ledger.budget_caps_exposed",
      states.count("UNRESOLVED") == 3)
check("ledger.budget_suppression_visible",
      sum(supp) == len(states) - 3 and any(supp))
rep4 = dl.report(led4)
check("ledger.suppressed_shown_in_report",
      "suppressed_by_budget" in rep4)

# discrimination recording marks registry suspect
led5 = dl.new_ledger("add caching", ap.scan("add caching"))
dl.record_discrimination(led5, "D1",
                         {"result": "DOES_NOT_DISCRIMINATE",
                          "divergence": 0.03})
check("ledger.registry_suspect_recorded",
      led5["entries"]["D1"]["discrimination"]["result"]
      == "DOES_NOT_DISCRIMINATE"
      and any("registry_suspect" in h["event"]
              for h in led5["entries"]["D1"]["history"]))
check("ledger.report_shows_suspect",
      "registry_suspect" in dl.report(led5))

# ----------------------------------------------------------------------
# 4. discriminate
# ----------------------------------------------------------------------

d = tempfile.mkdtemp()
pa, pb = os.path.join(d, "a.py"), os.path.join(d, "b.py")
with open(pa, "w") as fh:
    fh.write("def get(k):\n    return CACHE.get(k)\n")
with open(pb, "w") as fh:
    fh.write("import sqlite3\ndef get(k):\n"
             "    return DB.execute('select v from t where k=?',"
             " (k,)).fetchone()\n")
r_div = dc.measure(pa, pb)
check("disc.profiles_diverge", r_div["result"] == "DISCRIMINATES",
      str(r_div))

pc = os.path.join(d, "c.py")
with open(pc, "w") as fh:
    fh.write("def get(k):  # read cache\n    '''doc'''\n"
             "    return CACHE.get(k)\n")
r_cos = dc.measure(pa, pc)
check("disc.cosmetic_twins_do_not",
      r_cos["result"] == "DOES_NOT_DISCRIMINATE", str(r_cos))

pd = os.path.join(d, "d.py")
with open(pd, "w") as fh:
    fh.write("def get(k):\n    return CACHE.get(k, 42)\n")
r_const = dc.measure(pa, pd)
check("disc.constant_is_divergence",
      r_const["divergence"] > 0)

pe = os.path.join(d, "e.py")
with open(pe, "w") as fh:
    fh.write("def broken(:\n")
r_unm = dc.measure(pa, pe)
check("disc.unparseable_is_return_not_crash",
      r_unm["result"] == "UNMEASURABLE" and r_unm["divergence"] is None)

# ----------------------------------------------------------------------
# 5. end to end
# ----------------------------------------------------------------------

p1 = run_py("aperture_scan.py", "--selftest")
check("e2e.scanner_selftest", p1.returncode == 0)
p2 = run_py("discriminate.py", "--selftest")
check("e2e.discriminate_selftest", p2.returncode == 0)

demo = os.path.join(HERE, "ledgers", "demo.json")
if os.path.exists(demo):
    loaded = dl.load(demo)
    check("e2e.demo_ledger_loads", loaded["schema"] == "da-ledger/2")
    p3 = run_py("decision_ledger.py", demo, "--report")
    check("e2e.demo_report_runs", p3.returncode == 0
          and "UNRESOLVED DECISIONS" in p3.stdout)
    # CLI refuses silent resolve
    p4 = run_py("decision_ledger.py", demo, "--resolve", "D2",
                "--answer", "redis")
    check("e2e.cli_refuses_silent_resolve",
          p4.returncode == 4 and "REFUSED" in p4.stdout)
else:
    check("e2e.demo_ledger_present", False, "ledgers/demo.json")

# ----------------------------------------------------------------------
# 6. assessment frame
# ----------------------------------------------------------------------

f = af.new_frame()
check("frame.blank_all_unmapped",
      all(f[k]["state"] == "UNMAPPED" for k in af.FIELDS))
af._set_field(f, "human", "solo_dev", provenance={"by": "test"})
af._set_field(f, "ai", "claude-test", provenance={"by": "test"})
af.add_instrument(f, "crosslink_scan", "scanner",
                  "vibe-code-audit/crosslink_scan.py",
                  surface_map=["api_shape"])
st, hits = af.route(f, "api_shape")
check("frame.route_mapped", st == "FRAME_MAPPED" and len(hits) == 1)
st2, _ = af.route(f, "persistence")
check("frame.route_unmapped_no_guess", st2 == af.FRAME_UNMAPPED)
af.add_epistemic(f, "unverified", "pytest works on CI")
check("frame.epistemic_recorded", len(f["unverified"]) == 1)

# ----------------------------------------------------------------------
# 7. usefulness lab
# ----------------------------------------------------------------------

d_frame = tempfile.mkdtemp()
fp = os.path.join(d_frame, "f.json")
af.save(fp, f)
a_fix = os.path.join(HERE, "fixtures", "cache_profile_a.py")
b_fix = os.path.join(HERE, "fixtures", "cache_profile_b.py")
rec = ul.run_experiment(fp, "cache scope?", "caching", a_fix, b_fix,
                        friction_band="low")
check("lab.divergence_measured",
      rec["measurements"]["divergence"] == 0.7419)
check("lab.usefulness_computed",
      rec["measurements"]["actual_usefulness"] > 0.5)
check("lab.explanation_transparent",
      "divergence" in rec["measurements"]["usefulness_explanation"]
      and "friction" in rec["measurements"]["usefulness_explanation"])

c_fix = os.path.join(HERE, "fixtures", "color_profile_a.py")
d_fix = os.path.join(HERE, "fixtures", "color_profile_b.py")
rec2 = ul.run_experiment(fp, "log wording?", "cosmetic", c_fix, d_fix,
                         friction_band="low")
check("lab.wording_zero_usefulness",
      rec2["measurements"]["actual_usefulness"] == 0.0)

# friction penalty is explicit
rec_high = ul.run_experiment(fp, "cache scope?", "caching", a_fix, b_fix,
                             friction_band="high")
check("lab.friction_reduces_usefulness",
      rec_high["measurements"]["actual_usefulness"]
      < rec["measurements"]["actual_usefulness"])

# unparseable profile -> UNMEASURED usefulness, not crash
bad = os.path.join(d_frame, "bad.py")
with open(bad, "w") as fh:
    fh.write("def broken(:\n")
rec_bad = ul.run_experiment(fp, "q?", "s", a_fix, bad)
check("lab.unmeasurable_is_return",
      rec_bad["measurements"]["actual_usefulness"] is None
      and rec_bad["measurements"]["divergence_verdict"] == "UNMEASURABLE")

# compare across frames: same question, different frame fields
f2 = af.new_frame()
af._set_field(f2, "human", "team_lead", provenance={"by": "test"})
af._set_field(f2, "ai", "gpt-test", provenance={"by": "test"})
af.save(os.path.join(d_frame, "f2.json"), f2)
rec3 = ul.run_experiment(os.path.join(d_frame, "f2.json"),
                         "cache scope?", "caching", a_fix, b_fix,
                         friction_band="high")
e1 = os.path.join(d_frame, "e1.json")
e2 = os.path.join(d_frame, "e2.json")
with open(e1, "w") as fh:
    json.dump(rec, fh)
with open(e2, "w") as fh:
    json.dump(rec3, fh)
comp = ul.compare([e1, e2])
check("lab.compare_reports_delta",
      comp["result"] == "COMPARED" and comp["max_delta"] > 0)
check("lab.compare_no_universal_rank",
      "NOT evidence one question is universally" in comp["report"])

# ----------------------------------------------------------------------
# 8. frame-scoped ledger
# ----------------------------------------------------------------------

led6 = dl.new_ledger("add caching", ap.scan("add caching"), frame=f)
check("ledger.frame_scoped",
      led6["entries"]["D1"]["frame_id"].startswith("solo_dev+claude-test"))
dl.set_predicted_usefulness(led6, "D1", 0.8, rationale="seems key")
dl.record_discrimination(led6, "D1", {
    "result": "DISCRIMINATES", "divergence": 0.7419,
    "experiment": rec})
check("ledger.predicted_vs_actual",
      led6["entries"]["D1"]["actual_usefulness"] == 0.7419
      and led6["entries"]["D1"]["usefulness_prediction_delta"] == 0.0581)
rep6 = dl.report(led6)
check("ledger.report_shows_frame",
      "FRAME: solo_dev+claude-test" in rep6)
led7 = dl.new_ledger("make it fast", ap.scan("make it fast"), frame=f)
dl.record_discrimination(led7, "D1", {
    "result": "DOES_NOT_DISCRIMINATE", "divergence": 0.0,
    "experiment": rec2})
check("ledger.suspect_is_frame_local",
      "frame-local evidence" in dl.report(led7))

print("-" * 60)
print("checks: %d   failed: %d" % (CHECKS[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
