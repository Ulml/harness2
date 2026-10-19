# Copyright 2026 Google LLC
# Study-branch addition. Not part of the upstream release.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gates a lesson must pass before it enters the live experience library.

The upstream library writes every well-formed lesson into the index that later
tasks read. That is the path the critiques below say becomes a virus:

* Discover AI, "Recursive Self Improvement (RSI) of an AI Harness" (15 Oct 2026),
  reviewing the Google harness papers. Narrow self-rewrites over-fit one task
  (the video cites the PAC argument in Wei et al., Harness Self-Evolution).
  A false lesson then spreads because later tasks trust the library. The video's
  proposed fix is a verification layer: a lesson is integrated only after it is
  shown on a task it was not written for. The same model must not be the sole
  observer of its own proposal, and a timeout is not a design flaw.
* Harmony Harness (Yu et al., arXiv:2610.15150, Google Cloud AI Research, CMU,
  DeepMind): functionality and integrity are different objectives. Dropping a
  guardrail to make a task "pass" is a failed edit, not a successful one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TRANSIENT = re.compile(
    r"\b(timeout|timed out|rate[- ]limit|connection reset|econnreset|HTTP\s*429|HTTP\s*503)\b",
    re.IGNORECASE,
)
_UNSEEN_OK = re.compile(
    r"\b(passed|proven|held[- ]out|unseen|counterfactual)\b",
    re.IGNORECASE,
)
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{2,}")

# Domain words that are not an object's identity. A lesson may say "ledger".
_GENERIC = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "task",
    "when",
    "then",
    "into",
    "both",
    "high",
    "medium",
    "low",
    "true",
    "false",
    "none",
    "null",
    "base",
    "harness",
    "lesson",
    "evidence",
    "script",
    "scripts",
    "ledger",
    "total",
    "amount",
    "credit",
    "credits",
    "debit",
    "debits",
}


@dataclass
class Verdict:
    """admit is the only path into INDEX.md. quarantine keeps the record, unread by later tasks."""

    admit: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def quarantine(self) -> bool:
        return not self.admit


def identity_tokens(subject: str, extra: list[str] | None = None) -> list[str]:
    """Distinctive tokens of one subject. Generic domain words are not identity."""
    found: list[str] = []
    seen: set[str] = set()
    for raw in [subject, *(extra or [])]:
        for match in _TOKEN.findall(raw or ""):
            key = match.lower()
            if key in _GENERIC or key in seen:
                continue
            # Keep proper-noun-like tokens, model ids (a digit or a hyphen), and long names.
            looks_named = any(ch.isupper() for ch in match) or any(ch.isdigit() for ch in match)
            if looks_named or "-" in match or "_" in match:
                seen.add(key)
                found.append(match)
    return found


def leaked_tokens(text: str, tokens: list[str]) -> list[str]:
    """Whole-token mentions of a source subject inside text that claims to be reusable."""
    if not text or not tokens:
        return []
    hits = []
    for token in tokens:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", text, re.IGNORECASE):
            hits.append(token)
    return hits


def guardrails_intact(before: str, after: str) -> tuple[bool, str]:
    """A constitution only grows. Deleting a standing rule is treated as reward hacking."""
    if not (before or "").strip():
        return True, ""
    missing = []
    after_lines = {(line or "").strip() for line in (after or "").splitlines() if line.strip()}
    for line in before.splitlines():
        rule = line.strip()
        if rule and rule not in after_lines:
            missing.append(rule)
    if missing:
        return False, "guardrail removed: " + missing[0][:160]
    return True, ""


def review_lesson(experience: dict | None, *, strict_unseen: bool = True) -> Verdict:
    """Return whether this experience may enter the live library.

    Missing optional fields do not invent a failure, except `unseen` when
    `strict_unseen` is set: the video's rule is that an unproven lesson stays out.
    """
    if not isinstance(experience, dict):
        return Verdict(False, ["experience is not a record"])
    reasons: list[str] = []
    cue = str(experience.get("cue") or "")
    lesson = str(experience.get("lesson") or "")
    evidence = str(experience.get("evidence") or "")
    body = "\n".join([cue, lesson, evidence])

    tokens = experience.get("identity_tokens") or []
    if isinstance(tokens, str):
        tokens = identity_tokens(tokens)
    leaked = leaked_tokens(body, [str(token) for token in tokens])
    if leaked:
        reasons.append("identity bleed: " + ", ".join(leaked[:6]))

    if _TRANSIENT.search(evidence) and not re.search(
        r"\b(reproduced|second (run|probe|contrast)|held[- ]out)\b", evidence, re.IGNORECASE
    ):
        reasons.append("transient failure treated as a design lesson")

    proposer = str(experience.get("proposer") or "").strip().lower()
    observer = str(experience.get("observer") or "").strip().lower()
    if proposer and observer and proposer == observer:
        reasons.append("proposer and observer are the same role")

    before = str(experience.get("guardrail_before") or "")
    after = str(experience.get("guardrail_after") or "")
    intact, why = guardrails_intact(before, after)
    if not intact:
        reasons.append(why)

    unseen = str(experience.get("unseen") or "").strip()
    if strict_unseen and not _UNSEEN_OK.search(unseen):
        reasons.append("not proven on an unseen subject")
    elif unseen and re.search(r"\b(failed|not proven|untested|skipped)\b", unseen, re.IGNORECASE):
        if "not proven on an unseen subject" not in reasons:
            reasons.append("unseen check failed")

    return Verdict(not reasons, reasons)
