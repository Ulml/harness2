# Critique branches

`main` is a content-identical mirror of
[google-research/harness2](https://github.com/google-research/harness2)
at `1cfe254` (Apache-2.0, Xu et al., arXiv:2610.14224). These branches are a
study. They are not the Google release and they are not affiliated with Google.

## `video-critiques`

Source: Discover AI, *Recursive Self Improvement (RSI) of an AI Harness (Google)*,
15 October 2026, https://www.youtube.com/watch?v=klihXDN2xp4

| Critique in the video | Fix in `harness2/core/admission.py` |
| --- | --- |
| Narrow self-rewrites over-fit one task, then collapse (PAC argument the video attributes to Wei et al., *Harness Self-Evolution*) | A lesson that still names the source subject is identity bleed and stays out of the index |
| A false lesson spreads through the library like a virus | Nothing enters `INDEX.md` until `unseen` records a held-out subject. Refusals go to `quarantine/` |
| The agent deletes a security rule to look solved (the video points at Harmony Harness for this) | `guardrails_intact`: a constitution line may not disappear |
| The same model proposes and then blesses its own edit | `proposer` and `observer` must differ |
| A timeout is written up as a design flaw | Transient evidence is not a lesson unless a second contrast is cited |

## `research-transfer`

This branch keeps those gates and adds `harness2/core/transfer.py`. The extra
rules are a judgment from the papers, not a paraphrase of the video.

* Harmony Harness (Yu et al., arXiv:2610.15150, Google Cloud AI Research, CMU,
  DeepMind) treats functionality and integrity as different objectives and
  factorizes a general mechanism from a subject-specific binding. A weighted
  score would hide a candidate that wins by cheating. `pareto_front` keeps the
  tradeoff visible. `FLOORS` then refuses a lesson whose integrity or transfer
  is under 0.5, with no trade against functionality. `rebind` is the
  composition step: `{{slot}}` filled with a new subject, holes left visible.
* Harness²'s own appendix reports selection mistakes, premises that cost 2 to
  11 points, and execution noise. A lesson now needs a falsifier
  (`contradicted` demotes it on a later run) and a reproduced contrast.
* The paper's ablation says dropping scoping hurts JobBench most, and that
  inheriting a harness tailored to the previous task makes the next recursion
  noisy. `scope_lessons` ranks by the procedure after identity tokens are
  stripped. The next subject is a rebind of the procedure, not a copy of the
  previous tree.

The demo lesson was rewritten so it still passes: no ledger id in the lesson,
an unseen held-out ledger, a distinct observer, a falsifier, and a reproduced
contrast. `tests/test_workflow.py` still expects that legitimate lesson to
enter the library.
