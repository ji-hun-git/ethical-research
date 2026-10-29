"""The statistics checker and the research ledger. Standard library only: python -m unittest"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "ethical-research" / "scripts"))

import ledger  # noqa: E402
import stats_check  # noqa: E402


class Distributions(unittest.TestCase):
    """Critical values from standard tables, each at p = .05."""

    def test_critical_values(self):
        cases = [("t", 2.228, 10, None), ("t", 1.96, 100000, None), ("chi2", 3.841, 1, None),
                 ("chi2", 11.070, 5, None), ("F", 4.965, 1, 10), ("F", 3.354, 2, 27), ("z", 1.960, None, None)]
        for test, stat, df1, df2 in cases:
            with self.subTest(test=test, stat=stat):
                self.assertAlmostEqual(stats_check.p_value(test, stat, df1, df2), 0.05, places=3)

    def test_agrees_with_scipy(self):
        # values from scipy.stats (t.sf, f.sf, chi2.sf, norm.sf), computed once and pinned here
        cases = [("t", 2.2, 28, None, 3.622548e-02), ("t", 0.5, 40, None, 6.198147e-01), ("t", 8.0, 3, None, 4.076578e-03),
                 ("t", 1.2, 48, None, 2.360287e-01), ("t", 3.1, 1000, None, 1.989346e-03), ("F", 3.45, 2, 57, 3.851757e-02),
                 ("F", 0.8, 4, 120, 5.274822e-01), ("F", 25.0, 1, 10, 5.373336e-04), ("chi2", 3.84, 1, None, 5.004352e-02),
                 ("chi2", 50, 30, None, 1.240206e-02), ("chi2", 0.5, 5, None, 9.921233e-01),
                 ("chi2", 200, 150, None, 3.973186e-03), ("r", 0.3, 48, None, 3.428618e-02),
                 ("r", -0.45, 38, None, 3.574693e-03), ("z", 1.96, None, None, 4.999579e-02), ("z", 4.2, None, None, 2.669150e-05)]
        for test, stat, df1, df2, expected in cases:
            with self.subTest(test=test, stat=stat):
                got = stats_check.p_value(test, stat, df1, df2)
                self.assertLess(abs(got - expected) / expected, 1e-6)  # the pinned values carry seven digits

    def test_r_matches_its_t(self):
        r, df = 0.30, 48
        t = r * (df / (1 - r * r)) ** 0.5
        self.assertAlmostEqual(stats_check.p_value("r", r, df), stats_check.p_value("t", t, df), places=12)


class Scan(unittest.TestCase):
    def statuses(self, text):
        return [row["status"] for row in stats_check.scan(text)]

    def test_consistent_results_pass(self):
        text = ("t(28) = 2.20, p = .036; F(2, 57) = 3.45, p = .04; χ2(1, N = 100) = 3.84, p = .05; "
                "r(48) = .30, p = .03; z = 1.96, p = .05; t(40) = 0.50, ns.")
        self.assertEqual(self.statuses(text), ["consistent"] * 6)

    def test_rounding_of_the_statistic_is_allowed(self):
        # t = 2.0 could be anything from 1.95 to 2.05, so p = .056 is still possible
        self.assertEqual(self.statuses("t(20) = 2.0, p = .056"), ["consistent"])

    def test_a_wrong_p_is_inconsistent(self):
        self.assertEqual(self.statuses("t(28) = 2.20, p = .021"), ["inconsistent"])

    def test_a_flipped_decision_is_a_decision_error(self):
        self.assertEqual(self.statuses("t(28) = 1.20, p < .01"), ["decision error"])
        self.assertEqual(self.statuses("t(28) = 4.20, ns"), ["decision error"])

    def test_one_tailed_tests_are_recognised(self):
        self.assertEqual(self.statuses("A one-tailed test gave t(20) = 1.80, p = .04."), ["consistent"])
        self.assertEqual(self.statuses("The test gave t(20) = 1.80, p = .04."), ["decision error"])  # two-tailed p = .087

    def test_corrected_tests_are_left_to_a_person(self):
        self.assertEqual(self.statuses("After Bonferroni correction, t(28) = 2.20, p = .021."), ["check by hand"])
        self.assertEqual(self.statuses("R2(3) = 4.1, p = .02 and η2(1) = .30, p = .01"), [])  # not chi-square

    def test_unicode_minus_and_less_or_equal(self):
        self.assertEqual(self.statuses("t(28) = −2.20, p ≤ .04"), ["consistent"])

    def test_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            good, bad = Path(tmp, "good.txt"), Path(tmp, "bad.txt")
            good.write_text("t(28) = 2.20, p = .036", encoding="utf-8")
            bad.write_text("t(28) = 1.20, p < .01", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(stats_check.main([str(good)]), 0)
                self.assertEqual(stats_check.main([str(bad)]), 1)


class Grim(unittest.TestCase):
    def test_possible_and_impossible_means(self):
        self.assertEqual(stats_check.grim("3.48", 25)["status"], "consistent")    # 87 / 25
        self.assertEqual(stats_check.grim("3.47", 25)["status"], "inconsistent")  # no integer sum gives it
        self.assertEqual(stats_check.grim("5.19", 28)["status"], "inconsistent")

    def test_large_samples_are_not_testable(self):
        self.assertEqual(stats_check.grim("2.5", 200)["status"], "not testable")
        self.assertEqual(stats_check.grim("3.47", 25, 4)["status"], "not testable")


class Ledger(unittest.TestCase):
    def setUp(self):
        self.data = {"version": 1, "claims": [], "questions": []}

    def test_a_claim_without_evidence_owes_a_question(self):
        ledger.add_claim(self.data, "AI use lowers critical thinking")
        owed = ledger.owed(self.data)
        self.assertEqual(len(owed), 1)
        self.assertIn("no evidence", owed[0]["text"])

    def test_unchecked_evidence_still_owes_a_question(self):
        ledger.add_claim(self.data, "AI use lowers critical thinking")
        ledger.add_evidence(self.data, "C1", "Kim 2024", "unverified")
        self.assertIn("nobody has checked", ledger.owed(self.data)[0]["text"])
        ledger.add_evidence(self.data, "C1", "doi:10.1/x", "supports")
        self.assertEqual(ledger.owed(self.data), [])

    def test_contradicting_evidence_owes_a_question(self):
        ledger.add_claim(self.data, "X", strength="hedged")
        ledger.add_evidence(self.data, "C1", "doi:10.1/x", "contradicts")
        self.assertIn("contradicts", ledger.owed(self.data)[0]["text"])

    def test_assistant_claims_need_the_author(self):
        ledger.add_claim(self.data, "The effect is larger for novices", origin="assistant", strength="hedged")
        self.assertIn("came from the assistant", ledger.owed(self.data)[0]["text"])
        ledger.set_claim(self.data, "C1", "open", endorsed=True)
        self.assertEqual(ledger.owed(self.data), [])

    def test_accepted_risks_stop_coming_back(self):
        ledger.add_claim(self.data, "Single-school sample generalises")
        ledger.ask(self.data, "Does one school generalise?", about="C1")
        with self.assertRaises(ledger.LedgerError):
            ledger.accept(self.data, "Q1", " ")
        ledger.accept(self.data, "Q1", "stated as a limitation in section 5")
        ledger.accept(self.data, "C1", "kept as a hypothesis")
        status = ledger.status(self.data)
        self.assertEqual((status["open_questions"], status["owed_questions"], status["accepted"]), ([], [], 2))

    def test_session_start_puts_back_at_most_three_most_important_first(self):
        data = {"version": 1, "claims": [], "questions": []}
        for i in range(5):
            ledger.ask(data, f"Routine question {i}?", priority=3)
        ledger.ask(data, "The question that matters?", priority=1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "ledger.json")
            ledger.save(path, data)
            lines = ledger.session_start(path).splitlines()
        self.assertIn("The question that matters?", lines[1])
        self.assertEqual(sum(line.startswith("- Q") for line in lines), ledger.SESSION_ITEMS)
        self.assertIn("3 more", lines[-1])

    def test_supported_needs_supporting_evidence(self):
        ledger.add_claim(self.data, "X")
        with self.assertRaises(ledger.LedgerError):
            ledger.set_claim(self.data, "C1", "supported")
        ledger.add_evidence(self.data, "C1", "doi:10.1/x", "supports")
        self.assertEqual(ledger.set_claim(self.data, "C1", "supported")["status"], "supported")

    def test_questions_close_only_with_an_answer_or_a_reason(self):
        ledger.add_claim(self.data, "X")
        ledger.ask(self.data, "Why?", about="C1")
        with self.assertRaises(ledger.LedgerError):
            ledger.answer(self.data, "Q1", "  ")
        with self.assertRaises(ledger.LedgerError):
            ledger.withdraw(self.data, "Q1", "")
        with self.assertRaises(ledger.LedgerError):
            ledger.ask(self.data, "About a claim that does not exist", about="C9")
        ledger.answer(self.data, "Q1", "Because of the pilot data")
        self.assertEqual(ledger.status(self.data)["open_questions"], [])

    def test_session_start_is_silent_without_a_ledger_and_bounded_with_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, ".ethical-research", "ledger.json")
            self.assertEqual(ledger.session_start(path), "")
            data = {"version": 1, "claims": [], "questions": []}
            for i in range(200):
                ledger.ask(data, f"Question number {i} about the sampling frame and its limits?")
            ledger.save(path, data)
            text = ledger.session_start(path)
            self.assertTrue(text.startswith("Ethical Research ledger"))
            self.assertLessEqual(len(text), ledger.SESSION_LIMIT + 200)
            self.assertIn("do not answer them yourself", text)

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp, "ledger.json"))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(ledger.main(["--file", path, "init"]), 0)
                self.assertEqual(ledger.main(["--file", path, "claim", "X causes Y"]), 0)
                self.assertEqual(ledger.main(["--file", path, "ask", "Could Y cause X?", "--kind", "alternative",
                                              "--about", "C1"]), 0)
            out = io.StringIO()
            with redirect_stdout(out):
                ledger.main(["--file", path, "--json", "status"])
            status = json.loads(out.getvalue())
            self.assertEqual(len(status["open_questions"]), 1)
            self.assertEqual(len(status["owed_questions"]), 1)


if __name__ == "__main__":
    unittest.main()
