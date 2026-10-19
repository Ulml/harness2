# Copyright 2026 Google LLC
# Study-branch addition. Not part of the upstream release.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Transfer gates: Pareto floors, rebind, falsifiers, scoped retrieval."""

import unittest

from harness2.core.transfer import (
    contradicted,
    pareto_front,
    rebind,
    replication_ok,
    scope_lessons,
    transfer_block,
    unbound_slots,
)


def _lesson(**extra):
    base = {
        "cue": "When a seasonal efficiency ratio is given",
        "lesson": "Divide output energy by the seasonal ratio before pricing it.",
        "evidence": "The contrast reproduced on a second subject with different hours.",
        "falsifier": "A second subject whose billed energy matches output times hours, not output over SEER.",
        "objectives": {
            "functionality": 0.8,
            "integrity": 0.9,
            "transfer": 0.8,
            "non_regression": 0.7,
        },
    }
    base.update(extra)
    return base


class TransferTests(unittest.TestCase):
    def test_reproduced_lesson_with_falsifier_passes(self):
        self.assertEqual(transfer_block(_lesson()), [])
        self.assertTrue(replication_ok(_lesson()["evidence"]))

    def test_missing_falsifier_blocks(self):
        reasons = transfer_block(_lesson(falsifier=""))
        self.assertIn("lesson has no falsifier", reasons)

    def test_single_noisy_contrast_blocks(self):
        reasons = transfer_block(_lesson(evidence="It looked better once."))
        self.assertIn("contrast was not reproduced", reasons)

    def test_integrity_is_not_traded_for_functionality(self):
        reasons = transfer_block(
            _lesson(objectives={"functionality": 0.99, "integrity": 0.1, "transfer": 0.9})
        )
        self.assertTrue(any(reason.startswith("integrity") for reason in reasons))

    def test_falsifier_demotes_a_later_contradiction(self):
        lesson = _lesson()
        observation = (
            "falsified: a second subject whose billed energy matches output times hours, "
            "not output over SEER"
        )
        self.assertTrue(contradicted(lesson, observation))
        self.assertFalse(contradicted(lesson, "The invoice arrived late."))

    def test_rebind_swaps_the_subject_and_leaves_holes_visible(self):
        intent = "Évaluer {{marque}} {{modele}} à {{seer}} pour {{heures}} h."
        filled = rebind(intent, {"marque": "Mitsubishi", "modele": "MSZ-AP35", "seer": "7,6"})
        self.assertIn("Mitsubishi", filled)
        self.assertNotIn("Bosch", filled)
        self.assertIn("{{heures}}", filled)
        self.assertEqual(unbound_slots(intent, {"marque": "Mitsubishi"}), ["modele", "seer", "heures"])

    def test_pareto_keeps_tradeoffs_and_the_floor_rejects_the_cheat(self):
        honest = {"name": "honest", "objectives": {"functionality": 0.6, "integrity": 0.9, "transfer": 0.8, "non_regression": 0.7}}
        cheat = {"name": "cheat", "objectives": {"functionality": 0.95, "integrity": 0.2, "transfer": 0.3, "non_regression": 0.4}}
        both = {"name": "both", "objectives": {"functionality": 0.7, "integrity": 0.9, "transfer": 0.85, "non_regression": 0.7}}
        names = [item["name"] for item in pareto_front([honest, cheat, both])]
        # The cheat is non-dominated on functionality. A weighted score would have hidden that.
        # The independent floor is what refuses it.
        self.assertCountEqual(names, ["cheat", "both"])
        reasons = transfer_block(_lesson(objectives=cheat["objectives"]))
        self.assertTrue(any(reason.startswith("integrity") for reason in reasons))
        self.assertTrue(any(reason.startswith("transfer") for reason in reasons))

    def test_scope_ignores_the_previous_brand(self):
        lessons = [
            {"cue": "Bosch badge layout", "lesson": "Copy the Bosch badge"},
            {"cue": "seasonal efficiency ratio", "lesson": "Divide output by the seasonal ratio"},
        ]
        ranked = scope_lessons(lessons, "Compute seasonal efficiency for a heat pump", ["Bosch"])
        self.assertEqual(ranked[0]["cue"], "seasonal efficiency ratio")


if __name__ == "__main__":
    unittest.main()
