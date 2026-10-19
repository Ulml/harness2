# Critique branch — `video-critiques`

`main` is a content-identical mirror of
[google-research/harness2](https://github.com/google-research/harness2)
at `1cfe254` (Apache-2.0). This branch is **not** the Google release and is not
affiliated with Google. It adds the gates the Discover AI review asked for.

## What the video argues

Source: Discover AI, *Recursive Self Improvement (RSI) of an AI Harness (Google)*,
15 October 2026, https://www.youtube.com/watch?v=klihXDN2xp4

The review covers three papers. The code in this repository is the third,
Harness² (Xu et al., arXiv:2610.14224). The critiques it treats as still open,
and the fixes it points at, are:

| Critique | Where it is aimed | Fix this branch implements |
| --- | --- | --- |
| A narrow self-rewrite over-fits and then collapses (PAC argument, Wei et al., *Harness Self-Evolution*) | Any lesson that names one subject | `identity_tokens` / `leaked_tokens` refuse a lesson that still carries the source subject's name or model id |
| A false lesson spreads through the library like a virus | `Library.add` writes every well-formed lesson into `INDEX.md` | A lesson is quarantined under `quarantine/` until `unseen` records a held-out subject. Later tasks read only `harnesses/` |
| The agent deletes a security rule to make the task look solved | Harmony Harness's point, which the video endorses | `guardrails_intact`: a constitution line may not disappear |
| The same model proposes, executes, and blesses its own edit | Role collapse / self-deception | `proposer` and `observer` must differ when both are recorded |
| A timeout or 429 is written up as a design flaw | Misattributed noise | Transient evidence is not a lesson unless a second contrast is cited |

The code is `harness2/core/admission.py`. `Library.add` calls it before anything
reaches the live index. The demo reflector now records an unseen proof, a
distinct observer, and no identity token, so the existing workflow test still
sees a legitimate lesson enter the library. A lesson that fails a gate is kept
on disk and kept out of `INDEX.md`.

Harmony's multi-objective search and the factorized invariant/binding split are
**not** in this branch. They are the next one, `research-transfer`, because they
come from the papers and from failure cases the video only names in passing.
