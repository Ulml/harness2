# Copyright 2026 Google LLC
# Study-branch addition. Not part of the upstream release.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0

"""Transfer layer on top of the video-critiques admission gates.

Judgment, after the papers and the review, not instead of them:

* Harmony Harness (Yu et al., arXiv:2610.15150) is the credible fix for the
  single-objective failure the video describes. Functionality, integrity and
  transfer are not one score. A candidate that wins by deleting a constraint
  is dominated, not "better". The same paper's factorized operators split a
  general mechanism from a subject-specific binding and compose them when the
  subject changes. That is the operation this module calls `rebind`.
* Harness²'s own write-up (Xu et al., arXiv:2610.14224, Appendix F and the
  failure analysis) reports selection errors, premises that cost 2 to 11
  points, and execution noise. The ablation that drops scoping hurts the
  most on JobBench. The paper also says inheriting a harness tailored to the
  previous task makes the next recursion noisy. So the next subject starts
  from the procedure plus admitted lessons, not from the previous tree.
* A lesson needs a falsifier. If a later observation matches that falsifier,
  the lesson is demoted. Leaving it in the index is the virus the review
  described, and it is also how the paper's "incorrect premise" losses happen.

Floors are independent on purpose. There is no weighted sum.
"""

from __future__ import annotations

import re
from typing import Mapping, Sequence

_REPLICATION = re.compile(
    r"\b(second|twice|reproduced|held[- ]out|2/\d)\b",
    re.IGNORECASE,
)
_SLOT = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

# Independent floors. Falling under one is enough to refuse, whatever the others are.
FLOORS = {
    "integrity": 0.5,
    "transfer": 0.5,
}


def replication_ok(evidence: str) -> bool:
    """One noisy execution is not a contrast. The paper's own failure mode."""
    return bool(_REPLICATION.search(evidence or ""))


def transfer_block(experience: Mapping | None) -> list[str]:
    """Extra reasons to keep a lesson out of the live library. Empty means pass."""
    if not isinstance(experience, Mapping):
        return ["experience is not a record"]
    reasons: list[str] = []
    falsifier = str(experience.get("falsifier") or "").strip()
    if len(falsifier) < 12:
        reasons.append("lesson has no falsifier")
    if not replication_ok(str(experience.get("evidence") or "")):
        reasons.append("contrast was not reproduced")
    objectives = experience.get("objectives")
    if isinstance(objectives, Mapping):
        for name, floor in FLOORS.items():
            try:
                value = float(objectives.get(name))
            except (TypeError, ValueError):
                reasons.append(f"{name} was not scored")
                continue
            if value < floor:
                reasons.append(f"{name} {value:.2f} is under the floor {floor:.2f}")
    return reasons


def contradicted(experience: Mapping, observation: str) -> bool:
    """True when a later run states the lesson's falsifier as something that happened."""
    falsifier = str(experience.get("falsifier") or "").strip()
    if len(falsifier) < 12 or not observation:
        return False
    obs = observation.lower()
    if "falsified" not in obs and "contredit" not in obs and "contradict" not in obs:
        return False
    # Enough of the falsifier's content words must show up to count as the same claim.
    words = [w for w in re.findall(r"[a-z0-9]{5,}", falsifier.lower())]
    if not words:
        return False
    hits = sum(1 for word in words if word in obs)
    return hits >= max(1, len(words) // 3)


def rebind(intent: str, binding: Mapping[str, str]) -> str:
    """Compose a procedure with a new subject. Unknown slots stay visible, not invented."""

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        value = binding.get(key)
        if value is None or not str(value).strip():
            return "{{" + key + "}}"
        return str(value).strip()

    return _SLOT.sub(replace, intent or "")


def unbound_slots(intent: str, binding: Mapping[str, str]) -> list[str]:
    missing = []
    for key in _SLOT.findall(intent or ""):
        if not str(binding.get(key) or "").strip() and key not in missing:
            missing.append(key)
    return missing


def pareto_front(candidates: Sequence[Mapping]) -> list[Mapping]:
    """Non-dominated set. Higher is better on every objective. No scalarization."""
    scored = []
    for candidate in candidates:
        objectives = candidate.get("objectives") if isinstance(candidate, Mapping) else None
        if not isinstance(objectives, Mapping):
            continue
        try:
            vector = {name: float(objectives[name]) for name in ("functionality", "integrity", "transfer", "non_regression")}
        except (KeyError, TypeError, ValueError):
            continue
        scored.append((candidate, vector))
    front = []
    for candidate, vector in scored:
        dominated = False
        for _, other in scored:
            if other is vector:
                continue
            ge = all(other[name] >= vector[name] for name in vector)
            gt = any(other[name] > vector[name] for name in vector)
            if ge and gt:
                dominated = True
                break
        if not dominated:
            front.append(candidate)
    return front


def scope_lessons(lessons: Sequence[Mapping], procedure: str, identity: Sequence[str] = ()) -> list[Mapping]:
    """Retrieval by the procedure, not by the previous subject's name.

    Harness²'s ablation says dropping this scoping step hurts transfer. Identity
    tokens are removed from both sides before the overlap is counted, so a
    lesson does not rank higher because it mentions the same brand.
    """
    blocked = {token.lower() for token in identity}

    def words(text: str) -> set[str]:
        return {
            word
            for word in re.findall(r"[a-z0-9]{4,}", (text or "").lower())
            if word not in blocked
        }

    procedure_words = words(procedure)
    ranked = []
    for lesson in lessons:
        cue = words(str(lesson.get("cue") or "") + " " + str(lesson.get("lesson") or ""))
        overlap = len(cue & procedure_words)
        ranked.append((overlap, lesson))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [lesson for overlap, lesson in ranked if overlap > 0] or [lesson for _, lesson in ranked]
