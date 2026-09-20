# WORK ORDER -- decision-aperture, delivered verbatim

Condensed from the commissioning conversation. Nothing below the
rule is edited.

---

Create a CC0 sibling repo called decision-aperture to sit alongside
simulators, method-layer, and vibe-code-audit.

PURPOSE
  Help identify implementation-bearing decisions that haven't
  actually been made yet. Not a requirements generator. Not an
  opinionated framework.

DECISION STATES
  Distinguish: detected, unresolved, resolved, deferred, unmapped,
  unmeasured, not applicable.

MAY
  detect, expose, decompose, ask, route, record provenance.

MUST NOT
  silently resolve a decision. substitute a default for something
  unknown.

QUESTION GENERATION
  Cautious. Based on decision surfaces and predicted consequence.
  Do not assume a question is useful just because it sounds
  intelligent. Budget the questions; fatigue makes the tool bulk.

INITIAL TEST
  Take an underspecified coding request. Generate a question. Run
  two different answer profiles. If the resulting implementations
  don't diverge in meaningful ways, the question did not actually
  discriminate. That is measurable evidence about the instrument
  itself.

CONSTRAINTS
  CC0. stdlib only. no network. phone-buildable. states enforced
  in the suite, not promised in prose. absences are return types,
  first line, never errors. registry coverage is the measurement;
  the request is the sample.
