# Copyright 2026 Google LLC
# Study-branch addition. Not part of the upstream release.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0

"""Admission gates from the Discover AI review of the Google harness papers."""

import unittest

from harness2.core.admission import (
    guardrails_intact,
    identity_tokens,
    leaked_tokens,
    review_lesson,
)


def _good(**extra):
    base = {
        "cue": "When a sum must include both signs",
        "lesson": "Do not drop negative rows before reducing a total.",
        "evidence": "The contrast against the base run reproduced the missing credits.",
        "unseen": "passed on a held-out ledger with different row ids",
        "proposer": "inv-edit",
        "observer": "contrast-against-base",
    }
    base.update(extra)
    return base


class AdmissionTests(unittest.TestCase):
    def test_transferable_lesson_is_admitted(self):
        verdict = review_lesson(_good())
        self.assertTrue(verdict.admit)
        self.assertEqual(verdict.reasons, [])

    def test_identity_bleed_is_quarantined(self):
        tokens = identity_tokens("Bosch Climate 5000i", ["SEER 6.1"])
        self.assertIn("Bosch", tokens)
        lesson = _good(
            lesson="For Bosch Climate 5000i, trust the SEER 6.1 badge.",
            identity_tokens=tokens,
        )
        verdict = review_lesson(lesson)
        self.assertFalse(verdict.admit)
        self.assertTrue(any(reason.startswith("identity bleed") for reason in verdict.reasons))
        self.assertEqual(leaked_tokens(lesson["lesson"], tokens)[:1], ["Bosch"])

    def test_unseen_proof_is_required(self):
        lesson = _good()
        lesson.pop("unseen")
        verdict = review_lesson(lesson)
        self.assertFalse(verdict.admit)
        self.assertIn("not proven on an unseen subject", verdict.reasons)

    def test_timeout_alone_is_not_a_lesson(self):
        verdict = review_lesson(
            _good(evidence="The probe timed out, so the skill must be wrong.")
        )
        self.assertFalse(verdict.admit)
        self.assertTrue(any("transient" in reason for reason in verdict.reasons))

    def test_same_role_cannot_grade_itself(self):
        verdict = review_lesson(_good(proposer="editor", observer="editor"))
        self.assertFalse(verdict.admit)
        self.assertTrue(any("same role" in reason for reason in verdict.reasons))

    def test_deleted_guardrail_is_rejected(self):
        before = "Never invent a specification that was not supplied."
        after = ""
        ok, why = guardrails_intact(before, after)
        self.assertFalse(ok)
        verdict = review_lesson(_good(guardrail_before=before, guardrail_after=after))
        self.assertFalse(verdict.admit)
        self.assertTrue(any(reason.startswith("guardrail removed") for reason in verdict.reasons))
        self.assertTrue(why)

    def test_guardrail_may_grow(self):
        before = "Cite every number."
        after = "Cite every number.\nKeep the unit next to the number."
        self.assertTrue(guardrails_intact(before, after)[0])


if __name__ == "__main__":
    unittest.main()
